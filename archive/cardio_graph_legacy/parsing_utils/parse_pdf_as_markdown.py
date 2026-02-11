#!/usr/bin/env python
"""
Parse PDF files as markdown.

This script iterates over all PDF files in a directory, converts them to markdown,
and saves the markdown files to an output directory.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

import click
import fitz  # PyMuPDF
import pdfplumber
import pymupdf4llm
import pypdf
from docling.document_converter import DocumentConverter
from tabulate import tabulate
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("pdf_to_markdown")

DEFAULT_INPUT_DIR = (
    "/home/pwiesenbach/CardioGuidelinesGraph/src/data/guidelines/pdf/pages"
)
DEFAULT_OUTPUT_DIR = (
    "/home/pwiesenbach/CardioGuidelinesGraph/src/data/guidelines/markdown/pages"
)


def ensure_directory_exists(path: str) -> None:
    """Ensure the directory exists, create if it doesn't."""
    directory = Path(path)
    if not directory.exists():
        logger.info(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def get_pdf_files(directory: str) -> List[Path]:
    """Get all PDF files in a directory."""
    pdf_files = list(Path(directory).glob("**/*.pdf"))
    return pdf_files


def extract_tables_with_pdfplumber(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract tables from a PDF file using pdfplumber.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of dictionaries containing page number and tables found on that page
    """
    tables_by_page = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if tables:
                    tables_by_page.append({"page_num": i + 1, "tables": tables})
        return tables_by_page
    except Exception as e:
        logger.error(f"Error extracting tables with pdfplumber: {e}")
        return []


def extract_text_with_pymupdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract text blocks and tables from a PDF using PyMuPDF (fitz).

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of dictionaries containing structured text content from each page
    """
    structured_content = []

    try:
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc):
            # Extract text blocks with their formatting info
            blocks = page.get_text("dict")["blocks"]
            structured_content.append({"page_num": page_num + 1, "blocks": blocks})
        return structured_content
    except Exception as e:
        logger.error(f"Error extracting content with PyMuPDF: {e}")
        return []


def format_table_for_markdown(table: List[List[str]]) -> str:
    """
    Format a table for markdown using the tabulate library.

    Args:
        table: A list of lists representing rows and columns

    Returns:
        Markdown formatted table
    """
    if not table or not table[0]:
        return ""

    # Clean up table data
    cleaned_table = []
    for row in table:
        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
        cleaned_table.append(cleaned_row)

    # Use first row as header
    headers = cleaned_table[0]

    # Generate markdown table
    return tabulate(cleaned_table[1:], headers=headers, tablefmt="pipe")


def convert_with_pymupdf4llm(pdf_path: str) -> str:
    """
    Convert PDF to markdown using PyMuPDF4LLM library.
    
    This library is optimized for LLM use cases and preserves more formatting,
    especially tables and structure.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Markdown formatted string
    """
    try:
        # Use PyMuPDF4LLM's to_markdown function
        markdown = pymupdf4llm.to_markdown(pdf_path)
        return markdown
    except Exception as e:
        logger.error(f"Error converting with PyMuPDF4LLM: {e}")
        # Return empty string on failure so we can handle errors gracefully
        return ""
def convert_pdf_to_markdown(
    pdf_path: Path,
    output_dir: Path,
    converter: Literal["docling", "advanced", "pymupdf4llm"] = "docling",
    extract_tables: bool = True,
    force: bool = False,
) -> Optional[Path]:
    """
    Convert a PDF file to markdown with enhanced table support.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the markdown file
        converter: Conversion method to use:
                  - "docling": Uses docling for better overall conversion
                  - "advanced": Uses PyMuPDF + pdfplumber for better table extraction
                  - "pymupdf4llm": Uses PyMuPDF4LLM for LLM-optimized output
        extract_tables: Whether to extract and format tables (only applies with "advanced" converter)
        force: Whether to overwrite files without warning

    Returns:
        Path to the generated markdown file or None if conversion failed
    """
    # Preserve original filename but change extension to .md
    # This ensures if the file was named _1.pdf it will be saved as _1.md
    output_file = output_dir / f"{pdf_path.name.rsplit('.', 1)[0]}.md"

    try:
        if converter == "docling":
            # Use docling for conversion
            docling_converter = DocumentConverter()
            result = docling_converter.convert(str(pdf_path))
            doc = result.document
            markdown_content = doc.export_to_markdown()
        elif converter == "pymupdf4llm":
            # Use PyMuPDF4LLM for conversion
            markdown_content = convert_with_pymupdf4llm(str(pdf_path))
        else:  # converter == "advanced"
            # Use improved extraction with PyMuPDF and pdfplumber
            markdown_content = ""

            # First extract tables with pdfplumber
            tables_by_page = []
            if extract_tables:
                tables_by_page = extract_tables_with_pdfplumber(str(pdf_path))
                table_locations = {
                    page_data["page_num"]: page_data["tables"]
                    for page_data in tables_by_page
                }

            # Extract text with PyMuPDF for better text extraction
            pdf_doc = fitz.open(str(pdf_path))

            for page_num, page in enumerate(pdf_doc):
                page_num += 1  # 1-indexed page numbers

                # Add page header
                markdown_content += f"# Page {page_num}\n\n"

                # Extract text with structure
                text = page.get_text("text")

                # Basic markdown conversion
                # Convert headings (assuming text in all caps is a heading)
                text_blocks = text.split("\n\n")
                formatted_blocks = []

                for block in text_blocks:
                    lines = block.strip().split("\n")
                    if (
                        lines
                        and lines[0]
                        and lines[0].strip()
                        and lines[0].strip().isupper()
                    ):
                        # This might be a heading
                        formatted_blocks.append(f"## {lines[0]}\n")
                        if len(lines) > 1:
                            formatted_blocks.append("\n".join(lines[1:]))
                    else:
                        formatted_blocks.append(block)

                markdown_content += "\n\n".join(formatted_blocks)

                # Add tables if available for this page
                if extract_tables and page_num in table_locations:
                    tables = table_locations[page_num]
                    for i, table in enumerate(tables):
                        table_md = format_table_for_markdown(table)
                        if table_md:
                            markdown_content += f"\n\n### Table {i+1}\n\n"
                            markdown_content += table_md + "\n\n"

                markdown_content += "\n\n"

            # Clean up the content
            # Remove excessive newlines
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

        # Check if we have any content
        if not markdown_content.strip():
            logger.error(f"No markdown content was generated for {pdf_path}")
            return None
            
        # Check if file already exists and log a warning (unless force option is used)
        if output_file.exists() and not force:
            logger.warning(f"Overwriting existing file: {output_file}")

        # Write markdown to file (using "w" mode explicitly overwrites any existing content)
        with open(output_file, "w", encoding="utf-8") as f:
            # Clear file by truncating to 0 bytes (redundant with 'w' mode, but being extra safe)
            f.truncate(0)
            # Write the new content
            f.write(markdown_content)

        return output_file
    except Exception as e:
        logger.error(f"Error converting {pdf_path}: {e}")
        return None


@click.command()
@click.option(
    "--input-dir",
    default=DEFAULT_INPUT_DIR,
    help="Directory containing PDF files",
)
@click.option(
    "--output-dir",
    default=DEFAULT_OUTPUT_DIR,
    help="Directory to save markdown files",
)
@click.option(
    "--converter",
    type=click.Choice(["docling", "advanced", "pymupdf4llm"]),
    default="docling",
    help="Conversion method: docling (default), advanced (PyMuPDF+pdfplumber), or pymupdf4llm (LLM-optimized)",
)
@click.option(
    "--extract-tables/--no-tables",
    default=True,
    help="Extract and format tables in the output markdown (only with advanced converter)",
)
@click.option(
    "--single-file",
    help="Process only a single file instead of a directory",
)
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.option(
    "--force",
    is_flag=True,
    help="Force overwrite of existing files without warning",
)
def main(
    input_dir: str,
    output_dir: str,
    converter: str,
    extract_tables: bool,
    single_file: Optional[str],
    verbose: bool,
    force: bool,
) -> None:
    """
    Parse PDF files as markdown with enhanced table support.

    This script converts PDFs to markdown, with special handling for tables
    and document structure. It can process a single file or an entire directory.

    Multiple conversion methods are supported:
    - docling: Better overall conversion but slower
    - advanced: Custom extraction with PyMuPDF and pdfplumber for better tables
    - pymupdf4llm: LLM-optimized output with good table structure preservation
    """
    if verbose:
        logger.setLevel(logging.DEBUG)

    # Ensure output directory exists
    ensure_directory_exists(output_dir)
    output_dir_path = Path(output_dir)

    if single_file:
        pdf_path = Path(single_file)
        if not pdf_path.exists():
            logger.error(f"File not found: {pdf_path}")
            return

        logger.info(f"Processing single file: {pdf_path}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Using converter: {converter}")
        logger.info(
            f"Table extraction: {'enabled' if extract_tables and converter == 'advanced' else 'disabled'}"
        )

        output_file = convert_pdf_to_markdown(
            pdf_path, output_dir_path, converter, extract_tables, force
        )
        if output_file:
            logger.info(f"Successfully converted {pdf_path} to {output_file}")
        else:
            logger.error(f"Failed to convert {pdf_path}")
    else:
        logger.info(f"Input directory: {input_dir}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Using converter: {converter}")
        logger.info(
            f"Table extraction: {'enabled' if extract_tables and converter == 'advanced' else 'disabled'}"
        )

        # Get all PDF files
        pdf_files = get_pdf_files(input_dir)
        if not pdf_files:
            logger.warning(f"No PDF files found in {input_dir}")
            return

        # Make sure we don't process the same file multiple times
        pdf_files = list(set(pdf_files))

        logger.info(f"Found {len(pdf_files)} unique PDF files")

        # Convert PDFs to markdown
        success_count = 0

        for pdf_file in tqdm(pdf_files, desc="Converting PDFs"):
            output_file = convert_pdf_to_markdown(
                pdf_file, output_dir_path, converter, extract_tables, force
            )
            if output_file:
                success_count += 1
                logger.debug(f"Converted {pdf_file} to {output_file}")

        logger.info(
            f"Conversion complete: {success_count}/{len(pdf_files)} files converted"
        )


if __name__ == "__main__":
    main()
