import os, time, sys
from neo4j import GraphDatabase
from cardio_graph.neo4j_utils.feedneo4jdb import execute_cypher_file
from cardio_graph.neo4j_utils.graph_adjustments import (
    change_rdf_statement_labels,
    rdf_statement_cleanup,
    create_lowercase_value_property,
    normalize_nodes,
    cleanup_values,
    remove_redundant_properties,
)

URI = "bolt://neo4j-dev1.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")


def execute_cypher_folder_dev1(
    cypher_filepath="/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/md_to_cypher/",
    session=None,
    URI=URI,
    AUTH=AUTH,
):
    """
    Excutes all cypher files in the specified folder against the dev1 database.

    cypher_filepath: str
        Path to the folder containing cypher files.
    """
    start = time.time()
    print("Starting: excecute_cypher_folder_dev1")
    if session is not None:
        for file in sorted(os.listdir(cypher_filepath)):
            full_path = os.path.join(cypher_filepath, file)
            print(f"Executing Cypher file: {full_path}")
            execute_cypher_file(session, full_path)
            print(f"Completed Cypher file: {full_path}")
        print("Time:", time.time() - start)
        print("Total Nodes:", count_nodes(session))
        return
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j database.")
        with driver.session() as session:
            for file in sorted(os.listdir(cypher_filepath)):
                full_path = os.path.join(cypher_filepath, file)
                print(f"Executing Cypher file: {full_path}")
                execute_cypher_file(session, full_path)
                print(f"Completed Cypher file: {full_path}")
            print("Time:", time.time() - start)
            print("Total Nodes:", count_nodes(session))
    return


def count_nodes(session, database=None) -> int:
    """
    Counts the number of nodes in the running session from.

    Returns the count of nodes as an integer.


    session: neo4j.Session
        An active Neo4j session.
        from neo4j import GraphDatabase
        GraphDatabase.driver(URI, auth=AUTH)
        session = driver.session()
    """
    result = session.run("MATCH (n) RETURN count(n) AS c", database=database)
    rec = result.single()
    return 0 if rec is None else int(rec["c"])


def require_manual_delete(expected="delete"):
    """Require the user to type 'delete' in an interactive TTY."""
    if not sys.stdin.isatty():
        raise RuntimeError(
            "Interactive confirmation required, but no TTY detected. "
            "Run from a terminal or disable manual confirmation explicitly."
        )
    prompt = (
        "WARNING: This will permanently DELETE ALL nodes and relationships in the target DB.\n"
        "Type 'delete' (without quotes) to proceed: "
    )
    try:
        resp = input(prompt).strip().lower()
    except EOFError:
        raise RuntimeError("Confirmation aborted: no input available.")
    if resp != expected:
        raise RuntimeError("Confirmation aborted: typed value did not match 'delete'.")
    return


def delete_all_nodes_dev1(
    max_nodes=50000, dry_run=True, URI=URI, AUTH=AUTH, session=None
):
    """
    Deletes all current Nodes and Relationships in the dev1 database
    Requires a manual input to confirm deletion.

    max_nodes: int
        Maximum number of nodes allowed before deletion is aborted.
        This is a safety measure to prevent accidental deletion of large databases.
    dry_run: bool
        If True, the deletion step is simulated but not executed.
        This allows you to see what would happen without making any changes.

    session: neo4j.Session, optional, use for multiple operations in the same session

    """
    require_manual_delete(expected="delete")
    if session is not None:
        node_count = count_nodes(session)
        if node_count > max_nodes:
            print(
                f"Node count ({node_count}) exceeds max_nodes ({max_nodes}). Aborting deletion."
            )
            return
        print(f"Node count before deletion: {node_count}")

        if dry_run:
            print("Dry run enabled. No nodes will be deleted.")
            print(f"Would delete all nodes and relationships from dev1.")
            return

        session.run("MATCH (n) DETACH DELETE n")
        print("All nodes and relationships deleted from dev1, veryfying...")
        node_count_after = count_nodes(session)
        print(f"Node count after deletion: {node_count_after}")
    else:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("Connected to Neo4j database.")
            with driver.session() as session:

                node_count = count_nodes(session)
                if node_count > max_nodes:
                    print(
                        f"Node count ({node_count}) exceeds max_nodes ({max_nodes}). Aborting deletion."
                    )
                    return
                print(f"Node count before deletion: {node_count}")

                if dry_run:
                    print("Dry run enabled. No nodes will be deleted.")
                    print(f"Would delete all nodes and relationships from dev1.")
                    return

                session.run("MATCH (n) DETACH DELETE n")
                print("All nodes and relationships deleted from dev1, veryfying...")
                node_count_after = count_nodes(session)
                print(f"Node count after deletion: {node_count_after}")
    return


def reset_graph_from_cypher_folder(max_nodes=50000, dry_run=True, URI=URI, AUTH=AUTH):
    """
    Deletes all current Nodes and Relationships in the dev1 database
    and repopulates it from cypher files in the specified folder.

    max_nodes: int
        Maximum number of nodes allowed before deletion is aborted.
        This is a safety measure to prevent accidental deletion of large databases.
    dry_run: bool
        If True, the deletion step is simulated but not executed.
        This allows you to see what would happen without making any changes.
    """
    beginning = time.time()
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j database.")
        with driver.session() as session:
            delete_all_nodes_dev1(max_nodes, dry_run, session=session)
            execute_cypher_folder_dev1(session=session)
            print("Graph reset from cypher folder completed.")
            print("Parsing Time:", time.time() - beginning)
            print("postprocessing...")
            change_rdf_statement_labels(URI, AUTH, session=session)
            rdf_statement_cleanup(URI, AUTH, session=session)
            print("rdf_statments processed")
            create_lowercase_value_property(URI, AUTH, session=session)
            print("lowercase value property created")
            normalize_nodes(URI, AUTH, session=session)
            print("nodes normalized")
            remove_redundant_properties(URI, AUTH, session=session)
            print("redundant properties removed")
            cleanup_values(URI, AUTH, session=session)
            print("values cleaned up")
            print("Total Time:", time.time() - beginning)

    return


if __name__ == "__main__":
    reset_graph_from_cypher_folder(max_nodes=50000, dry_run=False)
