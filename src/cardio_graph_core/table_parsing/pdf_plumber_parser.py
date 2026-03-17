import fitz
import re, json
from pathlib import Path
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
CLASS_LEVEL_ONLY_PATTERN = re.compile(
    r"^\s*(IIa|IIb|III|II|I)\s*([ABC])\s*$",
    re.DOTALL,
)

CLASS_LEVEL_AT_END_PATTERN = re.compile(
    r"^(.*?)(?:\s+|\n+)(IIa|IIb|III|II|I)\s*([ABC])\s*$",
    re.DOTALL,
)


REC_TABLE_HEADERS_JSON = (
    "/prj/doctoral_letters/guide/data/parsing_tables/rec_table_headers.json"
)


def normalize_table_header_text(text: str) -> str:
    """
    Normalize PDF header text and JSON header text so they can be matched robustly.
    """
    if not text:
        return ""

    text = text.replace("\n", " ")
    text = text.replace("—", "-")
    text = text.replace("–", "-")
    text = text.replace("−", "-")
    text = text.replace("­", "")  # soft hyphen
    text = re.sub(r"\s*-\s*", " - ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # normalize known OCR-ish / PDF variants
    text = text.replace("Recommendation Table", "Recommendation Table")
    text = text.replace(" -Recommendations", " - Recommendations")
    text = text.replace("-Recommendations", "- Recommendations")
    text = text.replace("also Evidence", "also Evidence")

    return text


def extract_table_number(text: str):
    m = re.search(r"Recommendation Table\s+(\d+)", text)
    return int(m.group(1)) if m else None


def load_expected_table_headers(json_path=REC_TABLE_HEADERS_JSON):
    """
    Returns:
        headers_by_number: dict[int, dict]
        headers_by_page: dict[str, list[dict]]
    """
    with open(json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    headers_by_number = {}
    headers_by_page = {}

    for row in payload.get("data", []):
        raw_header = row.get("0", "").strip()
        raw_page = str(row.get("1", "")).strip()

        if not raw_header:
            continue

        norm_header = normalize_table_header_text(raw_header)
        table_no = extract_table_number(norm_header)

        item = {
            "raw_header": raw_header,
            "norm_header": norm_header,
            "page": raw_page,
            "table_no": table_no,
        }

        if table_no is not None:
            headers_by_number[table_no] = item

        headers_by_page.setdefault(raw_page, []).append(item)

    return headers_by_number, headers_by_page


def get_printed_page_number(page):
    """
    Extract printed journal/guideline page number from page text blocks.
    Example: '3496 ... ESC Guidelines' -> '3496'
    """
    blocks = page.get_text("blocks")

    for block in blocks:
        x0, y0, x1, y1, text, *_ = block
        text_clean = text.replace("\n", " ").strip()

        m = re.match(r"^(\d{3,5})\b", text_clean)
        if m and "ESC Guidelines" in text_clean:
            return m.group(1)

    return None


def normalize_class_level_text(text):
    """
    Normalize block text for class/level detection while preserving token boundaries.
    Important: do NOT remove all whitespace/newlines, otherwise ICA -> IC can falsely match.
    """
    text = text.replace("\u00ad", "")  # soft hyphen
    text = text.replace("­", "")
    text = text.replace("\xa0", " ")

    # normalize horizontal whitespace, preserve newlines as separators
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    return text.strip()


def check_class_level_block(block):
    x0, y0, x1, y1, text, *_ = block
    text_norm = normalize_class_level_text(text)

    return (
        CLASS_LEVEL_ONLY_PATTERN.match(text_norm) is not None
        or CLASS_LEVEL_AT_END_PATTERN.match(text_norm) is not None
    )


def extract_class_level(block):
    x0, y0, x1, y1, text, *_ = block
    text_norm = normalize_class_level_text(text)

    m = CLASS_LEVEL_ONLY_PATTERN.match(text_norm)
    if m:
        return m.group(1), m.group(2)

    m = CLASS_LEVEL_AT_END_PATTERN.match(text_norm)
    if m:
        return m.group(2), m.group(3)

    return None, None


def strip_class_level_from_block_text(block):
    """
    Remove trailing class/level marker only if it appears as a proper suffix
    at the end of the block, not as part of a word like ICA.
    """
    x0, y0, x1, y1, text, *_ = block
    text_norm = normalize_class_level_text(text)

    m = CLASS_LEVEL_AT_END_PATTERN.match(text_norm)
    if not m:
        return clean_output_text(text_norm)

    return clean_output_text(m.group(1).strip())


def is_continued_block(block):
    """
    Detect footer-like continuation marker blocks such as:
        'Continued'
        'Continued.'
        'Continued on next page'
        'Table continued'
    """
    x0, y0, x1, y1, text, *_ = block
    text_clean = clean_output_text(text).lower()

    text_clean = text_clean.replace("—", "-").replace("–", "-")
    text_clean = re.sub(r"\s+", " ", text_clean).strip()

    return text_clean in {
        "continued",
        "continued.",
        "continued on next page",
        "table continued",
        "table continued.",
        "recommendation table continued",
        "recommendation table continued.",
    }


def is_noise_block(block):
    """
    Skip obvious page artifacts that are not table content.
    """
    x0, y0, x1, y1, text, *_ = block
    text_clean = text.replace("\n", " ").strip()

    if not text_clean:
        return True

    if text_clean == "© ESC 2024":
        return True

    if "Downloaded from " in text_clean:
        return True

    if text_clean.endswith("ESC Guidelines"):
        return True

    return False


def block_is_in_region(
    block, start_y=0, end_y=None, x_range=None, min_x_overlap_ratio=0.25
):
    """
    Robust region filter:
    - use block midpoint in y so overlap at the border does not leak text in
    - optionally restrict blocks to the table column via x_range
    """
    x0, y0, x1, y1, text, *_ = block

    mid_y = (y0 + y1) / 2.0
    if mid_y < start_y:
        return False
    if end_y is not None and mid_y >= end_y:
        return False

    if x_range is not None:
        rx0, rx1 = x_range
        overlap = max(0.0, min(x1, rx1) - max(x0, rx0))
        block_width = max(1.0, x1 - x0)
        if (overlap / block_width) < min_x_overlap_ratio:
            return False

    return True


def _short(text, limit=140):
    text = text.replace("\n", "\\n")
    return text if len(text) <= limit else text[:limit] + " ..."


def _print_block(prefix, i, block, start_y, end_y):
    x0, y0, x1, y1, text, *_ = block
    print(f"{prefix} BLOCK {i}")
    print(f"  bbox=({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})")
    print(f"  region=({start_y:.1f}, {end_y if end_y is not None else 'inf'})")
    print(f"  text={repr(_short(text.strip(), 220))}")


def parse_recommendation_blocks(page, start_y=0, end_y=None, x_range=None, debug=False):
    drawing_rects = get_drawing_rects_with_fill(page)
    blocks = page.get_text("blocks")

    current_subheader = None
    current_subsubheader = None
    pending_blocks = []
    continued = False
    results = []
    table_started = False

    if debug:
        print("\n================ PARSE REGION ================")
        print(
            f"start_y={start_y:.1f}, end_y={end_y if end_y is not None else 'inf'}, x_range={x_range}"
        )

    for i, block in enumerate(blocks):
        x0, y0, x1, y1, text, *_ = block
        raw_text = text
        text = text.strip()

        if not text:
            if debug:
                _print_block("SKIP EMPTY", i, block, start_y, end_y)
            continue

        if is_noise_block(block):
            if debug:
                _print_block("SKIP NOISE", i, block, start_y, end_y)
            continue

        if not block_is_in_region(block, start_y=start_y, end_y=end_y, x_range=x_range):
            if debug:
                label = "SKIP OUTSIDE REGION"
                _print_block(label, i, block, start_y, end_y)
            continue

        if debug:
            _print_block("VISIT", i, block, start_y, end_y)

        if is_continued_block(block):
            continued = True
            if debug:
                print("  ACTION: mark region as continued")
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
        is_class_level = check_class_level_block(block)

        if debug:
            print("  CLASSIFY:")
            print(f"    match_found={match is not None}")
            print(f"    header_fill_ok={header_fill_ok}")
            print(f"    bold_ok={bold_ok}")
            print(f"    recommendation_like={recommendation_like}")
            print(f"    is_subheader={is_subheader}")
            print(f"    is_subsubheader={is_subsubheader}")
            print(f"    is_class_level={is_class_level}")
            print(f"    current_subheader={repr(current_subheader)}")
            print(f"    current_subsubheader={repr(current_subsubheader)}")
            print(f"    table_started={table_started}")
            print(f"    pending_count_before={len(pending_blocks)}")

        if is_subheader:
            pending_blocks = []
            current_subsubheader = None
            table_started = True

            if is_table_column_header(text):
                current_subheader = None
                if debug:
                    print(
                        "  ACTION: detected table column header row, not semantic subheader"
                    )
                    print("  ACTION: set current_subheader=None")
                    print("  ACTION: reset current_subsubheader=None")
                    print("  ACTION: table_started=True")
            else:
                current_subheader = text
                if debug:
                    print(f"  ACTION: set current_subheader={repr(current_subheader)}")
                    print("  ACTION: reset current_subsubheader=None")
                    print("  ACTION: table_started=True")
            continue

        if is_subsubheader:
            if not table_started:
                # ignore decorative/header-like filled blocks before the actual table starts
                if debug:
                    print(
                        "  ACTION: ignore subsubheader-like block before table_started"
                    )
                continue

            current_subsubheader = text
            pending_blocks = []

            if debug:
                print(
                    f"  ACTION: set current_subsubheader={repr(current_subsubheader)}"
                )
            continue

        if is_class_level:
            # never emit a recommendation before the table has started
            if not table_started:
                if debug:
                    print("  ACTION: ignore class/level block before table_started")
                continue

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

            # do not emit empty garbage rows
            if not recommendation_text:
                pending_blocks = []
                if debug:
                    print("  ACTION: skip empty recommendation row")
                continue

            if debug:
                print("  ACTION: FLUSH pending_blocks into recommendation")
                print(f"    pending_count={len(pending_blocks)}")
                for j, pb in enumerate(pending_blocks):
                    print(f"    pending[{j}]={repr(_short(pb[4].strip(), 160))}")
                print(
                    f"    stripped_current={repr(_short(current_text_without_class_level, 200))}"
                )
                print(f"    recommendation={repr(_short(recommendation_text, 240))}")
                print(f"    class={rec_class}, level={rec_level}")

            results.append(
                {
                    "recommendation": recommendation_text,
                    "class": rec_class,
                    "level": rec_level,
                    "subheader": current_subheader,
                    "subsubheader": current_subsubheader,
                }
            )

            pending_blocks = []
            if debug:
                print("  ACTION: reset pending_blocks=[] after emitting recommendation")
            continue

        # Critical fix:
        # never buffer anything until the actual table body has started
        if not table_started:
            if debug:
                print("  ACTION: ignore block because table_started=False")
            continue

        pending_blocks.append(block)

        if debug:
            print("  ACTION: append block to pending_blocks")
            print(
                "  REASON: table_started=True and block is body text (not header / not class-level)"
            )
            if current_subsubheader is None:
                print("  NOTE: current_subsubheader is None")
            print(f"  pending_count_after={len(pending_blocks)}")

    if debug and pending_blocks:
        print("\nEND OF REGION: leftover pending_blocks")
        for j, pb in enumerate(pending_blocks):
            print(f"  pending[{j}]={repr(_short(pb[4].strip(), 160))}")

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

    The candidate is validated against rec_table_headers.json using normalized
    text and/or table number, optionally restricted by printed page number.
    """
    drawing_rects = get_drawing_rects_with_fill(page)
    blocks = page.get_text("blocks")

    expected_by_number, expected_by_page = load_expected_table_headers()
    printed_page_no = get_printed_page_number(page)
    expected_for_page = expected_by_page.get(str(printed_page_no), [])

    prev_block = None
    header_blocks = []

    for i, block in enumerate(blocks):
        x0, y0, x1, y1, text, *_ = block
        text = text.strip()

        if not text:
            continue

        if is_noise_block(block):
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

            basic_candidate = ptext.startswith("Recommendation Table")

            norm_ptext = normalize_table_header_text(ptext)
            table_no = extract_table_number(norm_ptext)

            matched_item = None

            if table_no is not None and table_no in expected_by_number:
                matched_item = expected_by_number[table_no]

            page_specific_match = any(
                norm_ptext == item["norm_header"] for item in expected_for_page
            )

            exact_match = (
                matched_item is not None and norm_ptext == matched_item["norm_header"]
            )
            table_number_match = matched_item is not None
            page_match = matched_item is not None and str(matched_item["page"]) == str(
                printed_page_no
            )

            valid_table_header = basic_candidate and (
                page_specific_match or exact_match or table_number_match
            )

            canonical_header = None
            if matched_item is not None:
                canonical_header = clean_output_text(matched_item["raw_header"])
            else:
                canonical_header = clean_output_text(norm_ptext)

            if debug:
                print(f"\nBLOCK {i}")
                print("subheader:", repr(text))
                print("prev_text_block:", repr(ptext))
                print("normalized_prev_text:", repr(norm_ptext))
                print("printed_page_no:", printed_page_no)
                print("table_no:", table_no)
                print("basic_candidate:", basic_candidate)
                print("exact_match:", exact_match)
                print("table_number_match:", table_number_match)
                print("page_match:", page_match)
                print("page_specific_match:", page_specific_match)
                print("valid_table_header:", valid_table_header)
                print("canonical_header:", repr(canonical_header))

            if valid_table_header:
                header_blocks.append(
                    {
                        "text": ptext,
                        "normalized_text": norm_ptext,
                        "canonical_text": canonical_header,
                        "table_no": table_no,
                        "printed_page_no": printed_page_no,
                        "block": prev_block,
                        "rect": fitz.Rect(px0, py0, px1, py1),
                    }
                )

        prev_block = block

    return header_blocks


def is_table_column_header(text):
    """
    Detect the standard table column header row like:
    'Recommendations Classa Levelb'
    """
    if not text:
        return False

    norm = clean_output_text(text).lower()
    norm = re.sub(r"\s+", " ", norm).strip()

    return norm in {
        "recommendations classa levelb",
        "recommendations class a level b",
    }


def parse_all_tables_on_page(
    page,
    continued=False,
    continued_table_header=None,
    debug=False,
):
    header_blocks = get_table_header_blocks(page, debug=debug)

    start_points = []

    if continued:
        start_points.append(
            {
                "kind": "page_start",
                "table_header": continued_table_header,
                "sort_y": 0.0,
                "start_y": 0.0,
                "x_range": None,
            }
        )

    for hb in header_blocks:
        header_rect = hb["rect"]

        start_points.append(
            {
                "kind": "header",
                "table_header": hb.get("canonical_text") or hb["text"],
                "sort_y": header_rect.y0,
                "start_y": header_rect.y1,
                "x_range": (header_rect.x0 - 10, header_rect.x1 + 40),
            }
        )

    start_points.sort(key=lambda x: x["sort_y"])

    deduped = []
    seen = set()
    for sp in start_points:
        key = (
            round(sp["sort_y"], 1),
            round(sp["start_y"], 1),
            sp["table_header"],
            sp["kind"],
        )
        if key not in seen:
            seen.add(key)
            deduped.append(sp)
    start_points = deduped

    if debug:
        print("\n================ TABLE START POINTS ================")
        for idx, sp in enumerate(start_points):
            print(
                f"[{idx}] kind={sp['kind']} "
                f"header={repr(sp['table_header'])} "
                f"sort_y={sp['sort_y']:.1f} "
                f"start_y={sp['start_y']:.1f} "
                f"x_range={sp.get('x_range')}"
            )

    tables = []
    continued_table_header_for_next_page = None

    for i, sp in enumerate(start_points):
        start_y = sp["start_y"]
        end_y = start_points[i + 1]["sort_y"] if i + 1 < len(start_points) else None
        x_range = sp.get("x_range")

        if debug:
            print("\n===== TABLE REGION =====")
            print("kind:", sp["kind"])
            print("table_header:", repr(sp["table_header"]))
            print("start_y:", start_y)
            print("end_y:", end_y)
            print("x_range:", x_range)

        results, region_continued = parse_recommendation_blocks(
            page,
            start_y=start_y,
            end_y=end_y,
            x_range=x_range,
            debug=debug,
        )

        active_header = sp["table_header"]

        if results:
            tables.append(
                {
                    "table_header": active_header,
                    "results": results,
                }
            )

        if region_continued:
            continued_table_header_for_next_page = active_header
            if debug:
                print(
                    "CONTINUED TABLE DETECTED:",
                    repr(continued_table_header_for_next_page),
                )

    return tables, continued_table_header_for_next_page


def results_to_json(
    parsed_tables,
    source_file,
    caption=None,
    include_subheader_field=True,
):
    """
    Convert parsed tables into the target JSON structure.
    """
    if caption is None:
        caption = []

    tables_json = []

    for table_id, table in enumerate(parsed_tables):
        table_header = clean_output_text(table.get("table_header"))
        results = table.get("results", [])

        data = []
        for item in results:
            row = {
                "Table Header": table_header,
                "Section Header": clean_output_text(item.get("subheader")),
                "Subheader": clean_output_text(item.get("subsubheader")),
                "Recommendations": clean_output_text(item.get("recommendation", "")),
                "Class a": clean_output_text(item.get("class", "")),
                "Level b": clean_output_text(item.get("level", "")),
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


def get_table_number_from_header(header_text):
    if not header_text:
        return None
    return extract_table_number(normalize_table_header_text(header_text))


def same_table(header_a, header_b):
    return get_table_number_from_header(header_a) == get_table_number_from_header(
        header_b
    )


def write_single_table_json(output_dir, table_no, table_header, results, source_file):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = results_to_json(
        [
            {
                "table_header": table_header,
                "results": results,
            }
        ],
        source_file=source_file,
        caption=None,
        include_subheader_field=True,
    )

    out_path = output_dir / f"rec_table_{table_no}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return str(out_path)


def clean_output_text(text):
    """
    Clean extracted text for final JSON output.
    """
    if text is None:
        return None

    text = str(text)

    # remove soft hyphen characters
    text = text.replace("\u00ad", "")
    text = text.replace("­", "")

    # flatten line breaks / tabs
    text = text.replace("\n", " ")
    text = text.replace("\t", " ")

    # normalize spaces
    text = re.sub(r"\s+", " ", text).strip()

    # normalize dash variants a bit for output consistency
    text = text.replace("—", "—")
    text = text.replace("–", "–")

    return text


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


def get_guideline_page_number_from_filename(
    pdf_path, file_offset=14, first_guideline_page=3428
):
    """
    Map page filename like '_82.pdf' to guideline page number like 3496.

    Formula:
        guideline_page = first_guideline_page + (file_index - file_offset)

    Example:
        _82.pdf -> 3428 + (82 - 14) = 3496
    """
    pdf_path = Path(pdf_path)
    stem = pdf_path.stem  # e.g. "_82"

    m = re.search(r"(\d+)$", stem)
    if not m:
        return None

    file_index = int(m.group(1))
    return first_guideline_page + (file_index - file_offset)


def parse_expected_recommendation_tables_from_page_dir(
    pages_dir,
    output_dir,
    headers_json_path=REC_TABLE_HEADERS_JSON,
    file_offset=14,
    first_guideline_page=3428,
    debug=False,
):
    """
    Parse single-page PDF files in pages_dir, detect recommendation tables, and
    save each table as rec_table_<NUMBER>.json.

    Supports continuation across pages:
    - if a table on page N has a continuation marker, page N+1 is parsed with
      continued=True even if page N+1 has no entry in rec_table_headers.json
    - rows from continuation pages are appended to the same output JSON
    """
    pages_dir = Path(pages_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    expected_by_number, expected_by_page = load_expected_table_headers(
        headers_json_path
    )

    def page_sort_key(pdf_path):
        stem = Path(pdf_path).stem
        m = re.search(r"(\d+)$", stem)
        return int(m.group(1)) if m else 10**9

    written_files = []
    in_progress_table = None
    # structure:
    # {
    #   "table_no": int,
    #   "table_header": str,
    #   "results": list,
    #   "source_file": str,
    # }

    page_files = sorted(pages_dir.glob("*.pdf"), key=page_sort_key)

    for page_pdf in page_files:
        if debug:
            print(f"\n================ PAGE FILE ================")
            print(page_pdf)

        guideline_page_no = get_guideline_page_number_from_filename(
            page_pdf,
            file_offset=file_offset,
            first_guideline_page=first_guideline_page,
        )

        expected_items = expected_by_page.get(str(guideline_page_no), [])
        expected_table_numbers = {
            item["table_no"]
            for item in expected_items
            if item.get("table_no") is not None
        }

        if debug:
            print("guideline_page_no_from_filename:", guideline_page_no)
            print("expected_table_numbers:", sorted(expected_table_numbers))
            print(
                "in_progress_table:",
                None if in_progress_table is None else in_progress_table["table_no"],
            )

        # Important:
        # Parse page if either:
        # - JSON says a table starts here, or
        # - previous page said a table continues here
        if not expected_table_numbers and in_progress_table is None:
            if debug:
                print("SKIP: no new table starts here and no continuation in progress")
            continue

        doc = fitz.open(str(page_pdf))
        if len(doc) == 0:
            doc.close()
            continue

        page = doc[0]

        parsed_tables, continued_table_header_for_next_page = parse_all_tables_on_page(
            page,
            continued=(in_progress_table is not None),
            continued_table_header=(
                in_progress_table["table_header"]
                if in_progress_table is not None
                else None
            ),
            debug=debug,
        )

        if debug:
            print(
                "continued_table_header_for_next_page:",
                repr(continued_table_header_for_next_page),
            )
            print("detected_tables:", len(parsed_tables))

        # ---------------------------------------------------------
        # Step 1: merge continuation at top of page into in_progress
        # ---------------------------------------------------------
        if in_progress_table is not None:
            if parsed_tables and same_table(
                parsed_tables[0].get("table_header"),
                in_progress_table.get("table_header"),
            ):
                if debug:
                    print(
                        "MERGE continuation into in_progress_table:",
                        in_progress_table["table_no"],
                    )

                in_progress_table["results"].extend(parsed_tables[0].get("results", []))
                parsed_tables = parsed_tables[1:]
            else:
                if debug:
                    print(
                        "WARNING: expected continuation table on this page but first parsed table did not match"
                    )

            # Does the same table continue again to the next page?
            if same_table(
                continued_table_header_for_next_page,
                in_progress_table.get("table_header"),
            ):
                if debug:
                    print(
                        "in_progress_table continues again:",
                        in_progress_table["table_no"],
                    )
            else:
                out_path = write_single_table_json(
                    output_dir=output_dir,
                    table_no=in_progress_table["table_no"],
                    table_header=in_progress_table["table_header"],
                    results=in_progress_table["results"],
                    source_file=in_progress_table["source_file"],
                )
                written_files.append(out_path)

                if debug:
                    print("WROTE completed continued table:", out_path)

                in_progress_table = None

        # ---------------------------------------------------------
        # Step 2: process all newly started tables on this page
        # ---------------------------------------------------------
        continued_table_no_for_next_page = get_table_number_from_header(
            continued_table_header_for_next_page
        )

        for table in parsed_tables:
            parsed_header = table.get("table_header")
            parsed_table_no = get_table_number_from_header(parsed_header)

            if debug:
                print("\n--- DETECTED TABLE ---")
                print("parsed_header:", repr(parsed_header))
                print("parsed_table_no:", parsed_table_no)

            if parsed_table_no is None:
                if debug:
                    print("SKIP: could not extract table number from parsed header")
                continue

            canonical_item = expected_by_number.get(parsed_table_no)
            canonical_header = (
                clean_output_text(canonical_item["raw_header"])
                if canonical_item is not None
                else clean_output_text(parsed_header)
            )

            # If this is the table marked as continued, keep it open
            if parsed_table_no == continued_table_no_for_next_page:
                in_progress_table = {
                    "table_no": parsed_table_no,
                    "table_header": canonical_header,
                    "results": list(table.get("results", [])),
                    "source_file": str(page_pdf),
                }

                if debug:
                    print("OPEN in_progress_table:", parsed_table_no)
            else:
                out_path = write_single_table_json(
                    output_dir=output_dir,
                    table_no=parsed_table_no,
                    table_header=canonical_header,
                    results=table.get("results", []),
                    source_file=str(page_pdf),
                )
                written_files.append(out_path)

                if debug:
                    print("WROTE complete table:", out_path)

        doc.close()

    # ---------------------------------------------------------
    # Step 3: flush anything still open after last page
    # ---------------------------------------------------------
    if in_progress_table is not None:
        out_path = write_single_table_json(
            output_dir=output_dir,
            table_no=in_progress_table["table_no"],
            table_header=in_progress_table["table_header"],
            results=in_progress_table["results"],
            source_file=in_progress_table["source_file"],
        )
        written_files.append(out_path)

        if debug:
            print("WROTE final in_progress_table at end:", out_path)

    return written_files


if __name__ == "__main__":
    # doc = fitz.open(pdf_page_path)
    # page = doc[0]

    # json_out = page_to_json_table(
    #     pdf_page_path,
    #     continued=False,
    #     debug=True,
    # )

    # print("\n===== FINAL JSON OUTPUT =====")
    # print(json.dumps(json_out, indent=2))
    written = parse_expected_recommendation_tables_from_page_dir(
        pages_dir="/prj/doctoral_letters/guide/data/guidelines/pdf/pages",
        output_dir="//prj/doctoral_letters/guide/data/parsing_tables/rec_tables",
        headers_json_path="/prj/doctoral_letters/guide/data/parsing_tables/rec_table_headers.json",
        debug=True,
    )

    print("\n===== WRITTEN FILES =====")
    for p in written:
        print(p)
