import json
import logging
import os
from pathlib import Path

import click
from docling.datamodel import vlm_model_specs
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, VlmPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("PDFExtractor")

DEFAULT_PDF_PATH = (
    "/home/pwiesenbach/CardioGuidelinesGraph/src/data/guidelines/pdf_pages/_37.pdf"
)
DEFAULT_OUTPUT_DIR = (
    "/home/pwiesenbach/CardioGuidelinesGraph/src/data/guidelines/docling/"
)


def ensure_directory_exists(path: str) -> None:
    """Ensure the directory exists, create if it doesn't."""
    Path(path).mkdir(parents=True, exist_ok=True)


def setup_converter(
    extract_tables: bool = True, use_vlm: bool = False
) -> DocumentConverter:
    """Setup and configure the Docling document converter."""
    if use_vlm:
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                ),
            }
        )
        return converter

    else:
        # Use standard pipeline
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = extract_tables

        if extract_tables:
            pipeline_options.table_structure_options.do_cell_matching = True

        pdf_format_options = PdfFormatOption(pipeline_options=pipeline_options)
        return DocumentConverter(format_options={InputFormat.PDF: pdf_format_options})


def extract_text_from_pdf(
    pdf_path: str, output_dir: str, use_vlm: bool = False
) -> None:
    """Extract text content from PDF as markdown."""
    pdf_name = Path(pdf_path).stem
    output_path = Path(output_dir) / f"{pdf_name}.md"

    logger.info(
        f"Extracting text from: {pdf_path}" + (" (using VLM)" if use_vlm else "")
    )

    converter = setup_converter(extract_tables=False, use_vlm=use_vlm)
    result = converter.convert(pdf_path)
    doc = result.document

    try:
        markdown_content = doc.export_to_markdown()
        if markdown_content.strip():  # Only create directory if content exists
            ensure_directory_exists(output_dir)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            logger.info(f"Text saved to: {output_path}")
        else:
            logger.warning(f"No text content found in: {pdf_path}")
    except Exception as e:
        logger.error(f"Error saving text: {e}")


def extract_tables_from_pdf(
    pdf_path: str, output_dir: str, use_vlm: bool = False
) -> None:
    """Extract table structures from PDF."""
    pdf_name = Path(pdf_path).stem
    tables_dir = Path(output_dir) / pdf_name / "tables"

    logger.info(
        f"Extracting tables from: {pdf_path}" + (" (using VLM)" if use_vlm else "")
    )

    converter = setup_converter(extract_tables=True, use_vlm=use_vlm)
    result = converter.convert(pdf_path)
    doc = result.document

    logger.info(f"Found {len(doc.tables)} tables")

    if len(doc.tables) == 0:
        logger.warning("No tables detected")
        return

    # Only create directories if tables are found
    ensure_directory_exists(str(tables_dir))

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


def extract_images_from_pdf(
    pdf_path: str, output_dir: str, use_vlm: bool = False
) -> None:
    """Extract images from PDF."""
    pdf_name = Path(pdf_path).stem
    images_dir = Path(output_dir) / pdf_name / "images"

    logger.info(
        f"Extracting images from: {pdf_path}" + (" (using VLM)" if use_vlm else "")
    )

    converter = setup_converter(extract_tables=False, use_vlm=use_vlm)
    result = converter.convert(pdf_path)
    doc = result.document

    if not doc.pictures:
        logger.info("No images found")
        return

    # Only create directories if images are found
    ensure_directory_exists(str(images_dir))

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
    use_vlm: bool = False,
) -> None:
    """Process a single PDF file."""
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return

    logger.info(
        f"Processing: {pdf_path}" + (" (using SMOLDOCLING VLM)" if use_vlm else "")
    )

    if extract_text:
        extract_text_from_pdf(pdf_path, output_dir, use_vlm)

    if extract_tables:
        extract_tables_from_pdf(pdf_path, output_dir, use_vlm)

    if extract_images:
        extract_images_from_pdf(pdf_path, output_dir, use_vlm)


def process_pdf_directory(
    pdf_dir: str,
    output_dir: str,
    extract_text: bool,
    extract_tables: bool,
    extract_images: bool,
    use_vlm: bool = False,
) -> None:
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
            process_single_pdf(
                pdf_path,
                subdir_path,
                extract_text,
                extract_tables,
                extract_images,
                use_vlm,
            )

    return None


def validate_content_types(ctx, param, value):
    # This will be checked after all parameters are processed
    if (
        ctx.params.get("text") is False
        and ctx.params.get("tables") is False
        and ctx.params.get("images") is False
    ):
        raise click.UsageError(
            "At least one content type (--text, --tables, or --images) must be specified."
        )
    return value


@click.command()
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option(
    "--pdf-path", default=DEFAULT_PDF_PATH, help="Path to PDF file or directory"
)
@click.option("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory")
@click.option("--text", is_flag=True, help="Extract text from PDF")
@click.option("--tables", is_flag=True, help="Extract tables from PDF")
@click.option("--images", is_flag=True, help="Extract images from PDF")
@click.option(
    "--use-vlm",
    is_flag=True,
    help="Use SMOLDOCLING VLM for enhanced visual extraction",
    callback=validate_content_types,
)
def cli(verbose, pdf_path, output_dir, text, tables, images, use_vlm):
    """
    PDF content extractor for text, tables, and images.

    Specify which content types to extract using the --text, --tables, and --images flags.
    At least one content type must be specified.

    Examples:
      # Extract only tables
      python parse_pdfs_with_docling.py --tables --pdf-path file.pdf

      # Extract both text and images
      python parse_pdfs_with_docling.py --text --images --pdf-path file.pdf

      # Extract all content types
      python parse_pdfs_with_docling.py --text --tables --images --pdf-path file.pdf
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")

    logger.info(f"Extracting content from: {pdf_path}")
    logger.info(
        f"Content types: "
        + f"{'text ' if text else ''}"
        + f"{'tables ' if tables else ''}"
        + f"{'images ' if images else ''}"
    )

    if os.path.isfile(pdf_path):
        process_single_pdf(
            pdf_path,
            output_dir,
            extract_text=text,
            extract_tables=tables,
            extract_images=images,
            use_vlm=use_vlm,
        )
    else:
        # For directories, results are saved within process_pdf_directory in a subdirectory
        process_pdf_directory(
            pdf_path,
            output_dir,
            extract_text=text,
            extract_tables=tables,
            extract_images=images,
            use_vlm=use_vlm,
        )
        logger.info(f"Completed processing directory: {pdf_path}")


if __name__ == "__main__":
    cli()
