#!/usr/bin/env python3
"""
Generate a cardiovascular guideline ontology from SNOMED CT data

This script extracts relevant cardiovascular concepts from SNOMED CT
and generates an OWL/RDF ontology for use with cardiovascular guidelines.
"""

import argparse
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple

import pandas as pd
import yaml
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD

from cardio_graph.snomedct_utils.models import SnapDescription

# Import SnomedExplorer from snomed_query.py
from cardio_graph.snomedct_utils.snomed_query import SnomedExplorer

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "ontology_config.yaml")
with open(CONFIG_PATH, "r") as f:
    _config = yaml.safe_load(f)
SNOMED_CATEGORIES = _config.get("snomed_categories", [])
SNOMED_KEYWORDS = _config.get("snomed_keywords", {})


class CardioOntologyGenerator:

    def categorize_concepts_llm(self, concepts: List[Dict]) -> Dict[str, List[URIRef]]:
        """
        Categorize SNOMED concepts using an LLM via BAML, now with full description context.
        """
        from cardio_graph.baml_client.sync_client import b

        categories_map = {cat: [] for cat in SNOMED_CATEGORIES}

        for concept in concepts:
            concept_id = concept.get("conceptId") or concept.get("id")
            if not concept_id:
                continue

            # Fetch all descriptions for the concept
            all_descriptions = self.snomed_explorer.get_descriptions_for_concept(
                concept_id
            )

            # Find the FSN for best context, and collect other synonyms
            fsn = ""
            synonyms = []
            preferred_term = concept.get(
                "term", ""
            )  # Assume the initial term is preferred

            for desc in all_descriptions:
                if desc["type"] == "FSN":
                    fsn = desc["term"]
                # Avoid duplicating the preferred term in the synonym list
                elif desc["term"].lower() != preferred_term.lower():
                    synonyms.append(desc["term"])

            # Prepare the input for the BAML client
            baml_input = {
                "term": preferred_term,
                "description": fsn,  # Use the FSN as the primary description for the LLM
                "synonyms": ", ".join(synonyms),
            }

            try:
                # Assuming your BAML function can take this richer input
                result = b.CategorizeConcept(baml_input, SNOMED_CATEGORIES)
                assigned = result.categories
                concept_uri = self.add_snomed_concept(concept)
                for cat in assigned:
                    if cat in categories_map:
                        categories_map[cat].append(concept_uri)
                        self.g.add((concept_uri, RDFS.subClassOf, self.cgo[cat]))
            except Exception as e:
                print(f"Error categorizing concept '{preferred_term}': {e}")
                continue
        return categories_map

    def categorize_concepts(self, concepts: List[Dict]) -> Dict[str, List[URIRef]]:
        """Categorize SNOMED concepts into snomed categories using keywords from YAML config"""
        categories = {cat: [] for cat in SNOMED_CATEGORIES}
        for concept in concepts:
            concept_uri = self.add_snomed_concept(concept)
            term = concept.get("term", "").lower()
            for category, keyword_list in SNOMED_KEYWORDS.items():
                if any(keyword in term for keyword in keyword_list):
                    categories[category].append(concept_uri)
                    self.g.add((concept_uri, RDFS.subClassOf, self.cgo[category]))
        return categories

    def get_type_label(self, type_id: str) -> str:
        """Lookup human-readable label for a SNOMED CT typeId."""
        result = (
            self.snomed_explorer.session.query(SnapDescription)
            .filter_by(conceptId=type_id)
            .first()
        )
        if result and hasattr(result, "term"):
            return result.term
        return f"snomedRelationship_{type_id}"

    """Generate a cardiovascular ontology from SNOMED CT data"""

    def __init__(
        self,
        output_path: str = "cardio_ontology.owl",
        snomed_host: str = "10.250.135.23",
        snomed_port: str = "3306",
        snomed_user: str = "test_user",
        snomed_password: str = "medicaldatabase",
        snomed_database: str = "snomedct",
        base_uri: str = "http://dieterich-lab.org/ontologies/cardioguidelinesonto/",
        version: str = "0.1.0",
        debug_mode: bool = False,
    ):
        """Initialize the ontology generator"""
        self.output_path = output_path
        self.snomed_explorer = SnomedExplorer(
            host=snomed_host,
            port=snomed_port,
            user=snomed_user,
            password=snomed_password,
            database=snomed_database,
        )
        self.debug_mode = debug_mode

        # Initialize RDF graph and namespaces
        self.g = Graph()
        self.base = Namespace(base_uri)
        self.snomed = Namespace("http://snomed.info/id/")
        self.cgo = Namespace(f"{base_uri}#")  # CardioGuidelinesOntology namespace

        # Register namespaces
        self.g.bind("", self.base)
        self.g.bind("cgo", self.cgo)
        self.g.bind("snomed", self.snomed)
        self.g.bind("owl", OWL)
        self.g.bind("rdf", RDF)
        self.g.bind("rdfs", RDFS)
        self.g.bind("xsd", XSD)
        self.g.bind("skos", SKOS)
        self.g.bind("dcterms", DCTERMS)

        # Set ontology metadata
        self.ont_uri = URIRef(base_uri)
        self.g.add((self.ont_uri, RDF.type, OWL.Ontology))
        self.g.add(
            (self.ont_uri, DCTERMS.title, Literal("Cardiovascular Guidelines Ontology"))
        )
        self.g.add(
            (
                self.ont_uri,
                DCTERMS.description,
                Literal(
                    "An ontology for representing knowledge from cardiovascular guidelines, "
                    "with concepts derived from SNOMED CT and enhanced with guideline-specific classes."
                ),
            )
        )
        self.g.add(
            (
                self.ont_uri,
                DCTERMS.created,
                Literal(datetime.now().isoformat(), datatype=XSD.dateTime),
            )
        )
        self.g.add((self.ont_uri, OWL.versionInfo, Literal(version)))

        # Track classes and properties to avoid duplicates
        self.classes = set()
        self.properties = set()
        self.snomed_concepts = {}  # Map from SNOMED concept ID to URI

        # Initialize core classes and properties
        self._init_core_structure()

    def _init_core_structure(self):
        """Initialize the core ontology structure with specified classes and properties from YAML config"""
        import yaml
        from rdflib.namespace import XSD

        # Add core classes
        for class_entry in _config.get("core_classes", []):
            class_name = class_entry["name"]
            description = class_entry.get("description", "")
            class_uri = self.cgo[class_name]
            self.g.add((class_uri, RDF.type, OWL.Class))
            self.g.add((class_uri, RDFS.label, Literal(class_name)))
            self.g.add((class_uri, RDFS.comment, Literal(description)))
            self.classes.add(class_name)

        # Add subclass relationships (hardcoded for now, can be moved to YAML if needed)
        self.g.add(
            (self.cgo["Conjunction"], RDFS.subClassOf, self.cgo["LogicalJunction"])
        )
        self.g.add(
            (self.cgo["Disjunction"], RDFS.subClassOf, self.cgo["LogicalJunction"])
        )
        self.g.add(
            (
                self.cgo["ContrastingStatement"],
                RDFS.subClassOf,
                self.cgo["EvidenceStatement"],
            )
        )
        self.g.add(
            (self.cgo["CardiovascularDisease"], RDFS.subClassOf, self.cgo["Condition"])
        )
        self.g.add(
            (self.cgo["CardiacImaging"], RDFS.subClassOf, self.cgo["ClinicalAction"])
        )
        self.g.add(
            (self.cgo["CardiacProcedure"], RDFS.subClassOf, self.cgo["ClinicalAction"])
        )
        self.g.add(
            (
                self.cgo["CardiacRiskFactor"],
                RDFS.subClassOf,
                self.cgo["PatientPhenotype"],
            )
        )
        for therapy_class in [
            "AnticoagulationTherapy",
            "AntiplateletTherapy",
            "LipidLoweringTherapy",
            "AntihypertensiveTherapy",
            "HeartFailureTherapy",
        ]:
            self.g.add(
                (self.cgo[therapy_class], RDFS.subClassOf, self.cgo["ClinicalAction"])
            )
        self.g.add(
            (
                self.cgo["EmergencyCardiacCare"],
                RDFS.subClassOf,
                self.cgo["ClinicalWorkflow"],
            )
        )
        self.g.add(
            (
                self.cgo["CardiacRehabilitation"],
                RDFS.subClassOf,
                self.cgo["ClinicalWorkflow"],
            )
        )
        self.g.add(
            (
                self.cgo["PreventiveCardiology"],
                RDFS.subClassOf,
                self.cgo["ClinicalWorkflow"],
            )
        )

        # Add core object properties
        for prop_entry in _config.get("core_properties", []):
            prop_name = prop_entry["name"]
            domain = prop_entry.get("domain")
            range_name = prop_entry.get("range")
            description = prop_entry.get("description", "")
            prop_uri = self.cgo[prop_name]
            self.g.add((prop_uri, RDF.type, OWL.ObjectProperty))
            self.g.add((prop_uri, RDFS.label, Literal(prop_name)))
            self.g.add((prop_uri, RDFS.comment, Literal(description)))
            if domain:
                self.g.add((prop_uri, RDFS.domain, self.cgo[domain]))
            if range_name and range_name != "null":
                self.g.add((prop_uri, RDFS.range, self.cgo[range_name]))
            self.properties.add(prop_name)

        # Add data properties
        for data_entry in _config.get("data_properties", []):
            prop_name = data_entry["name"]
            domain = data_entry.get("domain")
            range_type = data_entry.get("range")
            description = data_entry.get("description", "")
            prop_uri = self.cgo[prop_name]
            self.g.add((prop_uri, RDF.type, OWL.DatatypeProperty))
            self.g.add((prop_uri, RDFS.label, Literal(prop_name)))
            self.g.add((prop_uri, RDFS.comment, Literal(description)))
            if domain and domain != "null":
                self.g.add((prop_uri, RDFS.domain, self.cgo[domain]))
            # Map YAML type string to rdflib XSD type
            xsd_map = {"string": XSD.string, "integer": XSD.integer, "date": XSD.date}
            self.g.add((prop_uri, RDFS.range, xsd_map.get(range_type, XSD.string)))
            self.properties.add(prop_name)

        # Create hierarchical evidence level structure

        # Create Recommendation Class structure
        evidence_class = self.cgo["EvidenceLevel"]
        self.g.add((evidence_class, RDF.type, OWL.Class))
        self.g.add((evidence_class, RDFS.label, Literal("Evidence Level")))
        self.g.add(
            (
                evidence_class,
                RDFS.comment,
                Literal("Classification of evidence strength in guidelines"),
            )
        )

        # Create subclasses for recommendation classification and evidence quality
        recommendation_class = self.cgo["RecommendationClass"]
        evidence_quality_class = self.cgo["EvidenceQuality"]

        self.g.add((recommendation_class, RDF.type, OWL.Class))
        self.g.add((recommendation_class, RDFS.label, Literal("Recommendation Class")))
        self.g.add(
            (
                recommendation_class,
                RDFS.comment,
                Literal("Classification of recommendation strength"),
            )
        )

        self.g.add((evidence_quality_class, RDF.type, OWL.Class))
        self.g.add((evidence_quality_class, RDFS.label, Literal("Evidence Quality")))
        self.g.add(
            (
                evidence_quality_class,
                RDFS.comment,
                Literal("Classification of evidence quality/level"),
            )
        )

        # Add recommendation class individuals from YAML
        for entry in _config.get("recommendation_levels", []):
            level_id = entry["id"]
            description = entry.get("description", "")
            short_def = entry.get("short_definition", "")
            level_uri = self.cgo[level_id]
            self.g.add((level_uri, RDF.type, recommendation_class))
            self.g.add((level_uri, RDFS.label, Literal(level_id)))
            self.g.add((level_uri, RDFS.comment, Literal(description)))
            self.g.add((level_uri, self.cgo["shortDefinition"], Literal(short_def)))

        # Add evidence quality individuals from YAML
        for entry in _config.get("evidence_qualities", []):
            level_id = entry["id"]
            description = entry.get("description", "")
            short_def = entry.get("short_definition", "")
            level_uri = self.cgo[level_id]
            self.g.add((level_uri, RDF.type, evidence_quality_class))
            self.g.add((level_uri, RDFS.label, Literal(level_id)))
            self.g.add((level_uri, RDFS.comment, Literal(description)))
            self.g.add((level_uri, self.cgo["shortDefinition"], Literal(short_def)))

        # Add combined evidence level individuals from YAML
        for entry in _config.get("combined_levels", []):
            level_id = entry["id"]
            label = entry.get("label", "")
            rec_class = entry.get("recommendation_class", "")
            evidence_quality = entry.get("evidence_quality", "")
            level_uri = self.cgo[level_id]
            self.g.add((level_uri, RDF.type, evidence_class))
            self.g.add((level_uri, RDFS.label, Literal(label)))
            self.g.add(
                (level_uri, self.cgo["hasRecommendationClass"], self.cgo[rec_class])
            )
            self.g.add(
                (level_uri, self.cgo["hasEvidenceQuality"], self.cgo[evidence_quality])
            )

        # Add specialized evidence level types for different guideline systems from YAML
        for entry in _config.get("guideline_systems", []):
            system_id = entry["id"]
            label = entry.get("label", "")
            system_uri = self.cgo[f"GuidelineSystem_{system_id}"]
            self.g.add((system_uri, RDF.type, self.cgo["GuidelineSystem"]))
            self.g.add((system_uri, RDFS.label, Literal(label)))

    def extract_cardiovascular_concepts(self, limit: int = 1000) -> List[Dict]:
        """
        Extracts cardiovascular concepts from SNOMED CT by running targeted searches
        based on the snomed_search_terms defined in the ontology_config.yaml.
        """
        print("Extracting cardiovascular concepts using a schema-aware approach...")

        all_concepts = []
        seen_ids = set()

        # Iterate through each core class that has search terms defined
        debug = getattr(self, "debug_mode", False)
        use_limit = 2 if debug else 200
        max_classes = 2 if debug else None
        max_terms = 2 if debug else None
        max_concepts = 10 if debug else None

        core_classes = _config.get("core_classes", [])
        if max_classes:
            core_classes = core_classes[:max_classes]

        for class_entry in core_classes:
            class_name = class_entry["name"]
            search_terms = class_entry.get("snomed_search_terms")

            if not search_terms:
                continue

            print(f"--> Searching for concepts related to class: {class_name}")
            terms = search_terms[:max_terms] if max_terms else search_terms
            for term in terms:
                concepts_for_term = self.snomed_explorer.search_concepts_by_term(
                    term, limit=use_limit
                )
                for concept in concepts_for_term:
                    concept_id = concept.get("conceptId") or concept.get("id")
                    if concept_id and concept_id not in seen_ids:
                        concept["_source_class"] = class_name
                        all_concepts.append(concept)
                        seen_ids.add(concept_id)
                        if max_concepts and len(all_concepts) >= max_concepts:
                            print(
                                f"[DEBUG] Reached max_concepts={max_concepts}, stopping early."
                            )
                            print(
                                f"Extracted {len(all_concepts)} unique concepts using schema-aware search."
                            )
                            return all_concepts

        print(
            f"Extracted {len(all_concepts)} unique concepts using schema-aware search."
        )
        return all_concepts

    def get_concept_relationships(self, concepts: List[Dict]) -> Dict[str, List[Dict]]:
        """Get relationships for the extracted concepts"""
        print("Retrieving concept relationships...")
        relationships = {}
        concept_count = len(concepts)
        processed = 0

        # Process concepts in batches to show progress
        batch_size = 100

        for i, concept in enumerate(concepts):
            # Extract concept ID based on available fields
            concept_id = None
            if "conceptId" in concept:
                concept_id = concept["conceptId"]
            elif "id" in concept:
                concept_id = concept["id"]

            if concept_id:
                rels = self.snomed_explorer.get_relationships(str(concept_id))
                if rels:
                    relationships[concept_id] = rels

            processed += 1
            if processed % batch_size == 0 or processed == concept_count:
                print(
                    f"Processed {processed}/{concept_count} concepts ({int(processed/concept_count*100)}%)"
                )

        print(f"Retrieved relationships for {len(relationships)} concepts")
        return relationships

    def add_snomed_concept(self, concept: Dict) -> URIRef:
        """Add a SNOMED CT concept to the ontology"""
        # Extract concept ID and term
        concept_id = None
        term = None

        if "conceptId" in concept:
            concept_id = concept["conceptId"]
        elif "id" in concept:
            concept_id = concept["id"]

        if "term" in concept:
            term = concept["term"]

        if not concept_id or not term:
            # Generate a random UUID for concepts without IDs
            concept_id = str(uuid.uuid4())
            if not term:
                term = f"Unknown Concept {concept_id}"

        # Check if we already have this concept
        if concept_id in self.snomed_concepts:
            return self.snomed_concepts[concept_id]

        # Create a URI for the concept
        concept_uri = self.snomed[str(concept_id)]

        # Add the concept as a class
        self.g.add((concept_uri, RDF.type, OWL.Class))
        self.g.add((concept_uri, RDFS.label, Literal(term)))

        # Add additional metadata if available
        if "active" in concept and concept["active"] == 1:
            self.g.add((concept_uri, self.cgo["isActive"], Literal(True)))

        # Store the URI for future reference
        self.snomed_concepts[concept_id] = concept_uri
        return concept_uri

    def add_relationships(self, concept_id: str, relationships: List[Dict]):
        """Add relationships for a concept to the ontology"""
        if concept_id not in self.snomed_concepts:
            return

        source_uri = self.snomed_concepts[concept_id]

        for rel in relationships:
            rel_type = rel.get("typeId")
            target_id = rel.get("destinationId")

            if not rel_type or not target_id:
                continue

            target_uri = self.snomed[str(target_id)]

            # Always create a relationship property and label
            rel_prop_uri = self.cgo[f"snomed_rel_{rel_type}"]
            if rel_prop_uri not in self.properties:
                self.g.add((rel_prop_uri, RDF.type, OWL.ObjectProperty))
                rel_name = self.get_type_label(str(rel_type))
                self.g.add((rel_prop_uri, RDFS.label, Literal(rel_name)))
                self.properties.add(rel_prop_uri)

            # Add the relationship triple
            self.g.add((source_uri, rel_prop_uri, target_uri))

            # For IS-A, also add subClassOf
            if str(rel_type) == "116680003":
                self.g.add((source_uri, RDFS.subClassOf, target_uri))

            # Ensure the target class exists in the ontology
            if target_id not in self.snomed_concepts:
                term = f"SNOMED Concept {target_id}"
                self.g.add((target_uri, RDF.type, OWL.Class))
                self.g.add((target_uri, RDFS.label, Literal(term)))
                self.snomed_concepts[target_id] = target_uri

    def generate_ontology(self, categorization_method: str = "keyword"):
        """Generate the complete cardiovascular guidelines ontology"""
        print("Generating cardiovascular guidelines ontology...")

        try:
            # Connect to the SNOMED CT database
            self.snomed_explorer.connect()

            # Extract concepts
            concepts = self.extract_cardiovascular_concepts()

            if not concepts:
                print("No cardiovascular concepts found in SNOMED CT")
                return False

            # Get relationships
            relationships = self.get_concept_relationships(concepts)

            # Add concepts to the ontology
            for concept in concepts:
                self.add_snomed_concept(concept)

            # Categorize concepts
            if categorization_method == "llm":
                print("Using LLM-based concept categorization...")
                categories = self.categorize_concepts_llm(concepts)
            else:
                print("Using keyword-based concept categorization...")
                categories = self.categorize_concepts(concepts)

            # Print category statistics
            for category, uris in categories.items():
                print(f"  - {category}: {len(uris)} concepts")

            # Add relationships
            for concept_id, rels in relationships.items():
                self.add_relationships(concept_id, rels)

            # Save the ontology to file
            self.g.serialize(destination=self.output_path, format="xml")
            print(f"Ontology generated successfully and saved to {self.output_path}")

            # Print statistics
            print(f"Ontology contains:")
            print(f"  - {len(self.classes)} core classes")
            print(f"  - {len(self.snomed_concepts)} SNOMED CT concepts")
            print(f"  - {len(self.properties)} properties")
            print(f"  - {len(self.g)} total RDF triples")

            return True

        except Exception as e:
            print(f"Error generating ontology: {e}")
            import traceback

            traceback.print_exc()
            return False

        finally:
            # Close the database connection
            self.snomed_explorer.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description="Generate a cardiovascular guideline ontology from SNOMED CT data"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="cardio_ontology.owl",
        help="Output file path for the generated ontology",
    )
    parser.add_argument(
        "--host", default="10.250.135.23", help="SNOMED CT database host"
    )
    parser.add_argument("--port", default="3306", help="SNOMED CT database port")
    parser.add_argument(
        "--user", default="test_user", help="SNOMED CT database username"
    )
    parser.add_argument(
        "--password", default="medicaldatabase", help="SNOMED CT database password"
    )
    parser.add_argument(
        "--database", default="snomedct", help="SNOMED CT database name"
    )
    parser.add_argument(
        "--base-uri",
        default="http://dieterich-lab.org/ontologies/cardioguidelinesonto/",
        help="Base URI for the ontology",
    )
    parser.add_argument("-v", "--version", default="0.1.0", help="Ontology version")

    parser.add_argument(
        "--categorization-method",
        choices=["keyword", "llm"],
        default="llm",
        help="Concept categorization method: 'keyword' (default) or 'llm' (large language model)",
    )

    parser.add_argument(
        "--dev",
        "--debug",
        action="store_true",
        dest="debug_mode",
        help="Run in dev/debug mode (limit=2 for all queries)",
    )

    args = parser.parse_args()

    generator = CardioOntologyGenerator(
        output_path=args.output,
        snomed_host=args.host,
        snomed_port=args.port,
        snomed_user=args.user,
        snomed_password=args.password,
        snomed_database=args.database,
        base_uri=args.base_uri,
        version=args.version,
        debug_mode=args.debug_mode,
    )

    success = generator.generate_ontology(
        categorization_method=args.categorization_method
    )
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
