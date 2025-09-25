import json
import os

from neo4j import GraphDatabase

from cardio_graph.baml_client.types import Triples
from cardio_graph.neo4j_utils.feedneo4jdb import execute_cypher_file

URI = "bolt://neo4j-dev1.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")


def pretty_print_triples(
    triples, visited_nodes=None, found_relations=None, zero_nodes=True
):
    for i, t in enumerate(triples.triples, 1):
        print(
            f"{i:2d}. {t.head_node_value} (ID: {t.head_node_id}) --[{t.relation}]--> {t.tail_node_value} (ID: {t.tail_node_id})"
        )
    # if visited_nodes is not None:
    #     print("\nVisited nodes:")
    #     for node in visited_nodes:
    #         print(node[1])
    # if zero_nodes is not None:
    #     print("\nZero nodes:")
    #     for node in zero_nodes:
    #         print(node[1])
    # if found_relations is not None:
    #     print("\nFound relations:")
    #     triples = []
    #     for rel in found_relations:
    #         print(
    #             rel[1][-3:],
    #             rel[2],
    #             rel[0],
    #             rel[3][-3:],
    #             rel[4]
    #                     )


def triples_to_cypher(triples: Triples) -> str:
    cypher_statements = []
    for i, t in enumerate(triples.triples, 1):
        head_node_label = t.head_node_label
        head_node_value = t.head_node_value
        head_node_id = t.head_node_id
        relation = t.relation
        tail_node_label = t.tail_node_label
        tail_node_value = t.tail_node_value
        tail_node_id = t.tail_node_id
        cypher_head = f"MERGE (n{head_node_id}:{head_node_label} {{id: '{head_node_id}', value: '{head_node_value}'}}) "
        cypher_tail = f"MERGE (n{tail_node_id}:{tail_node_label} {{id: '{tail_node_id}', value: '{tail_node_value}'}}) "
        cypher_triple = f"MERGE (n{head_node_id})-[:{relation}]->(n{tail_node_id})"
        if cypher_head not in cypher_statements:
            cypher_statements.append(cypher_head)
        if cypher_tail not in cypher_statements:
            cypher_statements.append(cypher_tail)
        cypher_statements.append(cypher_triple)
    # print("\n".join(cypher_statements))
    return cypher_statements


def execute_baml_cypher_dev1(cypher_filepath):
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j database.")
        with driver.session() as session:
            execute_cypher_file(session, cypher_filepath)
