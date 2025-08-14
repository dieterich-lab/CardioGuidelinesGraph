#!/usr/bin/env python
"""
Extraction Assessment Script

This script compares the table extraction results from docling and BAML systems,
calculating coverage metrics and storing evaluation results.
"""

import glob
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from baml_client.sync_client import b

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define paths
DOCLING_PATH = (
    "/home/pwiesenbach/CardioGuidelinesGraph/src/data/guidelines/docling/pdf_pages"
)
BAML_PATH = "/home/pwiesenbach/CardioGuidelinesGraph/src/data/guidelines/structures/from_pdf_images/pdf_pages"
COVERAGE_OUTPUT_PATH = (
    "/home/pwiesenbach/CardioGuidelinesGraph/src/data/guidelines/coverage"
)


def load_docling_files(page_id: str) -> Optional[str]:
    """
    Load and combine all docling table JSON files for a specific page.

    Args:
        page_id: The page ID (e.g., "_1")

    Returns:
        JSON string of all combined tables or None if not found
    """
    page_path = os.path.join(DOCLING_PATH, page_id, "tables")

    if not os.path.exists(page_path):
        return None

    # Find all table JSON files except summary
    table_files = glob.glob(os.path.join(page_path, "table_*.json"))
    if not table_files:
        return None

    # Load and combine all tables
    combined_tables = []
    for table_file in table_files:
        try:
            with open(table_file, "r", encoding="utf-8") as f:
                table_data = json.load(f)
                combined_tables.append(table_data)
        except Exception as e:
            logger.error(f"Error loading docling table file {table_file}: {e}")
            continue

    if not combined_tables:
        return None

    return json.dumps(combined_tables)


def load_baml_file(page_id: str) -> Optional[str]:
    """
    Load the BAML extraction JSON file for a specific page.

    Args:
        page_id: The page ID (e.g., "_1")

    Returns:
        JSON string or None if not found
    """
    file_path = os.path.join(BAML_PATH, f"{page_id}.json")

    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return json.dumps(data)
    except Exception as e:
        logger.error(f"Error loading BAML file {file_path}: {e}")
        return None


def evaluate_page(page_id: str) -> Optional[Dict[str, Any]]:
    """
    Evaluate the extraction results for a specific page.

    Args:
        page_id: The page ID (e.g., "_1")

    Returns:
        Evaluation results as a dictionary or None if evaluation couldn't be performed
    """
    docling_json = load_docling_files(page_id)
    baml_json = load_baml_file(page_id)

    if not docling_json or not baml_json:
        logger.warning(f"Missing extraction files for page {page_id}")
        return None

    try:
        results = b.TableEvaluation(docling_json, baml_json)
        return results.model_dump()
    except Exception as e:
        logger.error(f"Error evaluating page {page_id}: {e}")
        return None


def save_coverage_result(page_id: str, coverage_data: Dict[str, Any]) -> None:
    """
    Save the coverage evaluation result to a JSON file.

    Args:
        page_id: The page ID (e.g., "_1")
        coverage_data: The coverage evaluation data
    """
    os.makedirs(COVERAGE_OUTPUT_PATH, exist_ok=True)
    output_file = os.path.join(COVERAGE_OUTPUT_PATH, f"{page_id}_coverage.json")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(coverage_data, f, indent=2)
        logger.info(f"Saved coverage result for page {page_id}")
    except Exception as e:
        logger.error(f"Error saving coverage result for page {page_id}: {e}")


def get_all_page_ids() -> List[str]:
    """
    Get a list of all page IDs from both docling and BAML directories.

    Returns:
        List of unique page IDs
    """
    # Get docling page IDs
    docling_dirs = [
        os.path.basename(d) for d in glob.glob(os.path.join(DOCLING_PATH, "_*"))
    ]

    # Get BAML page IDs (remove .json extension)
    baml_files = glob.glob(os.path.join(BAML_PATH, "_*.json"))
    baml_ids = [os.path.splitext(os.path.basename(f))[0] for f in baml_files]

    # Combine and deduplicate
    all_ids = list(set(docling_dirs + baml_ids))
    all_ids.sort()

    return all_ids


def main():
    """Main function to run the extraction assessment."""
    logger.info("Starting extraction assessment")

    # Get all page IDs
    page_ids = get_all_page_ids()
    logger.info(f"Found {len(page_ids)} unique page IDs")

    # Track statistics
    total_pages = len(page_ids)
    processed_pages = 0
    skipped_pages = 0

    # Process each page
    for page_id in page_ids:
        logger.info(f"Processing page {page_id}")

        coverage_result = evaluate_page(page_id)
        if coverage_result:
            save_coverage_result(page_id, coverage_result)
            processed_pages += 1
        else:
            skipped_pages += 1

    # Log summary
    logger.info(f"Extraction assessment complete")
    logger.info(f"Total pages: {total_pages}")
    logger.info(f"Processed pages: {processed_pages}")
    logger.info(f"Skipped pages: {skipped_pages}")


if __name__ == "__main__":
    main()
