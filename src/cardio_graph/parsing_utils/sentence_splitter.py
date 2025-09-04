import logging
import os
from pathlib import Path

import click
import spacy
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("SentenceSplitter")


def ensure_directory_exists(path: str) -> None:
    """Ensure the directory exists, create if it doesn't."""
    directory = Path(path)
    if not directory.exists():
        logger.info(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def split_text_with_scispacy(text: str) -> list[str]:
    """Splits a given text into sentences using ScispaCy."""
    nlp = spacy.load("en_core_sci_lg")
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    return sentences


def split_text_with_langchain(
    text: str, chunk_size: int, chunk_overlap: int
) -> list[str]:
    """Splits a given text into chunks using Langchain's RecursiveCharacterTextSplitter."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    return chunks


@click.command()
@click.option(
    "--input-file",
    default="/prj/doctoral_letters/guide/data/guidelines/text/esc_ccs.txt",
    help="Path to the input text file.",
)
@click.option(
    "--output-dir",
    default="/prj/doctoral_letters/guide/data/guidelines/sentences",
    help="Directory to save the output file.",
)
@click.option(
    "--splitter",
    type=click.Choice(["scispacy", "langchain"], case_sensitive=False),
    default="scispacy",
    help="The sentence splitter to use.",
)
@click.option(
    "--chunk-size",
    default=500,
    help="Chunk size for Langchain's RecursiveCharacterTextSplitter.",
)
@click.option(
    "--chunk-overlap",
    default=0,
    help="Chunk overlap for Langchain's RecursiveCharacterTextSplitter.",
)
def main(
    input_file: str,
    output_dir: str,
    splitter: str,
    chunk_size: int,
    chunk_overlap: int,
):
    """Splits a text file into sentences or chunks and saves the result."""
    ensure_directory_exists(output_dir)

    output_file_path = Path(output_dir) / f"{Path(input_file).stem}_{splitter}.txt"

    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    logger.info(f"Splitting text from {input_file} using {splitter}...")

    if splitter == "scispacy":
        sentences = split_text_with_scispacy(text)
    elif splitter == "langchain":
        sentences = split_text_with_langchain(text, chunk_size, chunk_overlap)
    else:
        logger.error(f"Unknown splitter: {splitter}")
        return

    with open(output_file_path, "w", encoding="utf-8") as f:
        for sentence in sentences:
            f.write(sentence + "\n")

    logger.info(f"Successfully saved {len(sentences)} sentences to {output_file_path}")


if __name__ == "__main__":
    main()
