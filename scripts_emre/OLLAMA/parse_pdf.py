import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import click
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("DoclingParser")


def ensure_directory_exists(path: str) -> None:
    """Ensure the directory exists, create if it doesn't."""
    directory = Path(path)
    if not directory.exists():
        logger.info(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def setup_converter(
    extract_images: bool = True, extract_tables: bool = True
) -> DocumentConverter:
    """Setup and configure the Docling document converter."""
    # Configure PDF pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = extract_tables
    pipeline_options.table_structure_options.do_cell_matching = True

    # Configure format options
    pdf_format_options = PdfFormatOption(pipeline_options=pipeline_options)

    # Create converter with options
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: pdf_format_options,
        }
    )

    return converter


def extract_images_from_document(doc, output_dir: str) -> List[str]:
    """Extract and save images from the document."""
    image_paths = []
    images_dir = Path(output_dir) / "images"
    ensure_directory_exists(str(images_dir))

    for i, (image_ref, image) in enumerate(doc.pictures.items()):
        try:
            image_path = images_dir / f"image_{i:03d}.png"
            with open(image_path, "wb") as f:
                f.write(image.get_bytes())
            image_paths.append(str(image_path))
            logger.info(f"Saved image: {image_path}")
        except Exception as e:
            logger.error(f"Error saving image {i}: {e}")

    return image_paths


def extract_tables_from_document(doc, output_dir: str) -> List[Dict]:
    """Extract and save table structures from the document."""
    tables = []
    tables_dir = Path(output_dir) / "tables"
    ensure_directory_exists(str(tables_dir))

    for i, table in enumerate(doc.tables):
        try:
            table_data = {
                "table_id": i,
                "caption": getattr(table, "caption", ""),
                "num_rows": table.num_rows if hasattr(table, "num_rows") else 0,
                "num_cols": table.num_cols if hasattr(table, "num_cols") else 0,
                "data": [],
            }

            # Extract table data if available
            if hasattr(table, "table_data"):
                table_data["data"] = table.table_data
            elif hasattr(table, "to_dict"):
                table_data.update(table.to_dict())

            tables.append(table_data)

            # Save individual table as JSON
            table_path = tables_dir / f"table_{i:03d}.json"
            with open(table_path, "w", encoding="utf-8") as f:
                json.dump(table_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved table {i}: {table_path}")

        except Exception as e:
            logger.error(f"Error processing table {i}: {e}")

    return tables


def save_markdown(doc, output_path: str) -> str:
    """Save the document as markdown."""
    try:
        markdown_content = doc.export_to_markdown()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logger.info(f"Saved markdown: {output_path}")
        return markdown_content
    except Exception as e:
        logger.error(f"Error saving markdown: {e}")
        return ""


def save_document_metadata(doc, output_path: str) -> Dict:
    """Save document metadata and structure information."""
    try:
        metadata = {
            "title": getattr(doc, "title", ""),
            "num_pages": len(doc.pages) if hasattr(doc, "pages") else 0,
            "num_tables": len(doc.tables) if hasattr(doc, "tables") else 0,
            "num_images": len(doc.pictures) if hasattr(doc, "pictures") else 0,
            "language": getattr(doc, "language", ""),
            "creation_date": getattr(doc, "creation_date", ""),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved metadata: {output_path}")
        return metadata

    except Exception as e:
        logger.error(f"Error saving metadata: {e}")
        return {}


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def cli(verbose):
    """Parse PDF documents using IBM's Docling library."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command("parse")
@click.option(
    "--pdf-path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/esc_ccs.pdf",
    help="Path to the PDF file to parse.",
)
@click.option(
    "--output-dir",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/docling_output/",
    help="Directory to save parsed outputs.",
)
@click.option(
    "--extract-images", is_flag=True, default=True, help="Extract images from PDF."
)
@click.option(
    "--extract-tables", is_flag=True, default=True, help="Extract table structures."
)
@click.option(
    "--save-markdown", is_flag=True, default=True, help="Save document as markdown."
)
def parse_pdf(
    pdf_path: str,
    output_dir: str,
    extract_images: bool,
    extract_tables: bool,
    save_markdown: bool,
) -> None:
    """Parse a PDF file and extract markdown, tables, and images."""
    try:
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return

        # Setup output directory
        pdf_name = Path(pdf_path).stem
        full_output_dir = Path(output_dir) / pdf_name
        ensure_directory_exists(str(full_output_dir))

        logger.info(f"Starting PDF parsing: {pdf_path}")
        logger.info(f"Output directory: {full_output_dir}")

        # Setup converter
        converter = setup_converter(
            extract_images=extract_images, extract_tables=extract_tables
        )

        # Convert document
        logger.info("Converting document...")
        result = converter.convert(pdf_path)
        doc = result.document

        logger.info(f"Document converted successfully")
        logger.info(f"Pages: {len(doc.pages) if hasattr(doc, 'pages') else 'Unknown'}")
        logger.info(
            f"Tables: {len(doc.tables) if hasattr(doc, 'tables') else 'Unknown'}"
        )
        logger.info(
            f"Images: {len(doc.pictures) if hasattr(doc, 'pictures') else 'Unknown'}"
        )

        # Save markdown
        if save_markdown:
            markdown_path = full_output_dir / f"{pdf_name}.md"
            save_markdown(doc, str(markdown_path))

        # Extract images
        if extract_images:
            image_paths = extract_images_from_document(doc, str(full_output_dir))
            logger.info(f"Extracted {len(image_paths)} images")

        # Extract tables
        if extract_tables:
            tables = extract_tables_from_document(doc, str(full_output_dir))
            logger.info(f"Extracted {len(tables)} tables")

            # Save consolidated tables
            if tables:
                consolidated_tables_path = full_output_dir / "all_tables.json"
                with open(consolidated_tables_path, "w", encoding="utf-8") as f:
                    json.dump(tables, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved consolidated tables: {consolidated_tables_path}")

        # Save metadata
        metadata_path = full_output_dir / "metadata.json"
        metadata = save_document_metadata(doc, str(metadata_path))

        # Create summary
        summary = {
            "pdf_file": pdf_path,
            "output_directory": str(full_output_dir),
            "processing_completed": True,
            "extracted_components": {
                "markdown": save_markdown,
                "images": extract_images,
                "tables": extract_tables,
            },
            "statistics": metadata,
        }

        summary_path = full_output_dir / "processing_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info("PDF parsing completed successfully!")
        logger.info(f"Processing summary saved: {summary_path}")

    except Exception as e:
        logger.error(f"Error during PDF parsing: {e}")


@cli.command("batch")
@click.option(
    "--input-dir",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/pdfs/",
    help="Directory containing PDF files to process.",
)
@click.option(
    "--output-dir",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/docling_output/",
    help="Directory to save parsed outputs.",
)
@click.option(
    "--extract-images", is_flag=True, default=True, help="Extract images from PDFs."
)
@click.option(
    "--extract-tables", is_flag=True, default=True, help="Extract table structures."
)
@click.option(
    "--save-markdown", is_flag=True, default=True, help="Save documents as markdown."
)
def batch_parse(
    input_dir: str,
    output_dir: str,
    extract_images: bool,
    extract_tables: bool,
    save_markdown: bool,
) -> None:
    """Parse multiple PDF files in a directory."""
    try:
        if not os.path.exists(input_dir):
            logger.error(f"Input directory not found: {input_dir}")
            return

        pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
        if not pdf_files:
            logger.warning(f"No PDF files found in: {input_dir}")
            return

        logger.info(f"Found {len(pdf_files)} PDF files to process")

        # Process each PDF
        with click.progressbar(pdf_files, label="Processing PDFs") as files:
            for pdf_file in files:
                pdf_path = os.path.join(input_dir, pdf_file)
                ctx = click.get_current_context()
                ctx.invoke(
                    parse_pdf,
                    pdf_path=pdf_path,
                    output_dir=output_dir,
                    extract_images=extract_images,
                    extract_tables=extract_tables,
                    save_markdown=save_markdown,
                )

        logger.info("Batch processing completed!")

    except Exception as e:
        logger.error(f"Error during batch processing: {e}")


if __name__ == "__main__":
    cli()
