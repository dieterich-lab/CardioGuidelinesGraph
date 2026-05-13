from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from cardio_graph_core.query.baml_client.sync_client import b
from cardio_graph_core.query.query_helper_functions import entities_to_list
from cardio_graph_core.query.question import triple_batch, base_batch

DEFAULT_OUTPUT_DIR = (
    "/home/ecalik/cgg_working_dir/CardioGuidelinesGraph/outputs/index_eval"
)


def flatten_batches(batches: List[List[str]]) -> List[Dict[str, Any]]:
    rows = []

    for batch_idx, batch in enumerate(batches, start=1):
        for case_idx, question in enumerate(batch, start=1):
            rows.append(
                {
                    "batch_idx": batch_idx,
                    "case_idx": case_idx,
                    "question": question,
                }
            )

    return rows


def extract_entities_from_question(question: str) -> List[str]:
    extracted = b.PatientInfoExtractor(input=question)
    return entities_to_list(extracted)


def run_entity_extraction(
    questions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    results = []

    for i, item in enumerate(questions, start=1):
        question = item["question"]

        print("\n" + "=" * 120)
        print(f"QUESTION {i}/{len(questions)}")
        print("=" * 120)
        print(question)

        try:
            entities = extract_entities_from_question(question)
            success = True
            error = None

            print("Extracted entities:")
            for j, ent in enumerate(entities, start=1):
                print(f"  [{j}] {ent}")

        except Exception as e:
            entities = []
            success = False
            error = str(e)

            print("ERROR:")
            print(error)

        results.append(
            {
                **item,
                "success": success,
                "error": error,
                "entities": entities,
            }
        )

    return results


def write_entity_report(
    results: List[Dict[str, Any]],
    output_dir: str,
    report_name: str,
) -> Dict[str, str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    txt_path = out_dir / f"{report_name}.txt"
    json_path = out_dir / f"{report_name}.json"
    terms_path = out_dir / f"{report_name}_unique_entities.txt"

    unique_entities = sorted(
        {
            ent
            for row in results
            for ent in row.get("entities", [])
            if ent and str(ent).strip()
        },
        key=lambda x: x.lower(),
    )

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("PATIENT QUESTION ENTITY EXTRACTION REPORT\n")
        f.write("=" * 120 + "\n")
        f.write(f"Created at       : {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"Questions        : {len(results)}\n")
        f.write(f"Unique entities  : {len(unique_entities)}\n")
        f.write("=" * 120 + "\n\n")

        for row in results:
            f.write("#" * 120 + "\n")
            f.write(f"Batch/case : {row.get('batch_idx')}.{row.get('case_idx')}\n")
            f.write(f"Success    : {row.get('success')}\n")
            f.write(f"Question   : {row.get('question')}\n")

            if row.get("error"):
                f.write(f"Error      : {row.get('error')}\n")

            f.write("Entities:\n")
            entities = row.get("entities", [])
            if entities:
                for ent in entities:
                    f.write(f"  - {ent}\n")
            else:
                f.write("  - none\n")

            f.write("\n")

        f.write("\n" + "=" * 120 + "\n")
        f.write("UNIQUE ENTITIES\n")
        f.write("=" * 120 + "\n")
        for ent in unique_entities:
            f.write(f"{ent}\n")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "question_count": len(results),
                "unique_entity_count": len(unique_entities),
                "unique_entities": unique_entities,
                "results": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    with open(terms_path, "w", encoding="utf-8") as f:
        for ent in unique_entities:
            f.write(f"{ent}\n")

    return {
        "txt": str(txt_path),
        "json": str(json_path),
        "unique_entities": str(terms_path),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run BAML patient entity extraction over question batches."
    )

    parser.add_argument(
        "--batch-source",
        choices=["triple", "base"],
        default="triple",
        help="Which predefined question batch to use.",
    )

    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where reports are saved.",
    )

    parser.add_argument(
        "--report-name",
        default=None,
        help="Base report filename without extension.",
    )

    args = parser.parse_args()

    batches = triple_batch if args.batch_source == "triple" else base_batch
    questions = flatten_batches(batches)

    report_name = (
        args.report_name
        or f"entity_extraction_{args.batch_source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    results = run_entity_extraction(questions)

    paths = write_entity_report(
        results,
        output_dir=args.output_dir,
        report_name=report_name,
    )

    print("\nSaved entity extraction reports:")
    for kind, path in paths.items():
        print(f"  {kind}: {path}")


if __name__ == "__main__":
    main()
