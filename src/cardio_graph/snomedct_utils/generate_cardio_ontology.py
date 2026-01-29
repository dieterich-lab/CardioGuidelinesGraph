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

# Import client registry for LLM connections
from cardio_graph.extraction_utils.clients import create_client_registry
from cardio_graph.snomedct_utils.models import SnapDescription

# Import SnomedExplorer from snomed_query.py
from cardio_graph.snomedct_utils.snomed_query import SnomedExplorer

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "ontology_config.yaml")
with open(CONFIG_PATH, "r") as f:
    _config = yaml.safe_load(f)
SNOMED_CATEGORIES = _config.get("snomed_categories", [])
SNOMED_KEYWORDS = _config.get("snomed_keywords", {})


class CardioOntologyGenerator:

    def _concept_exists_in_database(self, concept_id) -> bool:
        """Check if a concept exists in the SNOMED CT concept table."""
        if not concept_id or not isinstance(concept_id, int):
            return False

        try:
            from sqlalchemy import text

            result = self.snomed_explorer.session.execute(
                text(
                    "SELECT 1 FROM concept WHERE id = :concept_id AND active = true LIMIT 1"
                ),
                {"concept_id": concept_id},
            )
            return result.fetchone() is not None
        except Exception:
            return False

    """Generate a cardiovascular ontology from SNOMED CT data"""

    def __init__(
        self,
        output_path: str = None,
        snomed_host: str = "snomed-ct2.internal",
        snomed_port: str = "5432",
        snomed_user: str = "readonly",
        snomed_password: str = "readonly",
        snomed_database: str = "snomed",
        snomed_sslrootcert: str = "/etc/ssl/certs/DieterichLab_CA.pem",
        snomed_sslmode: str = "verify-full",
        base_uri: str = "http://dieterich-lab.org/ontologies/cardioguidelinesonto/",
        version: str = "0.1.0",
        debug_mode: bool = False,
        modeling_approach: str = "class",
        model: str = "Qwen32b",
        node: str = "g4",
        ollama_port: int = "34",
        snomed_relations_mode: str = "none",  # 'none', 'curated', 'all'
        collect_synonyms: bool = True,  # Whether to use LLM for synonym collection
    ):
        """Initialize the ontology generator

        Args:
            modeling_approach: "instance" (SNOMED concepts as individuals) or "class" (SNOMED concepts as classes)
            model: Model name to use for LLM categorization (e.g., Qwen32b5, Gemma, GPT4oMini)
            node: Node identifier for Ollama models (g2, g3, g4, g5)
            ollama_port: Custom port number (overrides default node port)
            collect_synonyms: Whether to use LLM for collecting additional synonyms beyond SNOMED CT
        """
        # Set default output path based on modeling approach and SNOMED relations mode if not specified
        if output_path is None:
            ontologies_dir = "/prj/doctoral_letters/guide/data/ontologies"
            suffix = {
                "none": "coreonly",
                "curated": "curatedsnomed",
                "all": "allsnomed",
            }.get(snomed_relations_mode, "coreonly")
            # Add unique hash to make each run's output file unique
            suffix = f"{suffix}_{uuid.uuid4().hex[:8]}"
            if modeling_approach == "instance":
                output_path = f"{ontologies_dir}/cardio_ontology_instances_{suffix}.owl"
            else:
                output_path = f"{ontologies_dir}/cardio_ontology_class_{suffix}.owl"

        self.output_path = output_path
        self.snomed_relations_mode = snomed_relations_mode
        # Initialize ontology namespace (CGO) before any use
        self.cgo = Namespace(base_uri)
        self.snomed = Namespace("http://snomed.info/id/")
        self.g = Graph()
        self.g.bind("cgo", self.cgo)
        self.g.bind("snomed", self.snomed)
        self.snomed_explorer = SnomedExplorer(
            host=snomed_host,
            port=snomed_port,
            user=snomed_user,
            password=snomed_password,
            database=snomed_database,
            sslrootcert=snomed_sslrootcert,
            sslmode=snomed_sslmode,
        )
        self.debug_mode = debug_mode
        self.modeling_approach = modeling_approach
        self.as_individual = modeling_approach == "instance"
        self.collect_synonyms = collect_synonyms
        self.classes = set()
        self.properties = set()
        self.data_properties = set()
        self.snomed_concepts = dict()

        # Load guideline abbreviations
        self.abbreviations = self._load_abbreviations()

        # Initialize client registry for LLM connections
        try:
            self.client_registry = create_client_registry(model, node, ollama_port)
        except Exception as e:
            print(f"Warning: Could not create client registry: {e}")

            def generate_ontology(self):
                """Generate the complete cardiovascular guidelines ontology by creating classes directly from SNOMED CT concepts"""
                print("Generating cardiovascular guidelines ontology...")

                # Curated SNOMED relationship type IDs (example: add more as needed)
                curated_type_ids = {
                    "116676008",  # 'associated morphology'
                    "363698007",  # 'finding site'
                    "246454002",  # 'occurrence'
                    "363713009",  # 'has interpretation'
                    "370135005",  # 'pathological process'
                    "363714003",  # 'procedure site'
                    "363589002",  # 'associated with'
                    "260686004",  # 'method'
                    "363705008",  # 'has specimen'
                    "246075003",  # 'causative agent'
                }

                try:
                    # Connect to the SNOMED CT database
                    self.snomed_explorer.connect()

                    # Step 1: Extract cardiovascular concepts from SNOMED CT
                    concepts = self.extract_cardiovascular_concepts()

                    if not concepts:
                        print("No concepts extracted.")
                        return False

                    print(f"Extracted {len(concepts)} cardiovascular concepts")

                    # Step 2: Categorize concepts. This step now ALSO adds the concepts to the graph.
                    categorization_method = "llm"  # Use LLM for categorization
                    if categorization_method == "llm":
                        categories = self.categorize_concepts_llm(concepts)
                    else:
                        categories = self.categorize_concepts(concepts)

                    # Collect all SNOMED classes created
                    snomed_classes = {}
                    for cat_name, concept_uris in categories.items():
                        for uri in concept_uris:
                            snomed_classes[uri] = cat_name

                    print(f"Created {len(snomed_classes)} ontology classes")

                    # Print category statistics
                    for cat_name, concept_uris in categories.items():
                        print(f"  - {cat_name}: {len(concept_uris)} concepts")

                    # Step 3: Extract relationship data and create hierarchy
                    concept_ids_list = [
                        int(c["conceptId"])
                        for c in concepts
                        if "conceptId" in c and c["conceptId"] is not None
                    ]

                    if concept_ids_list:
                        if self.snomed_relations_mode == "none":
                            # Only add is-a relationships (taxonomy)
                            print("Adding only SNOMED is-a (taxonomy) relationships.")
                            # (Assume existing logic already does this)
                        elif self.snomed_relations_mode == "curated":
                            print("Adding curated SNOMED relationships.")
                            for cid in concept_ids_list:
                                rels = self.snomed_explorer.get_relationships(cid)
                                curated_rels = [
                                    r
                                    for r in rels
                                    if str(r.get("typeId")) in curated_type_ids
                                    or str(r.get("typeid")) in curated_type_ids
                                ]
                                self.add_relationships(cid, curated_rels)
                        elif self.snomed_relations_mode == "all":
                            print("Adding all SNOMED relationships.")
                            for cid in concept_ids_list:
                                rels = self.snomed_explorer.get_relationships(cid)
                                self.add_relationships(cid, rels)

                    # Save the ontology to file
                    self.g.serialize(destination=self.output_path, format="xml")
                    print(
                        f"Ontology generated successfully and saved to {self.output_path}"
                    )

                    # Print statistics
                    print("--- Final Ontology Statistics ---")
                    print(f"  - {len(self.classes)} core classes")
                    print(f"  - {len(snomed_classes)} SNOMED-derived classes")
                    print(f"  - {len(self.properties)} object properties")
                    print(f"  - {len(self.data_properties)} data properties")
                    print(f"  - {len(self.g)} total RDF triples")
                    print(
                        f"  - Modeling approach: {self.modeling_approach}-based (direct SNOMED concept mapping)"
                    )
                    print(f"  - SNOMED relations mode: {self.snomed_relations_mode}")

                    return True

                except Exception as e:
                    print(f"Error generating ontology: {e}")
                    import traceback

                    traceback.print_exc()
                    return False

                finally:
                    # Close the database connection
                    self.snomed_explorer.disconnect()

        # --- Core class creation (from config) ---
        pending_subclasses = []
        seen = set()
        for class_entry in _config.get("core_classes", []) or []:
            class_name = class_entry.get("name")
            if not class_name:
                continue
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
            seen.add(class_name)

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

    def _load_abbreviations(self) -> Dict[str, str]:
        """Load guideline-internal abbreviations from abbrv.txt file.
        
        Returns:
            Dictionary mapping full terms to their abbreviations
        """
        abbrv_path = os.path.join(os.path.dirname(__file__), "abbrv.txt")
        abbreviations = {}
        
        try:
            with open(abbrv_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # Split by "; " and parse each abbreviation
            entries = content.split("; ")
            for entry in entries:
                entry = entry.strip()
                if not entry or entry.endswith('. a'):  # Skip the trailing ". a"
                    continue
                    
                if ", " in entry:
                    abbr, full_term = entry.split(", ", 1)
                    abbr = abbr.strip()
                    full_term = full_term.strip()
                    if abbr and full_term:
                        abbreviations[full_term.lower()] = abbr
                        
        except Exception as e:
            print(f"Warning: Could not load abbreviations file: {e}")
            
        print(f"Loaded {len(abbreviations)} guideline abbreviations")
        return abbreviations

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
                baml_options = (
                    {"client_registry": self.client_registry}
                    if self.client_registry
                    else {}
                )
                result = b.CategorizeConcept(
                    baml_input,
                    SNOMED_CATEGORIES,
                    baml_options=baml_options,
                )
                assigned_categories = result.categories

                # Conditionally collect LLM synonyms based on flag
                llm_synonyms = []
                if self.collect_synonyms:
                    llm_synonyms = result.synonyms or []

                # DEBUG: Print synonym information
                if llm_synonyms:
                    print(
                        f"[DEBUG] LLM generated synonyms for '{preferred_term}': {llm_synonyms}"
                    )
                if synonyms:
                    print(f"[DEBUG] SNOMED synonyms for '{preferred_term}': {synonyms}")

                # Combine SNOMED synonyms with LLM-generated synonyms, avoiding duplicates
                combined_synonyms = list(set(synonyms + llm_synonyms))
                if (
                    llm_synonyms
                ):  # Only print combined message when LLM synonyms were actually collected
                    print(
                        f"[DEBUG] Combined synonyms for '{preferred_term}': {combined_synonyms}"
                    )

                # Add guideline abbreviations if the preferred term or any synonym matches
                guideline_abbreviations = []
                # Check preferred term
                if preferred_term.lower() in self.abbreviations:
                    guideline_abbreviations.append(self.abbreviations[preferred_term.lower()])
                # Check SNOMED synonyms
                for synonym in synonyms:
                    if synonym.lower() in self.abbreviations:
                        guideline_abbreviations.append(self.abbreviations[synonym.lower()])
                
                # Add unique abbreviations to combined synonyms
                if guideline_abbreviations:
                    guideline_abbreviations = list(set(guideline_abbreviations))  # Remove duplicates
                    combined_synonyms.extend(guideline_abbreviations)
                    combined_synonyms = list(set(combined_synonyms))  # Remove any new duplicates
                    print(f"[DEBUG] Added guideline abbreviations for '{preferred_term}': {guideline_abbreviations}")

                # The 'add_snomed_concept' function will now handle setting the correct label
                # so we just need to pass the original concept dict to it.
                for cat_name in assigned_categories:
                    if cat_name in categories_map:
                        category_class_uri = self.cgo[cat_name]

                        # Pass the category to the creation function
                        concept_uri = self.add_snomed_concept(
                            concept,
                            category_class_uri,
                            synonyms=combined_synonyms,
                            as_individual=self.as_individual,
                        )
                        categories_map[cat_name].append(concept_uri)

            except Exception as e:
                print(f"Error categorizing concept '{preferred_term}': {e}")
                continue

        return categories_map

    def categorize_concepts(self, concepts: List[Dict]) -> Dict[str, List[URIRef]]:
        """Categorize SNOMED concepts into snomed categories using source class from extraction"""
        categories = {cat: [] for cat in SNOMED_CATEGORIES}
        for concept in concepts:
            # Use the source class that was determined during extraction
            source_class = concept.get("_source_class")
            if source_class and source_class in categories:
                category_class_uri = self.cgo[source_class]
                concept_uri = self.add_snomed_concept(
                    concept,
                    category_class_uri,
                    synonyms=None,
                    as_individual=self.as_individual,
                )
                categories[source_class].append(concept_uri)
            else:
                # Fallback: try to categorize based on keywords in the term
                term = concept.get("term", "").lower()
                assigned = False
                for cat, keywords in SNOMED_KEYWORDS.items():
                    if any(kw in term for kw in keywords):
                        category_class_uri = self.cgo[cat]
                        concept_uri = self.add_snomed_concept(
                            concept,
                            category_class_uri,
                            synonyms=None,
                            as_individual=self.as_individual,
                        )
                        categories[cat].append(concept_uri)
                        assigned = True
                        break
                if not assigned:
                    # Default to Condition if nothing matches
                    if "Condition" in categories:
                        category_class_uri = self.cgo["Condition"]
                        concept_uri = self.add_snomed_concept(
                            concept,
                            category_class_uri,
                            synonyms=None,
                            as_individual=self.as_individual,
                        )
                        categories["Condition"].append(concept_uri)

        return categories

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
        Extracts cardiovascular concepts from SNOMED CT by finding concepts that exist
        in both the concept and description tables, ensuring data consistency.
        """
        print("Extracting cardiovascular concepts using validated database queries...")

        all_concepts = []
        seen_ids = set()

        # Use broad cardiovascular search terms
        cardiovascular_terms = _config.get("cardiovascular_search_terms", [])

        print(
            f"Using {len(cardiovascular_terms)} broad search terms to extract concepts..."
        )

        for term in cardiovascular_terms:
            print(f"--> Searching for: '{term}'")

            # Find concepts that exist in both concept and description tables
            try:
                from sqlalchemy import text

                # Query for concepts that have descriptions containing the search term
                # and also exist in the concept table
                query = text(
                    """
                    SELECT DISTINCT d.conceptid, d.term, d.typeid, c.active as concept_active
                    FROM description d
                    JOIN concept c ON d.conceptid = c.id
                    WHERE d.term ILIKE :search_term
                    AND d.active = true
                    AND c.active = true
                    LIMIT :limit_per_term
                """
                )

                result = self.snomed_explorer.session.execute(
                    query, {"search_term": f"%{term}%", "limit_per_term": 50}
                )

                for row in result:
                    concept_id = int(row[0])
                    if concept_id in seen_ids:
                        continue
                    seen_ids.add(concept_id)

                    # Get full description info for this concept
                    descriptions = self.snomed_explorer.get_descriptions_for_concept(
                        concept_id
                    )
                    if descriptions:
                        # Use the first FSN or synonym as the primary term
                        primary_term = descriptions[0]["term"]
                        for desc in descriptions:
                            if desc.get("type") == "FSN":
                                primary_term = desc["term"]
                                break

                        concept_dict = {
                            "conceptId": concept_id,
                            "id": concept_id,
                            "term": primary_term,
                            "active": True,
                            "descriptions": descriptions,
                        }
                        all_concepts.append(concept_dict)

            except Exception as e:
                print(f"Error searching for term '{term}': {e}")
                continue

            if len(all_concepts) >= limit:
                print(f"Reached concept limit of {limit}")
                break

        print(f"Extracted {len(all_concepts)} validated cardiovascular concepts")
        return all_concepts

    def add_snomed_concept(
        self,
        concept: Dict,
        category_class: URIRef = None,
        synonyms: List[str] = None,
        as_individual: bool = False,
    ) -> URIRef:
        """
        Adds a SNOMED CT concept to the ontology as a class.

        Args:
            concept: SNOMED concept dictionary
            category_class: Optional CGO category class URI (for backward compatibility)
            synonyms: List of synonym terms
            as_individual: If True, creates as NamedIndividual. If False, creates as OWL Class.

        Returns:
            URI of the created concept
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

        if as_individual:
            # Create as NamedIndividual instance of the category class
            self.g.add((concept_uri, RDF.type, OWL.NamedIndividual))
            if category_class:
                self.g.add((concept_uri, RDF.type, category_class))
        else:
            # Create as OWL Class
            self.g.add((concept_uri, RDF.type, OWL.Class))
            # If category_class is provided, make it a subclass
            if category_class:
                self.g.add((concept_uri, RDFS.subClassOf, category_class))

        # Always use the fetched preferred_term for the official label.
        self.g.add((concept_uri, RDFS.label, Literal(preferred_term)))

        # Add SNOMED ID as data property
        if isinstance(concept_id, int):
            self.g.add((concept_uri, self.cgo["hasSnomedId"], Literal(str(concept_id))))

        # Add all synonyms as alternative labels
        if synonyms:
            print(
                f"    Adding {len(synonyms)} synonyms as SKOS altLabels for concept {concept_id}: {synonyms}"
            )
            for synonym in synonyms:
                print(f"      - {synonym}")
                self.g.add((concept_uri, SKOS.altLabel, Literal(synonym)))
        # No longer printing "No synonyms to add" since that's expected for many concepts

        if concept.get("active") == 1:
            self.g.add((concept_uri, self.cgo["isActive"], Literal(True)))

        self.snomed_concepts[concept_id] = concept_uri
        return concept_uri

    def add_relationships(self, concept_id: int, relationships: List[Dict]):
        """Add relationships for a concept to the ontology

        Args:
            concept_id: The concept ID from the relationships map key
            relationships: List of relationship dictionaries (all have sourceId, destinationId, typeId)
        """
        # Determine relationship direction based on whether concept_id is in our ontology
        is_outgoing = concept_id in self.snomed_concepts

        if is_outgoing:
            # concept_id is the source of outgoing relationships
            source_uri = self.snomed_concepts[concept_id]
        else:
            # concept_id is the source of incoming relationships (source not in our ontology)
            # We need to verify that the destination is one of our concepts
            pass

        for rel in relationships:
            rel_type = rel.get("typeId") or rel.get("typeid")
            source_id = rel.get("sourceId") or rel.get("sourceid")
            destination_id = rel.get("destinationId") or rel.get("destinationid")

            if not rel_type or not source_id or not destination_id:
                continue

            if is_outgoing:
                # Outgoing: our_concept -> destinationId
                if source_id != concept_id:
                    continue

                target_uri = self.snomed[str(destination_id)]

                # Ensure target exists
                if destination_id not in self.snomed_concepts:
                    term = f"SNOMED Concept {destination_id}"
                    if self.as_individual:
                        self.g.add((target_uri, RDF.type, OWL.NamedIndividual))
                    else:
                        self.g.add((target_uri, RDF.type, OWL.Class))
                    self.g.add((target_uri, RDFS.label, Literal(term)))
                    self.snomed_concepts[destination_id] = target_uri

                rel_prop_uri = self.cgo[f"snomed_rel_{rel_type}"]
                if rel_prop_uri not in self.properties:
                    if self.as_individual:
                        self.g.add((rel_prop_uri, RDF.type, OWL.ObjectProperty))
                    else:
                        self.g.add((rel_prop_uri, RDF.type, OWL.ObjectProperty))
                    rel_name = self.get_type_label(rel_type)
                    self.g.add((rel_prop_uri, RDFS.label, Literal(rel_name)))
                    self.properties.add(rel_prop_uri)

                # Add the relationship triple
                self.g.add((source_uri, rel_prop_uri, target_uri))

            else:
                # Incoming: sourceId -> our_concept (where destinationId should be in our ontology)
                if destination_id not in self.snomed_concepts:
                    continue

                if source_id != concept_id:
                    continue

                source_uri = self.snomed[str(source_id)]
                target_uri = self.snomed_concepts[destination_id]

                # Ensure source exists
                if source_id not in self.snomed_concepts:
                    term = f"SNOMED Concept {source_id}"
                    if self.as_individual:
                        self.g.add((source_uri, RDF.type, OWL.NamedIndividual))
                    else:
                        self.g.add((source_uri, RDF.type, OWL.Class))
                    self.g.add((source_uri, RDFS.label, Literal(term)))
                    self.snomed_concepts[source_id] = source_uri

                rel_prop_uri = self.cgo[f"snomed_rel_{rel_type}"]
                if rel_prop_uri not in self.properties:
                    if self.as_individual:
                        self.g.add((rel_prop_uri, RDF.type, OWL.ObjectProperty))
                    else:
                        self.g.add((rel_prop_uri, RDF.type, OWL.ObjectProperty))
                    rel_name = self.get_type_label(rel_type)
                    self.g.add((rel_prop_uri, RDFS.label, Literal(rel_name)))
                    self.properties.add(rel_prop_uri)

                # Add the relationship triple
                self.g.add((source_uri, rel_prop_uri, target_uri))

    def generate_ontology(self):
        """Generate the complete cardiovascular guidelines ontology by creating classes directly from SNOMED CT concepts"""
        print("Generating cardiovascular guidelines ontology...")

        try:
            # Connect to the SNOMED CT database
            self.snomed_explorer.connect()

            # Step 1: Extract cardiovascular concepts from SNOMED CT
            limit = 5 if self.debug_mode else 1000
            concepts = self.extract_cardiovascular_concepts(limit=limit)

            if not concepts:
                print("No cardiovascular concepts found in SNOMED CT")
                return False

            print(f"Extracted {len(concepts)} cardiovascular concepts")

            # Step 2: Categorize concepts. This step now ALSO adds the concepts to the graph.
            categorization_method = "llm"  # Use LLM for categorization
            if categorization_method == "llm":
                print("Using LLM-based concept categorization...")
                categories = self.categorize_concepts_llm(concepts)
            else:
                print("Using keyword-based concept categorization...")
                categories = self.categorize_concepts(concepts)

            # Collect all SNOMED classes created
            snomed_classes = {}
            for cat_name, concept_uris in categories.items():
                for uri in concept_uris:
                    # Extract concept ID from URI or from the graph
                    # Since URI is snomed:id, get id from uri
                    uri_str = str(uri)
                    if uri_str.startswith("http://snomed.info/id/"):
                        concept_id = int(uri_str.split("/")[-1])
                        snomed_classes[concept_id] = uri

            print(f"Created {len(snomed_classes)} ontology classes")

            # Print category statistics
            for cat_name, concept_uris in categories.items():
                print(f"  {cat_name}: {len(concept_uris)} concepts")

            # Step 3: Extract relationship data and create hierarchy

            # Step 3: Extract relationship data and create hierarchy
            concept_ids_list = [
                int(c["conceptId"])
                for c in concepts
                if "conceptId" in c and c["conceptId"] is not None
            ]

            if concept_ids_list:
                print("--- Fetching SNOMED Relationships for Hierarchy ---")
                outgoing_relationships = (
                    self.snomed_explorer.get_outgoing_relationships_in_batch(
                        concept_ids_list
                    )
                )
                print(
                    f"Found outgoing relationships for {len(outgoing_relationships)} concepts"
                )

                # Create subclass relationships based on SNOMED "Is a" relationships
                print("Creating ontology hierarchy from SNOMED relationships...")
                hierarchy_relationships = 0
                for concept_id, relationships in outgoing_relationships.items():
                    if concept_id not in snomed_classes:
                        continue

                    source_uri = snomed_classes[concept_id]
                    for rel in relationships:
                        rel_type = rel.get("typeId")
                        destination_id = rel.get("destinationId")

                        # Look for "Is a" relationships (SNOMED typeId 116680003)
                        if rel_type == 116680003 and destination_id in snomed_classes:
                            parent_uri = snomed_classes[destination_id]
                            self.g.add((source_uri, RDFS.subClassOf, parent_uri))
                            hierarchy_relationships += 1

                print(f"Created {hierarchy_relationships} subclass relationships")

            # Save the ontology to file
            self.g.serialize(destination=self.output_path, format="xml")
            print(f"Ontology generated successfully and saved to {self.output_path}")

            # Print statistics
            print("--- Final Ontology Statistics ---")
            print(f"  - {len(self.classes)} core classes")
            print(f"  - {len(snomed_classes)} SNOMED-derived classes")
            print(f"  - {len(self.properties)} object properties")
            print(f"  - {len(self.data_properties)} data properties")
            print(f"  - {len(self.g)} total RDF triples")
            print("  - Modeling approach: class-based (direct SNOMED concept mapping)")

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
        help="Output file path for the generated ontology (optional - will be set automatically based on modeling approach)",
    )
    parser.add_argument(
        "--host", default="snomed-ct2.internal", help="SNOMED CT database host"
    )
    parser.add_argument("--port", default="5432", help="SNOMED CT database port")
    parser.add_argument(
        "--user", default="readonly", help="SNOMED CT database username"
    )
    parser.add_argument(
        "--password", default="readonly", help="SNOMED CT database password"
    )
    parser.add_argument("--database", default="snomed", help="SNOMED CT database name")
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
        help="Concept categorization method: 'keyword' (default) or 'llm' (large language model) - DEPRECATED: Direct class creation is now used",
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
    parser.add_argument(
        "--modeling-approach",
        choices=["instance", "class"],
        default="class",
        help="How to model SNOMED concepts: 'instance' (as individuals) or 'class' (as classes)",
    )
    parser.add_argument(
        "--sslrootcert",
        default="/etc/ssl/certs/DieterichLab_CA.pem",
        help="Path to SSL root certificate for database connection",
    )
    parser.add_argument(
        "--sslmode",
        default="verify-full",
        help="SSL mode for database connection (verify-full, require, etc.)",
    )
    parser.add_argument(
        "--model",
        default="Qwen32b",
        help="Model name to use for LLM categorization (e.g., Qwen32b, Qwen8b, GPT41Nano)",
    )
    parser.add_argument(
        "--node",
        choices=["g2", "g3", "g4", "g5"],
        default="g5",
        help="Node identifier for Ollama models",
    )
    parser.add_argument(
        "--ollama-port",
        type=int,
        help="Custom port number for Ollama server (overrides default node port)",
    )

    parser.add_argument(
        "--snomed-relations",
        choices=["none", "curated", "all"],
        default="none",
        help="Which SNOMED relationships to include: none (only is-a), curated (selected types), or all. Output filename will reflect this mode.",
    )

    parser.add_argument(
        "--no-synonyms",
        action="store_true",
        help="Skip LLM-based synonym collection (only use SNOMED CT synonyms)",
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
        snomed_sslrootcert=args.sslrootcert,
        snomed_sslmode=args.sslmode,
        base_uri=args.base_uri,
        version=args.version,
        debug_mode=args.debug_mode,
        modeling_approach=args.modeling_approach,
        model=args.model,
        node=args.node,
        ollama_port=getattr(args, "ollama_port", None),
        snomed_relations_mode=args.snomed_relations,
        collect_synonyms=not args.no_synonyms,
    )

    if not args.no_preflight:
        generator.preflight_report()
    generator.generate_ontology()


if __name__ == "__main__":
    main()
