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


def get_output_directory(
    input_path: str, source_type: str, is_batch: bool = True
) -> str:
    """Generate output directory path based on input path and processing type."""
    if source_type == "image":
        base_dir = input_path.replace("images", "table_structures")
        if not is_batch:
            return str(Path(base_dir).parent / "from_images" / Path(base_dir).stem)
        return base_dir
    else:  # markdown
        base_dir = input_path.replace("markdown", "table_structures")
        if not is_batch:
            return str(Path(base_dir).parent / "from_markdown" / Path(base_dir).name)
        return base_dir


def process_files(
    file_paths: list[str], source_type: str, is_batch: bool = True
) -> tuple[list, list]:
    """Process multiple files and return combined results."""
    all_triples, all_trees = list(), list()

    label = f"Parsing {'images' if source_type == 'image' else 'chunks'}"
    with click.progressbar(file_paths, length=len(file_paths), label=label) as progress:
        for file_path in progress:
            if source_type == "image":
                triples, trees = parse_image(file_path)
            else:  # markdown chunk
                triples, trees = parse_markdown(file_path)
            all_triples.extend(triples)
            all_trees.extend(trees)

    return all_triples, all_trees


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def cli(verbose):
    """Process images from PDFs for table extraction and analysis."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command("images")
@click.option(
    "--path",
    help="Path to image directory or single image file.",
)
@click.option(
    "--single", is_flag=True, help="Process single image file instead of directory."
)
def parse_images(path: str, single: bool) -> None:
    """Parse images and save extracted structures as JSON files."""
    # Set default path based on single flag
    if path is None:
        if single:
            path = "/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/images/page37_tab6.png"
        else:
            path = "/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/images/esc_ccs/"

    try:
        if not os.path.exists(path):
            logger.error(f"Path not found: {path}")
            return

        if single:
            if not os.path.isfile(path):
                logger.error(f"Single file expected but got directory: {path}")
                return
            logger.info(f"Parsing single image: {path}")
            triples, trees = parse_image(path)
            output_dir = get_output_directory(path, "image", is_batch=False)
        else:
            if not os.path.isdir(path):
                logger.error(f"Directory expected but got file: {path}")
                return
            file_paths = glob.glob(os.path.join(path, "*"))
            if not file_paths:
                logger.warning(f"No images found in: {path}")
                return
            triples, trees = process_files(file_paths, "image", is_batch=True)
            output_dir = get_output_directory(path, "image", is_batch=True)

        save_results(triples, trees, output_dir, "tables")
        logger.info(f"Found {len(triples)} triples and {len(trees)} trees")

    except Exception as e:
        logger.error(f"Error during image parsing: {e}")


@cli.command("markdown")
@click.option(
    "--path",
    help="Path to markdown file.",
)
@click.option(
    "--single",
    is_flag=True,
    help="Parse file as single chunk instead of splitting into multiple chunks.",
)
def parse_markdown_files(path: str, single: bool) -> None:
    """Parse markdown files and save extracted structures as JSON files."""
    # Set default path based on single flag
    if path is None:
        if single:
            path = "/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/markdown/page37_tab6.md"
        else:
            path = "/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/markdown/esc_ccs.md"

    try:
        if not os.path.exists(path):
            logger.error(f"Markdown file not found: {path}")
            return

        with open(path, "r") as f:
            markdown_content = f.read()

        if single:
            logger.info(f"Parsing markdown file as single chunk: {path}")
            triples, trees = parse_markdown(markdown_content)
            output_dir = get_output_directory(path, "markdown", is_batch=False)
        else:
            from langchain_text_splitters import MarkdownTextSplitter

            markdown_splitter = MarkdownTextSplitter()
            chunks = markdown_splitter.split_text(markdown_content)
            triples, trees = process_files(chunks, "markdown", is_batch=True)
            output_dir = get_output_directory(path, "markdown", is_batch=True)

        save_results(triples, trees, output_dir, "tables")
        logger.info(f"Found {len(triples)} triples and {len(trees)} trees")

    except Exception as e:
        logger.error(f"Error during markdown parsing: {e}")


if __name__ == "__main__":
    # Example usage:
    # python parse_tables.py images --single  # Uses default single image
    # python parse_tables.py markdown --single-chunk  # Uses default single markdown file
    # python parse_tables.py images  # Processes directory of images
    # python parse_tables.py markdown  # Processes markdown file with chunking
    cli()
