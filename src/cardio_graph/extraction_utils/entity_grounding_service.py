#!/usr/bin/env python3
"""
Entity Grounding Service (EGS) for the Cardio Guidelines Knowledge Graph.

This service performs the following steps:
1.  Parses the foundational `cardio_ontology.owl` file.
2.  Extracts all named individuals (SNOMED concepts, etc.), their labels, and synonyms.
3.  Builds a fast, local full-text search index using Whoosh.
4.  Provides a `ground()` method that takes raw text, identifies entity mentions using
    spaCy, and links them to the concepts in the ontology via the search index.

Installation:
pip install rdflib spacy whoosh
python -m spacy download en_core_web_sm
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Tuple

# RDF and Ontology Parsing
import rdflib

# Named Entity Recognition
import spacy
from rdflib.namespace import OWL, RDF, RDFS, SKOS

# Full-Text Search Indexing
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
    def __init__(self, ontology_path: str, index_path: str = "egs_index"):
        """
        Initializes the Entity Grounding Service.

        Args:
            ontology_path: Path to the .owl ontology file.
            index_path: Directory where the Whoosh search index will be stored.
        """
        if not os.path.exists(ontology_path):
            raise FileNotFoundError(f"Ontology file not found at: {ontology_path}")

        self.ontology_path = ontology_path
        self.index_path = index_path

        print("Loading spaCy NER model...")
        # Using a small, efficient model. For higher accuracy, 'en_core_web_trf' could be used.
        self.nlp = spacy.load("en_core_web_sm")

        if not os.path.exists(self.index_path) or not index.exists_in(self.index_path):
            print(f"Index not found at '{self.index_path}'. Building a new one...")
            self._build_index()
        else:
            print(f"Loading existing index from '{self.index_path}'...")

        self.ix = index.open_dir(self.index_path)

    def _parse_ontology(self) -> Iterator[Dict]:
        """
        Parses the OWL file and yields a dictionary for each named individual.
        """
        print(f"Parsing ontology file: {self.ontology_path}...")
        g = rdflib.Graph()
        g.parse(self.ontology_path)

        # This SPARQL query is the heart of the parsing step. It finds all individuals
        # and gathers their label, type, and all alternative labels (synonyms).
        query = """
        SELECT ?individual ?label (GROUP_CONCAT(?altLabel; separator="||") AS ?synonyms) ?type
        WHERE {
            ?individual rdf:type owl:NamedIndividual .
            ?individual rdfs:label ?label .
            ?individual rdf:type ?type .
            
            # We want the specific cgo: type, not the generic owl:NamedIndividual type
            FILTER(?type != owl:NamedIndividual)

            # Optionally bind synonyms if they exist
            OPTIONAL { ?individual skos:altLabel ?altLabel . }
        }
        GROUP BY ?individual ?label ?type
        """

        results = g.query(query)
        print(f"Found {len(results)} individuals in the ontology.")

        for row in results:
            yield {
                "id": str(row.individual),
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

        print(f"Committing {count} documents to the index...")
        writer.commit()
        print("Index build complete.")

    def ground(self, text: str) -> List[GroundedEntity]:
        """
        The main method of the service. Takes raw text and returns a list of grounded entities.
        """
        grounded_entities = []
        doc = self.nlp(text)

        with self.ix.searcher() as searcher:
            # We parse queries against the 'content' field, which has all text
            query_parser = QueryParser("content", self.ix.schema, group=OrGroup)

            # Process each entity mention found by spaCy's NER
            for ent in doc.ents:
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

        return grounded_entities


# --- Main block to demonstrate and test the service ---
if __name__ == "__main__":
    # Define paths to your files
    ONTOLOGY_FILE = "cardio_ontology.owl"
    INDEX_DIR = "egs_index"

    # Check if the ontology file exists
    if not os.path.exists(ONTOLOGY_FILE):
        print(f"ERROR: Ontology file '{ONTOLOGY_FILE}' not found.")
        print("Please run the ontology generator script first to create it.")
    else:
        # 1. Initialize the service. This will build the index if it doesn't exist.
        egs = EntityGroundingService(ontology_path=ONTOLOGY_FILE, index_path=INDEX_DIR)

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
