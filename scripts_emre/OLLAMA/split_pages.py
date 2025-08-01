import logging
import os
from pathlib import Path
from typing import List

import click
from PyPDF2 import PdfReader, PdfWriter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("pdf_splitter")


def ensure_directory_exists(path: str) -> None:
    """Ensure the directory exists, create if it doesn't."""
    directory = Path(path)
    if not directory.exists():
        logger.info(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def split_pdf(input_path: str, output_prefix: str = "page") -> List[str]:
    """
    Splits a PDF file into individual pages.

    Args:
        input_path (str): The path to the input PDF file.
        output_prefix (str, optional): The prefix for the output filenames.
                                       Defaults to "page".

    Returns:
        List[str]: List of paths to generated PDF files
    """
    output_files = []

    try:
        if not os.path.exists(input_path):
            logger.error(f"PDF file not found: {input_path}")
            return output_files

        output_dir = os.path.dirname(output_prefix)
        if output_dir and not os.path.exists(output_dir):
            ensure_directory_exists(output_dir)

        reader = PdfReader(input_path)
        num_pages = len(reader.pages)

        # Track errors for reporting after progress bar completes
        errors = []

        with click.progressbar(
            range(num_pages), length=num_pages, label="Splitting PDF pages"
        ) as pages:
            for page_num in pages:
                try:
                    writer = PdfWriter()
                    writer.add_page(reader.pages[page_num])

                    output_path = f"{output_prefix}_{page_num + 1}.pdf"
                    with open(output_path, "wb") as outfile:
                        writer.write(outfile)
                    output_files.append(output_path)
                except Exception as e:
                    errors.append((page_num + 1, str(e)))

        # Report any errors after the progress bar completes
        for page_num, error in errors:
            logger.error(f"Error processing page {page_num}: {error}")

        logger.info(f"Successfully split PDF into {len(output_files)} pages")
        return output_files

    except Exception as e:
        logger.error(f"An error occurred while splitting the PDF: {str(e)}")
        return output_files


@click.command()
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option(
    "--input-path",
    "-i",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/esc_ccs.pdf",
    type=click.Path(exists=True),
    help="Path to the input PDF file",
)
@click.option(
    "--output-path",
    "-o",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/pages/",
    help="Directory path for output files with optional prefix",
)
def cli(verbose, input_path, output_path):
    """PDF Splitting Tool: Split a PDF file into individual pages"""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")

    logger.info(f"Starting PDF splitting for: {input_path}")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        ensure_directory_exists(output_dir)

    output_files = split_pdf(input_path, output_path)

    if output_files:
        logger.info(f"PDF split complete. {len(output_files)} pages created.")
        for i, file_path in enumerate(output_files[:3], 1):
            logger.info(f"Example {i}: {file_path}")
        if len(output_files) > 3:
            logger.info(f"... and {len(output_files) - 3} more files")


if __name__ == "__main__":
    cli()
