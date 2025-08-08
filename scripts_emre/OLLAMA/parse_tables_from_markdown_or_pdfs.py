import base64
import glob
import json
import logging
import os
import sys
from pathlib import Path

import click
import fitz
from baml_py import Image
from langchain_text_splitters import MarkdownTextSplitter

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


def extract_images_from_pdf(pdf_path: str, output_dir: str) -> list[str]:
    """Extract images from PDF using fitz and return list of image paths."""
    pdf_name = Path(pdf_path).stem
    ensure_directory_exists(str(output_dir))

    doc = fitz.open(pdf_path)
    image_paths = []

    for page_num in range(len(doc)):
        try:
            page = doc[page_num]
            pix = page.get_pixmap(
                matrix=fitz.Identity,
                dpi=None,
                colorspace=fitz.csRGB,
                clip=None,
                alpha=True,
                annots=True,
            )
            img_path = Path(output_dir) / f"{pdf_name}.png"
            pix.save(str(img_path))
            image_paths.append(str(img_path))
        except Exception as e:
            logger.error(f"Error extracting page {page_num} from {pdf_path}: {e}")

    doc.close()
    logger.info(f"Extracted {len(image_paths)} images from {pdf_path}")
    return image_paths


def parse_table_from_image(img_path: str) -> list:
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


def parse_table_from_chunk(chunk: str) -> list:
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


def process_single_pdf(pdf_path: str, output_dir: str) -> list:
    """Process a single PDF file and return extracted table results."""
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return []

    logger.info(f"Processing PDF: {pdf_path}")

    # Extract images from PDF
    image_paths = extract_images_from_pdf(pdf_path, output_dir)

    if not image_paths:
        logger.warning(f"No images extracted from {pdf_path}")
        return []

    # Process each image for table extraction
    all_results = []
    with click.progressbar(image_paths, label="Parsing images for tables") as images:
        for img_path in images:
            try:
                results = parse_table_from_image(img_path)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Error processing image {img_path}: {e}")

    return all_results


def process_pdf_directory(pdf_dir: str, output_dir: str) -> list:
    """Process all PDF files in a directory."""
    if not os.path.exists(pdf_dir):
        logger.error(f"Directory not found: {pdf_dir}")
        return []

    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        logger.warning(f"No PDF files found in: {pdf_dir}")
        return []

    logger.info(f"Found {len(pdf_files)} PDF files")
    all_results = []

    with click.progressbar(pdf_files, label="Processing PDFs") as files:
        for pdf_file in files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            results = process_single_pdf(pdf_path, output_dir)
            all_results.extend(results)

    return all_results


def process_files(
    file_paths_or_chunks: list, file_type: str, is_batch: bool = False
) -> list:
    """Process a list of files or chunks and return all extracted structures."""
    all_results = []

    if file_type == "image":
        with click.progressbar(
            file_paths_or_chunks, label="Processing images"
        ) as items:
            for file_path in items:
                try:
                    results = parse_table_from_image(file_path)
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Error processing image {file_path}: {e}")

    elif file_type == "markdown":
        with click.progressbar(
            file_paths_or_chunks, label="Processing markdown chunks"
        ) as items:
            for chunk in items:
                try:
                    results = parse_table_from_chunk(chunk)
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Error processing markdown chunk: {e}")

    return all_results


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def cli(verbose):
    """Process images from PDFs for table extraction and analysis."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command("markdown")
@click.option(
    "--path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/markdown/esc_ccs.md",
    help="Path to markdown file.",
)
def parse_markdown_files(path: str) -> None:
    """Parse markdown files and save extracted structures as JSON files."""
    try:
        if not os.path.exists(path):
            logger.error(f"Markdown file not found: {path}")
            return

        if os.path.isfile(path):
            with open(path, "r") as f:
                markdown_content = f.read()

            markdown_splitter = MarkdownTextSplitter()
            chunks = markdown_splitter.split_text(markdown_content)
            results = process_files(chunks, "markdown", is_batch=True)
        else:
            logger.error(
                f"Directory processing not supported for markdown command: {path}"
            )
            return

        output_dir = (
            Path(path.replace("markdown", "table_structures")).parent / "from_markdown"
        )

        save_results(results, str(output_dir), f"{Path(path).stem}.json")
        logger.info(f"Found {len(results)} total structures")

    except Exception as e:
        logger.error(f"Error during markdown parsing: {e}")


@cli.command("pdf")
@click.option(
    "--path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/esc_ccs.pdf",
    help="Path to PDF file or directory containing PDF files.",
)
@click.option(
    "--output-dir",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/table_structures/from_pdf_images",
    help="Output directory for results.",
)
def parse_tables_from_pdfs(path: str, output_dir: str) -> None:
    """Parse PDFs by extracting images on-demand and save extracted table structures as JSON files."""
    try:
        if not os.path.exists(path):
            logger.error(f"Path not found: {path}")
            return

        if os.path.isfile(path):
            logger.info(f"Processing single PDF: {path}")
            results = process_single_pdf(path, output_dir)
            filename = f"{Path(path).stem}.json"
        else:
            logger.info(f"Processing PDF directory: {path}")
            results = process_pdf_directory(path, output_dir)
            filename = f"{Path(path).stem}.json"

        if results:
            save_results(results, output_dir, filename)
            logger.info(f"Found {len(results)} total table structures")
        else:
            logger.warning("No table structures found")

    except Exception as e:
        logger.error(f"Error during PDF parsing: {e}")


if __name__ == "__main__":
    cli()
