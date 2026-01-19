import logging
import spacy
import time
import re
from pathlib import Path
from typing import Optional
from pathlib import Path
from typing import Callable, Any
from neo4j import GraphDatabase
from cardio_graph.extraction_utils.clients import create_client_registry
from cardio_graph.baml_client.sync_client import b  # isort:skip
from cardio_graph.extraction_utils.entity_grounding_service import (
    EntityGroundingService,
)
from dataclasses import dataclass


@dataclass(frozen=True)
class DepTriple:
    head_id: int
    head_text: str
    dep: str
    tail_id: int
    tail_text: str


@dataclass
class Statement:
    id: str
    predicate_id: int
    predicate_text: str
    subj: object | None = None  # token_id or statement_id
    objs: list = None  # token_ids
    children: list = None  # statement_ids

    def __post_init__(self):
        self.objs = self.objs or []
        self.children = self.children or []


URI = "bolt://neo4j-dev4.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")

SUBJECT_DEPS = {"nsubj", "nsubjpass", "csubj"}

OBJECT_DEPS = {"dobj", "pobj", "iobj", "attr", "oprd", "obl"}

CLAUSE_DEPS = {
    "ROOT",
    "relcl",
    "acl",
    "acl:relcl",
    "advcl",
    "ccomp",
    "xcomp",
    "parataxis",
}
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[
#         logging.FileHandler("new_graph_construction.log", mode="a", encoding="utf-8"),
#         logging.StreamHandler(),
#     ],
# )

# Ground entities in text
test_text = """ The first step is a general clinical evaluation that focuses on as-sessing  symptoms  and  signs  of  CCS,  differentiating  non-cardiac
causes of chest pain and ruling out ACS. This initial clinical evaluation
requires recording a 12-lead resting electrocardiogram (ECG), basic
blood tests, and in selected individuals, chest X-ray imaging and pul-monary function testing."""

test_text2 = """Depression is common (15%–20% prevalence) in CVD, and associated
with poor adherence and worse outcomes, including MACE and premature
death."""

test_text3 = """For
anxiety, a recent meta-analysis involving 16 studies reported a prevalence
in post-MI between 5.5% and 58%, and a 27% greater risk of
poor clinical outcomes in anxious patients compared with those without
anxiety.1130 In contrast, in a 15-year follow-up of 1109 patients with
CCS moderate anxiety did not increase the risk of cardiovascular
events compared with low anxiety levels."""

test_text_list = [test_text, test_text2, test_text3]


def spacy_triples_to_cypher(triples: list[DepTriple]) -> str:
    """
    Converts spaCy dependency triples to Cypher statements for Neo4j.
    """
    cypher_statements = []
    for deptriple in triples:
        head_node_value = deptriple.head_text
        head_node_id = deptriple.head_id
        relation = deptriple.dep
        tail_node_value = deptriple.tail_text
        tail_node_id = deptriple.tail_id
        cypher_head = f"MERGE (n{head_node_id}:Node {{id: '{head_node_id}', value: '{head_node_value}'}}) "
        cypher_tail = f"MERGE (n{tail_node_id}:Node {{id: '{tail_node_id}', value: '{tail_node_value}'}}) "
        cypher_triple = f"MERGE (n{head_node_id})-[:{relation}]->(n{tail_node_id})"
        if cypher_head not in cypher_statements:
            cypher_statements.append(cypher_head)
        if cypher_tail not in cypher_statements:
            cypher_statements.append(cypher_tail)
        cypher_statements.append(cypher_triple)
    # print("\n".join(cypher_statements))
    return cypher_statements


def spacy_to_dev4(text):
    """
    Extract dependency triples using spaCy and load them into neo4j dev4
    """
    triples = extract_dependency_triples(text)
    cypher = spacy_triples_to_cypher(triples)
    query = "\n".join(cypher)
    print("queries:" + query)
    print("connecting to neo4j dev4")
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j database.")

        with driver.session() as session:
            print("running query")
            session.run(query)
            print("query executed.")
    return


def CoreEntities(doc) -> None:
    """
    Extract core entities from a spacy doc
    """
    entities = []
    for ent in doc.ents:
        entities.append(ent.text)
    return "\n".join(entities)


def GroundingGPT(text: str) -> None:
    """
    Ground entities using the BAML API Grounder
    """

    grounded_entities = b.APIGrounder(text)
    for i, t in enumerate(grounded_entities.entities, 1):
        print(f"{i:2d}.[{t}]")
    return None


def SpacySandbox(text: str) -> None:
    print("loading spacy en_core_sci_lg")
    nlp = spacy.load("en_core_sci_lg")
    print("loading complete")
    doc = nlp(text)
    # for token in doc:
    #     print(token.i, token.text, token.dep_, token.head.text)
    for sent in doc.sents:
        print_tree(sent.root)
    entities = CoreEntities(doc)
    print("Entities found:", entities)

    return None


def SubjectIdentifier(token):
    """Identify subjects of a given token in the dependency parse tree.

    Args:
        token (spacy.tokens.Token): The token for which to identify subjects.

    Returns:
        list: A list of subject tokens.
    """
    subject_list = []
    for child in token.children:
        if child.dep_ in SUBJECT_DEPS:
            subject_list.append(child)
    return subject_list


def ObjectIdentifier(token):
    """Identify objects of a given token in the dependency parse tree.

    Args:
        token (spacy.tokens.Token): The token for which to identify objects.

    Returns:
        list: A list of object tokens.
    """
    object_list = []
    for child in token.children:
        if child.dep_ in {"dobj", "pobj", "iobj"}:
            object_list.append(child)
        if child.dep_ == "nmod":
            for grandchild in child.children:
                if grandchild.dep_ == "case":
                    object_list.append(child)
    return object_list


def SpacyExtractStatements(doc):
    statements = []
    for sent in doc.sents:
        print_tree(sent.root)
        print(sent.root, sent.root.dep_, sent.root.i, list(sent.root.children))
        predicate = sent.root
        subject_list = SubjectIdentifier(sent.root)
        object_list = ObjectIdentifier(sent.root)
        if not subject_list or not object_list:
            print("ERROR No subjects and objects found for root:", predicate.text)
            print("Subjects found:", [subj.text for subj in subject_list])
            print("Objects found:", [obj.text for obj in object_list])
            continue
        for subj in subject_list:
            for obj in object_list:
                print(f"Statement: {subj.text} -- {predicate.text} --> {obj.text}")
                statements.append(
                    Statement(
                        id=f"S{len(statements)+1}",
                        predicate_id=predicate.i,
                        predicate_text=predicate.text,
                        subj=subj.text,
                        objs=obj.text,
                    )
                )

    return statements


def SpacyExStaWrapper(text_list: list) -> None:
    """
    Main wrapper function to extract statements from a list of texts using only spaCy.
    """
    print("loading spacy en_core_sci_lg")
    nlp = spacy.load("en_core_sci_lg")
    print("loading complete")
    for text in text_list:
        doc = nlp(text)
        statements = SpacyExtractStatements(doc)
        print_statements(statements)
    return None


def print_tree(token, depth=0):
    """
    Print a spaCy token and its children in a tree format.
    """
    print("  " * depth + f"{token.text} ({token.dep_})")
    for child in token.children:
        print_tree(child, depth + 1)


def dependency_tree_to_string(token, depth=0):
    """
    Convert a spaCy token and its children into a string representation of the dependency tree.
    """
    lines = []
    lines.append("  " * depth + f"{token.text} ({token.dep_})")
    for child in token.children:
        lines.append(dependency_tree_to_string(child, depth + 1))
    return "\n".join(lines)


def paragraph_dep_trees_to_string(doc):
    """
    Convert the dependency trees of all sentences in a spaCy doc to a string representation.
    """
    blocks = []
    for i, sent in enumerate(doc.sents, start=1):
        block = []
        block.append(f"[Sentence {i}]")
        block.append(dependency_tree_to_string(sent.root))
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def extract_tree(token):
    """Extract the dependency tree starting from the given token."""
    return {
        "text": token.text,
        "i": token.i,
        "dep": token.dep_,
        "pos": token.pos_,
        "children": [extract_tree(child) for child in token.children],
    }


def extract_statements(text: str):
    """
    Extract statements from text using spaCy.
    This function is still a work in progress
    """
    print("loading spacy en_core_sci_lg")
    nlp = spacy.load("en_core_sci_lg")
    print("loading complete")
    doc = nlp(text)
    statements = []
    stmt_index = {}

    def new_statement(token, parent_id=None):
        stmt_id = f"S{len(statements)+1}"

        # subject (very rough)
        subject = None
        for child in token.children:
            if child.dep_ in {"nsubj", "nsubjpass"}:
                subject = child.text

        stmt = {
            "id": stmt_id,
            "predicate": token.text,
            "dep": token.dep_,
            "subject": subject,
            "parent": parent_id,
            "span": doc[token.left_edge.i : token.right_edge.i + 1].text,
        }

        statements.append(stmt)
        stmt_index[token.i] = stmt_id

        # recurse into nested clauses
        for child in token.children:
            if child.dep_ in CLAUSE_DEPS:
                new_statement(child, parent_id=stmt_id)

    for sent in doc.sents:
        new_statement(sent.root)

    return statements


def extract_dependency_triples(text: str):
    """
    Extract dependency triples from text using spaCy.
    """
    print("loading spacy en_core_sci_lg")
    nlp = spacy.load("en_core_sci_lg")
    print("loading complete")
    doc = nlp(text)
    triples = []

    for token in doc:
        if token.dep_ != "ROOT":
            triples.append(
                DepTriple(
                    head_id=token.head.i,
                    head_text=token.head.text,
                    dep=token.dep_,
                    tail_id=token.i,
                    tail_text=token.text,
                )
            )
    return triples


def new_triple_gen_wrapper(
    output_path="/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/new_graph_construction/cypher/",
    URI="bolt://neo4j-dev3.internal:7687",
    AUTH=("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"),
    chunk_dir="/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/new_graph_construction/chunks/text_chunks",
):
    """
    The main Wrapper function to process all chunk files in a directory and generate Cypher statements with the pipeline.
    """
    print("loading spacy en_core_sci_lg")
    nlp = spacy.load("en_core_sci_lg")
    print("loading complete")
    chunk_path = Path(chunk_dir)
    for chunk_file in chunk_path.glob("*.md"):
        print(f"Processing chunk file: {chunk_file.name}")
        with open(chunk_file, "r", encoding="utf-8") as f:
            paragraph = f.read()
            print("generating statements for paragraph")
            generate_statements_for_paragraph_safe(
                paragraph=paragraph,
                path=output_path,
                URI=URI,
                AUTH=AUTH,
                name=chunk_file.stem,
                nlp=nlp,
            )
            print(f"Completed processing for: {chunk_file.name}")
    return


def generate_statements_for_paragraph(
    paragraph: str,
    path="/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/new_graph_construction/cypher/",
    URI="bolt://neo4j-dev3.internal:7687",
    AUTH=("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"),
    name="test_paragraph",
    nlp=None,
) -> None:
    """
    The main function to generate statements for a given paragraph.
    1. create dependency trees + extract core entities
    2. run statement pipeline
    3. construct triples + cypher
    """
    path = Path(path + f"{name}.txt")

    doc = nlp(paragraph)
    dependency_trees = paragraph_dep_trees_to_string(doc)
    entities = CoreEntities(doc)
    first_pass_statements = b.CreateStatements(
        text=paragraph, dependency_tree=dependency_trees
    )
    post_judge_statements = b.JudgeStatements(
        statements=first_pass_statements,
        text=paragraph,
        dependency_tree=dependency_trees,
    )
    post_normalize_statements = b.NormalizeSubjObj(
        statements=post_judge_statements,
        text=paragraph,
        dependency_tree=dependency_trees,
    )
    and_nodes = b.ExtractAND(
        statements=post_normalize_statements, entities=entities, text=paragraph
    )
    pretty_print_statements(post_normalize_statements)
    pretty_print_and_nodes(and_nodes)
    statement_list, and_list = statement_and_and_to_lists(
        post_normalize_statements, and_nodes
    )
    and_triples, and_index = and_to_triples(and_list)
    triples = and_triples + statement_to_triples(statement_list, and_index)
    cypher_statements = triples_to_cypher(triples)
    with open(path, "w", encoding="utf-8") as f:
        for item in cypher_statements:
            f.write(f"{item}\n")
    execute_cypher(cypher_statements, URI, AUTH)
    return


def retry(
    fn: Callable[[], Any],
    name: str,
    retries: int = 3,
    base_delay: float = 0.5,
):
    """
    Retry wrapper with exponential backoff.
    """
    last_exception = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as e:
            last_exception = e
            print(f"[WARN] {name} failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(base_delay * (2 ** (attempt - 1)))
    raise RuntimeError(f"{name} failed after {retries} attempts") from last_exception


def generate_statements_for_paragraph_safe(
    paragraph: str,
    path="/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/new_graph_construction/cypher/",
    URI="bolt://neo4j-dev3.internal:7687",
    AUTH=("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"),
    name="test_paragraph",
    nlp=None,
) -> None:
    """
    The safe version of generate_statements_for_paragraph with retry logic.
    1. create dependency trees + extract core entities
    2. run statement pipeline with retries
    3. construct triples + cypher with retries
    """
    path = Path(path + f"{name}.txt")

    # --- NLP + preprocessing ---
    doc = retry(
        lambda: nlp(paragraph),
        name="nlp(paragraph)",
    )

    dependency_trees = retry(
        lambda: paragraph_dep_trees_to_string(doc),
        name="paragraph_dep_trees_to_string",
    )

    entities = retry(
        lambda: CoreEntities(doc),
        name="CoreEntities",
    )

    # --- Statement pipeline ---
    first_pass_statements = retry(
        lambda: b.CreateStatements(
            text=paragraph,
            dependency_tree=dependency_trees,
        ),
        name="b.CreateStatements",
    )

    post_judge_statements = retry(
        lambda: b.JudgeStatements(
            statements=first_pass_statements,
            text=paragraph,
            dependency_tree=dependency_trees,
        ),
        name="b.JudgeStatements",
    )

    post_normalize_statements = retry(
        lambda: b.NormalizeSubjObj(
            statements=post_judge_statements,
            text=paragraph,
            dependency_tree=dependency_trees,
        ),
        name="b.NormalizeSubjObj",
    )

    and_nodes = retry(
        lambda: b.ExtractAND(
            statements=post_normalize_statements,
            entities=entities,
            text=paragraph,
        ),
        name="b.ExtractAND",
    )

    # --- Debug output (non-critical, no retry) ---
    # pretty_print_statements(post_normalize_statements)
    # pretty_print_and_nodes(and_nodes)

    # --- Graph construction ---
    statement_list, and_list = retry(
        lambda: statement_and_and_to_lists(post_normalize_statements, and_nodes),
        name="statement_and_and_to_lists",
    )

    and_triples, and_index = retry(
        lambda: and_to_triples(and_list),
        name="and_to_triples",
    )

    triples = retry(
        lambda: and_triples + statement_to_triples(statement_list, and_index),
        name="statement_to_triples",
    )

    cypher_statements = retry(
        lambda: triples_to_cypher(triples),
        name="triples_to_cypher",
    )

    # --- File output ---
    retry(
        lambda: path.write_text("\n".join(cypher_statements), encoding="utf-8"),
        name="write cypher file",
    )

    # --- Neo4j execution ---
    retry(
        lambda: execute_cypher(cypher_statements, URI, AUTH),
        name="execute_cypher",
    )

    return


def statement_and_and_to_lists(statements, and_nodes):
    """Convert statements and AND nodes with baml classes to list of dictionaries."""
    statement_list = []
    and_list = []
    for i, s in enumerate(statements.statements, 1):
        statement_list.append(
            {
                "id": s.id,
                "type": s.type,
                "subject": s.subject,
                "predicate": s.predicate,
                "object": s.object,
            }
        )
    for i, s in enumerate(and_nodes.and_statements, 1):
        and_list.append(
            {
                "id": s.id,
                "type": "AND",
                "and_node": s.and_node,
                "entities": s.atomic_entities,
            }
        )

    return statement_list, and_list


def print_statements(statements):
    for stmt in statements:
        print(
            f"Statement ID: {stmt.id}, Predicate: {stmt.predicate_text} (ID: {stmt.predicate_id}), Subject: {stmt.subj}, Objects: {stmt.objs}"
        )
    return


def pretty_print_statements(statements):
    for i, s in enumerate(statements.statements, 1):
        print(
            f"{i:2d}. Statement Node: {s.id} \n   Type: {s.type} \n Subject: {s.subject} \n Predicate: {s.predicate} \n   Object: {s.object}\n"
        )
    return


def pretty_print_and_nodes(statements):
    for i, s in enumerate(statements.and_statements, 1):
        print(
            f"{i:2d}. AND Node: {s.id} \n   AND Node: {s.and_node} \n Entities: {s.atomic_entities}\n"
        )
    return


def statement_to_triples(statement_list, and_index):
    """
    Convert statement list to triples for graph construction.
    needs to run after and_to_triples to get and_index"""
    triples = []
    statement_index = []
    id_index = []
    for stmt in statement_list:
        id_index.append(stmt["id"])
        statement_index.append(stmt["subject"])
        statement_index.append(stmt["object"])
    for stmt in statement_list:
        if stmt["id"] in statement_index:
            if stmt["subject"] in id_index:
                tail_label = "rdf_statement"
            elif stmt["subject"] in and_index:
                tail_label = "AND"
            else:
                tail_label = "Node"
            triples.append(
                {
                    "head_node_label": "rdf_statement",
                    "head_node": stmt["id"],
                    "relation": "rdf_subject",
                    "tail_node": stmt["subject"],
                    "tail_node_label": tail_label,
                }
            )

            triples.append(
                {
                    "head_node_label": "rdf_statement",
                    "head_node": stmt["id"],
                    "relation": "rdf_predicate",
                    "tail_node": stmt["predicate"],
                    "tail_node_label": "Predicate",
                }
            )
            if stmt["object"] in id_index:
                tail_label = "rdf_statement"
            elif stmt["object"] in and_index:
                tail_label = "AND"
            else:
                tail_label = "Node"
            triples.append(
                {
                    "head_node_label": "rdf_statement",
                    "head_node": stmt["id"],
                    "relation": "rdf_object",
                    "tail_node": stmt["object"],
                    "tail_node_label": tail_label,
                }
            )
        else:
            head_label = "Node"
            tail_label = "Node"
            if stmt["subject"] in id_index:
                head_label = "rdf_statement"
            elif stmt["subject"] in and_index:
                head_label = "AND"
            if stmt["object"] in id_index:
                tail_label = "rdf_statement"
            elif stmt["object"] in and_index:
                tail_label = "AND"
            triples.append(
                {
                    "head_node_label": head_label,
                    "head_node": stmt["subject"],
                    "relation": stmt["predicate"],
                    "tail_node": stmt["object"],
                    "tail_node_label": tail_label,
                }
            )

    return triples


def and_to_triples(and_list):
    """
    Convert AND nodes to triples for graph construction."""
    triples = []
    and_index = []
    for and_node in and_list:
        and_index.append(and_node["and_node"])
        entities = and_node["entities"]
        for entity in entities:
            triples.append(
                {
                    "head_node": entity,
                    "head_node_label": "Node",
                    "relation": "part_of",
                    "tail_node": and_node["and_node"],
                    "tail_node_label": "AND",
                }
            )

    return triples, and_index


def cypher_safe(s: str) -> str:
    """
    Make a string safe for use as a Neo4j label or relationship type."""
    s = s.strip()
    s = re.sub(r"['’]", "", s)  # remove apostrophes (ASCII + Unicode)
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)  # replace everything else
    s = re.sub(r"_+", "_", s)  # collapse underscores
    return s.upper().strip("_")


def triples_to_cypher(triples):
    """
    Converts triples to Cypher statements for Neo4j.
    Returns a list of Cypher statements as strings.
    """
    cypher_statements = []
    for t in triples:
        head_node_label = cypher_safe(t["head_node_label"])
        head_node_value = t["head_node"]
        relation = cypher_safe(t["relation"])
        tail_node_label = cypher_safe(t["tail_node_label"])
        tail_node_value = t["tail_node"]
        cypher_head = f"MERGE (h:{head_node_label} {{value: '{head_node_value}'}}) "
        cypher_tail = f"MERGE (t:{tail_node_label} {{value: '{tail_node_value}'}}) "
        cypher_triple = f"MERGE (h)-[:{relation}]->(t)"
        cypher_query = cypher_head + cypher_tail + cypher_triple
        cypher_statements.append(cypher_query)
    # print("\n".join(cypher_statements))
    return cypher_statements


def execute_cypher(cypher_triple_list, URI, AUTH):
    """
    Executes a list of Cypher statements against a Neo4j database.
    """
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j database.")
        with driver.session() as session:
            for triple in cypher_triple_list:
                print("running query")
                session.run(triple)
                print("query executed.")
    return


if __name__ == "__main__":
    # spacy_to_dev4(test_text2)
    # generate_statements(test_text2)
    SpacySandbox(test_text)
    # SpacyExStaWrapper(test_text_list)
    # print(EntityGroundingService().ground(test_text2))
    # generate_statements_for_paragraph(test_text3)
    # new_triple_gen_wrapper()
