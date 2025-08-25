#!/usr/bin/env python3
"""
Generate a cardiovascular guideline ontology from SNOMED CT data

This script extracts relevant cardiovascular concepts from SNOMED CT
and generates an OWL/RDF ontology for use with cardiovascular guidelines.
"""

import argparse
import os
import uuid
from datetime import datetime
from typing import Dict, List

import yaml
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD

from cardio_graph.snomedct_utils.models import SnapDescription

# Import SnomedExplorer from snomed_query.py
from cardio_graph.snomedct_utils.snomed_query import SnomedExplorer

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "ontology_config.yaml")
with open(CONFIG_PATH, "r") as f:
    _config = yaml.safe_load(f)
SNOMED_CATEGORIES = _config.get("snomed_categories", [])
SNOMED_KEYWORDS = _config.get("snomed_keywords", {})
NEGATIVE_KEYWORDS = _config.get("retrieval_filters", {}).get("negative_keywords", [])


class CardioOntologyGenerator:

    def categorize_concepts_llm(self, concepts: List[Dict]) -> Dict[str, List[URIRef]]:
        """
        Categorize SNOMED concepts using an LLM via BAML, with full description context.
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

            preferred_term = ""
            fsn = ""
            synonyms = []

            # Find the preferred term first (based on your get_descriptions_for_concept logic)
            for desc in all_descriptions:
                if desc.get(
                    "is_preferred"
                ):  # Assumes get_descriptions is updated to provide this
                    preferred_term = desc["term"]
                    break

            # If not found via refset, fall back to the initial term
            if not preferred_term:
                preferred_term = concept.get("term", "")

            # Now collect FSN and synonyms
            for desc in all_descriptions:
                if desc["type"] == "FSN":
                    fsn = desc["term"]
                # Add to synonyms if it's not the preferred term
                elif desc["term"].lower() != preferred_term.lower():
                    synonyms.append(desc["term"])

            # Make sure FSN isn't also in the synonym list
            if fsn and fsn.lower() != preferred_term.lower():
                synonyms = [s for s in synonyms if s.lower() != fsn.lower()]

            baml_input = {
                "term": preferred_term,
                "description": fsn,
                "synonyms": ", ".join(
                    sorted(list(set(synonyms)))
                ),  # Ensure unique, sorted synonyms
            }

            try:
                result = b.CategorizeConcept(baml_input, SNOMED_CATEGORIES)
                assigned_categories = result.categories

                # The 'add_snomed_concept' function will now handle setting the correct label
                # so we just need to pass the original concept dict to it.
                for cat_name in assigned_categories:
                    if cat_name in categories_map:
                        category_class_uri = self.cgo[cat_name]

                        # Pass the category to the creation function
                        concept_uri = self.add_snomed_concept(
                            concept, category_class_uri, synonyms=synonyms
                        )
                        categories_map[cat_name].append(concept_uri)

            except Exception as e:
                print(f"Error categorizing concept '{preferred_term}': {e}")
                continue

        return categories_map

    def categorize_concepts(self, concepts: List[Dict]) -> Dict[str, List[URIRef]]:
        """Categorize SNOMED concepts into snomed categories using keywords from YAML config"""
        categories = {cat: [] for cat in SNOMED_CATEGORIES}
        for concept in concepts:
            term = concept.get("term", "").lower()
            for category_name, keyword_list in SNOMED_KEYWORDS.items():
                if any(keyword in term for keyword in keyword_list):
                    category_class_uri = self.cgo[category_name]
                    concept_uri = self.add_snomed_concept(
                        concept, category_class_uri, synonyms=None
                    )
                    categories[category_name].append(concept_uri)
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
        from rdflib.namespace import XSD

        # Add core classes
        for class_entry in _config.get("ontology_classes", []):
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
        for prop_entry in _config.get("ontology_properties", []):
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

    def extract_cardiovascular_concepts(self, limit: int = 1000) -> List[Dict]:
        """
        Extracts cardiovascular concepts from SNOMED CT by running targeted searches
        based on the snomed_search_terms defined in the ontology_config.yaml.
        """
        print("Extracting cardiovascular concepts using a schema-aware approach...")

        all_concepts = []
        seen_ids = set()

        # --- Debugging Setup (from your code) ---
        debug = getattr(self, "debug_mode", False)
        use_limit = 2 if debug else 200
        max_classes = 2 if debug else None
        max_terms = 2 if debug else None
        max_concepts = 10 if debug else None

        ontology_classes = _config.get("ontology_classes", [])
        if max_classes:
            ontology_classes = ontology_classes[:max_classes]

        for class_entry in ontology_classes:
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
                filtered_concepts = []
                for concept in concepts_for_term:
                    concept_term = concept.get("term", "").lower()
                    if not any(
                        neg_word in concept_term for neg_word in NEGATIVE_KEYWORDS
                    ):
                        filtered_concepts.append(concept)

                for concept in filtered_concepts:
                    concept_id = None
                    id_keys_to_try = [
                        "conceptId",
                        "id",
                        "referencedComponentId",
                        "sourceId",
                    ]
                    for key in id_keys_to_try:
                        if key in concept and concept[key]:
                            concept_id = concept[key]
                            break  # Found it, stop looking

                    if not concept_id:
                        # If we still can't find an ID, we must skip this record and warn the user.
                        print(
                            f"  [WARNING] Skipping record because no valid ID key was found. Data: {concept}"
                        )
                        continue
                    # --- END OF FIX ---

                    if concept_id not in seen_ids:
                        # To avoid KeyErrors later, we will standardize the ID key.
                        # We will add 'conceptId' to the dictionary if it's not already there.
                        if "conceptId" not in concept:
                            concept["conceptId"] = concept_id

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

    def add_snomed_concept(
        self, concept: Dict, category_class: URIRef, synonyms: List[str] = None
    ) -> URIRef:
        """
        Adds a SNOMED CT concept to the ontology, ensuring its rdfs:label
        is always the canonical Preferred Term.
        """
        concept_id = concept.get("conceptId") or concept.get("id")
        if not concept_id:
            concept_id = str(uuid.uuid4())  # Handle concepts without IDs

        if concept_id in self.snomed_concepts:
            return self.snomed_concepts[concept_id]

        # --- KEY IMPROVEMENT ---
        # Fetch the canonical preferred term directly from the explorer.
        # Do not trust the 'term' field from the initial search result.
        preferred_term = self.snomed_explorer.get_preferred_term(concept_id)

        # If we can't find a preferred term, fall back to the term from the search,
        # but log a warning.
        if not preferred_term:
            preferred_term = concept.get("term", f"Unknown Concept {concept_id}")
            print(
                f"Warning: No preferred term found for {concept_id}. Using '{preferred_term}'."
            )

        concept_uri = self.snomed[str(concept_id)]

        # Declare it as an individual of the specific class from our schema.
        self.g.add((concept_uri, RDF.type, OWL.NamedIndividual))
        self.g.add((concept_uri, RDF.type, category_class))  # e.g., type cgo:Condition

        # Always use the fetched preferred_term for the official label.
        self.g.add((concept_uri, RDFS.label, Literal(preferred_term)))

        # Add all synonyms as alternative labels
        if synonyms:
            for synonym in synonyms:
                self.g.add((concept_uri, SKOS.altLabel, Literal(synonym)))

        if concept.get("active") == 1:
            self.g.add((concept_uri, self.cgo["isActive"], Literal(True)))

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
            # Not 100% correct as individuals (in owl-terms)
            # should not be able to sub-class themselves.
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

            # Step 1: Extract a list of candidate concept dictionaries
            concepts = self.extract_cardiovascular_concepts()

            if not concepts:
                print("No cardiovascular concepts found in SNOMED CT")
                return False

            # Step 2: Extract all relationship data for the found concepts in a single batch
            concept_ids_list = [c["conceptId"] for c in concepts if "conceptId" in c]
            relationships = self.snomed_explorer.get_relationships_in_batch(
                concept_ids_list
            )

            # Step 3: Categorize concepts. This step now ALSO adds the concepts to the graph.
            if categorization_method == "llm":
                print("Using LLM-based concept categorization...")
                categories = self.categorize_concepts_llm(concepts)
            else:
                print("Using keyword-based concept categorization...")
                # Note: The keyword version will also need to be updated to call the new add_snomed_concept
                categories = self.categorize_concepts(concepts)

            # Print category statistics
            print("--- Category Statistics ---")
            for category, uris in categories.items():
                print(f"  - {category}: {len(uris)} concepts")

            # Step 4: Add all the relationships between the concepts we just added.
            print("--- Adding Relationships ---")
            for concept_id, rels in relationships.items():
                self.add_relationships(
                    str(concept_id), rels
                )  # Ensure concept_id is a string

            # Save the ontology to file
            self.g.serialize(destination=self.output_path, format="xml")
            print(f"Ontology generated successfully and saved to {self.output_path}")

            # Print statistics
            print("--- Final Ontology Statistics ---")
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

    generator.generate_ontology(categorization_method=args.categorization_method)


if __name__ == "__main__":
    main()
