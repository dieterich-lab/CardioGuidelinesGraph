import logging
import os
import sys
from pathlib import Path

import click
from langchain_text_splitters import MarkdownTextSplitter

sys.path.append("..")  # isort:skip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("MarkdownChunker")


def ensure_directory_exists(path: str) -> None:
    """Ensure the directory exists, create if it doesn't."""
    directory = Path(path)
    if not directory.exists():
        logger.info(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def split_markdown_into_chunks(
    markdown_content: str, chunk_size: int = 1000, chunk_overlap: int = 200
) -> list[str]:
    """Split markdown content into chunks using MarkdownTextSplitter."""
    try:
        markdown_splitter = MarkdownTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        chunks = markdown_splitter.split_text(markdown_content)
        logger.info(f"Split markdown into {len(chunks)} chunks")
        return chunks
    except Exception as e:
        logger.error(f"Error splitting markdown: {e}")
        return []


def save_chunks_to_files(
    chunks: list[str], output_dir: str, base_filename: str
) -> None:
    """Save each chunk to a separate file."""
    ensure_directory_exists(output_dir)

    for i, chunk in enumerate(chunks):
        chunk_filename = f"{base_filename}_chunk_{i:03d}.md"
        chunk_path = os.path.join(output_dir, chunk_filename)

        try:
            with open(chunk_path, "w", encoding="utf-8") as f:
                f.write(chunk)
            logger.debug(f"Saved chunk {i} to: {chunk_path}")
        except Exception as e:
            logger.error(f"Error saving chunk {i}: {e}")

    logger.info(f"Saved {len(chunks)} chunks to: {output_dir}")


def process_markdown_file(
    input_path: str, output_dir: str, chunk_size: int = 1000, chunk_overlap: int = 200
) -> None:
    """Process a single markdown file and split it into chunks."""
    if not os.path.exists(input_path):
        logger.error(f"Markdown file not found: {input_path}")
        return

    logger.info(f"Processing markdown file: {input_path}")

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        logger.info(f"Read {len(markdown_content)} characters from file")

        # Split into chunks
        chunks = split_markdown_into_chunks(markdown_content, chunk_size, chunk_overlap)

        if not chunks:
            logger.warning("No chunks generated")
            return

        # Save chunks to files
        base_filename = Path(input_path).stem
        save_chunks_to_files(chunks, output_dir, base_filename)

    except Exception as e:
        logger.error(f"Error processing markdown file: {e}")


@click.command()
@click.option(
    "--input-file",
    default="/prj/doctoral_letters/guide/data/guidelines/markdown/esc_ccs.md",
    help="Path to input markdown file.",
)
@click.option(
    "--output-dir",
    default="/prj/doctoral_letters/guide/data/guidelines/markdown/chunks",
    help="Output directory for chunks.",
)
@click.option(
    "--chunk-size",
    default=1000,
    type=int,
    help="Size of each chunk in characters.",
)
@click.option(
    "--chunk-overlap",
    default=200,
    type=int,
    help="Overlap between chunks in characters.",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def split_markdown(
    input_file: str, output_dir: str, chunk_size: int, chunk_overlap: int, verbose: bool
) -> None:
    """Split a markdown file into chunks and save them to separate files."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        process_markdown_file(input_file, output_dir, chunk_size, chunk_overlap)
        logger.info("Markdown chunking completed successfully")

    except Exception as e:
        logger.error(f"Error during markdown chunking: {e}")


if __name__ == "__main__":
    split_markdown()
