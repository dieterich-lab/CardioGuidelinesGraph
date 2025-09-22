import re
from pathlib import Path
import numpy as np
import tiktoken
from cardio_graph.extraction_utils.parse_structures_from_markdown_or_pdfs import (
    process_single_markdown,
)

# -------- Settings --------
INPUT_DIR = Path(
    "/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/docling_md_copy"
)
TABLE_DIR = Path(
    "/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/chunks/table_chunks"
)
TEXT_DIR = Path(
    "/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/chunks/text_chunks"
)
MODEL = "gpt-3.5-turbo"  # reference for tiktoken token counting
MAX_TOKENS = 500  # optional, for grouping paragraphs
OVERLAP = 50
# --------------------------

TABLE_DIR.mkdir(parents=True, exist_ok=True)

TEXT_DIR.mkdir(parents=True, exist_ok=True)


def count_tokens(text: str, model: str = MODEL) -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def remove_tables(md_text: str) -> str:
    """Remove Markdown tables (lines starting with '|' and their separators)."""
    lines = md_text.splitlines()
    clean_lines = []
    inside_table = False

    for line in lines:
        if line.strip().startswith("|"):
            inside_table = True
            continue
        if inside_table and re.match(r"^\s*\|?[-: ]+\|[-:| ]*$", line):
            continue
        else:
            inside_table = False
            clean_lines.append(line)
    return "\n".join(clean_lines)


def split_markdown_sections(md_text: str):
    """Split markdown into (heading, content) by headings."""
    sections = []
    current_heading = "INTRO"
    buffer = []

    lines = md_text.splitlines()
    for line in lines:
        if re.match(r"^#{1,6}\s+", line):  # heading line
            if buffer:
                sections.append((current_heading, "\n".join(buffer).strip()))
                buffer = []
            current_heading = line.strip()
        else:
            buffer.append(line)
    if buffer:
        sections.append((current_heading, "\n".join(buffer).strip()))
    return sections


def split_paragraphs(text: str):
    return [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]


def chunk_markdown(md_text: str, max_tokens: int = MAX_TOKENS, overlap: int = OVERLAP):
    """
    Hybrid chunker: split by headings, then paragraphs.
    Paragraphs are never split further, even if they exceed max_tokens.
    """
    md_text = remove_tables(md_text)
    sections = split_markdown_sections(md_text)
    enc = tiktoken.encoding_for_model(MODEL)
    chunks = []

    for heading, content in sections:
        paragraphs = split_paragraphs(content)
        buffer, buffer_tokens = [], 0

        for para in paragraphs:
            t_len = count_tokens(para)
            if buffer_tokens + t_len > max_tokens and buffer:
                # flush buffer
                chunks.append((heading, " ".join(buffer)))
                buffer, buffer_tokens = [], 0
            buffer.append(para)
            buffer_tokens += t_len

        if buffer:
            chunks.append((heading, " ".join(buffer)))

    # add overlap
    final_chunks = []
    for i, (heading, text) in enumerate(chunks):
        tokens = enc.encode(text)
        if i > 0 and overlap > 0:
            prev_tokens = enc.encode(chunks[i - 1][1])
            overlap_tokens = prev_tokens[-overlap:]
            text = enc.decode(overlap_tokens + tokens)
        final_chunks.append((heading, text))

    return final_chunks


def extract_table_name(text: str, fallback_idx: int) -> str:
    """Extract table number/name for filename."""
    # Look for 'Recommendation Table 20', 'Recommendation Table 8', etc.
    match = re.search(r"(Recommendation\s*Table\s*\d+)", text, re.IGNORECASE)
    if match:
        return match.group(1).replace(" ", "_") + ".md"
    # Otherwise generic fallback
    return f"Table_{fallback_idx}.md"


def analyze_md_folder(md_dir: Path):
    """Parse all .md files in a folder, count tokens for non-table paragraphs, save tables & text separately."""
    lengths = []
    table_counter = 1
    text_counter = 1

    for md_file in sorted(md_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        paragraphs = split_paragraphs(text)

        for p in paragraphs:
            if p.startswith("|") and "\n|---" in p:
                # Save table to file
                fname = extract_table_name(text, table_counter)
                out_file = TABLE_DIR / fname
                out_file.write_text(p, encoding="utf-8")
                print(f"Saved table -> {out_file}")
                table_counter += 1
            else:
                # Save paragraph to text_chunks
                fname = f"Paragraph_{text_counter}.md"
                out_file = TEXT_DIR / fname
                out_file.write_text(p, encoding="utf-8")
                print(f"Saved paragraph -> {out_file}")
                text_counter += 1

                # Count tokens
                lengths.append(count_tokens(p))

    return lengths


def find_table_headers(md_text: str):
    """
    Find full multi-line table headers like:
    Recommendation Table 1 **— Recommendations for ...**
    **continuation line**
    **continuation line**
    Stop before the first |--- style table row.
    """
    headers = []
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect start of a table header
        if re.match(
            r"^(Recommendation\s*Table\s*\d+\s+\*\*.*|Table\s*\d+\s+\*\*.*)",
            line,
            re.IGNORECASE,
        ):
            header_block = [line]
            i += 1

            # Collect continuation lines that are also bold (**...**), but not table rows
            while i < len(lines):
                nxt = lines[i].strip()
                if nxt.startswith("|"):  # table starts
                    break
                if (
                    nxt.startswith("**")
                    and nxt.endswith("**")
                    or nxt.startswith("**")
                    or nxt.endswith("**")
                ):
                    header_block.append(nxt)
                    i += 1
                elif nxt == "":
                    i += 1  # skip blank lines inside header
                else:
                    break

            headers.append("\n".join(header_block))
        else:
            i += 1
    return headers


def find_table_headers_with_next_section(md_text: str):
    """
    Find table headers and also the next section/subsection header.
    """
    results = []
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect start of a Recommendation Table or Table
        if re.match(
            r"^(Recommendation\s*Table\s*\d+\s+\*\*.*|Table\s*\d+\s+\*\*.*)",
            line,
            re.IGNORECASE,
        ):
            # Capture full header block
            header_block = [line]
            i += 1
            while i < len(lines):
                nxt = lines[i].strip()
                if nxt.startswith("|"):  # stop before table content
                    break
                if (
                    (nxt.startswith("**") and nxt.endswith("**"))
                    or nxt.startswith("**")
                    or nxt.endswith("**")
                ):
                    header_block.append(nxt)
                    i += 1
                elif nxt == "":
                    i += 1
                else:
                    break

            table_header = "\n".join(header_block)

            # Now search forward for next section/subsection header
            next_header = None
            j = i
            while j < len(lines):
                candidate = lines[j].strip()
                # small italic header like _3.1.2.2. ..._
                if re.match(r"^_[0-9]+\.[0-9.]*\s+.*_$", candidate):
                    next_header = candidate
                    break
                # bold section header like **3.2. ...**
                if re.match(r"^\*\*[0-9]+\.[0-9.]*\s+.*\*\*$", candidate):
                    next_header = candidate
                    break
                j += 1

            results.append((table_header, next_header))
        else:
            i += 1
    return results


def process_md_folder(md_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    counter = 1
    for md_file in sorted(md_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        chunks = chunk_markdown(text, max_tokens=MAX_TOKENS, overlap=OVERLAP)
        for heading, chunk in chunks:
            fname = f"Paragraph_{counter}.md"
            out_path = out_dir / fname
            out_path.write_text(chunk, encoding="utf-8")
            print(f"Saved -> {out_path}")
            counter += 1


if __name__ == "__main__":
    print(f"Processing Markdown files in {INPUT_DIR}")
    process_md_folder(INPUT_DIR, TEXT_DIR)
