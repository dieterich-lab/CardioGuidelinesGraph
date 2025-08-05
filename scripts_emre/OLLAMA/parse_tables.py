import base64
import glob
import json
import logging
import os
import sys
from pathlib import Path

import click
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


def parse_image(img_path: str) -> list:
    """Process a single image and return all extracted structures."""
    with open(img_path, "rb") as image_file:
        img_b64 = base64.b64encode(image_file.read()).decode("utf-8")
    img = Image.from_base64("image/png", img_b64)
    res = b.Image2Table(img=img)

    results = []
    for x in res.list:
        result_data = x.model_dump()
        result_data["source_filepath"] = img_path
        results.append(result_data)

    return results


def parse_markdown(chunk: str) -> list:
    """Process a markdown chunk to extract all structures."""
    try:
        res = b.Markdown2Table(markdown=chunk)

        results = []
        for x in res.list:
            result_data = x.model_dump()
            result_data["source_markdown_chunk"] = chunk
            results.append(result_data)

        return results
    except Exception as e:
        logger.error(f"Error processing markdown chunk: {e}")
        return []


def save_results(results: list, output_dir: str, filename: str) -> None:
    """Save all results to a single JSON file."""
    ensure_directory_exists(output_dir)

    tables_file = os.path.join(output_dir, filename)

    with open(tables_file, "w") as f:
        json.dump(results, f, indent=4)

    logger.info(f"Results saved to: {tables_file}")


def process_files(
    file_paths: list[str], source_type: str, is_batch: bool = True
) -> list:
    """Process multiple files and return combined results."""
    all_results = []

    label = f"Parsing {'images' if source_type == 'image' else 'chunks'}"
    with click.progressbar(file_paths, length=len(file_paths), label=label) as progress:
        for file_path in progress:
            if source_type == "image":
                results = parse_image(file_path)
            else:  # markdown chunk
                results = parse_markdown(file_path)
            all_results.extend(results)

    return all_results


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
            results = parse_image(path)
        else:
            if not os.path.isdir(path):
                logger.error(f"Directory expected but got file: {path}")
                return
            file_paths = glob.glob(os.path.join(path, "*"))
            if not file_paths:
                logger.warning(f"No images found in: {path}")
                return
            results = process_files(file_paths, "image", is_batch=True)
        output_dir = (
            Path(path.replace("images", "table_structures")).parent / "from_images"
        )

        save_results(results, output_dir, f"{Path(path).stem}.json")
        logger.info(f"Found {len(results)} total structures")

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
            results = parse_markdown(markdown_content)
        else:
            from langchain_text_splitters import MarkdownTextSplitter

            markdown_splitter = MarkdownTextSplitter()
            chunks = markdown_splitter.split_text(markdown_content)
            results = process_files(chunks, "markdown", is_batch=True)
        output_dir = (
            Path(path.replace("markdown", "table_structures")).parent / "from_markdown"
        )

        save_results(results, output_dir, f"{Path(path).stem}.json")
        logger.info(f"Found {len(results)} total structures")

    except Exception as e:
        logger.error(f"Error during markdown parsing: {e}")


if __name__ == "__main__":
    # Example usage:
    # python parse_tables.py images --single  # Uses default single image
    # python parse_tables.py markdown --single  # Uses default single markdown file
    # python parse_tables.py images  # Processes directory of images
    # python parse_tables.py markdown  # Processes markdown file with chunking
    cli()
