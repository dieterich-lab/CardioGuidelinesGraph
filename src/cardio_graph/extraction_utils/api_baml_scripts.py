import os, time, logging
from pathlib import Path
from cardio_graph.baml_client.sync_client import b  # isort:skip
from cardio_graph.neo4j_utils.baml_to_cypher import (
    triples_to_cypher,
    execute_baml_cypher_dev1,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("apiconverter.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

output_path = "/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/md_to_cypher"
out_dir = "/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/md_to_cypher"

medium_text = (
    "The CLARIFY registry found that many CCS patients with angina experience a "
    "resolution of symptoms over time, often without changes in treatment or revascularization"
)
diff_text = (
    "the ORBITA 2 trial demonstrated that patients with stable angina, "
    "who were receiving minimal or no antianginal medication and had objective evidence of ischaemia, "
    "experienced a lower angina symptom score following PCI treatment compared with a placebo procedure, indicating a better health status with respect to angina."
)

paragraph = """In CAD patients with moderate or severe inducible ischaemia but no
left main disease nor LVEF of <35%, the largest-to-date ISCHEMIA trial,
up to 5 years, did not show significant benefit of an initial invasive strategy
over an initial conservative strategy for the primary endpoint of ischaemic
cardiovascular events or death from any cause,47 triggering
discussion about the role of initial angiography followed by revascularization
when feasible, in this type of CCS patients, once optimal medical
therapy has been established. The CLARIFY registry found that many
CCS patients with angina experience a resolution of symptoms over
time, often without changes in treatment or revascularization, and experience
good outcomes.404 While these findings suggest that this type
of CCS patients should initially receive conservative medical management,
it is worth noting that patients who were randomly assigned
to the invasive strategy in the ISCHEMIA trial experienced significantly
lower rates of spontaneous MI and greater improvement in
angina-related health status compared with those assigned to the conservative
strategy.47,50 Furthermore, the ORBITA 2 trial demonstrated
that patients with stable angina, who were receiving minimal or no antianginal
medication and had objective evidence of ischaemia, experienced
a lower angina symptom score following PCI treatment
compared with a placebo procedure, indicating a better health status
with respect to angina.52 Although initial conservative medical management
of CCS patients is generally preferred, symptom improvement by
revascularization should therefore not be neglected if patients remain
symptomatic despite antianginal treatment.
"""


def main(text):
    response = b.APIEasyFormatting(text)
    nested = b.APIPrototypeNester(sentences=response, original=text)
    triples = b.APIHypergrapher(nested)
    print(triples)
    return


def safe_call_APITotalConverter(text, retries=3, delay=2):
    for attempt in range(1, retries + 1):
        start = time.time()
        try:
            logging.info(f"Attempt {attempt} - calling APITotalConverter")
            result = b.APITotalConverter(text)
            duration = time.time() - start
            logging.info(f"Attempt {attempt} succeeded in {duration:.2f} seconds")
            return result
        except Exception as e:
            duration = time.time() - start
            logging.warning(
                f"Attempt {attempt} failed after {duration:.2f} seconds: {e}"
            )
            if attempt == retries:
                logging.error(
                    f"All {retries} attempts failed for input starting: {text[:50]}"
                )
                raise
            time.sleep(delay)


def OneFunction(text, file_id=None, output_path=output_path):
    """
    This function takes a text input, processes it to extract triples using the BAML OPEN-AI-API,
    Then converts these triples into Cypher statements, writes them to a file,
    and executes the Cypher statements against a Neo4j database.(dev1)
    """
    if file_id is None:
        file_id = text[0:4]

    logging.info(f"Calling LLM for text ID: {file_id}")

    triples = safe_call_APITotalConverter(text=text)

    print("Extracted Triples \ngenerating cypher statements")
    logging.info(f"Extracted triples. Generating Cypher statements.")

    cypher = triples_to_cypher(triples)
    logging.debug(f"Generated Cypher")
    print(cypher)

    print(f"Writing Cypher statements to file and executing in Neo4j dev1")
    logging.info(f"Writing Cypher statements to path and executing in Neo4j (dev1).")

    with open(os.path.join(output_path, f"baml_cypher_output{file_id}.txt"), "w") as f:
        f.write("\n".join(cypher))
    execute_baml_cypher_dev1(
        os.path.join(output_path, f"baml_cypher_output{file_id}.txt")
    )
    return


def chunk_md_folder_wrapper(md_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    counter = 1
    for md_file in sorted(md_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        # print(text)
        # print("LLM processing")
        # # OneFunction(text, file_id=f"{counter:03d}", output_path=out_dir)
        # print(counter)
        if counter >= 38:
            print(text)
            print("LLM processing")
            logging.info(f"Processing file {md_file.name} (#{counter})")
            OneFunction(text, file_id=f"{counter:03d}", output_path=out_dir)
            logging.info(f"Completed file {md_file.name} (#{counter})")
            print(counter)
        counter += 1
    return


def ChunkAndRoll():
    return


if __name__ == "__main__":
    md_dir = Path(
        "/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/chunks/text_chunks"
    )
    out_dir = Path(
        "/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/md_to_cypher"
    )
    # print(medium_text)
    # OneFunction(paragraph)
    # OneFunction(medium_text)
    # execute_baml_cypher_dev1(
    #     os.path.join(output_path, f"baml_cypher_output{paragraph[0:4]}.txt")
    # )
    chunk_md_folder_wrapper(
        md_dir=md_dir,
        out_dir=out_dir,
    )
    print(" Done ")
