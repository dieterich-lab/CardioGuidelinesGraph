import fitz

pdf_page_path = "/prj/doctoral_letters/guide/data/guidelines/pdf/pages/_62.pdf"


# --------------------------------------------------
# color helpers
# --------------------------------------------------


def avg_rgb(fill):
    if not fill or len(fill) != 3:
        return None
    return sum(fill) / 3.0


def rgb_spread(fill):
    if not fill or len(fill) != 3:
        return None
    return max(fill) - min(fill)


def is_header_fill(fill, avg_min=0.76, avg_max=0.82, max_spread=0.03, debug=False):
    """
    Detect the medium-grey header bars that correspond to subheaders.
    Tuned from observed values:
      header    ~ 0.7833
      body row  ~ 0.9333
    """
    if not fill or len(fill) != 3:
        return False

    avg = avg_rgb(fill)
    spread = rgb_spread(fill)

    ok = (avg_min <= avg <= avg_max) and (spread <= max_spread)

    if debug:
        print(
            f"is_header_fill: fill={fill}, avg={avg:.4f}, spread={spread:.4f}, ok={ok}"
        )

    return ok


# --------------------------------------------------
# geometry helpers
# --------------------------------------------------


def rect_overlap_ratio(a, b):
    inter = a & b
    if inter.is_empty:
        return 0.0

    ia = inter.get_area()
    aa = a.get_area()
    ba = b.get_area()
    denom = min(aa, ba)

    if denom == 0:
        return 0.0

    return ia / denom


def rect_contains(inner, outer, tol=2.0):
    return (
        inner.x0 >= outer.x0 - tol
        and inner.y0 >= outer.y0 - tol
        and inner.x1 <= outer.x1 + tol
        and inner.y1 <= outer.y1 + tol
    )


# --------------------------------------------------
# text helpers
# --------------------------------------------------


def is_bold_span(span):
    font = (span.get("font") or "").lower()
    flags = span.get("flags", 0)
    text = span.get("text", "")

    reasons = []

    if "bold" in font:
        reasons.append("font-name")
    if flags & 16:
        reasons.append("flag16")
    if any(k in font for k in ["black", "heavy", "semibold", "demi"]):
        reasons.append("font-weight-name")

    # keep this only as a weak fallback
    stripped = text.strip()
    if stripped and stripped.upper() == stripped and any(c.isalpha() for c in stripped):
        reasons.append("all-caps")

    return len(reasons) > 0, reasons


def block_has_bold_text(page, block_rect, overlap_threshold=0.15, debug=False):
    """
    Inspect spans overlapping the block and decide whether there is bold text.
    """
    text_dict = page.get_text("dict")

    bold_found = False
    matched_spans = []

    for block in text_dict["blocks"]:
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "")
                if not text or not text.strip():
                    continue

                span_rect = fitz.Rect(span["bbox"])
                inside = rect_contains(span_rect, block_rect, tol=2.0)
                overlap = rect_overlap_ratio(span_rect, block_rect)

                if inside or overlap >= overlap_threshold:
                    bold, reasons = is_bold_span(span)
                    matched_spans.append(
                        {
                            "text": text,
                            "rect": span_rect,
                            "font": span.get("font", ""),
                            "flags": span.get("flags", 0),
                            "size": span.get("size", 0),
                            "bold": bold,
                            "reasons": reasons,
                        }
                    )
                    if bold:
                        bold_found = True

    if debug:
        print("\n  SPANS FOR BLOCK")
        for sp in matched_spans:
            print(
                f"   text={repr(sp['text'])} "
                f"font={sp['font']} flags={sp['flags']} size={sp['size']} "
                f"bold={sp['bold']} reasons={sp['reasons']}"
            )

    return bold_found, matched_spans


# --------------------------------------------------
# rect matching
# --------------------------------------------------


def get_drawing_rects_with_fill(page):
    rects = []

    for i, d in enumerate(page.get_drawings()):
        rect = d.get("rect")
        fill = d.get("fill")

        if not rect:
            continue

        rects.append(
            {
                "drawing_index": i,
                "rect": rect,
                "fill": fill,
                "avg_grey": avg_rgb(fill),
                "spread": rgb_spread(fill),
                "type": d.get("type"),
            }
        )

    return rects


def get_matching_rect_for_block(block, drawing_rects, min_overlap=0.10):
    bx0, by0, bx1, by1 = block[:4]
    block_rect = fitz.Rect(bx0, by0, bx1, by1)

    best = None
    best_score = -1.0

    for dr in drawing_rects:
        rect = dr["rect"]
        contains = rect_contains(block_rect, rect, tol=2.0)
        overlap = rect_overlap_ratio(block_rect, rect)

        score = 10.0 + overlap if contains else overlap

        if overlap >= min_overlap or contains:
            if score > best_score:
                best_score = score
                best = {
                    **dr,
                    "contains": contains,
                    "overlap": overlap,
                    "block_rect": block_rect,
                }

    return best


# --------------------------------------------------
# optional text-shape filter
# --------------------------------------------------


def looks_like_recommendation_body(text):
    """
    Optional rejection rule:
    recommendation rows often start with bullet and are longer.
    """
    stripped = text.strip()
    return stripped.startswith("•")


# --------------------------------------------------
# main classifier
# --------------------------------------------------


def classify_blocks_as_subheaders(page, debug=True):
    drawing_rects = get_drawing_rects_with_fill(page)
    blocks = page.get_text("blocks")

    results = []

    for i, block in enumerate(blocks):
        text = block[4]
        block_rect = fitz.Rect(block[:4])

        match = get_matching_rect_for_block(block, drawing_rects, min_overlap=0.10)

        if match is None:
            if debug:
                print("\n" + "=" * 80)
                print(f"BLOCK {i}")
                print("text:", repr(text))
                print(" -> no matching rect")
            continue

        header_fill_ok = is_header_fill(match["fill"])
        bold_ok, matched_spans = block_has_bold_text(page, block_rect, debug=False)
        recommendation_like = looks_like_recommendation_body(text)

        is_subheader = header_fill_ok

        result = {
            "block_index": i,
            "text": text,
            "block_rect": block_rect,
            "matching_rect": match["rect"],
            "drawing_index": match["drawing_index"],
            "fill": match["fill"],
            "avg_grey": match["avg_grey"],
            "spread": match["spread"],
            "contains": match["contains"],
            "overlap": match["overlap"],
            "header_fill_ok": header_fill_ok,
            "bold_ok": bold_ok,
            "recommendation_like": recommendation_like,
            "is_subheader": is_subheader,
        }
        results.append(result)

        if debug:
            print("\n" + "=" * 80)
            print(f"BLOCK {i}")
            print("text:", repr(text))
            print("block_rect:", block_rect)
            print("matching_rect:", match["rect"])
            print("drawing_index:", match["drawing_index"])
            print("fill:", match["fill"])
            print("avg_grey:", match["avg_grey"])
            print("spread:", match["spread"])
            print("contains:", match["contains"])
            print("overlap:", match["overlap"])
            print("header_fill_ok:", header_fill_ok)
            print("bold_ok:", bold_ok)
            print("recommendation_like:", recommendation_like)
            print("IS_SUBHEADER:", is_subheader)

    return results

    # --------------------------------------------------
    # convenience: only return the subheaders
    # --------------------------------------------------


def get_subsubheaders(page, debug=False):
    drawing_rects = get_drawing_rects_with_fill(page)
    blocks = page.get_text("blocks")

    subsubheaders = []

    for i, block in enumerate(blocks):
        text = block[4]
        block_rect = fitz.Rect(block[:4])

        match = get_matching_rect_for_block(block, drawing_rects, min_overlap=0.10)
        if match is None:
            continue

        header_fill_ok = is_header_fill(match["fill"])
        is_subsubheader = header_fill_ok

        if is_subsubheader:
            result = {
                "block_index": i,
                "text": text,
                "block_rect": block_rect,
                "matching_rect": match["rect"],
                "drawing_index": match["drawing_index"],
                "fill": match["fill"],
                "avg_grey": match["avg_grey"],
                "spread": match["spread"],
                "contains": match["contains"],
                "overlap": match["overlap"],
                "is_subsubheader": True,
            }
            subsubheaders.append(result)

            if debug:
                print("\nSUBSUBHEADER")
                print("block_index:", i)
                print("text:", repr(text))
                print("avg_grey:", match["avg_grey"])
                print("fill:", match["fill"])

    return subsubheaders


# ---- run ----
if __name__ == "__main__":

    # --------------------------------------------------
    # run
    # --------------------------------------------------

    doc = fitz.open(pdf_page_path)
    page = doc[0]

    subheaders = get_subsubheaders(page, debug=True)

    print("\n" + "=" * 80)
    print("DETECTED SUBHEADERS")
    print("=" * 80)
    for sh in subheaders:
        print(f"\nBLOCK {sh['block_index']}")
        print("text:", repr(sh["text"]))
        print("avg_grey:", sh["avg_grey"])
        print("fill:", sh["fill"])
