#!/usr/bin/env python3
"""
Entity Grounding Service (EGS) for the Cardio Guidelines Knowledge Graph.

This service performs the following steps:
1.  Parses the foundational `cardio_ontology.owl` file (class-based modeling).
2.  Extracts all classes (SNOMED concepts, etc.), their labels, and synonyms.
3.  Builds a fast, local full-text search index using Whoosh.
4.  Provides a `ground()` method that takes raw text, identifies entity mentions using
    spaCy, and links them to the concepts in the ontology via the search index.

Installation:
pip install rdflib spacy whoosh scispacy
python -m spacy download en_core_web_sm
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_ner_bc5cdr_md-0.5.4.tar.gz
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Tuple

import click
import rdflib
import spacy
from rdflib.namespace import OWL, RDF, RDFS, SKOS
from whoosh import index
from whoosh.fields import STORED, TEXT, Schema
from whoosh.qparser import OrGroup, QueryParser


@dataclass
class GroundedEntity:
    """A data structure to hold a grounded entity mention."""

    mention: str  # The text span from the original document (e.g., "HFrEF")
    span: Tuple[int, int]  # The character start/end position of the mention
    id: str  # The canonical ID from the ontology (e.g., "snomed:443620008")
    label: str  # The canonical preferred label (e.g., "Heart failure with reduced ejection fraction")
    type: str  # The class type from our ontology (e.g., "cgo:Condition")
    score: float = 0.0  # The search relevance score from Whoosh


class EntityGroundingService:
    def __init__(
        self,
        ontology_path: str = "/prj/doctoral_letters/guide/data/ontologies/cardio_ontology_class.owl",
        index_path: str = "/prj/doctoral_letters/guide/data/egs_index",
        rebuild_index: bool = False,
    ):
        """
        Initializes the Entity Grounding Service.

        Args:
            ontology_path: Path to the .owl ontology file. Defaults to the cardio ontology.
            index_path: Directory where the Whoosh search index will be stored. Defaults to egs_index.
            rebuild_index: If True, force rebuild the index even if it exists.
        """
        if not os.path.exists(ontology_path):
            raise FileNotFoundError(f"Ontology file not found at: {ontology_path}")

        self.ontology_path = ontology_path
        self.index_path = index_path

        print("Loading spaCy NER model (scispaCy biomedical model)...")
        # Using a biomedical NER model for better medical entity recognition en_core_sci_lg en_ner_bc5cdr_md
        self.nlp = spacy.load("en_core_sci_lg")

        if (
            rebuild_index
            or not os.path.exists(self.index_path)
            or not index.exists_in(self.index_path)
        ):
            print(f"Building/rebuilding index at '{self.index_path}'...")
            self._build_index()
        else:
            print(f"Loading existing index from '{self.index_path}'...")

        self.ix = index.open_dir(self.index_path)

        # Load ontology graph for exact matching
        print("Loading ontology graph for exact matching...")
        self.g = rdflib.Graph()
        self.g.parse(self.ontology_path)

    def _parse_ontology(self) -> Iterator[Dict]:
        """
        Parses the OWL file and yields a dictionary for each class (for class-based modeling).
        Includes validation to ensure the ontology has expected structure.
        """
        print(f"Parsing ontology file: {self.ontology_path}...")
        g = rdflib.Graph()
        g.parse(self.ontology_path)

        # Validate ontology structure
        classes = list(g.subjects(RDF.type, OWL.Class))
        if not classes:
            raise ValueError(
                "Ontology does not contain any Classes. Check the ontology file."
            )

        # This SPARQL query is the heart of the parsing step. It finds all classes
        # (for class-based modeling) and gathers their label, type, and all alternative labels (synonyms).
        query = """
        SELECT ?entity ?label (GROUP_CONCAT(?altLabel; separator="||") AS ?synonyms) ?type
        WHERE {
            ?entity rdf:type owl:Class .
            ?entity rdfs:label ?label .

            # Get the superclass (cgo: type)
            ?entity rdfs:subClassOf ?type .
            FILTER(STRSTARTS(STR(?type), "http://dieterich-lab.org/ontologies/cardioguidelinesonto"))

            # Optionally bind synonyms if they exist
            OPTIONAL { ?entity skos:altLabel ?altLabel . }
        }
        GROUP BY ?entity ?label ?type
        """

        results = g.query(query)
        print(f"Found {len(results)} classes in the ontology.")

        if len(results) == 0:
            print(
                "Warning: No classes with labels and types found. Ontology may be incomplete."
            )

        for row in results:
            yield {
                "id": str(row.entity),
                "label": str(row.label),
                "synonyms": str(row.synonyms).split("||") if row.synonyms else [],
                "type": str(row.type),
            }

    def _build_index(self):
        """
        Builds a Whoosh search index from the ontology individuals.
        This is a one-time operation.
        """
        # Define the structure (schema) of the search index
        schema = Schema(
            id=STORED(),  # The URI/ID of the concept (e.g., snomed:123)
            label=STORED(),  # The canonical preferred label
            type=STORED(),  # The cgo: class type
            content=TEXT(
                stored=False
            ),  # A searchable field combining label and synonyms
        )

        if not os.path.exists(self.index_path):
            os.makedirs(self.index_path)

        ix = index.create_in(self.index_path, schema)
        writer = ix.writer()

        print("Populating search index...")
        count = 0
        for concept in self._parse_ontology():
            # Combine the label and all synonyms into one searchable text field
            content_string = " ".join([concept["label"]] + concept["synonyms"])

            writer.add_document(
                id=concept["id"],
                label=concept["label"],
                type=concept["type"],
                content=content_string,
            )
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} concepts...")

        print(f"Committing {count} documents to the index...")
        writer.commit()
        print("Index build complete.")

    def ground(self, text: str) -> List[GroundedEntity]:
        """
        The main method of the service. Takes raw text and returns a list of grounded entities.
        """
        grounded_entities = []
        entities = []
        doc = self.nlp(text)

        print(f"Processing text with {len(doc.ents)} detected entities...")

        with self.ix.searcher() as searcher:
            # We parse queries against the 'content' field, which has all text
            query_parser = QueryParser("content", self.ix.schema, group=OrGroup)

            # Process each entity mention found by spaCy's NER
            for ent in doc.ents:
                entities.append(ent.text)
                # Create a search query from the entity text.
                # The OrGroup helps match multi-word entities better.
                query = query_parser.parse(ent.text)

                # Search for the top 1 match in our index
                results = searcher.search(query, limit=1)

                if results:
                    top_hit = results[0]
                    grounded = GroundedEntity(
                        mention=ent.text,
                        span=(ent.start_char, ent.end_char),
                        id=top_hit["id"],
                        label=top_hit["label"],
                        type=top_hit["type"],
                        score=top_hit.score,
                    )
                    grounded_entities.append(grounded)
                    print(
                        f"Grounded '{ent.text}' to '{top_hit['label']}' (score: {top_hit.score:.2f})"
                    )
                else:
                    print(f"No match found for entity '{ent.text}'")

        print(f"Grounding complete. Found {len(grounded_entities)} grounded entities.")
        return grounded_entities

    def ground_exact_first(self, text: str) -> List[GroundedEntity]:
        """
        Ground entities using exact matching first (synonyms and labels), then fuzzy as fallback.
        This prevents false matches like 'beta blockers' -> 'Beta blocker target dose not achieved'.
        """
        grounded_entities = []
        doc = self.nlp(text)

        print(
            f"Processing text with {len(doc.ents)} detected entities (exact-first mode)..."
        )

        # Process each entity mention found by spaCy's NER
        for ent in doc.ents:
            print(f"Checking entity: '{ent.text}'")

            # First try exact match in ontology synonyms
            exact_matches = self._find_exact_synonym_matches(ent.text)

            if exact_matches:
                print(f"  Found {len(exact_matches)} exact synonym matches")
                # Use the first exact match
                match = exact_matches[0]
                grounded = GroundedEntity(
                    mention=ent.text,
                    span=(ent.start_char, ent.end_char),
                    id=match["id"],
                    label=match["label"],
                    type=match["type"],
                    score=1.0,  # Exact match gets perfect score
                )
                grounded_entities.append(grounded)
                print(f"  Grounded to: '{match['label']}' (exact synonym)")
                continue

            # If no exact synonym match, try exact match in labels
            exact_label_matches = self._find_exact_label_matches(ent.text)

            if exact_label_matches:
                print(f"  Found {len(exact_label_matches)} exact label matches")
                # Use the first exact match
                match = exact_label_matches[0]
                grounded = GroundedEntity(
                    mention=ent.text,
                    span=(ent.start_char, ent.end_char),
                    id=match["id"],
                    label=match["label"],
                    type=match["type"],
                    score=1.0,  # Exact match gets perfect score
                )
                grounded_entities.append(grounded)
                print(f"  Grounded to: '{match['label']}' (exact label)")
                continue

            # No exact matches found - do NOT ground this entity
            print(f"  No exact matches found for '{ent.text}' - skipping")
            continue

        print(f"Grounding complete. Found {len(grounded_entities)} grounded entities.")
        return grounded_entities

    def _find_exact_synonym_matches(self, term: str) -> List[dict]:
        """Find exact matches in ontology synonyms."""
        matches = []

        query = f"""
        SELECT ?entity ?label ?type WHERE {{
            ?entity skos:altLabel ?synonym .
            ?entity rdfs:label ?label .
            ?entity rdfs:subClassOf ?type .
            FILTER(STRSTARTS(STR(?type), "http://dieterich-lab.org/ontologies/cardioguidelinesonto"))
            FILTER(LCASE(STR(?synonym)) = LCASE("{term}"))
        }}
        """

        results = self.g.query(query)
        for row in results:
            matches.append(
                {"id": str(row.entity), "label": str(row.label), "type": str(row.type)}
            )

        return matches

    def _find_exact_label_matches(self, term: str) -> List[dict]:
        """Find exact matches in ontology labels."""
        matches = []

        query = f"""
        SELECT ?entity ?label ?type WHERE {{
            ?entity rdfs:label ?label .
            ?entity rdfs:subClassOf ?type .
            FILTER(STRSTARTS(STR(?type), "http://dieterich-lab.org/ontologies/cardioguidelinesonto"))
            FILTER(LCASE(STR(?label)) = LCASE("{term}"))
        }}
        """

        results = self.g.query(query)
        for row in results:
            matches.append(
                {"id": str(row.entity), "label": str(row.label), "type": str(row.type)}
            )

        return matches


# --- CLI using Click ---
@click.group()
@click.option(
    "--ontology-path",
    default="/prj/doctoral_letters/guide/data/ontologies/cardio_ontology.owl",
    help="Path to the OWL ontology file.",
)
@click.option(
    "--index-path",
    default="egs_index",
    help="Directory where the Whoosh search index will be stored.",
)
@click.option(
    "--rebuild-index",
    is_flag=True,
    help="Force rebuild the search index even if it exists.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging.",
)
@click.pass_context
def cli(ctx, ontology_path, index_path, rebuild_index, verbose):
    """Entity Grounding Service CLI."""
    ctx.ensure_object(dict)
    ctx.obj["ontology_path"] = ontology_path
    ctx.obj["index_path"] = index_path
    ctx.obj["rebuild_index"] = rebuild_index
    ctx.obj["verbose"] = verbose


@cli.command()
@click.argument("text")
@click.pass_context
def ground(ctx, text):
    """Ground entities in the provided text."""
    try:
        egs = EntityGroundingService(
            ontology_path=ctx.obj["ontology_path"],
            index_path=ctx.obj["index_path"],
            rebuild_index=ctx.obj["rebuild_index"],
        )
        found_entities = egs.ground(text)

        if not found_entities:
            click.echo("No entities were grounded.")
        else:
            for entity in found_entities:
                click.echo(
                    f"Mention: '{entity.mention}' -> ID: {entity.id}, Label: '{entity.label}', Type: {entity.type}, Score: {entity.score:.2f}"
                )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


def demo():
    """Demo/Main Block: Provides a working example with sample text, making it easy to test. It checks for the ontology file and handles missing files gracefully."""
    # Define paths to your files
    ONTOLOGY_FILE = (
        "/prj/doctoral_letters/guide/data/ontologies/cardio_ontology_class.owl"
    )
    INDEX_DIR = "/prj/doctoral_letters/guide/data/egs_index"

    # Check if the ontology file exists
    if not os.path.exists(ONTOLOGY_FILE):
        print(f"ERROR: Ontology file '{ONTOLOGY_FILE}' not found.")
        print("Please run the ontology generator script first to create it.")
        return

    # 1. Initialize the service. This will build the index if it doesn't exist.
    egs = EntityGroundingService(
        ontology_path=ONTOLOGY_FILE, index_path=INDEX_DIR, rebuild_index=True
    )

    # 2. Define a sample text chunk from a clinical guideline
    sample_text = (
        "For patients with HFrEF and an LVEF below 40%, SGLT2 inhibitors are "
        "recommended as a foundational therapy. This recommendation is based on the "
        "DAPA-HF trial. Beta-blockers should also be considered to reduce the "
        "risk of myocardial infarction."
    )

    print("\n--- Grounding Sample Text ---")
    print(f'Input Text: "{sample_text}"')

    # 3. Call the ground() method to perform entity linking
    found_entities = egs.ground(sample_text)

    # 4. Print the results
    print("\n--- Found Entities ---")
    if not found_entities:
        print("No entities were grounded.")
    else:
        for entity in found_entities:
            print(
                f"  Mention: '{entity.mention}'\n"
                f"    -> ID: {entity.id}\n"
                f"    -> Label: '{entity.label}'\n"
                f"    -> Type: {entity.type}\n"
                f"    -> Score: {entity.score:.2f}\n"
            )


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        demo()
    else:
        cli()
