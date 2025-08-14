import base64
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


def extract_images_from_pdf(pdf_path: str, output_dir: str) -> list[tuple]:
    """Extract images from PDF using fitz and return list of image data and paths."""
    pdf_name = Path(pdf_path).stem
    ensure_directory_exists(str(output_dir))

    doc = fitz.open(pdf_path)
    image_data = []

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
            img_path = Path(output_dir) / f"{pdf_name}_page_{page_num:03d}.png"

            # Store image data and path instead of saving immediately
            image_data.append((pix, str(img_path), page_num))

        except Exception as e:
            logger.error(f"Error extracting page {page_num} from {pdf_path}: {e}")

    doc.close()
    logger.info(f"Extracted {len(image_data)} images from {pdf_path}")
    return image_data


def parse_structures_from_image(pix, img_path: str) -> list:
    """
    Process an in-memory image and return all extracted structures.

    Args:
        pix: A pixmap object (in-memory image from PDF)
        img_path: Path where the image would be saved (for metadata only)

    Returns:
        List of extracted structures
    """
    try:
        # Convert pixmap to base64
        img_bytes = pix.tobytes("png")
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        # Process the image to extract structures
        img = Image.from_base64("image/png", img_b64)
        res = b.Image2Structure(img=img)

        results = []
        for x in res.list:
            result_data = x.model_dump()
            result_data["source_filepath"] = img_path
            results.append(result_data)

        return results
    except Exception as e:
        logger.error(f"Error processing image for {img_path}: {e}")
        return []


def parse_structures_from_chunk(chunk: str) -> list:
    """Process a markdown chunk to extract all structures."""
    try:
        res = b.Markdown2Structure(markdown=chunk)

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

    structures_file = os.path.join(output_dir, filename)

    with open(structures_file, "w") as f:
        json.dump(results, f, indent=4)

    logger.info(f"Results saved to: {structures_file}")


def process_single_pdf(pdf_path: str, output_dir: str) -> list:
    """Process a single PDF file and return extracted structure results."""
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return []

    logger.info(f"Processing PDF: {pdf_path}")

    # Extract images from PDF but don't save them yet
    image_data = extract_images_from_pdf(pdf_path, output_dir)

    if not image_data:
        logger.warning(f"No images extracted from {pdf_path}")
        return []

    # Process each image for structure extraction
    all_results = []
    saved_images_count = 0

    with click.progressbar(image_data, label="Parsing images for structures") as images:
        for pix, img_path, page_num in images:
            try:
                # Process the image to find structures using unified function
                results = parse_structures_from_image(pix, img_path)

                # Only save the image if structures were found
                if results:
                    # Save the image to disk
                    pix.save(img_path)
                    all_results.extend(results)
                    saved_images_count += 1
            except Exception as e:
                logger.error(f"Error processing image for page {page_num}: {e}")

    logger.info(
        f"Found structures in {saved_images_count} out of {len(image_data)} images"
    )
    return all_results


def process_pdf_directory(pdf_dir: str, output_dir: str) -> None:
    """Process all PDF files in a directory, saving results for each file separately."""
    if not os.path.exists(pdf_dir):
        logger.error(f"Directory not found: {pdf_dir}")
        return None

    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        logger.warning(f"No PDF files found in: {pdf_dir}")
        return None

    # Create a subdirectory based on input directory name
    input_dir_name = Path(pdf_dir).name
    subdir_path = os.path.join(output_dir, input_dir_name)
    ensure_directory_exists(subdir_path)

    logger.info(f"Found {len(pdf_files)} PDF files")

    with click.progressbar(pdf_files, label="Processing PDFs") as files:
        for pdf_file in files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            results = process_single_pdf(pdf_path, subdir_path)

            if results:
                # Save results for this specific PDF
                filename = f"{Path(pdf_file).stem}.json"
                save_results(results, subdir_path, filename)
                logger.info(f"Saved {len(results)} structures for {pdf_file}")
            else:
                logger.warning(f"No structures found in {pdf_file}")

    return None


def process_files(chunks: list) -> list:
    """Process a list of markdown chunks and return all extracted structures."""
    all_results = []

    with click.progressbar(chunks, label="Processing markdown chunks") as items:
        for chunk in items:
            try:
                results = parse_structures_from_chunk(chunk)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Error processing markdown chunk: {e}")

    return all_results


@click.group()
def cli():
    """Process PDFs and markdown files for structure extraction and analysis."""


@cli.command("markdown")
@click.option(
    "--path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/src/data/guidelines/markdown/esc_ccs.md",
    help="Path to markdown file.",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def parse_structures_from_markdown(path: str, verbose: bool) -> None:
    """Parse markdown files and save extracted structures as JSON files."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        if not os.path.exists(path):
            logger.error(f"Markdown file not found: {path}")
            return

        if os.path.isfile(path):
            with open(path, "r") as f:
                markdown_content = f.read()

            markdown_splitter = MarkdownTextSplitter()
            chunks = markdown_splitter.split_text(markdown_content)
            results = process_files(chunks)
        else:
            logger.error(
                f"Directory processing not supported for markdown command: {path}"
            )
            return

        output_dir = (
            Path(path.replace("markdown", "structures")).parent / "from_markdown"
        )

        save_results(results, str(output_dir), f"{Path(path).stem}.json")
        logger.info(f"Found {len(results)} total structures")

    except Exception as e:
        logger.error(f"Error during markdown parsing: {e}")


@cli.command("pdf")
@click.option(
    "--path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/src/data/guidelines/esc_ccs.pdf",
    help="Path to PDF file or directory containing PDF files.",
)
@click.option(
    "--output-dir",
    default="/home/pwiesenbach/CardioGuidelinesGraph/src/data/guidelines/structures/from_pdf_images",
    help="Output directory for results.",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def parse_structures_from_pdf(path: str, output_dir: str, verbose: bool) -> None:
    """Parse PDFs by extracting images on-demand and save extracted structures as JSON files."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        if not os.path.exists(path):
            logger.error(f"Path not found: {path}")
            return

        if os.path.isfile(path):
            logger.info(f"Processing single PDF: {path}")
            results = process_single_pdf(path, output_dir)
            filename = f"{Path(path).stem}.json"

            if results:
                save_results(results, output_dir, filename)
                logger.info(f"Found {len(results)} total structures")
            else:
                logger.warning("No structures found")
        else:
            logger.info(f"Processing PDF directory: {path}")
            # For directories, results are saved within process_pdf_directory
            process_pdf_directory(path, output_dir)
            logger.info(f"Completed processing directory: {path}")

    except Exception as e:
        logger.error(f"Error during PDF parsing: {e}")


if __name__ == "__main__":
    cli()
