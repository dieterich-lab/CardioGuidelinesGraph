#!/usr/bin/env python3
"""
Test script to check what get_descriptions_for_concept returns
"""

from sqlalchemy import text

from cardio_graph.snomedct_utils.snomed_query import SnomedExplorer

explorer = SnomedExplorer()
explorer.connect()

# First, check what tables exist
print("Checking available tables...")
result = explorer.session.execute(
    text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
    )
)
tables = [row[0] for row in result.fetchall()]
print(f"Available tables: {tables}")

# Check if description table exists
if "description" in tables:
    print("Description table exists")
    # Try a direct query
    try:
        # Test with a concept that we know has descriptions
        test_concept_id = 137675006  # From our earlier test

        # Check without active filter
        result = explorer.session.execute(
            text(
                f"SELECT COUNT(*) FROM description WHERE conceptid = {test_concept_id}"
            )
        )
        total_count = result.fetchone()[0]
        print(f"Total descriptions for concept {test_concept_id}: {total_count}")

        # Check with active filter
        result = explorer.session.execute(
            text(
                f"SELECT COUNT(*) FROM description WHERE conceptid = {test_concept_id} AND active = true"
            )
        )
        active_count = result.fetchone()[0]
        print(f"Active descriptions for concept {test_concept_id}: {active_count}")

        # Check what the active values are
        result = explorer.session.execute(
            text(
                f"SELECT active, COUNT(*) FROM description WHERE conceptid = {test_concept_id} GROUP BY active"
            )
        )
        print(f"Active value distribution for concept {test_concept_id}:")
        for row in result.fetchall():
            print(f"  active={row[0]}: {row[1]} descriptions")

        # Show sample descriptions
        result = explorer.session.execute(
            text(
                f"SELECT term, typeid, active FROM description WHERE conceptid = {test_concept_id} LIMIT 5"
            )
        )
        print(f"Sample descriptions for concept {test_concept_id}:")
        for row in result.fetchall():
            print(f"  term='{row[0]}', typeid={row[1]}, active={row[2]}")

    except Exception as e:
        print(f"Error querying description table: {e}")
else:
    print("Description table does NOT exist")

# Test with a known heart failure concept
test_concept_id = (
    137675006  # "No FH: Ischaemic heart disease" - we know this has descriptions
)

print(f"\nTesting get_descriptions_for_concept for concept ID: {test_concept_id}")

descriptions = explorer.get_descriptions_for_concept(test_concept_id)
print(f"Returned {len(descriptions)} descriptions:")
for desc in descriptions:
    print(
        f"  Type: {desc.get('type', 'Unknown')}, Term: '{desc.get('term', 'Unknown')}'"
    )

explorer.disconnect()
