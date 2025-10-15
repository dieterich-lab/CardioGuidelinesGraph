import logging
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

import click
from langchain_text_splitters import RecursiveCharacterTextSplitter

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


def extract_tables_from_markdown(markdown_content: str) -> Tuple[str, List[str]]:
    """
    Extract tables from markdown content and return cleaned content and table list.

    Returns:
        Tuple of (cleaned_markdown, list_of_tables)
    """
    # Pattern to match markdown tables (header row + separator + data rows)
    table_pattern = r"(\|.*\|\n\|[\s\-\|:]+\|\n(?:\|.*\|\n)+)"

    tables = []
    table_counter = 0

    def replace_table(match):
        nonlocal table_counter
        table_content = match.group(1)
        tables.append(table_content.strip())
        table_counter += 1
        # Replace table with a placeholder that indicates where the table was
        return f"[TABLE_{table_counter}]\n\n"

    # Remove tables from content and collect them
    cleaned_content = re.sub(
        table_pattern, replace_table, markdown_content, flags=re.MULTILINE
    )

    logger.info(f"Extracted {len(tables)} tables from markdown content")
    return cleaned_content, tables


def clean_page_artifacts(markdown_content: str) -> str:
    """
    Remove page headers, footers, and other PDF conversion artifacts from markdown content.

    This addresses issues where sentences get split across page breaks during chunking.
    """
    # Comprehensive patterns for page artifacts based on observed variations
    patterns = [
        # Full pattern with URL and "from Downloaded"
        r"2025 April 02 on user Heidelberg Universität.*?from Downloaded",
        # Pattern with URL and "Downloaded" at end
        r"2025 April 02 on user Heidelberg Universität.*?Downloaded",
        # Pattern with just URL
        r"2025 April 02 on user Heidelberg Universität.*?https://academic\.oup\.com/eurheartj/article/\d+/\d+/\d+",
        # Pattern ending with "by Downloaded"
        r"2025 April 02 on user Heidelberg Universität by Downloaded",
        # Simple pattern without additional text
        r"2025 April 02 on user Heidelberg Universität",
    ]

    cleaned_content = markdown_content
    total_removed = 0
    for pattern in patterns:
        before_len = len(cleaned_content)
        cleaned_content = re.sub(
            pattern, "", cleaned_content, flags=re.MULTILINE | re.DOTALL
        )
        removed = before_len - len(cleaned_content)
        if removed > 0:
            total_removed += removed
            logger.debug(f"Pattern removed {removed} characters")

    # Remove standalone "---" lines that might be left over
    cleaned_content = re.sub(r"^---\s*$", "", cleaned_content, flags=re.MULTILINE)

    # Clean up extra whitespace
    cleaned_content = re.sub(r"\n{3,}", "\n\n", cleaned_content)

    logger.info(
        f"Cleaned page artifacts from markdown content - removed {total_removed} characters"
    )
    return cleaned_content.strip()


def save_tables_to_files(
    tables: List[str], output_dir: str, base_filename: str
) -> None:
    """Save each table to a separate file."""
    tables_dir = os.path.join(output_dir, "tables")
    ensure_directory_exists(tables_dir)

    # Clean up old table files with the same base filename
    import glob

    old_table_pattern = os.path.join(tables_dir, f"{base_filename}_table_*.md")
    old_tables = glob.glob(old_table_pattern)
    for old_table in old_tables:
        try:
            os.remove(old_table)
            logger.debug(f"Removed old table file: {old_table}")
        except Exception as e:
            logger.warning(f"Could not remove old table file {old_table}: {e}")

    for i, table in enumerate(tables):
        table_filename = f"{base_filename}_table_{i:03d}.md"
        table_path = os.path.join(tables_dir, table_filename)

        try:
            with open(table_path, "w", encoding="utf-8") as f:
                f.write(table)
            logger.debug(f"Saved table {i} to: {table_path}")
        except Exception as e:
            logger.error(f"Error saving table {i}: {e}")

    logger.info(f"Saved {len(tables)} tables to: {tables_dir}")


def split_markdown_into_chunks(
    markdown_content: str, chunk_size: int = 1000, chunk_overlap: int = 200
) -> List[str]:
    """
    Split markdown content into chunks using sentence-aware splitting.

    Uses RecursiveCharacterTextSplitter with sentence-aware separators to avoid
    splitting mid-sentence.
    """
    try:
        # Use sentence-aware separators: prioritize sentence endings, then paragraphs, then words
        separators = [
            "\n\n",  # Paragraph breaks
            ". ",  # Sentence endings (period + space)
            "! ",  # Sentence endings (exclamation + space)
            "? ",  # Sentence endings (question + space)
            "\n",  # Line breaks
            " ",  # Word boundaries
            "",  # Character level (fallback)
        ]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False,
        )

        chunks = text_splitter.split_text(markdown_content)
        logger.info(f"Split markdown into {len(chunks)} chunks")
        return chunks
    except Exception as e:
        logger.error(f"Error splitting markdown: {e}")
        return []


def save_chunks_to_files(
    chunks: List[str], output_dir: str, base_filename: str
) -> None:
    """Save each chunk to a separate file."""
    ensure_directory_exists(output_dir)

    # Clean up old chunk files with the same base filename
    import glob

    old_chunk_pattern = os.path.join(output_dir, f"{base_filename}_chunk_*.md")
    old_chunks = glob.glob(old_chunk_pattern)
    for old_chunk in old_chunks:
        try:
            os.remove(old_chunk)
            logger.debug(f"Removed old chunk file: {old_chunk}")
        except Exception as e:
            logger.warning(f"Could not remove old chunk file {old_chunk}: {e}")

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
    input_path: str,
    output_dir: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    extract_tables: bool = True,
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

        # Clean page artifacts first
        cleaned_content = clean_page_artifacts(markdown_content)
        logger.info(f"After cleaning page artifacts: {len(cleaned_content)} characters")

        # Debug: Check if artifacts still exist
        if "2025 April 02 on user Heidelberg" in cleaned_content:
            logger.warning("WARNING: Page artifacts still found in cleaned content!")
            # Count occurrences
            count = cleaned_content.count("2025 April 02 on user Heidelberg")
            logger.warning(f"Found {count} remaining page artifacts")
        else:
            logger.info("Page artifacts successfully removed from content")

        # Extract tables if requested
        if extract_tables:
            cleaned_content, tables = extract_tables_from_markdown(cleaned_content)
            logger.info(
                f"Original content: {len(markdown_content)} chars, cleaned content: {len(cleaned_content)} chars"
            )
        else:
            tables = []

        # Split into chunks
        chunks = split_markdown_into_chunks(cleaned_content, chunk_size, chunk_overlap)

        if not chunks:
            logger.warning("No chunks generated")
            return

        # Save chunks to files
        base_filename = Path(input_path).stem
        save_chunks_to_files(chunks, output_dir, base_filename)

        # Save tables to separate files if extracted
        if extract_tables and tables:
            save_tables_to_files(tables, output_dir, base_filename)

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
@click.option(
    "--extract-tables/--no-extract-tables",
    default=True,
    help="Extract tables to separate files and remove from chunks.",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def split_markdown(
    input_file: str,
    output_dir: str,
    chunk_size: int,
    chunk_overlap: int,
    extract_tables: bool,
    verbose: bool,
) -> None:
    """Split a markdown file into chunks and save them to separate files."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        process_markdown_file(
            input_file, output_dir, chunk_size, chunk_overlap, extract_tables
        )
        logger.info("Markdown chunking completed successfully")

    except Exception as e:
        logger.error(f"Error during markdown chunking: {e}")


if __name__ == "__main__":
    split_markdown()
