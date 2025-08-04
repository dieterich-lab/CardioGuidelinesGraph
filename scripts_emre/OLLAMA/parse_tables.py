import base64
import glob
import json
import logging
import os
import pickle
import sys
from pathlib import Path

import click
import fitz
from baml_client.types import IfElseTree, SemanticTriple
from baml_py import Image

sys.path.append("..")  # isort:skip

from baml_client.sync_client import b  # isort:skip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("pdf_processor")


def ensure_directory_exists(path: str) -> None:
    """Ensure the directory exists, create if it doesn't."""
    directory = Path(path)
    if not directory.exists():
        logger.info(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def process_single_image(img_path: str) -> tuple[list, list]:
    """Process a single image and return triples and trees."""
    with open(img_path, "rb") as image_file:
        img_b64 = base64.b64encode(image_file.read()).decode("utf-8")
    img = Image.from_base64("image/png", img_b64)
    res = b.Image2Table(img=img)

    triples, trees = list(), list()
    for x in res.list:
        if type(x) is SemanticTriple:
            triples.append(x.model_dump())
        elif type(x) is IfElseTree:
            trees.append(x.model_dump())

    return triples, trees


def save_results(
    triples: list, trees: list, output_dir: str, filename_prefix: str = ""
) -> None:
    """Save triples and trees to JSON files."""
    ensure_directory_exists(output_dir)

    prefix = f"{filename_prefix}_" if filename_prefix else ""
    triples_file = os.path.join(output_dir, f"{prefix}triples.json")
    trees_file = os.path.join(output_dir, f"{prefix}trees.json")

    with open(triples_file, "w") as f:
        json.dump(triples, f, indent=4)

    with open(trees_file, "w") as f:
        json.dump(trees, f, indent=4)

    logger.info(f"Results saved to: {triples_file} and {trees_file}")


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def cli(verbose):
    """Process images from PDFs for table extraction and analysis."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command("parse")
@click.option(
    "--imgx-path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/images/esc_ccs/",
    help="Path to the directory with images.",
)
def parse_image_to_table(imgx_path: str) -> None:
    """Parse images and save extracted triples from tables as json files."""
    try:
        if not os.path.exists(imgx_path):
            logger.error(f"Image directory not found: {imgx_path}")
            return

        imgx_paths = glob.glob(os.path.join(imgx_path, "*"))
        if not imgx_paths:
            logger.warning(f"No images found in: {imgx_path}")
            return

        all_triples, all_trees = list(), list()
        with click.progressbar(
            imgx_paths, length=len(imgx_paths), label="Parsing images"
        ) as images:
            for img_path in images:
                triples, trees = process_single_image(img_path)
                all_triples.extend(triples)
                all_trees.extend(trees)

        # Create output directory and save results
        json_path = imgx_path.replace("images", "tables_json")
        save_results(all_triples, all_trees, json_path, "tables")

    except Exception as e:
        logger.error(f"Error during image parsing: {e}")


@cli.command("test")
@click.option(
    "--test-image",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/images/page37/36.png",
    help="Path to the test image to parse.",
)
def parse_single_test_image(test_image: str) -> None:
    """Parse a single test image for rapid prototyping."""
    img_path = test_image

    try:
        if not os.path.exists(img_path):
            logger.error(f"Test image not found: {img_path}")
            return

        logger.info(f"Parsing test image: {img_path}")

        triples, trees = process_single_image(img_path)

        # Save results to test directory
        output_dir = (
            Path(
                "/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/table_structures"
            )
            / Path(img_path).parent.name
        )
        save_results(triples, trees, str(output_dir))

    except Exception as e:
        logger.error(f"Error during test image parsing: {e}")


if __name__ == "__main__":
    cli()
