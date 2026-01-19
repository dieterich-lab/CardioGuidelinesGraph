from neo4j import GraphDatabase

URI = "bolt://neo4j-dev1.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")


def change_rdf_statement_labels(URI=URI, AUTH=AUTH, session=None):
    """
    Change all nodes with 'value' property containing 'rdf_statement'
    Removes label 'Node' and adds label 'STATEMENT'.
    Returns None.

    """
    if session is not None:
        session.run(
            """
        MATCH (n)
        WHERE n.value CONTAINS "rdf_statement"
        REMOVE n:Node
        SET n:STATEMENT
        """
        )
        print("Labels updated successfully.")
        return
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j database.")
        with driver.session() as session:
            session.run(
                """
            MATCH (n)
            WHERE n.value CONTAINS "rdf_statement"
            REMOVE n:Node
            SET n:STATEMENT
            """
            )
            print("Labels updated successfully.")
    return


def rdf_statement_cleanup(URI=URI, AUTH=AUTH, session=None):
    """
    Cleans up RDF statement nodes by removing unnecessary values.
    Returns None.
    """
    if session is not None:
        session.run(
            """
        MATCH (n:STATEMENT)
        SET n.value = "rdf_statement"
        """
        )
        print("RDF statement nodes cleaned up successfully.")
        return
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j database.")
        with driver.session() as session:
            session.run(
                """
            MATCH (n:STATEMENT)
            SET n.value = "rdf_statement"
            """
            )
            print("RDF statement nodes cleaned up successfully.")
    return


def create_lowercase_value_property(URI=URI, AUTH=AUTH, session=None):
    """
    Creates a new property 'value_lower' with the lowercase version of 'value'.
    Returns None.
    """
    if session is not None:
        session.run(
            """
        MATCH (n)
        WHERE n.value IS NOT NULL
        SET n.value_lower = toLower(n.value)
        """
        )
        print("Lowercase 'value_lower' property created successfully.")
        return
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j database.")
        with driver.session() as session:
            session.run(
                """
            MATCH (n)
            WHERE n.value IS NOT NULL
            SET n.value_lower = toLower(n.value)
            """
            )
            print("Lowercase 'value_lower' property created successfully.")
    return


def check_duplicates(URI=URI, AUTH=AUTH, session=None):
    """
    Checks for duplicate (not Statement, not AND) nodes based on the 'value_lower' property set in create_lowercase_value_property().
    """
    if session is not None:
        result = session.run(
            """
        MATCH (n:Node)
        WHERE n.value_lower IS NOT NULL
        WITH n.value_lower AS v, collect(n) AS nodes
        WHERE size(nodes) > 1
        RETURN v AS value_lower, size(nodes) AS dup_count, [x IN nodes | elementID(x) ] AS node_ids
        ORDER BY dup_count DESC, value_lower
        """
        )
        duplicates = [record.data() for record in result]
        print("Duplicate check completed.")
        return duplicates
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j database.")
        with driver.session() as session:
            result = session.run(
                """
            MATCH (n:Node)
            WHERE n.value_lower IS NOT NULL
            WITH n.value_lower AS v, collect(n) AS nodes
            WHERE size(nodes) > 1
            RETURN v AS value_lower, size(nodes) AS dup_count, [x IN nodes | elementID(x) ] AS node_ids
            ORDER BY dup_count DESC, value_lower
            """
            )
            duplicates = [record.data() for record in result]
            print("Duplicate check completed.")
    return duplicates


def print_duplicates(duplicates):
    """Prints the duplicates in a readable format."""
    if not duplicates:
        print("No duplicates found.")
    else:
        print("\nDuplicates found:\n")
        for d in duplicates:
            print(f"value_lower: {d['value_lower']}")
            print(f"  count: {d['dup_count']}")
            print(f"  node_ids: {d['node_ids']}")
            print("-" * 50)


def normalize_nodes(URI=URI, AUTH=AUTH, session=None):
    """
    Normalize nodes by changing labels, cleaning up RDF statements, and creating lowercase properties.
    """
    if session is not None:
        summary = session.run(
            """
            CALL apoc.periodic.iterate(
            "MATCH (n:Node) WHERE n.value_lower IS NOT NULL
            WITH n.value_lower AS v, collect(n) AS nodes
            WHERE size(nodes) > 1
            RETURN nodes",
            "CALL apoc.refactor.mergeNodes(nodes, {mergeRels:true, properties:'combine', preserveExisting:true})
            YIELD node RETURN 1",
            { batchSize: 1, parallel:false}
            )
            YIELD batches, total, committedOperations, failedOperations, failedBatches, retries
            RETURN batches, total, committedOperations, failedOperations, failedBatches, retries;
            """
        ).data()

        print("Merge completed:")
        for row in summary:
            print(row)
        return
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j database.")
        with driver.session() as session:
            summary = session.run(
                """
            CALL apoc.periodic.iterate(
            "MATCH (n:Node) WHERE n.value_lower IS NOT NULL
            WITH n.value_lower AS v, collect(n) AS nodes
            WHERE size(nodes) > 1
            RETURN nodes",
            "CALL apoc.refactor.mergeNodes(nodes, {mergeRels:true, properties:'combine', preserveExisting:true})
            YIELD node RETURN 1",
            { batchSize: 1, parallel:false}
            )
            YIELD batches, total, committedOperations, failedOperations, failedBatches, retries
            RETURN batches, total, committedOperations, failedOperations, failedBatches, retries;
            """
            ).data()

            print("Merge completed:")
            for row in summary:
                print(row)
    return


def cleanup_values(URI=URI, AUTH=AUTH, session=None):
    """
    removes the LIST OF STRINGS from normalization and keeps the first entry as a value for the node
    """
    if session is not None:
        result = session.run(
            """
        MATCH (n:Node)
        WHERE apoc.meta.cypher.type(n.value) = 'LIST OF STRING' AND size(n.value) > 0
        SET n.value = n.value[0]
        RETURN count(n) AS collapsed;
        """
        )
        collapsed_count = result.single()["collapsed"]
        print(f"{collapsed_count} values cleaned up successfully.")
        return
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j database.")
        with driver.session() as session:
            result = session.run(
                """
            MATCH (n:Node)
            WHERE apoc.meta.cypher.type(n.value) = 'LIST OF STRING' AND size(n.value) > 0
            SET n.value = n.value[0]
            RETURN count(n) AS collapsed;
            """
            )
            collapsed_count = result.single()["collapsed"]
            print(f"{collapsed_count} values cleaned up successfully.")
    return


def remove_redundant_properties(URI=URI, AUTH=AUTH, session=None):
    """
    Removes redundant properties from nodes.
    """
    if session is not None:
        session.run(
            """
        MATCH (n)
        REMOVE n.value_lower
        REMOVE n.id
        """
        )
        print("value_lower and id properties removed successfully.")
        return
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j database.")
        with driver.session() as session:
            session.run(
                """
            MATCH (n)
            REMOVE n.value_lower
            REMOVE n.id
            """
            )
            print("value_lower and id properties removed successfully.")
    return


if __name__ == "__main__":
    cleanup_values()
