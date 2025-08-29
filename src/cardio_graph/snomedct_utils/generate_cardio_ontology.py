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
            all_descriptions = []
            if isinstance(concept_id, int):
                # Only call get_descriptions_for_concept for actual SNOMED CT concept IDs
                all_descriptions = self.snomed_explorer.get_descriptions_for_concept(
                    concept_id
                )
            else:
                # For UUID concepts, just use the term from the concept dict
                all_descriptions = [
                    {
                        "term": concept.get("term", ""),
                        "type": "PreferredTerm",
                        "typeId": None,
                    }
                ]

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

    def get_type_label(self, type_id: int) -> str:
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

        # Track classes and properties to avoid duplicates (initialize once)
        self.classes = set()
        self.properties = set()  # Object properties (store URIs)
        self.data_properties = set()  # Datatype properties (store URIs)
        self.snomed_concepts = {}  # Map from SNOMED concept ID to URI

        # Initialize core classes and properties
        self._init_core_structure()

    def _init_core_structure(self):
        """Initialize the core ontology structure from YAML (core_classes, core_properties, data_properties)."""
        from rdflib.namespace import XSD

        # First pass: declare classes & collect subclass axioms
        pending_subclasses = []  # (child, parent)
        seen: set[str] = set()
        for class_entry in _config.get("core_classes", []) or []:
            class_name = class_entry.get("name")
            if not class_name:
                continue
            if class_name in seen:
                print(
                    f"[WARN] Duplicate class definition for '{class_name}' ignored (keeping first)."
                )
                continue
            seen.add(class_name)
            class_uri = self.cgo[class_name]
            self.g.add((class_uri, RDF.type, OWL.Class))
            self.g.add((class_uri, RDFS.label, Literal(class_name)))
            desc = class_entry.get("description")
            if desc:
                self.g.add((class_uri, RDFS.comment, Literal(desc)))
            for term in class_entry.get("snomed_search_terms", []) or []:
                self.g.add((class_uri, SKOS.altLabel, Literal(term)))
            parent = class_entry.get("subclass_of")
            if parent:
                pending_subclasses.append((class_name, parent))
            self.classes.add(class_name)

        # Second pass: subclass axioms
        for child, parent in pending_subclasses:
            if parent not in seen:
                print(
                    f"[WARN] subclass_of parent '{parent}' for '{child}' not defined; skipping."
                )
                continue
            self.g.add((self.cgo[child], RDFS.subClassOf, self.cgo[parent]))

        # Object properties
        for prop_entry in _config.get("core_properties", []) or []:
            prop_name = prop_entry.get("name")
            if not prop_name:
                continue
            prop_uri = self.cgo[prop_name]
            self.g.add((prop_uri, RDF.type, OWL.ObjectProperty))
            self.g.add((prop_uri, RDFS.label, Literal(prop_name)))
            desc = prop_entry.get("description")
            if desc:
                self.g.add((prop_uri, RDFS.comment, Literal(desc)))
            domain = prop_entry.get("domain")
            if domain and domain in self.classes:
                self.g.add((prop_uri, RDFS.domain, self.cgo[domain]))
            rng = prop_entry.get("range")
            if rng and rng != "null" and rng in self.classes:
                self.g.add((prop_uri, RDFS.range, self.cgo[rng]))
            self.properties.add(prop_uri)

        # Datatype properties
        datatype_map = {
            "string": XSD.string,
            "integer": XSD.integer,
            "float": XSD.float,
            "date": XSD.date,
            "dateTime": XSD.dateTime,
            "boolean": XSD.boolean,
        }
        for dprop in _config.get("data_properties", []) or []:
            name = dprop.get("name")
            if not name:
                continue
            uri = self.cgo[name]
            self.g.add((uri, RDF.type, OWL.DatatypeProperty))
            self.g.add((uri, RDFS.label, Literal(name)))
            desc = dprop.get("description")
            if desc:
                self.g.add((uri, RDFS.comment, Literal(desc)))
            domain = dprop.get("domain")
            if domain and domain != "null" and domain in self.classes:
                self.g.add((uri, RDFS.domain, self.cgo[domain]))
            rng = dprop.get("range")
            if rng and rng != "null":
                rng_lower = str(rng).lower()
                # If the range names a class, we skip because this should be an object property.
                if rng in self.classes:
                    print(
                        f"[WARN] Datatype property '{name}' has class range '{rng}' – skipping range assertion (did you intend an object property?)"
                    )
                else:
                    dt = datatype_map.get(rng_lower)
                    if dt:
                        self.g.add((uri, RDFS.range, dt))
                    else:
                        # Fallback: treat as string if unknown
                        print(
                            f"[WARN] Unknown datatype '{rng}' for data property '{name}', defaulting to xsd:string"
                        )
                        self.g.add((uri, RDFS.range, XSD.string))
            self.data_properties.add(uri)

    def preflight_report(self):
        """Print a validation report comparing YAML schema to what was loaded into the graph."""
        cfg_classes = {
            c.get("name") for c in _config.get("core_classes", []) if c.get("name")
        }
        missing = [
            c
            for c in cfg_classes
            if self.cgo[c]
            not in [s for s, _, _ in self.g.triples((None, RDF.type, OWL.Class))]
        ]
        subclass_issues = []
        for c in _config.get("core_classes", []) or []:
            parent = c.get("subclass_of")
            if parent and parent not in cfg_classes:
                subclass_issues.append((c["name"], parent))
        from rdflib.namespace import OWL as _OWL

        obj_props = {
            s for s, _, _ in self.g.triples((None, RDF.type, _OWL.ObjectProperty))
        }
        data_props = {
            s for s, _, _ in self.g.triples((None, RDF.type, _OWL.DatatypeProperty))
        }
        print("--- Preflight Schema Report ---")
        print(f"Core classes in YAML: {len(cfg_classes)} | Loaded: {len(self.classes)}")
        if missing:
            print(f"[WARN] Missing class declarations for: {missing}")
        else:
            print("All YAML core_classes declared.")
        if subclass_issues:
            print("[WARN] subclass_of references missing parents:", subclass_issues)
        print(
            f"Object properties (core_properties): expected {len(_config.get('core_properties', []))} | Declared: {len(obj_props)}"
        )
        print(
            f"Data properties: expected {len(_config.get('data_properties', []))} | Declared: {len(data_props)}"
        )
        # SNOMED category coverage
        missing_categories = [c for c in SNOMED_CATEGORIES if c not in cfg_classes]
        if missing_categories:
            print(
                f"[WARN] SNOMED categories not defined as classes: {missing_categories}"
            )
        else:
            print("All SNOMED categories have corresponding classes.")
        print("--------------------------------")
        return {
            "core_classes_yaml": len(cfg_classes),
            "core_classes_loaded": len(self.classes),
            "object_properties_yaml": len(_config.get("core_properties", [])),
            "object_properties_loaded": len(obj_props),
            "data_properties_yaml": len(_config.get("data_properties", [])),
            "data_properties_loaded": len(data_props),
            "subclass_issues": subclass_issues,
            "missing_classes": missing,
            "missing_categories": missing_categories,
        }

    # (No mutations performed in preflight beyond report; data property declaration occurs earlier in init)

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
        use_limit = 10 if debug else 200
        max_classes = 10 if debug else None
        max_terms = 2 if debug else None
        max_concepts = 10 if debug else None

        ontology_classes = _config.get("core_classes", [])
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

                for concept in concepts_for_term:
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
        preferred_term = None
        if isinstance(concept_id, int):
            # Only call get_preferred_term for actual SNOMED CT concept IDs
            preferred_term = self.snomed_explorer.get_preferred_term(concept_id)

        # If we can't find a preferred term, fall back to the term from the search,
        # but log a warning.
        if not preferred_term:
            preferred_term = concept.get("term", f"Unknown Concept {concept_id}")
            if isinstance(concept_id, int):
                print(
                    f"Warning: No preferred term found for {concept_id}. Using '{preferred_term}'."
                )

        concept_uri = self.snomed[str(concept_id)]

        # Add the concept as a Class, and make it a subclass of the given category
        self.g.add((concept_uri, RDF.type, OWL.Class))
        if category_class:
            self.g.add((concept_uri, RDFS.subClassOf, category_class))

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

    def add_relationships(self, concept_id: int, relationships: List[Dict]):
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
                rel_name = self.get_type_label(rel_type)
                self.g.add((rel_prop_uri, RDFS.label, Literal(rel_name)))
                self.properties.add(rel_prop_uri)

            # Add the relationship triple
            self.g.add((source_uri, rel_prop_uri, target_uri))

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

            # Step 3: Extract all relationship data for the found concepts
            concept_ids_list = [c["conceptId"] for c in concepts if "conceptId" in c]

            print("--- Fetching Outgoing Relationships ---")
            outgoing_relationships = (
                self.snomed_explorer.get_outgoing_relationships_in_batch(
                    concept_ids_list
                )
            )
            print("--- Fetching Incoming Relationships ---")
            incoming_relationships = (
                self.snomed_explorer.get_incoming_relationships_in_batch(
                    concept_ids_list
                )
            )

            # Merge the two dictionaries into a single, unified structure
            all_relationships = outgoing_relationships.copy()
            for source_id, rels in incoming_relationships.items():
                all_relationships[source_id].extend(rels)

            # Step 4: Add all relationships using a single, simple loop
            print("--- Adding All Relationships ---")
            for concept_id, rels in all_relationships.items():
                self.add_relationships(concept_id, rels)

            # Save the ontology to file
            self.g.serialize(destination=self.output_path, format="xml")
            print(f"Ontology generated successfully and saved to {self.output_path}")

            # Print statistics
            print("--- Final Ontology Statistics ---")
            print(f"  - {len(self.classes)} core classes")
            print(f"  - {len(self.snomed_concepts)} SNOMED CT concepts")
            print(
                f"  - {len(self.properties)} object properties (incl. dynamic SNOMED rel props)"
            )
            print(f"  - {len(self.data_properties)} data properties")
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
    parser.add_argument(
        "--no-preflight",
        action="store_true",
        help="Skip preflight schema validation report.",
    )
    # Native BAML logging control (see BAML docs: BAML_LOG env var)
    parser.add_argument(
        "--baml-log-level",
        choices=["off", "error", "warn", "info", "debug", "trace"],
        help="Set BAML logging verbosity (native). 'warn' hides normal thinking output; 'off' hides all BAML logs.",
    )
    parser.add_argument(
        "--baml-log-truncate",
        type=int,
        help="Truncate each BAML log chunk to N characters (sets BOUNDARY_MAX_LOG_CHUNK_CHARS).",
    )
    parser.add_argument(
        "--quiet-llm",
        action="store_true",
        help="Convenience: equivalent to --baml-log-level warn (hide thinking, keep warnings).",
    )
    parser.add_argument(
        "--silent-llm",
        action="store_true",
        help="Convenience: equivalent to --baml-log-level off (suppress all BAML LLM logs).",
    )

    args = parser.parse_args()

    # Resolve BAML logging preferences (precedence: --silent-llm > --quiet-llm > explicit level)
    chosen_level = None
    if args.silent_llm:
        chosen_level = "off"
    elif args.quiet_llm:
        chosen_level = "warn"
    elif args.baml_log_level:
        chosen_level = args.baml_log_level
    if chosen_level:
        os.environ["BAML_LOG"] = chosen_level
    if args.baml_log_truncate is not None:
        os.environ["BOUNDARY_MAX_LOG_CHUNK_CHARS"] = str(args.baml_log_truncate)

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

    if not args.no_preflight:
        generator.preflight_report()
    generator.generate_ontology(categorization_method=args.categorization_method)


if __name__ == "__main__":
    main()
