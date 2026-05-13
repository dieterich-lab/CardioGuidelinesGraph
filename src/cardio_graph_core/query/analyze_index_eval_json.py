from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, List, Optional, Tuple

GENERIC_TOKENS = {
    "patient",
    "patients",
    "with",
    "without",
    "and",
    "or",
    "the",
    "a",
    "an",
    "of",
    "for",
    "in",
    "on",
    "to",
    "due",
    "by",
    "at",
    "after",
    "before",
    "who",
    "is",
    "are",
    "being",
    "been",
    "has",
    "have",
    "had",
    "finding",
    "findings",
    "level",
    "risk",
    "functionally",
    "significant",
}


LEXICAL_INDEX_HINTS = [
    "lexical",
    "original",
    "standardized",
    "aliases",
]

VECTOR_INDEX_HINTS = [
    "vector",
]


def norm_text(s: Any) -> str:
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s).strip().lower())


def tokenize(s: Any) -> List[str]:
    return re.findall(r"[a-z0-9]+", norm_text(s))


def content_tokens(s: Any) -> set[str]:
    return {t for t in tokenize(s) if t not in GENERIC_TOKENS}


def safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def safe_mean(xs: List[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return mean(xs) if xs else None


def safe_median(xs: List[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return median(xs) if xs else None


def fmt(x: Any, digits: int = 4) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{digits}f}"
    return str(x)


def canonical_hit_label(hit: Dict[str, Any]) -> str:
    if not hit:
        return "-"

    return (
        hit.get("concept_preferred_term")
        or hit.get("concept_display_name")
        or hit.get("concept_name")
        or hit.get("concept_entity_standardized_candidate")
        or hit.get("concept_entity")
        or hit.get("entity_standardized_candidate")
        or hit.get("entity")
        or hit.get("question")
        or hit.get("decision_id")
        or "-"
    )


def canonical_concept_id(hit: Dict[str, Any]) -> str:
    if not hit:
        return "-"

    return (
        hit.get("concept_snomed_id")
        or hit.get("concept_element_id")
        or canonical_hit_label(hit)
        or "-"
    )


def canonical_decision_id(hit: Dict[str, Any]) -> str:
    return hit.get("decision_id") or hit.get("rule_unique_id") or "-"


def index_kind(index_name: str, hits: Optional[List[Dict[str, Any]]] = None) -> str:
    if hits:
        for h in hits:
            t = h.get("index_type")
            if t:
                return str(t).upper()

    name = index_name.lower()

    if any(h in name for h in VECTOR_INDEX_HINTS):
        return "VECTOR"

    if any(h in name for h in LEXICAL_INDEX_HINTS):
        return "FULLTEXT"

    return "UNKNOWN"


def token_overlap_ratio(query: str, candidate: str) -> float:
    q = content_tokens(query)
    c = content_tokens(candidate)

    if not q:
        return 0.0

    return len(q & c) / len(q)


def jaccard(query: str, candidate: str) -> float:
    q = content_tokens(query)
    c = content_tokens(candidate)

    if not q and not c:
        return 0.0

    return len(q & c) / len(q | c) if q | c else 0.0


def entropy_from_counter(counter: Counter) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0

    ent = 0.0
    for count in counter.values():
        p = count / total
        ent -= p * math.log2(p)

    return ent


def normalized_entropy(counter: Counter) -> float:
    if not counter:
        return 0.0
    if len(counter) == 1:
        return 0.0

    ent = entropy_from_counter(counter)
    max_ent = math.log2(len(counter))
    return ent / max_ent if max_ent else 0.0


def load_eval_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def flatten_eval(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Converts nested report JSON into rows:
      one row per term/index.
    """
    rows = []

    terms = data.get("terms", [])
    indexes = data.get("indexes", [])
    results = data.get("results", {})

    for term in terms:
        term_results = results.get(term, {})

        for index_name in indexes:
            hits = term_results.get(index_name, [])
            top = hits[0] if hits else None

            row = {
                "term": term,
                "index_name": index_name,
                "index_kind": index_kind(index_name, hits),
                "has_hit": bool(hits),
                "hit_count": len(hits),
                "top_score": safe_float(top.get("score")) if top else None,
                "top_label": canonical_hit_label(top) if top else None,
                "top_decision_id": canonical_decision_id(top) if top else None,
                "top_entity_original": top.get("entity_original") if top else None,
                "top_question": top.get("question") if top else None,
                "top_context": top.get("context") if top else None,
                "top_operator": top.get("operator") if top else None,
                "top_threshold": top.get("threshold") if top else None,
                "top_unit": top.get("unit") if top else None,
                "top_token_overlap": (
                    token_overlap_ratio(term, canonical_hit_label(top)) if top else 0.0
                ),
                "top_jaccard": (
                    jaccard(term, canonical_hit_label(top)) if top else 0.0
                ),
                "hits": hits,
            }

            rows.append(row)

    return rows


def load_gold_annotations(path: str) -> Dict[str, Dict[str, str]]:
    gold = {}

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required = {"term", "expected_concept_name"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Gold CSV missing required columns: {missing}")

        for row in reader:
            term = norm_text(row.get("term"))
            if not term:
                continue

            gold[term] = {
                "term": row.get("term", "").strip(),
                "expected_concept_name": row.get("expected_concept_name", "").strip(),
                "expected_snomed_id": row.get("expected_snomed_id", "").strip(),
                "acceptable_concept_names": row.get(
                    "acceptable_concept_names", ""
                ).strip(),
                "acceptable_snomed_ids": row.get("acceptable_snomed_ids", "").strip(),
                "variant_category": row.get("variant_category", "").strip()
                or "unknown",
                "source_term": row.get("source_term", "").strip(),
                "language": row.get("language", "").strip() or "unknown",
                "include_in_primary_eval": row.get("include_in_primary_eval", "")
                .strip()
                .lower()
                or "yes",
                "notes": row.get("notes", "").strip(),
            }

    return gold


def split_acceptables(value: str) -> set[str]:
    if not value:
        return set()

    return {norm_text(x) for x in str(value).split("|") if norm_text(x)}


def canonical_hit_label(hit: Dict[str, Any]) -> str:
    if not hit:
        return "-"

    return (
        hit.get("concept_preferred_term")
        or hit.get("concept_display_name")
        or hit.get("concept_name")
        or hit.get("concept_entity_standardized_candidate")
        or hit.get("concept_entity")
        or hit.get("entity_standardized_candidate")
        or hit.get("entity")
        or hit.get("question")
        or hit.get("decision_id")
        or "-"
    )


def canonical_concept_snomed(hit: Dict[str, Any]) -> str:
    if not hit:
        return ""

    return norm_text(hit.get("concept_snomed_id"))


def hit_matches_gold(hit: Dict[str, Any], gold_row: Dict[str, str]) -> bool:
    if not hit:
        return False

    hit_snomed = canonical_concept_snomed(hit)
    hit_label = norm_text(canonical_hit_label(hit))

    expected_snomed = norm_text(gold_row.get("expected_snomed_id"))
    expected_name = norm_text(gold_row.get("expected_concept_name"))

    acceptable_snomeds = split_acceptables(gold_row.get("acceptable_snomed_ids", ""))
    acceptable_names = split_acceptables(gold_row.get("acceptable_concept_names", ""))

    valid_snomeds = set()
    if expected_snomed:
        valid_snomeds.add(expected_snomed)
    valid_snomeds |= acceptable_snomeds

    valid_names = set()
    if expected_name:
        valid_names.add(expected_name)
    valid_names |= acceptable_names

    if valid_snomeds and hit_snomed in valid_snomeds:
        return True

    if valid_names and hit_label in valid_names:
        return True

    return False


def rank_of_first_gold_match(
    hits: List[Dict[str, Any]],
    gold_row: Dict[str, str],
) -> Optional[int]:
    for hit in hits:
        if hit_matches_gold(hit, gold_row):
            return hit.get("rank")

    return None


def analyze_gold_metrics(
    data: Dict[str, Any],
    gold: Dict[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    results = data.get("results", {})
    indexes = data.get("indexes", [])

    rows = []

    for raw_term, per_index in results.items():
        gold_row = gold.get(norm_text(raw_term))
        if not gold_row:
            continue

        for index_name in indexes:
            hits = per_index.get(index_name, [])
            top = hits[0] if hits else None

            rank = rank_of_first_gold_match(hits, gold_row)
            top1_correct = rank == 1
            recall_at_k = rank is not None
            reciprocal_rank = 1.0 / rank if rank else 0.0

            rows.append(
                {
                    "term": raw_term,
                    "index_name": index_name,
                    "variant_category": gold_row.get("variant_category", "unknown"),
                    "source_term": gold_row.get("source_term", ""),
                    "language": gold_row.get("language", "unknown"),
                    "include_in_primary_eval": gold_row.get(
                        "include_in_primary_eval", "yes"
                    ),
                    "notes": gold_row.get("notes", ""),
                    "expected_concept_name": gold_row.get("expected_concept_name"),
                    "expected_snomed_id": gold_row.get("expected_snomed_id"),
                    "top_concept": canonical_hit_label(top) if top else None,
                    "top_snomed_id": top.get("concept_snomed_id") if top else None,
                    "top_entity_original": top.get("entity_original") if top else None,
                    "top_decision_id": top.get("decision_id") if top else None,
                    "top_score": safe_float(top.get("score")) if top else None,
                    "has_hit": bool(hits),
                    "gold_rank": rank,
                    "top1_correct": top1_correct,
                    "recall_at_k": recall_at_k,
                    "reciprocal_rank": reciprocal_rank,
                }
            )

    return rows


def summarize_gold_by_index(gold_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_index = defaultdict(list)

    for row in gold_rows:
        by_index[row["index_name"]].append(row)

    summaries = []

    for index_name, rows in sorted(by_index.items()):
        n = len(rows)
        top1 = sum(1 for r in rows if r["top1_correct"])
        recall = sum(1 for r in rows if r["recall_at_k"])
        no_hit = sum(1 for r in rows if not r["has_hit"])
        mrr = mean([r["reciprocal_rank"] for r in rows]) if rows else 0.0

        summaries.append(
            {
                "index_name": index_name,
                "gold_terms": n,
                "accuracy_at_1": top1 / n if n else 0.0,
                "recall_at_k": recall / n if n else 0.0,
                "mrr": mrr,
                "top1_correct": top1,
                "recall_count": recall,
                "no_hit_count": no_hit,
            }
        )

    summaries.sort(
        key=lambda x: (
            -x["accuracy_at_1"],
            -x["mrr"],
            -x["recall_at_k"],
            x["index_name"],
        )
    )

    return summaries


def summarize_gold_grouped(
    gold_rows: List[Dict[str, Any]],
    group_fields: List[str],
) -> List[Dict[str, Any]]:
    """
    Summarize gold performance grouped by arbitrary fields, e.g.
      ["index_name", "variant_category"]
      ["index_name", "language"]
      ["index_name", "include_in_primary_eval"]
    """
    grouped = defaultdict(list)

    for row in gold_rows:
        key = tuple(row.get(field, "") for field in group_fields)
        grouped[key].append(row)

    summaries = []

    for key, rows in sorted(grouped.items()):
        n = len(rows)
        top1 = sum(1 for r in rows if r["top1_correct"])
        recall = sum(1 for r in rows if r["recall_at_k"])
        no_hit = sum(1 for r in rows if not r["has_hit"])
        mrr = mean([r["reciprocal_rank"] for r in rows]) if rows else 0.0

        item = {
            "gold_terms": n,
            "accuracy_at_1": top1 / n if n else 0.0,
            "recall_at_k": recall / n if n else 0.0,
            "mrr": mrr,
            "top1_correct": top1,
            "recall_count": recall,
            "no_hit_count": no_hit,
        }

        for field, value in zip(group_fields, key):
            item[field] = value

        summaries.append(item)

    summaries.sort(
        key=lambda x: (
            x.get("index_name", ""),
            x.get("variant_category", ""),
            x.get("language", ""),
            x.get("include_in_primary_eval", ""),
        )
    )

    return summaries


def summarize_gold_primary_by_index(
    gold_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    primary_rows = [
        r
        for r in gold_rows
        if str(r.get("include_in_primary_eval", "")).lower() == "yes"
    ]
    return summarize_gold_by_index(primary_rows)


def summarize_gold_failures_by_category(
    gold_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Aggregates failure counts by variant category and index.
    """
    grouped = defaultdict(list)

    for row in gold_rows:
        key = (row.get("index_name"), row.get("variant_category", "unknown"))
        grouped[key].append(row)

    out = []

    for (index_name, category), rows in grouped.items():
        n = len(rows)
        top1_failures = [r for r in rows if not r["top1_correct"]]
        recall_failures = [r for r in rows if not r["recall_at_k"]]
        no_hits = [r for r in rows if not r["has_hit"]]

        out.append(
            {
                "index_name": index_name,
                "variant_category": category,
                "gold_terms": n,
                "top1_failure_count": len(top1_failures),
                "top1_failure_rate": len(top1_failures) / n if n else 0.0,
                "recall_failure_count": len(recall_failures),
                "recall_failure_rate": len(recall_failures) / n if n else 0.0,
                "no_hit_count": len(no_hits),
                "example_top1_failures": " | ".join(
                    f"{r['term']} -> {r.get('top_concept') or '-'}"
                    for r in top1_failures[:5]
                ),
                "example_recall_failures": " | ".join(
                    r["term"] for r in recall_failures[:5]
                ),
            }
        )

    out.sort(
        key=lambda x: (
            -x["top1_failure_rate"],
            -x["recall_failure_rate"],
            x["index_name"],
            x["variant_category"],
        )
    )

    return out


def analyze_per_index(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_index = defaultdict(list)

    for r in rows:
        by_index[r["index_name"]].append(r)

    summaries = []

    for index_name, rs in sorted(by_index.items()):
        hit_rows = [r for r in rs if r["has_hit"]]
        top_scores = [r["top_score"] for r in hit_rows if r["top_score"] is not None]
        overlaps = [r["top_token_overlap"] for r in hit_rows]
        jaccards = [r["top_jaccard"] for r in hit_rows]

        summaries.append(
            {
                "index_name": index_name,
                "index_kind": rs[0]["index_kind"] if rs else "UNKNOWN",
                "terms_total": len(rs),
                "terms_with_hit": len(hit_rows),
                "coverage": len(hit_rows) / len(rs) if rs else 0.0,
                "mean_top_score": safe_mean(top_scores),
                "median_top_score": safe_median(top_scores),
                "min_top_score": min(top_scores) if top_scores else None,
                "max_top_score": max(top_scores) if top_scores else None,
                "mean_top_token_overlap": safe_mean(overlaps),
                "median_top_token_overlap": safe_median(overlaps),
                "mean_top_jaccard": safe_mean(jaccards),
                "median_top_jaccard": safe_median(jaccards),
                "no_hit_terms": [r["term"] for r in rs if not r["has_hit"]],
            }
        )

    summaries.sort(
        key=lambda x: (
            -x["coverage"],
            -(x["mean_top_token_overlap"] or 0.0),
            x["index_name"],
        )
    )

    return summaries


def analyze_per_term(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_term = defaultdict(list)

    for r in rows:
        by_term[r["term"]].append(r)

    summaries = []

    for term, rs in sorted(by_term.items()):
        hit_rows = [r for r in rs if r["has_hit"]]

        labels = [r["top_label"] for r in hit_rows if r["top_label"]]
        label_counter = Counter(labels)

        lexical_rows = [r for r in hit_rows if r["index_kind"] == "FULLTEXT"]
        vector_rows = [r for r in hit_rows if r["index_kind"] == "VECTOR"]

        lexical_labels = {r["top_label"] for r in lexical_rows if r["top_label"]}
        vector_labels = {r["top_label"] for r in vector_rows if r["top_label"]}

        overlap_scores = [r["top_token_overlap"] for r in hit_rows]
        jaccard_scores = [r["top_jaccard"] for r in hit_rows]
        top_scores = [r["top_score"] for r in hit_rows if r["top_score"] is not None]

        most_common_label, most_common_count = (
            label_counter.most_common(1)[0] if label_counter else (None, 0)
        )

        agreement_rate = most_common_count / len(hit_rows) if hit_rows else 0.0

        lex_vec_agree = (
            bool(lexical_labels & vector_labels)
            if lexical_labels and vector_labels
            else False
        )

        no_hit_indexes = [r["index_name"] for r in rs if not r["has_hit"]]

        summaries.append(
            {
                "term": term,
                "index_count": len(rs),
                "hit_index_count": len(hit_rows),
                "coverage": len(hit_rows) / len(rs) if rs else 0.0,
                "no_hit_indexes": no_hit_indexes,
                "unique_top_labels": len(label_counter),
                "top_label_entropy": normalized_entropy(label_counter),
                "majority_top_label": most_common_label,
                "majority_count": most_common_count,
                "agreement_rate": agreement_rate,
                "lexical_top_labels": sorted(lexical_labels),
                "vector_top_labels": sorted(vector_labels),
                "lexical_vector_overlap": sorted(lexical_labels & vector_labels),
                "lexical_vector_agree": lex_vec_agree,
                "mean_top_score": safe_mean(top_scores),
                "median_top_score": safe_median(top_scores),
                "mean_top_token_overlap": safe_mean(overlap_scores),
                "median_top_token_overlap": safe_median(overlap_scores),
                "mean_top_jaccard": safe_mean(jaccard_scores),
                "median_top_jaccard": safe_median(jaccard_scores),
                "rows": rs,
            }
        )

    for s in summaries:
        difficulty = 0.0

        # Lower coverage = harder.
        difficulty += 2.0 * (1.0 - s["coverage"])

        # More disagreement = harder.
        difficulty += 2.0 * s["top_label_entropy"]

        # Low agreement = harder.
        difficulty += 1.5 * (1.0 - s["agreement_rate"])

        # Lexical/vector disagreement = harder.
        if not s["lexical_vector_agree"]:
            difficulty += 1.0

        # Low token overlap = suspicious/harder.
        mean_overlap = s["mean_top_token_overlap"] or 0.0
        difficulty += 1.0 * (1.0 - mean_overlap)

        s["difficulty_score"] = difficulty

    summaries.sort(key=lambda x: (-x["difficulty_score"], x["term"]))

    return summaries


def analyze_pairwise_index_agreement(
    rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Agreement between indexes based on top_label equality over shared-hit terms.
    """
    by_term = defaultdict(dict)

    for r in rows:
        by_term[r["term"]][r["index_name"]] = r

    indexes = sorted({r["index_name"] for r in rows})
    out = []

    for i, idx_a in enumerate(indexes):
        for idx_b in indexes[i + 1 :]:
            comparable = 0
            agree = 0
            both_hit = 0
            either_miss = 0

            for term, term_map in by_term.items():
                a = term_map.get(idx_a)
                b = term_map.get(idx_b)

                if not a or not b:
                    continue

                if a["has_hit"] and b["has_hit"]:
                    both_hit += 1
                    comparable += 1
                    if a["top_label"] == b["top_label"]:
                        agree += 1
                else:
                    either_miss += 1

            out.append(
                {
                    "index_a": idx_a,
                    "index_b": idx_b,
                    "both_hit_terms": both_hit,
                    "either_miss_terms": either_miss,
                    "top1_agreement_count": agree,
                    "top1_agreement_rate": agree / comparable if comparable else None,
                }
            )

    out.sort(
        key=lambda x: (
            -(x["top1_agreement_rate"] or -1.0),
            -x["both_hit_terms"],
            x["index_a"],
            x["index_b"],
        )
    )

    return out


def analyze_suspicious_hits(
    rows: List[Dict[str, Any]], overlap_threshold: float = 0.25
) -> List[Dict[str, Any]]:
    suspicious = []

    for r in rows:
        if not r["has_hit"]:
            continue

        if r["top_token_overlap"] <= overlap_threshold:
            suspicious.append(
                {
                    "term": r["term"],
                    "index_name": r["index_name"],
                    "index_kind": r["index_kind"],
                    "top_label": r["top_label"],
                    "top_entity_original": r["top_entity_original"],
                    "top_score": r["top_score"],
                    "top_token_overlap": r["top_token_overlap"],
                    "top_jaccard": r["top_jaccard"],
                    "decision_id": r["top_decision_id"],
                }
            )

    suspicious.sort(
        key=lambda x: (
            x["top_token_overlap"],
            x["top_jaccard"],
            x["term"],
            x["index_name"],
        )
    )

    return suspicious


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_analysis_report(
    input_json: str,
    output_dir: str,
    *,
    report_name: Optional[str] = None,
    difficult_top_n: int = 30,
    suspicious_top_n: int = 50,
    gold_csv: Optional[str] = None,
) -> Dict[str, str]:
    data = load_eval_json(input_json)
    rows = flatten_eval(data)
    gold = load_gold_annotations(gold_csv) if gold_csv else {}
    gold_metrics = analyze_gold_metrics(data, gold) if gold else []
    gold_summary = summarize_gold_by_index(gold_metrics) if gold_metrics else []
    gold_primary_summary = (
        summarize_gold_primary_by_index(gold_metrics) if gold_metrics else []
    )
    gold_by_category = (
        summarize_gold_grouped(gold_metrics, ["index_name", "variant_category"])
        if gold_metrics
        else []
    )
    gold_by_language = (
        summarize_gold_grouped(gold_metrics, ["index_name", "language"])
        if gold_metrics
        else []
    )
    gold_by_primary_flag = (
        summarize_gold_grouped(gold_metrics, ["index_name", "include_in_primary_eval"])
        if gold_metrics
        else []
    )
    gold_failures_by_category = (
        summarize_gold_failures_by_category(gold_metrics) if gold_metrics else []
    )
    per_index = analyze_per_index(rows)
    per_term = analyze_per_term(rows)
    pairwise = analyze_pairwise_index_agreement(rows)
    suspicious = analyze_suspicious_hits(rows)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if report_name is None:
        report_name = f"index_eval_stats_{timestamp}"

    txt_path = out_dir / f"{report_name}.txt"
    per_index_csv = out_dir / f"{report_name}_per_index.csv"
    per_term_csv = out_dir / f"{report_name}_per_term.csv"
    pairwise_csv = out_dir / f"{report_name}_pairwise_agreement.csv"
    suspicious_csv = out_dir / f"{report_name}_suspicious_hits.csv"
    json_path = out_dir / f"{report_name}.json"
    gold_metrics_csv = out_dir / f"{report_name}_gold_metrics.csv"
    gold_summary_csv = out_dir / f"{report_name}_gold_summary_by_index.csv"
    gold_primary_summary_csv = (
        out_dir / f"{report_name}_gold_primary_summary_by_index.csv"
    )
    gold_by_category_csv = out_dir / f"{report_name}_gold_by_variant_category.csv"
    gold_by_language_csv = out_dir / f"{report_name}_gold_by_language.csv"
    gold_by_primary_flag_csv = out_dir / f"{report_name}_gold_by_primary_flag.csv"
    gold_failures_by_category_csv = (
        out_dir / f"{report_name}_gold_failures_by_category.csv"
    )

    if gold_metrics:
        write_csv(
            gold_metrics_csv,
            gold_metrics,
            [
                "term",
                "index_name",
                "variant_category",
                "source_term",
                "language",
                "include_in_primary_eval",
                "expected_concept_name",
                "expected_snomed_id",
                "top_concept",
                "top_snomed_id",
                "top_entity_original",
                "top_decision_id",
                "top_score",
                "has_hit",
                "gold_rank",
                "top1_correct",
                "recall_at_k",
                "reciprocal_rank",
                "notes",
            ],
        )

        write_csv(
            gold_summary_csv,
            gold_summary,
            [
                "index_name",
                "gold_terms",
                "accuracy_at_1",
                "recall_at_k",
                "mrr",
                "top1_correct",
                "recall_count",
                "no_hit_count",
            ],
        )
        write_csv(
            gold_primary_summary_csv,
            gold_primary_summary,
            [
                "index_name",
                "gold_terms",
                "accuracy_at_1",
                "recall_at_k",
                "mrr",
                "top1_correct",
                "recall_count",
                "no_hit_count",
            ],
        )

        write_csv(
            gold_by_category_csv,
            gold_by_category,
            [
                "index_name",
                "variant_category",
                "gold_terms",
                "accuracy_at_1",
                "recall_at_k",
                "mrr",
                "top1_correct",
                "recall_count",
                "no_hit_count",
            ],
        )

        write_csv(
            gold_by_language_csv,
            gold_by_language,
            [
                "index_name",
                "language",
                "gold_terms",
                "accuracy_at_1",
                "recall_at_k",
                "mrr",
                "top1_correct",
                "recall_count",
                "no_hit_count",
            ],
        )

        write_csv(
            gold_by_primary_flag_csv,
            gold_by_primary_flag,
            [
                "index_name",
                "include_in_primary_eval",
                "gold_terms",
                "accuracy_at_1",
                "recall_at_k",
                "mrr",
                "top1_correct",
                "recall_count",
                "no_hit_count",
            ],
        )

        write_csv(
            gold_failures_by_category_csv,
            gold_failures_by_category,
            [
                "index_name",
                "variant_category",
                "gold_terms",
                "top1_failure_count",
                "top1_failure_rate",
                "recall_failure_count",
                "recall_failure_rate",
                "no_hit_count",
                "example_top1_failures",
                "example_recall_failures",
            ],
        )
    write_csv(
        per_index_csv,
        per_index,
        [
            "index_name",
            "index_kind",
            "terms_total",
            "terms_with_hit",
            "coverage",
            "mean_top_score",
            "median_top_score",
            "min_top_score",
            "max_top_score",
            "mean_top_token_overlap",
            "median_top_token_overlap",
            "mean_top_jaccard",
            "median_top_jaccard",
        ],
    )

    write_csv(
        per_term_csv,
        per_term,
        [
            "term",
            "index_count",
            "hit_index_count",
            "coverage",
            "unique_top_labels",
            "top_label_entropy",
            "majority_top_label",
            "majority_count",
            "agreement_rate",
            "lexical_vector_agree",
            "mean_top_score",
            "median_top_score",
            "mean_top_token_overlap",
            "median_top_token_overlap",
            "mean_top_jaccard",
            "median_top_jaccard",
            "difficulty_score",
        ],
    )

    write_csv(
        pairwise_csv,
        pairwise,
        [
            "index_a",
            "index_b",
            "both_hit_terms",
            "either_miss_terms",
            "top1_agreement_count",
            "top1_agreement_rate",
        ],
    )

    write_csv(
        suspicious_csv,
        suspicious,
        [
            "term",
            "index_name",
            "index_kind",
            "top_label",
            "top_entity_original",
            "top_score",
            "top_token_overlap",
            "top_jaccard",
            "decision_id",
        ],
    )

    serializable_per_term = []
    for t in per_term:
        t2 = dict(t)
        t2.pop("rows", None)
        serializable_per_term.append(t2)

    analysis_json = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_json": input_json,
        "per_index": per_index,
        "per_term": serializable_per_term,
        "pairwise_agreement": pairwise,
        "suspicious_hits": suspicious,
        "gold_summary_by_index": gold_summary,
        "gold_primary_summary_by_index": gold_primary_summary,
        "gold_by_variant_category": gold_by_category,
        "gold_by_language": gold_by_language,
        "gold_by_primary_flag": gold_by_primary_flag,
        "gold_failures_by_category": gold_failures_by_category,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(analysis_json, f, indent=2, ensure_ascii=False, default=str)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("INDEX EVALUATION STATISTICAL ANALYSIS\n")
        f.write("=" * 120 + "\n")
        f.write(f"Created at        : {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"Input JSON        : {input_json}\n")
        f.write(f"Terms             : {len(data.get('terms', []))}\n")
        f.write(f"Indexes           : {len(data.get('indexes', []))}\n")
        f.write(f"Rows analyzed     : {len(rows)}\n")
        f.write("=" * 120 + "\n\n")

        f.write("WHAT THESE METRICS MEAN\n")
        f.write("-" * 120 + "\n")
        f.write(
            "coverage                  = fraction of terms for which an index returned at least one hit\n"
        )
        f.write(
            "top_label_entropy          = disagreement across indexes for a term; higher means less consensus\n"
        )
        f.write(
            "agreement_rate             = fraction of hit-producing indexes that share the majority top label\n"
        )
        f.write(
            "lexical_vector_agree       = whether any lexical top label equals any vector top label\n"
        )
        f.write(
            "top_token_overlap          = fraction of query content tokens found in the top hit label\n"
        )
        f.write(
            "difficulty_score           = heuristic score combining missing hits, disagreement, and weak lexical overlap\n"
        )
        f.write(
            "\nNote: without gold labels, this is a proxy analysis, not true accuracy.\n\n"
        )

        f.write("=" * 120 + "\n")
        f.write("PER-INDEX SUMMARY\n")
        f.write("=" * 120 + "\n")

        for s in per_index:
            f.write("\n" + "-" * 120 + "\n")
            f.write(f"Index                  : {s['index_name']} [{s['index_kind']}]\n")
            f.write(
                f"Coverage               : {fmt(s['coverage'])} ({s['terms_with_hit']}/{s['terms_total']})\n"
            )
            f.write(f"Mean top score         : {fmt(s['mean_top_score'])}\n")
            f.write(f"Median top score       : {fmt(s['median_top_score'])}\n")
            f.write(f"Mean token overlap     : {fmt(s['mean_top_token_overlap'])}\n")
            f.write(f"Median token overlap   : {fmt(s['median_top_token_overlap'])}\n")
            f.write(f"Mean Jaccard           : {fmt(s['mean_top_jaccard'])}\n")
            f.write(f"Median Jaccard         : {fmt(s['median_top_jaccard'])}\n")

            no_hits = s.get("no_hit_terms") or []
            if no_hits:
                f.write(f"No-hit terms ({len(no_hits)}):\n")
                for term in no_hits[:20]:
                    f.write(f"  - {term}\n")
                if len(no_hits) > 20:
                    f.write(f"  ... +{len(no_hits) - 20} more\n")
        if gold_summary:
            f.write("\n\n" + "=" * 120 + "\n")
            f.write("GOLD-LABEL EVALUATION BY INDEX\n")
            f.write("=" * 120 + "\n")

            for s in gold_summary:
                f.write("\n" + "-" * 120 + "\n")
                f.write(f"Index          : {s['index_name']}\n")
                f.write(f"Gold terms     : {s['gold_terms']}\n")
                f.write(
                    f"Accuracy@1     : {fmt(s['accuracy_at_1'])} "
                    f"({s['top1_correct']}/{s['gold_terms']})\n"
                )
                f.write(
                    f"Recall@K       : {fmt(s['recall_at_k'])} "
                    f"({s['recall_count']}/{s['gold_terms']})\n"
                )
                f.write(f"MRR            : {fmt(s['mrr'])}\n")
        if gold_by_category:
            f.write("\n\n" + "=" * 120 + "\n")
            f.write("GOLD-LABEL EVALUATION BY VARIANT CATEGORY\n")
            f.write("=" * 120 + "\n")

            current_index = None
            for s in gold_by_category:
                if s["index_name"] != current_index:
                    current_index = s["index_name"]
                    f.write("\n" + "-" * 120 + "\n")
                    f.write(f"Index: {current_index}\n")
                    f.write("-" * 120 + "\n")

                f.write(
                    f"  {s['variant_category']:<24} "
                    f"n={s['gold_terms']:<4} "
                    f"acc@1={fmt(s['accuracy_at_1'])} "
                    f"recall@k={fmt(s['recall_at_k'])} "
                    f"mrr={fmt(s['mrr'])} "
                    f"no_hits={s['no_hit_count']}\n"
                )

        if gold_by_language:
            f.write("\n\n" + "=" * 120 + "\n")
            f.write("GOLD-LABEL EVALUATION BY LANGUAGE\n")
            f.write("=" * 120 + "\n")

            current_index = None
            for s in gold_by_language:
                if s["index_name"] != current_index:
                    current_index = s["index_name"]
                    f.write("\n" + "-" * 120 + "\n")
                    f.write(f"Index: {current_index}\n")
                    f.write("-" * 120 + "\n")

                f.write(
                    f"  {s['language']:<10} "
                    f"n={s['gold_terms']:<4} "
                    f"acc@1={fmt(s['accuracy_at_1'])} "
                    f"recall@k={fmt(s['recall_at_k'])} "
                    f"mrr={fmt(s['mrr'])} "
                    f"no_hits={s['no_hit_count']}\n"
                )

        if gold_primary_summary:
            f.write("\n\n" + "=" * 120 + "\n")
            f.write("PRIMARY-EVAL GOLD SUMMARY BY INDEX\n")
            f.write("=" * 120 + "\n")

            for s in gold_primary_summary:
                f.write(
                    f"{s['index_name']}: "
                    f"n={s['gold_terms']}, "
                    f"acc@1={fmt(s['accuracy_at_1'])}, "
                    f"recall@k={fmt(s['recall_at_k'])}, "
                    f"mrr={fmt(s['mrr'])}, "
                    f"no_hits={s['no_hit_count']}\n"
                )

        if gold_failures_by_category:
            f.write("\n\n" + "=" * 120 + "\n")
            f.write("GOLD FAILURES BY VARIANT CATEGORY\n")
            f.write("=" * 120 + "\n")

            for s in gold_failures_by_category[:80]:
                f.write("\n" + "-" * 120 + "\n")
                f.write(f"Index                 : {s['index_name']}\n")
                f.write(f"Variant category      : {s['variant_category']}\n")
                f.write(f"Gold terms            : {s['gold_terms']}\n")
                f.write(
                    f"Top-1 failure rate    : {fmt(s['top1_failure_rate'])} ({s['top1_failure_count']}/{s['gold_terms']})\n"
                )
                f.write(
                    f"Recall failure rate   : {fmt(s['recall_failure_rate'])} ({s['recall_failure_count']}/{s['gold_terms']})\n"
                )
                f.write(f"No-hit count          : {s['no_hit_count']}\n")
                if s.get("example_top1_failures"):
                    f.write(f"Example top-1 failures: {s['example_top1_failures']}\n")
                if s.get("example_recall_failures"):
                    f.write(f"Example recall fails  : {s['example_recall_failures']}\n")
        f.write("\n\n" + "=" * 120 + "\n")
        f.write(f"TOP {difficult_top_n} DIFFICULT TERMS\n")
        f.write("=" * 120 + "\n")

        for s in per_term[:difficult_top_n]:
            f.write("\n" + "-" * 120 + "\n")
            f.write(f"Term                   : {s['term']}\n")
            f.write(f"Difficulty score       : {fmt(s['difficulty_score'])}\n")
            f.write(
                f"Coverage               : {fmt(s['coverage'])} ({s['hit_index_count']}/{s['index_count']})\n"
            )
            f.write(f"Unique top labels      : {s['unique_top_labels']}\n")
            f.write(f"Top-label entropy      : {fmt(s['top_label_entropy'])}\n")
            f.write(f"Majority top label     : {s['majority_top_label'] or '-'}\n")
            f.write(f"Agreement rate         : {fmt(s['agreement_rate'])}\n")
            f.write(f"Lexical/vector agree   : {s['lexical_vector_agree']}\n")
            f.write(f"Mean token overlap     : {fmt(s['mean_top_token_overlap'])}\n")
            f.write("Lexical top labels:\n")
            for label in s["lexical_top_labels"]:
                f.write(f"  - {label}\n")
            f.write("Vector top labels:\n")
            for label in s["vector_top_labels"]:
                f.write(f"  - {label}\n")
            if s["no_hit_indexes"]:
                f.write("No-hit indexes:\n")
                for idx in s["no_hit_indexes"]:
                    f.write(f"  - {idx}\n")

        f.write("\n\n" + "=" * 120 + "\n")
        f.write("PAIRWISE INDEX TOP-1 AGREEMENT\n")
        f.write("=" * 120 + "\n")

        for p in pairwise:
            f.write(
                f"{p['index_a']}  <->  {p['index_b']}: "
                f"agreement={fmt(p['top1_agreement_rate'])}, "
                f"agree_count={p['top1_agreement_count']}, "
                f"both_hit_terms={p['both_hit_terms']}, "
                f"either_miss_terms={p['either_miss_terms']}\n"
            )

        f.write("\n\n" + "=" * 120 + "\n")
        f.write(f"TOP {suspicious_top_n} SUSPICIOUS TOP-1 HITS BY TOKEN OVERLAP\n")
        f.write("=" * 120 + "\n")

        for s in suspicious[:suspicious_top_n]:
            f.write("\n" + "-" * 120 + "\n")
            f.write(f"Term              : {s['term']}\n")
            f.write(f"Index             : {s['index_name']} [{s['index_kind']}]\n")
            f.write(f"Top label         : {s['top_label']}\n")
            f.write(f"Original          : {s['top_entity_original'] or '-'}\n")
            f.write(f"Score             : {fmt(s['top_score'])}\n")
            f.write(f"Token overlap     : {fmt(s['top_token_overlap'])}\n")
            f.write(f"Jaccard           : {fmt(s['top_jaccard'])}\n")
            f.write(f"Decision ID       : {s['decision_id'] or '-'}\n")

        f.write("\n\n" + "=" * 120 + "\n")
        f.write("OUTPUT FILES\n")
        f.write("=" * 120 + "\n")
        f.write(f"Per-index CSV          : {per_index_csv}\n")
        f.write(f"Per-term CSV           : {per_term_csv}\n")
        f.write(f"Pairwise agreement CSV : {pairwise_csv}\n")
        f.write(f"Suspicious hits CSV    : {suspicious_csv}\n")
        f.write(f"Analysis JSON          : {json_path}\n")
        if gold_metrics:
            f.write(f"Gold metrics CSV              : {gold_metrics_csv}\n")
            f.write(f"Gold summary CSV              : {gold_summary_csv}\n")
            f.write(f"Gold primary summary CSV      : {gold_primary_summary_csv}\n")
            f.write(f"Gold by category CSV          : {gold_by_category_csv}\n")
            f.write(f"Gold by language CSV          : {gold_by_language_csv}\n")
            f.write(f"Gold by primary flag CSV      : {gold_by_primary_flag_csv}\n")
            f.write(
                f"Gold failures by category CSV : {gold_failures_by_category_csv}\n"
            )
    output_paths = {
        "txt": str(txt_path),
        "json": str(json_path),
        "per_index_csv": str(per_index_csv),
        "per_term_csv": str(per_term_csv),
        "pairwise_csv": str(pairwise_csv),
        "suspicious_csv": str(suspicious_csv),
    }

    if gold_metrics:
        output_paths["gold_metrics_csv"] = str(gold_metrics_csv)
        output_paths["gold_summary_csv"] = str(gold_summary_csv)
        output_paths["gold_primary_summary_csv"] = str(gold_primary_summary_csv)
        output_paths["gold_by_category_csv"] = str(gold_by_category_csv)
        output_paths["gold_by_language_csv"] = str(gold_by_language_csv)
        output_paths["gold_by_primary_flag_csv"] = str(gold_by_primary_flag_csv)
        output_paths["gold_failures_by_category_csv"] = str(
            gold_failures_by_category_csv
        )

    return output_paths


def main():
    parser = argparse.ArgumentParser(
        description="Statistically analyze an index evaluation JSON report."
    )

    parser.add_argument(
        "--input-json",
        required=True,
        help="Path to index evaluation JSON file generated by index_diagnostics.py.",
    )
    parser.add_argument(
        "--gold-csv",
        default=None,
        help="Optional gold concept CSV with term, expected_concept_name, expected_snomed_id.",
    )

    parser.add_argument(
        "--output-dir",
        default="/home/ecalik/cgg_working_dir/CardioGuidelinesGraph/outputs/index_eval",
        help="Directory where analysis files are saved.",
    )

    parser.add_argument(
        "--report-name",
        default=None,
        help="Base output filename without extension.",
    )

    parser.add_argument(
        "--difficult-top-n",
        type=int,
        default=30,
        help="Number of difficult terms to show in the text report.",
    )

    parser.add_argument(
        "--suspicious-top-n",
        type=int,
        default=50,
        help="Number of suspicious hits to show in the text report.",
    )

    args = parser.parse_args()

    paths = write_analysis_report(
        input_json=args.input_json,
        output_dir=args.output_dir,
        report_name=args.report_name,
        difficult_top_n=args.difficult_top_n,
        suspicious_top_n=args.suspicious_top_n,
        gold_csv=args.gold_csv,
    )

    print("\nSaved statistical analysis:")
    for kind, path in paths.items():
        print(f"  {kind}: {path}")


if __name__ == "__main__":
    main()
