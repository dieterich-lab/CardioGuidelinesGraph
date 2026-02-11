"""
This script demonstrates the "In-Graph Versioning" approach for managing different
states or versions of the graph data within a single Neo4j database.

---
What is In-Graph Versioning?
---
Instead of creating full database backups, this method involves tagging nodes and
relationships with a 'state' property. This allows you to "save" a version of your
graph, perform experiments on a new version, and easily switch between them or
revert changes without deleting and re-uploading the entire database.

It's ideal for:
- Experimenting with new data processing or analysis techniques.
- Comparing different versions of the graph.
- Quickly reverting a set of changes.

---
How to use this approach in your project:
---
1.  **Tag your data on upload:**
    When you upload your primary or "golden" dataset, add a state property to all
    nodes and relationships. For example: `SET n.state = 'base_v1'`

2.  **Work on a new state:**
    When you want to make modifications, create new or modified data with a new
    state name. For example: `CREATE (d:Drug {name: 'NewDrug', state: 'experiment_A'})`

3.  **Query a specific state:**
    In your analysis scripts, always include a WHERE clause to filter by the state
    you want to work with. For example: `MATCH (d:Drug) WHERE d.state = 'base_v1'`

4.  **Revert a state:**
    To undo an experiment, simply delete all data associated with that state.
    For example: `MATCH (n) WHERE n.state = 'experiment_A' DETACH DELETE n`

This script provides functions to test these operations.
"""

import os

from neo4j import GraphDatabase, exceptions

# --- Configuration ---
# Update these with your database credentials
URI = "bolt://neo4j-dev2.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")


def run_query(driver, query, **params):
    """A helper function to execute a Cypher query."""
    try:
        records, _, _ = driver.execute_query(query, **params)
        return records
    except Exception as e:
        print(f"   [ERROR] Query failed: {e}")
        return None


def check_connection(driver):
    """Tests the basic connectivity to the database."""
    print("1. Checking database connection...")
    try:
        driver.verify_connectivity()
        print("   Connection successful!")
        return True
    except exceptions.AuthError as e:
        print(f"   [FATAL] Authentication failed: {e}. Check your credentials.")
        return False
    except exceptions.ServiceUnavailable as e:
        print(
            f"   [FATAL] Connection failed: {e}. Check if the database is running and the URI is correct."
        )
        return False


def create_data_with_state(driver, state_name):
    """Demonstrates creating a node with a specific state tag."""
    print(f"\n2. Creating a sample node with state: '{state_name}'")
    query = """
    CREATE (n:StateTestNode {name: 'StateVersioningTest', state: $state_name, timestamp: timestamp()})
    RETURN elementId(n) as node_id
    """
    records = run_query(driver, query, state_name=state_name)
    if records:
        print(f"   Successfully created a test node with ID: {records[0]['node_id']}.")
        return True
    else:
        print("   Failed to create a test node.")
        return False


def read_data_by_state(driver, state_name):
    """Demonstrates querying for nodes that belong to a specific state."""
    print(f"\n3. Reading nodes specifically from state: '{state_name}'")
    query = "MATCH (n:StateTestNode {state: $state_name}) RETURN count(n) as count"
    records = run_query(driver, query, state_name=state_name)
    if records:
        count = records[0]["count"]
        print(f"   Found {count} node(s) with state '{state_name}'.")
        return count > 0
    else:
        print("   Failed to query for test nodes.")
        return False


def cleanup_state_data(driver, state_name):
    """Demonstrates reverting/deleting all data associated with a specific state."""
    print(f"\n4. Cleaning up (deleting) all data for state: '{state_name}'")
    query = "MATCH (n:StateTestNode {state: $state_name}) DETACH DELETE n"
    run_query(driver, query, state_name=state_name)
    print("   Cleanup complete.")


def main():
    """Main function to demonstrate and test the in-graph versioning workflow."""
    print("--- In-Graph State Versioning Demo ---")
    driver = None
    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)

        if not check_connection(driver):
            return

        # Define a unique name for our test state
        test_state = "my_experiment_v1"

        # --- Workflow Demonstration ---
        # Step 1: Create new data and assign it to our experimental state.
        if create_data_with_state(driver, test_state):
            # Step 2: Query the database, ensuring we only see data from our state.
            read_data_by_state(driver, test_state)
            # Step 3: "Revert" the changes by deleting all data associated with the state.
            cleanup_state_data(driver, test_state)

    finally:
        if driver:
            driver.close()
        print("\n--- Demo Finished ---")


if __name__ == "__main__":
    main()
