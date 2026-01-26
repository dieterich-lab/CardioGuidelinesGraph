#!/usr/bin/env python3
"""
Test what concepts are found by search and if they have descriptions
"""

from cardio_graph.snomedct_utils.snomed_query import SnomedExplorer

explorer = SnomedExplorer()
explorer.connect()

# Test the search that the ontology generator uses
print("Testing search for 'heart'...")
concepts = explorer.search_concepts_by_term("heart", limit=5)

print(f"Found {len(concepts)} concepts:")
for concept in concepts[:1]:  # Just check first 1
    concept_id = concept.get("conceptId") or concept.get("id")
    term = concept.get("term", "Unknown")
    print(f"  ID: {concept_id}, Term: '{term}'")

    # First check if concept exists in concept table
    from sqlalchemy import text

    result = explorer.session.execute(
        text(f"SELECT id FROM concept WHERE id = {concept_id}")
    )
    exists = result.fetchone()
    print(f"    -> Concept exists in concept table: {exists is not None}")

    # Check if this concept has descriptions
    if concept_id and isinstance(concept_id, int) and exists:
        try:
            descriptions = explorer.get_descriptions_for_concept(concept_id)
            print(f"    -> {len(descriptions)} descriptions")
            if descriptions:
                for desc in descriptions[:2]:  # Show first 2 descriptions
                    print(f"       {desc.get('type')}: '{desc.get('term')}'")
            synonyms = [d for d in descriptions if d.get("type") == "Synonym"]
            print(f"    -> {len(synonyms)} synonyms")
        except Exception as e:
            print(f"    -> Error getting descriptions: {e}")
    else:
        print(
            f"    -> Skipping description check (concept_id: {concept_id}, exists: {exists is not None})"
        )

explorer.disconnect()
