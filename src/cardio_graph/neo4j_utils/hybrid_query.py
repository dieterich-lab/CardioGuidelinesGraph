from neo4j import GraphDatabase
import os


# Database configuration
URI = "bolt://neo4j-dev2.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")
DIR = "/prj/doctoral_letters/guide/outputs2/test_query"


def HybridQuery(string):
    # Use a set of node IDs instead of node objects
    visited_nodes = set()
    zero_nodes = set()
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("Connected to Neo4j database.")
            #cypher onehop query
            with driver.session() as session:
                print("test")

    except Exception as e:
        print(f"Database connection error: {str(e)}")

if __name__ == "__main__":
    print(os.environ["OPENAI_API_KEY"])