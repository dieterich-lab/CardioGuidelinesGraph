from hashlib import md5
from typing import List

from json_repair import repair_json
from langchain_community.graphs import Neo4jGraph
from langchain_community.graphs.graph_document import GraphDocument
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import (
    BaseGenerationOutputParser,
    JsonOutputToolsParser,
)
from langchain_core.outputs import ChatGeneration, Generation

from .utils import Timeout

BASE_ENTITY_LABEL = "__Entity__"
EXCLUDED_LABELS = ["_Bloom_Perspective_", "_Bloom_Scene_"]
EXCLUDED_RELS = ["_Bloom_HAS_SCENE_"]
EXHAUSTIVE_SEARCH_LIMIT = 10000
LIST_LIMIT = 128
# Threshold for returning all available prop values in graph schema
DISTINCT_VALUE_LIMIT = 10

include_docs_query = (
    "MERGE (d:DOCUMENT {id:$document.metadata.id}) "
    "SET d.page_content = $document.page_content "
    "SET d += $document.metadata "
    "WITH d "
)


def _remove_backticks(text: str) -> str:
    return text.replace("`", "")


def escape_json(s):
    _s = ""
    for ss in s:
        _s += ss
        if ss in ["{", "}"]:
            _s += ss
    return _s


def _get_node_import_query(baseEntityLabel: bool, include_source: bool) -> str:
    if baseEntityLabel:
        return (
            f"{include_docs_query if include_source else ''}"
            "UNWIND $data AS row "
            f"MERGE (source:`{BASE_ENTITY_LABEL}` {{id: row.id}}) "
            "SET source += row.properties "
            f"{'MERGE (d)-[:MENTIONS]->(source) ' if include_source else ''}"
            "WITH source, row "
            "CALL apoc.create.addLabels(source, [row.type]) YIELD node "
            "RETURN distinct 'done' AS result"
        )
    else:
        return (
            f"{include_docs_query if include_source else ''}"
            "UNWIND $data AS row "
            "CALL apoc.merge.node([toUpper(row.type)], {value: row.id}, "
            "row.properties, {}) YIELD node "
            f"{'MERGE (d)-[:MENTIONS]->(node) ' if include_source else ''}"
            "RETURN distinct 'done' AS result"
        )


def _get_rel_import_query(baseEntityLabel: bool) -> str:
    if baseEntityLabel:
        return (
            "UNWIND $data AS row "
            f"MERGE (source:`{BASE_ENTITY_LABEL}` {{id: row.source}}) "
            f"MERGE (target:`{BASE_ENTITY_LABEL}` {{id: row.target}}) "
            "WITH source, target, row "
            "CALL apoc.merge.relationship(source, row.type, "
            "{}, row.properties, target) YIELD rel "
            "RETURN distinct 'done'"
        )
    else:
        return (
            # "MATCH (d:Document {id:$document.metadata.id}) "
            # "WITH d "
            "UNWIND $data AS row "
            "CALL apoc.merge.node([toUpper(row.source_label)], {value: row.source},"
            "{}, {}) YIELD node as source "
            "CALL apoc.merge.node([toUpper(row.target_label)], {value: row.target},"
            "{}, {}) YIELD node as target "
            "CALL apoc.merge.relationship(source, 'CONNECTED', {}, row.properties, target) YIELD rel "
            "SET rel.chunks = coalesce(rel.chunks, []) + row.chunk "  # here, we collect all the text chunks where a relation was found
            "SET rel.value = row.type "
            "RETURN distinct 'done' "
        )


class MyNeo4jGraph(Neo4jGraph):
    def add_graph_documents(
        self,
        graph_documents: List[GraphDocument],
        include_source: bool = False,
        baseEntityLabel: bool = False,
    ) -> None:
        """
        This method constructs nodes and relationships in the graph based on the
        provided GraphDocument objects.

        Parameters:
        - graph_documents (List[GraphDocument]): A list of GraphDocument objects
        that contain the nodes and relationships to be added to the graph. Each
        GraphDocument should encapsulate the structure of part of the graph,
        including nodes, relationships, and the source document information.
        - include_source (bool, optional): If True, stores the source document
        and links it to nodes in the graph using the MENTIONS relationship.
        This is useful for tracing back the origin of data. Merges source
        documents based on the `id` property from the source document metadata
        if available; otherwise it calculates the MD5 hash of `page_content`
        for merging process. Defaults to False.
        - baseEntityLabel (bool, optional): If True, each newly created node
        gets a secondary __Entity__ label, which is indexed and improves import
        speed and performance. Defaults to False.
        """
        if baseEntityLabel:  # Check if constraint already exists
            constraint_exists = any(
                [
                    el["labelsOrTypes"] == [BASE_ENTITY_LABEL]
                    and el["properties"] == ["id"]
                    for el in self.structured_schema.get("metadata", {}).get(
                        "constraint", []
                    )
                ]
            )

            if not constraint_exists:
                # Create constraint
                self.query(
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (b:{BASE_ENTITY_LABEL}) "
                    "REQUIRE b.id IS UNIQUE;"
                )
                self.refresh_schema()  # Refresh constraint information

        node_import_query = _get_node_import_query(baseEntityLabel, include_source)
        rel_import_query = _get_rel_import_query(baseEntityLabel)
        for document in graph_documents:
            if not document.source.metadata.get("id"):
                document.source.metadata["id"] = md5(
                    document.source.page_content.encode("utf-8")
                ).hexdigest()

            # Remove backticks from node types
            for node in document.nodes:
                node.type = _remove_backticks(node.type)
            # Import nodes
            self.query(
                node_import_query,
                {
                    "data": [el.__dict__ for el in document.nodes],
                    "document": document.source.__dict__,
                },
            )
            # Import relationships
            self.query(
                rel_import_query,
                {
                    "document": document.source.__dict__,
                    "data": [
                        {
                            "source": el.source.id,
                            "source_label": _remove_backticks(el.source.type),
                            "target": el.target.id,
                            "target_label": _remove_backticks(el.target.type),
                            "type": _remove_backticks(el.type),
                            # "type": _remove_backticks(
                            #     el.type.replace(" ", "_").upper()
                            # ),
                            "properties": el.properties,
                            "chunk": document.source.page_content,
                        }
                        for el in document.relationships
                    ],
                },
            )


def parse_msg(msg, keyword):
    if msg is None:
        return None
    parsed = msg["parsed"]
    if parsed is None:
        _parsed = repair_json(msg["raw"].content, return_objects=True)
        if isinstance(_parsed, dict) and keyword in _parsed:
            return _parsed[keyword]
        for p in _parsed:
            if not isinstance(p, dict):
                continue
            if keyword in p:
                parsed = [t for t in p[keyword] if len(t) == 3]
                break
            for _, v in p.items():
                if keyword in v:
                    parsed = [t for t in v[keyword] if len(t) == 3]
                    break
    else:
        parsed = msg["parsed"][keyword]

    return parsed


class CustomParser(JsonOutputToolsParser):
    # class CustomParser(BaseGenerationOutputParser[str]):

    def parse_result(self, result: List[Generation], *, partial: bool = False) -> str:
        generation = None
        # generation = result[0]
        if generation is None:
            return None
        parsed = generation["parsed"]
        if parsed is None:
            _parsed = repair_json(generation["raw"].content, return_objects=True)
            for p in _parsed:
                if not isinstance(p, dict):
                    continue
                if "triples" in p:
                    parsed = [t for t in p["triples"] if len(t) == 3]
                    break
                for _, v in p.items():
                    if "triples" in v:
                        parsed = [t for t in v["triples"] if len(t) == 3]
                        break
        else:
            parsed = generation["parsed"]["triples"]
        return parsed


def attempt(x, s, func, args):
    c = 0
    res = None
    while c < x:
        try:
            with Timeout(s):
                res = func(args)
                break
        except Timeout.Timeout:
            print("Timeout")
            c += 1
    return res
