import fitz
import re, json
from cardio_graph_core.table_parsing.inspect_pdf_drawings import (
    get_drawing_rects_with_fill,
    get_matching_rect_for_block,
    is_header_fill,
    block_has_bold_text,
    looks_like_recommendation_body,
)

pdf_page_path = "/prj/doctoral_letters/guide/data/guidelines/pdf/pages/_82.pdf"

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


def parse_recommendation_blocks(page, start_y=0, end_y=None, debug=False):
    """
    Parse recommendation blocks in reading order within a vertical region of the page.

    Args:
        page: fitz.Page
        start_y: start parsing from this y-position (inclusive)
        end_y: stop parsing at this y-position (exclusive). If None, parse to page end.
        debug: bool

    Returns:
        tuple[list[dict], bool]:
            - results: parsed recommendation entries
            - continued: True if a 'Continued' block was detected in this region
    """
    drawing_rects = get_drawing_rects_with_fill(page)
    blocks = page.get_text("blocks")

    if end_y is None:
        end_y = float("inf")

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

        # Only parse blocks inside the requested vertical slice
        if y1 <= start_y:
            continue
        if y0 >= end_y:
            continue

        if is_continued_block(block):
            continued = True
            if debug:
                print(f"\nBLOCK {i} -> CONTINUED")
                print("text:", repr(text))
                print("region:", (start_y, end_y))
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
                print("region:", (start_y, end_y))
            continue

        if is_subsubheader:
            current_subsubheader = text
            pending_blocks = []

            if debug:
                print(f"\nBLOCK {i} -> SUBSUBHEADER")
                print("text:", repr(text))
                print("region:", (start_y, end_y))
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
                print("region:", (start_y, end_y))

            pending_blocks = []
            continue

        pending_blocks.append(block)

        if debug:
            print(f"\nBLOCK {i} -> TEXT")
            print("text:", repr(text))
            print("region:", (start_y, end_y))

    return results, continued


def get_table_headers(page, debug=False):
    return [h["text"] for h in get_table_header_blocks(page, debug=debug)]


def get_table_header(page, debug=False):
    headers = get_table_headers(page, debug=debug)
    return headers[0] if headers else None


def get_table_header_blocks(page, debug=False):
    """
    Return all detected table header blocks with coordinates.

    A table header is the closest non-empty text block immediately before a
    subheader block, and must start with 'Recommendation Table'.

    Returns:
        list[dict] with keys:
            - text: str
            - block: original PyMuPDF block tuple
            - rect: fitz.Rect
    """
    drawing_rects = get_drawing_rects_with_fill(page)
    blocks = page.get_text("blocks")

    prev_block = None
    header_blocks = []

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

        if prev_block is not None and is_subheader:
            px0, py0, px1, py1, ptext, *_ = prev_block
            ptext = ptext.strip()

            valid_table_header = ptext.startswith("Recommendation Table")

            if debug:
                print(f"\nBLOCK {i}")
                print("subheader:", repr(text))
                print("prev_text_block:", repr(ptext))
                print("valid_table_header:", valid_table_header)

            if valid_table_header:
                header_blocks.append(
                    {
                        "text": ptext,
                        "block": prev_block,
                        "rect": fitz.Rect(px0, py0, px1, py1),
                    }
                )

        prev_block = block

    return header_blocks


def parse_all_tables_on_page(page, continued=False, debug=False):
    """
    Parse all recommendation tables on a page.

    Rules:
    - If continued=False:
        parse starting at each detected table header.
    - If continued=True:
        parse the first table from the top of the page (y=0),
        then parse any later tables starting at their detected headers.

    Returns:
        list[dict], bool

        tables = [
            {
                "table_header": <str | None>,
                "results": <list[dict]>,
            },
            ...
        ]

        page_continued = True if any parsed region contains a 'Continued' marker.
    """
    header_blocks = get_table_header_blocks(page, debug=debug)

    start_points = []

    if continued:
        start_points.append(
            {
                "kind": "page_start",
                "table_header": None,
                "y0": 0,
            }
        )

    for hb in header_blocks:
        start_points.append(
            {
                "kind": "header",
                "table_header": hb["text"],
                "y0": hb["rect"].y0,
            }
        )

    start_points.sort(key=lambda x: x["y0"])

    # Deduplicate exact same start positions if necessary
    deduped = []
    seen = set()
    for sp in start_points:
        key = (round(sp["y0"], 1), sp["table_header"], sp["kind"])
        if key not in seen:
            seen.add(key)
            deduped.append(sp)
    start_points = deduped

    tables = []
    page_continued = False

    for i, sp in enumerate(start_points):
        start_y = sp["y0"]
        end_y = start_points[i + 1]["y0"] if i + 1 < len(start_points) else None

        if debug:
            print("\n===== TABLE REGION =====")
            print("kind:", sp["kind"])
            print("table_header:", repr(sp["table_header"]))
            print("start_y:", start_y)
            print("end_y:", end_y)

        results, region_continued = parse_recommendation_blocks(
            page,
            start_y=start_y,
            end_y=end_y,
            debug=debug,
        )

        page_continued = page_continued or region_continued

        # Skip empty parses
        if results:
            tables.append(
                {
                    "table_header": sp["table_header"],
                    "results": results,
                }
            )

    return tables, page_continued


def results_to_json(
    parsed_tables,
    source_file,
    caption=None,
    include_subheader_field=True,
):
    """
    Convert parsed tables into the target JSON structure.

    Args:
        parsed_tables: list[dict]
            [
                {
                    "table_header": <str | None>,
                    "results": <list[dict]>
                },
                ...
            ]
    """
    if caption is None:
        caption = []

    tables_json = []

    for table_id, table in enumerate(parsed_tables):
        table_header = table.get("table_header")
        results = table.get("results", [])

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

        tables_json.append(
            {
                "table_id": table_id,
                "source_file": source_file,
                "caption": caption,
                "data": data,
            }
        )

    output = {
        "source_file": source_file,
        "total_tables": len(tables_json),
        "tables": tables_json,
    }

    return output


def page_to_json_table(pdf_page_path, continued=False, debug=False):
    doc = fitz.open(pdf_page_path)
    page = doc[0]

    parsed_tables, page_continued = parse_all_tables_on_page(
        page,
        continued=continued,
        debug=debug,
    )

    print("\nContinued on next page:", page_continued)
    print("\n===== FINAL OUTPUT =====")
    for t in parsed_tables:
        print("\n--- TABLE ---")
        print("header:", repr(t["table_header"]))
        for r in t["results"]:
            print(r)

    final_json = results_to_json(
        parsed_tables,
        source_file=pdf_page_path,
        caption=None,
        include_subheader_field=True,
    )
    return final_json


if __name__ == "__main__":
    doc = fitz.open(pdf_page_path)
    page = doc[0]

    header_blocks = get_table_header_blocks(page, debug=True)

    print("\n===== TABLE HEADERS =====")
    for hb in header_blocks:
        print(repr(hb["text"]), hb["rect"])

    json_out = page_to_json_table(
        pdf_page_path,
        continued=False,  # set True when this page continues a table from previous page
        debug=True,
    )

    print("\n===== FINAL JSON OUTPUT =====")
    print(json.dumps(json_out, indent=2))
