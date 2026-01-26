#!/usr/bin/env python3
"""
Debug script to investigate why get_descriptions_for_concept returns empty for HFrEF concept ID 4542150014
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from cardio_graph.snomedct_utils.snomed_query import SnomedExplorer


def debug_descriptions():
    explorer = SnomedExplorer()
    explorer.connect()

    hfref_concept_id = 4542150014

    print(f"Debugging get_descriptions_for_concept for concept ID: {hfref_concept_id}")

    # First, let's list all available tables
    from sqlalchemy import text

    result = explorer.session.execute(
        text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
        )
    )
    tables = [row[0] for row in result.fetchall()]
    print(f"Available tables: {tables}")

    # Check if concept exists - try different table names
    concept_found = False
    for table_name in ["concept", "snap_concept", "full_concept"]:
        if table_name in tables:
            try:
                query = text(
                    f"SELECT id, active FROM {table_name} WHERE id = :concept_id LIMIT 1"
                )
                result = explorer.session.execute(
                    query, {"concept_id": hfref_concept_id}
                )
                row = result.fetchone()
                if row:
                    print(
                        f"Concept found in {table_name}: id={row[0]}, active={row[1]}"
                    )
                    concept_found = True
                    break
            except Exception as e:
                print(f"Error querying {table_name}: {e}")

    if not concept_found:
        print("Concept not found in any concept table")

    # Check descriptions - try different table names
    for table_name in ["description", "snap_description", "full_description"]:
        if table_name in tables:
            try:
                query = text(
                    f"SELECT id, term, active, typeid, conceptid FROM {table_name} WHERE conceptid = :concept_id LIMIT 5"
                )
                result = explorer.session.execute(
                    query, {"concept_id": hfref_concept_id}
                )
                rows = result.fetchall()
                print(f"Descriptions in {table_name}: {len(rows)} found")
                for row in rows:
                    print(
                        f"  id={row[0]}, term='{row[1]}', active={row[2]}, typeid={row[3]}, conceptid={row[4]}"
                    )
            except Exception as e:
                print(f"Error querying {table_name}: {e}")

    # Also check what the search method finds
    print("\n=== CHECKING SEARCH RESULTS ===")
    search_results = explorer.search_concepts_by_term("HFrEF", limit=10)
    print(f"Search for 'HFrEF' returned {len(search_results)} results:")
    for result in search_results:
        print(
            f"  conceptid={result['conceptid']}, term='{result['term']}', active={result['active']}"
        )

    # Check if 4542150014 appears in search results
    found_in_search = any(r["conceptid"] == hfref_concept_id for r in search_results)
    print(f"Concept {hfref_concept_id} found in search results: {found_in_search}")

    # Also search for the exact term from SLURM output
    print("\n=== SEARCHING FOR EXACT TERM FROM SLURM ===")
    exact_search_results = explorer.search_concepts_by_term(
        "HFrEF - heart failure with reduced ejection fraction", limit=5
    )
    print(f"Search for exact term returned {len(exact_search_results)} results:")
    for result in exact_search_results:
        print(
            f"  conceptid={result['conceptid']}, term='{result['term']}', active={result['active']}"
        )

    # Also search for the full term
    print("\n=== SEARCHING FOR FULL TERM ===")
    full_search_results = explorer.search_concepts_by_term(
        "Heart failure with reduced ejection fraction", limit=15
    )
    print(
        f"Search for 'Heart failure with reduced ejection fraction' returned {len(full_search_results)} results:"
    )
    for result in full_search_results:
        print(
            f"  conceptid={result['conceptid']}, term='{result['term']}', active={result['active']}"
        )
        if result["conceptid"] == hfref_concept_id:
            print(f"    *** FOUND TARGET CONCEPT {hfref_concept_id} ***")

    # Now try the method on the concept that was actually found
    if search_results:
        actual_concept_id = search_results[0]["conceptid"]
        print(
            f"\n=== TESTING get_descriptions_for_concept on found concept {actual_concept_id} ==="
        )
        result = explorer.get_descriptions_for_concept(actual_concept_id)
        print(f"get_descriptions_for_concept returned: {result}")

    # Now try the method
    result = explorer.get_descriptions_for_concept(hfref_concept_id)
    print(f"get_descriptions_for_concept for {hfref_concept_id} returned: {result}")

    explorer.disconnect()


if __name__ == "__main__":
    debug_descriptions()
