#!/usr/bin/env python3
"""
Script to inspect SNOMED CT descriptions for heart failure concepts.
Check what synonyms/abbreviations are actually stored in the database.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.cardio_graph.snomedct_utils.snomed_query import SnomedExplorer


def inspect_heart_failure_descriptions():
    explorer = SnomedExplorer()
    explorer.connect()

    # First, find the concept ID for "Heart failure with reduced ejection fraction"
    print("Searching for 'Heart failure with reduced ejection fraction'...")
    concepts = explorer.search_concepts_by_term(
        "Heart failure with reduced ejection fraction", limit=10
    )

    for concept in concepts:
        print(f"\nConcept ID: {concept.get('conceptId', concept.get('id'))}")
        print(f"Term: {concept.get('term', 'N/A')}")

        # Get all descriptions for this concept
        concept_id = concept.get("conceptId") or concept.get("id")
        if isinstance(concept_id, int):
            print(f"Fetching descriptions for concept {concept_id}...")
            descriptions = explorer.get_descriptions_for_concept(concept_id)

            print(f"Found {len(descriptions)} descriptions:")
            for desc in descriptions:
                print(f"  Type: {desc['type']}, Term: '{desc['term']}'")

                # Check for abbreviations
                term = desc["term"].lower()
                if any(
                    abbrev in term
                    for abbrev in [
                        "hfref",
                        "hfrEF",
                        "HFrEF",
                        "hf-ref",
                        "heart failure ref",
                    ]
                ):
                    print(f"    *** FOUND ABBREVIATION: {desc['term']} ***")

    # Also search for HFrEF directly
    print("\n\n=== SEARCHING FOR 'HFrEF' DIRECTLY ===")
    hfref_concepts = explorer.search_concepts_by_term("HFrEF", limit=20)
    print(f"Found {len(hfref_concepts)} concepts containing 'HFrEF':")

    for concept in hfref_concepts:
        concept_id = concept.get("conceptId") or concept.get("id")
        term = concept.get("term", "N/A")
        print(f"  ID: {concept_id}, Term: '{term}'")

        # Get descriptions
        if isinstance(concept_id, int):
            descriptions = explorer.get_descriptions_for_concept(concept_id)
            print(f"    Descriptions for concept {concept_id}:")
            for desc in descriptions:
                print(f"      {desc['type']}: '{desc['term']}'")

    # Specifically check the HFrEF concept
    hfref_concept_id = 4542150014
    print(f"\n\n=== DETAILED INSPECTION OF HFrEF CONCEPT (ID: {hfref_concept_id}) ===")
    descriptions = explorer.get_descriptions_for_concept(hfref_concept_id)
    print(f"Descriptions for HFrEF concept:")
    for desc in descriptions:
        print(f"  {desc['type']}: '{desc['term']}'")

    # Check database structure for description-related tables
    print("\n\n=== DATABASE TABLES ===")
    structure = explorer.explore_database_structure()
    desc_tables = [table for table in structure.keys() if "desc" in table.lower()]
    print(f"Description-related tables: {desc_tables}")

    for table in desc_tables:
        print(f"\nColumns in {table}:")
        print(f"  {structure[table]}")

    explorer.disconnect()


if __name__ == "__main__":
    inspect_heart_failure_descriptions()
