import json
import logging
import os
from pathlib import Path

import click
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("PDFExtractor")

DEFAULT_PDF_PATH = "/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/pdf_pages/_37.pdf"
# DEFAULT_PDF_PATH = (
#     "/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/esc_ccs.pdf"
# )
DEFAULT_OUTPUT_DIR = (
    "/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/docling/"
)


def ensure_directory_exists(path: str) -> None:
    """Ensure the directory exists, create if it doesn't."""
    Path(path).mkdir(parents=True, exist_ok=True)


def setup_converter(extract_tables: bool = True) -> DocumentConverter:
    """Setup and configure the Docling document converter."""
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = extract_tables

    if extract_tables:
        pipeline_options.table_structure_options.do_cell_matching = True

    pdf_format_options = PdfFormatOption(pipeline_options=pipeline_options)
    return DocumentConverter(format_options={InputFormat.PDF: pdf_format_options})


def extract_text_from_pdf(pdf_path: str, output_dir: str) -> None:
    """Extract text content from PDF as markdown."""
    pdf_name = Path(pdf_path).stem
    output_path = Path(output_dir) / f"{pdf_name}.md"
    ensure_directory_exists(output_dir)

    logger.info(f"Extracting text from: {pdf_path}")

    converter = setup_converter(extract_tables=False)
    result = converter.convert(pdf_path)
    doc = result.document

    try:
        markdown_content = doc.export_to_markdown()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logger.info(f"Text saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error saving text: {e}")


def extract_tables_from_pdf(pdf_path: str, output_dir: str) -> None:
    """Extract table structures from PDF."""
    pdf_name = Path(pdf_path).stem
    tables_dir = Path(output_dir) / pdf_name / "tables"
    ensure_directory_exists(str(tables_dir))

    logger.info(f"Extracting tables from: {pdf_path}")

    converter = setup_converter(extract_tables=True)
    result = converter.convert(pdf_path)
    doc = result.document

    logger.info(f"Found {len(doc.tables)} tables")

    if len(doc.tables) == 0:
        logger.warning("No tables detected")
        return

    tables = []
    for i, table in enumerate(doc.tables):
        try:
            table_data = {
                "table_id": i,
                "source_file": pdf_path,
                "caption": table.captions,
                "data": [],
            }

            # Try to extract table data
            if hasattr(table, "export_to_dataframe"):
                try:
                    df = table.export_to_dataframe()
                    if df is not None and not df.empty:
                        table_data["data"] = df.to_dict("records")
                        table_data["num_rows"] = len(df)
                        table_data["num_cols"] = len(df.columns)
                        logger.info(
                            f"Table {i}: {len(df)} rows x {len(df.columns)} cols"
                        )
                except Exception as e:
                    logger.warning(f"DataFrame extraction failed: {e}")

            # Try markdown export if dataframe failed
            if not table_data["data"] and hasattr(table, "export_to_markdown"):
                try:
                    md_content = table.export_to_markdown()
                    if md_content:
                        table_data["markdown_content"] = md_content
                        logger.info(f"Table {i}: extracted as markdown")
                except Exception as e:
                    logger.warning(f"Markdown extraction failed: {e}")

            if not table_data["data"] and "markdown_content" not in table_data:
                table_data["extraction_failed"] = True
                logger.warning(f"Could not extract data from table {i}")

            tables.append(table_data)

            # Save individual table
            table_path = tables_dir / f"table_{i:03d}.json"
            with open(table_path, "w", encoding="utf-8") as f:
                json.dump(table_data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            logger.error(f"Error processing table {i}: {e}")

    # Save summary
    if tables:
        summary_path = tables_dir / "tables_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "source_file": pdf_name,
                    "total_tables": len(tables),
                    "tables": tables,
                },
                f,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        logger.info(f"Saved {len(tables)} tables to {tables_dir}")


def extract_images_from_pdf(pdf_path: str, output_dir: str) -> None:
    """Extract images from PDF."""
    pdf_name = Path(pdf_path).stem
    images_dir = Path(output_dir) / pdf_name / "images"
    ensure_directory_exists(str(images_dir))

    logger.info(f"Extracting images from: {pdf_path}")

    converter = setup_converter(extract_tables=False)
    result = converter.convert(pdf_path)
    doc = result.document

    if not doc.pictures:
        logger.info("No images found")
        return

    image_paths = []
    for i, image in enumerate(doc.pictures):
        try:
            image_path = images_dir / f"image_{i:03d}.png"
            with open(image_path, "wb") as f:
                f.write(image.get_bytes())
            image_paths.append(str(image_path))
        except Exception as e:
            logger.error(f"Error saving image {i}: {e}")

    if image_paths:
        # Save metadata
        metadata = {
            "source_file": pdf_name,
            "total_images": len(image_paths),
            "image_paths": image_paths,
        }
        metadata_path = images_dir / "images_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(image_paths)} images to {images_dir}")


def process_single_pdf(
    pdf_path: str,
    output_dir: str,
    extract_text: bool,
    extract_tables: bool,
    extract_images: bool,
) -> None:
    """Process a single PDF file."""
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return

    logger.info(f"Processing: {pdf_path}")

    if extract_text:
        extract_text_from_pdf(pdf_path, output_dir)

    if extract_tables:
        extract_tables_from_pdf(pdf_path, output_dir)

    if extract_images:
        extract_images_from_pdf(pdf_path, output_dir)


def process_pdf_directory(
    pdf_dir: str,
    output_dir: str,
    extract_text: bool,
    extract_tables: bool,
    extract_images: bool,
) -> None:
    """Process all PDF files in a directory."""
    if not os.path.exists(pdf_dir):
        logger.error(f"Directory not found: {pdf_dir}")
        return

    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        logger.warning(f"No PDF files found in: {pdf_dir}")
        return

    logger.info(f"Found {len(pdf_files)} PDF files")

    with click.progressbar(pdf_files, label="Processing PDFs") as files:
        for pdf_file in files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            process_single_pdf(
                pdf_path, output_dir, extract_text, extract_tables, extract_images
            )


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def cli(verbose):
    """Simple PDF extractor for text, tables, and images."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command("text")
@click.option("--pdf-path", default=DEFAULT_PDF_PATH, help="Path to PDF file")
@click.option("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory")
def text(pdf_path: str, output_dir: str) -> None:
    """Extract text from PDF."""
    if os.path.isfile(pdf_path):
        process_single_pdf(
            pdf_path,
            output_dir,
            extract_text=True,
            extract_tables=False,
            extract_images=False,
        )
    else:
        process_pdf_directory(
            pdf_path,
            output_dir,
            extract_text=True,
            extract_tables=False,
            extract_images=False,
        )


@cli.command("tables")
@click.option("--pdf-path", default=DEFAULT_PDF_PATH, help="Path to PDF file")
@click.option("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory")
def tables(pdf_path: str, output_dir: str) -> None:
    """Extract tables from PDF."""
    if os.path.isfile(pdf_path):
        process_single_pdf(
            pdf_path,
            output_dir,
            extract_text=False,
            extract_tables=True,
            extract_images=False,
        )
    else:
        process_pdf_directory(
            pdf_path,
            output_dir,
            extract_text=False,
            extract_tables=True,
            extract_images=False,
        )


@cli.command("images")
@click.option("--pdf-path", default=DEFAULT_PDF_PATH, help="Path to PDF file")
@click.option("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory")
def images(pdf_path: str, output_dir: str) -> None:
    """Extract images from PDF."""
    if os.path.isfile(pdf_path):
        process_single_pdf(
            pdf_path,
            output_dir,
            extract_text=False,
            extract_tables=False,
            extract_images=True,
        )
    else:
        process_pdf_directory(
            pdf_path,
            output_dir,
            extract_text=False,
            extract_tables=False,
            extract_images=True,
        )


@cli.command("all")
@click.option("--pdf-path", default=DEFAULT_PDF_PATH, help="Path to PDF file")
@click.option("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory")
def all_content(pdf_path: str, output_dir: str) -> None:
    """Extract text, tables, and images from PDF."""
    if os.path.isfile(pdf_path):
        process_single_pdf(
            pdf_path,
            output_dir,
            extract_text=True,
            extract_tables=True,
            extract_images=True,
        )
    else:
        process_pdf_directory(
            pdf_path,
            output_dir,
            extract_text=True,
            extract_tables=True,
            extract_images=True,
        )


if __name__ == "__main__":
    cli()
