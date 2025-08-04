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
logger = logging.getLogger("StructureExtractor")


def ensure_directory_exists(path: str) -> None:
    """Ensure the directory exists, create if it doesn't."""
    directory = Path(path)
    if not directory.exists():
        logger.info(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def parse_image(img_path: str) -> tuple[list, list]:
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


def parse_markdown(chunk: str) -> tuple[list, list]:
    """Process a markdown chunk to extract triples and trees."""
    try:
        # Assuming the chunk is a valid markdown table, we can use the baml_client
        res = b.Markdown2Table(markdown=chunk)

        triples, trees = list(), list()
        for x in res.list:
            if type(x) is SemanticTriple:
                triples.append(x.model_dump())
            elif type(x) is IfElseTree:
                trees.append(x.model_dump())

        return triples, trees
    except Exception as e:
        logger.error(f"Error processing markdown chunk: {e}")
        return [], []


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


@cli.command("parse_images")
@click.option(
    "--imgx-path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/images/esc_ccs/",
    help="Path to the directory with images.",
)
def parse_tables_from_images(imgx_path: str) -> None:
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
                triples, trees = parse_image(img_path)
                all_triples.extend(triples)
                all_trees.extend(trees)

        # Create output directory and save results
        json_path = imgx_path.replace("image", "tables_structures")
        save_results(all_triples, all_trees, json_path, "tables")

    except Exception as e:
        logger.error(f"Error during image parsing: {e}")


@cli.command("parse_markdown")
@click.option(
    "--markdown-path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/markdown/esc_ccs.md",
    help="Path to the markdown file.",
)
def parse_table_from_markdown(markdown_path: str) -> None:
    from langchain_text_splitters import MarkdownTextSplitter

    """Parse markdown files and save extracted triples from tables as json files."""
    try:
        if not os.path.exists(markdown_path):
            logger.error(f"Markdown file not found: {markdown_path}")
            return

        with open(markdown_path, "r") as f:
            markdown_content = f.read()

        # Process the markdown content to extract tables
        markdown_splitter = MarkdownTextSplitter()
        chunks = markdown_splitter.split_text(markdown_content)

        all_triples, all_trees = list(), list()
        with click.progressbar(
            chunks, length=len(chunks), label="Parsing chunks"
        ) as chunk_progress:
            for chunk in chunk_progress:
                triples, trees = parse_markdown(chunk)
                all_triples.extend(triples)
                all_trees.extend(trees)

        # Create output directory and save results
        json_path = markdown_path.replace("markdown", "table_structures")
        save_results(all_triples, all_trees, json_path, "tables")

    except Exception as e:
        logger.error(f"Error during markdown parsing: {e}")


@cli.command("test_image")
@click.option(
    "--img-path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/images/page37_tab6.png",
    help="Path to the test image to parse.",
)
def parse_single_test_image(img_path: str) -> None:
    """Parse a single test image for rapid prototyping."""

    try:
        if not os.path.exists(img_path):
            logger.error(f"Test image not found: {img_path}")
            return

        logger.info(f"Parsing test image: {img_path}")

        triples, trees = parse_image(img_path)

        # Save results to test directory
        _output_dir = img_path.replace("images", "table_structures")
        output_dir = Path(_output_dir).parent / "from_images" / Path(_output_dir).stem

        save_results(triples, trees, str(output_dir))

    except Exception as e:
        logger.error(f"Error during test image parsing: {e}")


@cli.command("test_markdown")
@click.option(
    "--markdown-path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/markdown/page37_tab6.md",
    help="Path to the test markdown file to parse.",
)
def parse_single_test_markdown(markdown_path: str) -> None:
    """Parse a single test markdown file for rapid prototyping."""

    try:
        if not os.path.exists(markdown_path):
            logger.error(f"Test markdown file not found: {markdown_path}")
            return

        logger.info(f"Parsing markdown file file: {markdown_path}")

        with open(markdown_path, "r") as f:
            markdown_content = f.read()

        triples, trees = parse_markdown(markdown_content)

        # Save results to test directory

        _output_dir = markdown_path.replace("markdown", "table_structures")
        output_dir = Path(_output_dir).parent / "from_markdown" / Path(_output_dir).name

        save_results(triples, trees, str(output_dir))

    except Exception as e:
        logger.error(f"Error during test markdown parsing: {e}")


if __name__ == "__main__":
    cli()
