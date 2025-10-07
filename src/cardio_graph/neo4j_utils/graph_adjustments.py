from neo4j import GraphDatabase

URI = "bolt://neo4j-dev1.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")


def change_rdf_statement_labels(URI=URI, AUTH=AUTH):
    """
    Change all nodes with 'value' property containing 'rdf_statement'
    Removes label 'Node' and adds label 'STATEMENT'.
    Returns None.

    """
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


def rdf_statement_cleanup(URI=URI, AUTH=AUTH):
    """
    Cleans up RDF statement nodes by removing unnecessary values.
    Returns None.
    """
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
