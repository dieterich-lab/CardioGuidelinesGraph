import fitz
import re, json
from cardio_graph_core.table_parsing.inspect_pdf_drawings import (
    get_drawing_rects_with_fill,
    get_matching_rect_for_block,
    is_header_fill,
    block_has_bold_text,
    looks_like_recommendation_body,
)

pdf_page_path = "/prj/doctoral_letters/guide/data/guidelines/pdf/pages/_63.pdf"

CLASS_LEVEL_PATTERN = re.compile(r"(IIa|IIb|III|II|I)(A|B|C)")
CLASS_LEVEL_AT_END_PATTERN = re.compile(
    r"^(.*?)(?:\s*)(IIa|IIb|III|II|I)(?:\s*)(A|B|C)\s*$",
    re.DOTALL,
)


def check_class_level_block(block):
    x0, y0, x1, y1, text, *_ = block
    text_clean = text.replace("\n", "").strip()
    return CLASS_LEVEL_PATTERN.search(text_clean) is not None


def extract_class_level(block):
    x0, y0, x1, y1, text, *_ = block
    text_clean = text.replace("\n", "").strip()

    m = CLASS_LEVEL_PATTERN.search(text_clean)
    if not m:
        return None, None

    return m.group(1), m.group(2)


def strip_class_level_from_block_text(block):
    """
    Remove trailing class/level marker from a class-level block while preserving
    the recommendation text contained in that same block.
    """
    x0, y0, x1, y1, text, *_ = block
    text_clean = re.sub(r"\s+", " ", text).strip()

    m = CLASS_LEVEL_AT_END_PATTERN.match(text_clean)
    if not m:
        return text_clean

    return m.group(1).strip()


def is_continued_block(block):
    """
    Detect footer-like continuation marker blocks such as:
        'Continued'
    """
    x0, y0, x1, y1, text, *_ = block
    text_clean = text.replace("\n", " ").strip()
    return text_clean == "Continued"


def parse_recommendation_blocks(page, debug=False):
    """
    Parse a guideline recommendation table in reading order and reconstruct
    recommendation entries.

    The parser maintains the currently active subheader and subsubheader while
    buffering ordinary recommendation text blocks. When a class/level block is
    encountered, it finalizes one recommendation record consisting of:

        {
            "recommendation": <full recommendation text>,
            "class": <recommendation class>,
            "level": <evidence level>,
            "subheader": <current subheader>,
            "subsubheader": <current subsubheader or None>,
        }

    Parsing logic per block:
    1. If block is a subheader:
       - replace current subheader
       - clear current subsubheader
       - clear pending recommendation text
    2. Else if block is a subsubheader:
       - replace current subsubheader
       - clear pending recommendation text
    3. Else if block is a class/level block:
       - combine buffered text with the current block text stripped of the
         trailing class/level marker
       - save a recommendation entry
       - clear pending recommendation text
    4. Else:
       - append block to pending recommendation text

    The function also detects whether the page contains a block with the exact
    text 'Continued' and returns this as a boolean flag.

    Returns:
        tuple[list[dict], bool]:
            - results: parsed recommendation entries
            - continued: True if a 'Continued' block was detected, else False
    """

    drawing_rects = get_drawing_rects_with_fill(page)
    blocks = page.get_text("blocks")

    current_subheader = None
    current_subsubheader = None
    pending_blocks = []
    continued = False

    results = []

    for i, block in enumerate(blocks):
        x0, y0, x1, y1, text, *_ = block
        text = text.strip()

        if not text:
            continue

        if is_continued_block(block):
            continued = True
            if debug:
                print(f"\nBLOCK {i} -> CONTINUED")
                print("text:", repr(text))
            continue

        block_rect = fitz.Rect(x0, y0, x1, y1)

        match = get_matching_rect_for_block(block, drawing_rects, min_overlap=0.10)

        header_fill_ok = False
        bold_ok = False
        recommendation_like = False

        if match is not None:
            header_fill_ok = is_header_fill(match["fill"])
            bold_ok, _ = block_has_bold_text(page, block_rect, debug=False)
            recommendation_like = looks_like_recommendation_body(text)

        is_subheader = header_fill_ok and bold_ok and not recommendation_like
        is_subsubheader = header_fill_ok and not is_subheader

        if is_subheader:
            current_subheader = text
            current_subsubheader = None
            pending_blocks = []

            if debug:
                print(f"\nBLOCK {i} -> SUBHEADER")
                print("text:", repr(text))
            continue

        if is_subsubheader:
            current_subsubheader = text
            pending_blocks = []

            if debug:
                print(f"\nBLOCK {i} -> SUBSUBHEADER")
                print("text:", repr(text))
            continue

        if check_class_level_block(block):
            rec_class, rec_level = extract_class_level(block)

            accumulated_text = " ".join(
                b[4].replace("\n", " ").strip() for b in pending_blocks
            ).strip()

            current_text_without_class_level = strip_class_level_from_block_text(block)

            if accumulated_text and current_text_without_class_level:
                recommendation_text = (
                    f"{accumulated_text} {current_text_without_class_level}".strip()
                )
            elif accumulated_text:
                recommendation_text = accumulated_text
            else:
                recommendation_text = current_text_without_class_level

            results.append(
                {
                    "recommendation": recommendation_text,
                    "class": rec_class,
                    "level": rec_level,
                    "subheader": current_subheader,
                    "subsubheader": current_subsubheader,
                }
            )

            if debug:
                print(f"\nBLOCK {i} -> CLASS/LEVEL")
                print("text:", repr(text))
                print(
                    "text_without_class_level:", repr(current_text_without_class_level)
                )
                print("recommendation:", repr(recommendation_text))
                print("class:", rec_class)
                print("level:", rec_level)
                print("subheader:", repr(current_subheader))
                print("subsubheader:", repr(current_subsubheader))

            pending_blocks = []
            continue

        pending_blocks.append(block)

        if debug:
            print(f"\nBLOCK {i} -> TEXT")
            print("text:", repr(text))

    return results, continued


def results_to_json(
    results,
    source_file,
    table_header,
    table_id=0,
    caption=None,
    include_subheader_field=True,
):
    """
    Convert parsed recommendation results into the target JSON structure.

    Mapping:
    - Table Header   <- table_header
    - Section Header <- parsed item["subheader"]
    - Subheader      <- parsed item["subsubheader"]   (if present)
    - Recommendations<- parsed item["recommendation"]
    - Class a        <- parsed item["class"]
    - Level b        <- parsed item["level"]
    """
    if caption is None:
        caption = []

    data = []

    for item in results:
        row = {
            "Table Header": table_header,
            "Section Header": item.get("subheader"),
            "Subheader": item.get("subsubheader"),
            "Recommendations": item.get("recommendation", ""),
            "Class a": item.get("class", ""),
            "Level b": item.get("level", ""),
        }
        data.append(row)

    output = {
        "source_file": source_file,
        "total_tables": 1,
        "tables": [
            {
                "table_id": table_id,
                "source_file": source_file,
                "caption": caption,
                "data": data,
            }
        ],
    }

    return output


def get_table_header(page, debug=False):
    """
    Return the table header from the page.

    Heuristic:
    - iterate blocks in reading order
    - find the first block that is a subheader
    - the table header is assumed to be the closest non-empty text block
      immediately before that first subheader

    This matches pages where the structure is:
        [table header]
        [first section header / subheader]
        [recommendation rows...]

    Returns:
        str | None
    """
    drawing_rects = get_drawing_rects_with_fill(page)
    blocks = page.get_text("blocks")

    prev_text_block = None

    for i, block in enumerate(blocks):
        x0, y0, x1, y1, text, *_ = block
        text = text.strip()

        if not text:
            continue

        block_rect = fitz.Rect(x0, y0, x1, y1)

        match = get_matching_rect_for_block(block, drawing_rects, min_overlap=0.10)

        header_fill_ok = False
        bold_ok = False
        recommendation_like = False

        if match is not None:
            header_fill_ok = is_header_fill(match["fill"])
            bold_ok, _ = block_has_bold_text(page, block_rect, debug=False)
            recommendation_like = looks_like_recommendation_body(text)

        is_subheader = header_fill_ok and bold_ok and not recommendation_like

        if debug:
            print(f"\nBLOCK {i}")
            print("text:", repr(text))
            print("is_subheader:", is_subheader)
            print("prev_text_block:", repr(prev_text_block))

        if is_subheader:
            if debug:
                print("\n-> FIRST SUBHEADER FOUND")
                print("subheader:", repr(text))
                print("table_header:", repr(prev_text_block))
            return prev_text_block

        prev_text_block = text

    return None


def page_to_json_table(pdf_page_path, debug=False):

    doc = fitz.open(pdf_page_path)
    page = doc[0]

    # debug_blocks(page)
    table_header = get_table_header(page, debug)
    results, continued = parse_recommendation_blocks(page, debug)
    print("\nContinued on next page:", continued)
    print("\n===== FINAL OUTPUT =====")
    for r in results:
        print(r)
    final_json = results_to_json(
        results,
        source_file=pdf_page_path,
        table_header=table_header,
        table_id=0,
        caption=None,
        include_subheader_field=True,
    )
    return final_json


if __name__ == "__main__":

    doc = fitz.open(pdf_page_path)
    page = doc[0]

    # debug_blocks(page)
    table_header = get_table_header(page, debug=True)
    results, continued = parse_recommendation_blocks(page, debug=True)
    print("\nContinued on next page:", continued)
    print("\n===== FINAL OUTPUT =====")
    for r in results:
        print(r)
    final = results_to_json(
        results,
        source_file=pdf_page_path,
        table_header=table_header,
        table_id=0,
        caption=None,
        include_subheader_field=True,
    )
    print(json.dumps(final, indent=4, ensure_ascii=False))
