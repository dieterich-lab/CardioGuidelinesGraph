import base64
import glob
import json
import logging
import os
import pickle
import sys
from pathlib import Path

import click
import fitz
from baml_client.types import IfElseTree, SemanticTriple
from baml_py import Image

sys.path.append("..")  # isort:skip

from baml_client.sync_client import b  # isort:skip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("pdf_processor")


def ensure_directory_exists(path: str) -> None:
    """Ensure the directory exists, create if it doesn't."""
    directory = Path(path)
    if not directory.exists():
        logger.info(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def cli(verbose):
    """Process images from PDFs for structure extraction and analysis."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command("extract")
@click.option(
    "--pdf-path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/esc_ccs.pdf",
    help="Path to the PDF file.",
)
@click.option(
    "--img-path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/images/esc_ccs/",
    help="Path to the directory to save images.",
)
def extract_images(pdf_path: str, img_path: str) -> None:
    """Extract images from PDF and save them as PNG files."""
    try:
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return

        ensure_directory_exists(img_path)
        doc = fitz.open(pdf_path)

        # Temporarily store errors to report after progress bar completes
        errors = []
        with click.progressbar(
            enumerate(doc), length=len(doc), label="Extracting images"
        ) as pages:
            for count, page in pages:
                try:
                    pix = page.get_pixmap(
                        matrix=fitz.Identity,
                        dpi=None,
                        colorspace=fitz.csRGB,
                        clip=None,
                        alpha=True,
                        annots=True,
                    )
                    output_path = os.path.join(img_path, f"{count}.png")
                    pix.save(output_path)
                except Exception as e:
                    errors.append((count + 1, str(e)))

        # Report errors after progress bar completes
        for page_num, error in errors:
            logger.error(f"Error processing page {page_num}: {error}")

        logger.info(f"Successfully extracted {len(doc)} pages to {img_path}")
    except Exception as e:
        logger.error(f"Error during image extraction: {e}")


@cli.command("parse")
@click.option(
    "--imgx-path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/images/esc_ccs/",
    help="Path to the directory with images.",
)
def parse_images(imgx_path: str) -> None:
    """Parse images and save extracted structures as pickle files."""
    try:
        if not os.path.exists(imgx_path):
            logger.error(f"Image directory not found: {imgx_path}")
            return

        imgx_paths = glob.glob(os.path.join(imgx_path, "*"))
        if not imgx_paths:
            logger.warning(f"No images found in: {imgx_path}")
            return

        # Create output directory for pickle files
        pkl_path = Path(imgx_path.replace("images", "structures_pkl"))
        ensure_directory_exists(str(pkl_path))

        # Temporarily store errors to report after progress bar completes
        errors = []
        with click.progressbar(
            imgx_paths, length=len(imgx_paths), label="Parsing images"
        ) as images:
            for img_path in images:
                try:
                    with open(img_path, "rb") as image_file:
                        img_b64 = base64.b64encode(image_file.read()).decode("utf-8")
                    img = Image.from_base64("image/png", img_b64)
                    res = b.Image2Tree(img=img)

                    pkl_name = Path(img_path).stem + ".pkl"
                    with open(pkl_path / pkl_name, "wb") as pkl_file:
                        pickle.dump(res, pkl_file)
                except Exception as e:
                    errors.append((img_path, str(e)))

        # Report errors after progress bar completes
        for img_path, error in errors:
            logger.error(f"Error parsing image {img_path}: {error}")

        logger.info(f"Successfully parsed {len(imgx_paths)} images")
    except Exception as e:
        logger.error(f"Error during image parsing: {e}")


@cli.command("save_json")
@click.option(
    "--imgx-path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/images/esc_ccs/",
    help="Path to the directory with images to read structures from.",
)
def save_json(imgx_path: str) -> None:
    """Read structures from pickle files and save as JSON."""
    try:
        pkl_path = Path(imgx_path.replace("images", "structures_pkl"))
        if not pkl_path.exists():
            logger.error(f"Pickle directory not found: {pkl_path}")
            return

        struct_paths = glob.glob(str(pkl_path / "*.pkl"))
        if not struct_paths:
            logger.warning(f"No pickle files found in: {pkl_path}")
            return

        # Create output directory for JSON files
        json_path = imgx_path.replace("images", "structures_json")
        ensure_directory_exists(json_path)

        triples, trees = list(), list()

        # Temporarily store errors to report after progress bar completes
        errors = []
        with click.progressbar(
            struct_paths, length=len(struct_paths), label="Processing structures"
        ) as paths:
            for struc_path in paths:
                try:
                    with open(struc_path, "rb") as pkl_file:
                        res = pickle.load(pkl_file)
                    for x in res.list:
                        if type(x) is SemanticTriple:
                            triples.append(x.model_dump())
                        elif type(x) is IfElseTree:
                            trees.append(x.model_dump())
                except Exception as e:
                    errors.append((struc_path, str(e)))

        # Report errors after progress bar completes
        for struc_path, error in errors:
            logger.error(f"Error processing structure file {struc_path}: {error}")

        triples_file = os.path.join(json_path, "triples.json")
        trees_file = os.path.join(json_path, "trees.json")

        with open(triples_file, "w") as f:
            json.dump(triples, f, indent=4)

        with open(trees_file, "w") as f:
            json.dump(trees, f, indent=4)

        logger.info(f"Extracted {len(triples)} triples and {len(trees)} trees")
        logger.info(f"Results saved to {triples_file} and {trees_file}")
    except Exception as e:
        logger.error(f"Error during JSON conversion: {e}")


@cli.command("process_all")
@click.option(
    "--pdf-path",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/esc_ccs.pdf",
    help="Path to the PDF file.",
)
@click.option(
    "--output-dir",
    default="/home/pwiesenbach/CardioGuidelinesGraph/scripts_emre/data/guidelines/",
    help="Base output directory.",
)
@click.pass_context
def process_all(ctx, pdf_path: str, output_dir: str) -> None:
    """Run the entire pipeline: extract images, parse them, and save as JSON."""
    pdf_name = Path(pdf_path).stem
    img_path = os.path.join(output_dir, "images", pdf_name) + "/"

    logger.info("Starting full processing pipeline")

    # Extract images from PDF
    ctx.invoke(extract_images, pdf_path=pdf_path, img_path=img_path)

    # Parse images
    ctx.invoke(parse_images, imgx_path=img_path)

    # Save as JSON
    ctx.invoke(save_json, imgx_path=img_path)

    logger.info("Complete pipeline execution finished successfully")


if __name__ == "__main__":
    cli()
