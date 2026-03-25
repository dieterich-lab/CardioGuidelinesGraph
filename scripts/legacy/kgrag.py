import argparse
import os
from operator import itemgetter

from langchain_community.vectorstores import Neo4jVector
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_ollama import ChatOllama, OllamaEmbeddings
from pydantic import BaseModel, Field

from cardio_graph_core.legacy_graph_pipeline.graph_utils import MyNeo4jGraph
from cardio_graph_core.legacy_graph_pipeline.questions import *
from cardio_graph_core.legacy_graph_pipeline.rerank import rerank
from cardio_graph_core.legacy_graph_pipeline.structured_classes import (
    Entities,
    MedicEntities,
)
from cardio_graph_core.legacy_graph_pipeline.templates import NODES

os.environ["NEO4J_URI"] = f"bolt+s://neo4j-dev1.dieterichlab.org:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"


graph = MyNeo4jGraph()

graph.refresh_schema()

parser = argparse.ArgumentParser()
parser.add_argument(
    "--dev",
    action="store_true",
)
parser.add_argument(
    "--model", choices=["nemo", "mixtral_big", "mixtral_small"], default="v03"
)
args = parser.parse_args()
model_dict = {
    "nemo": "mistral-nemo",
    "mixtral_big": "mixtral:8x22b",
    "mixtral_small": "mixtral:8x7b",
    "v03": "mistral:v0.3",
}
model = model_dict[args.model]

g4 = "10.250.135.153"
g2 = "10.250.135.143"
g5 = "10.250.135.156"
port34 = "11434"
port35 = "11435"
port36 = "11436"
PORT = port35
llm = ChatOllama(
    model=model,
    base_url=f"http://{g4}:{PORT}",
    temperature=0.0,
    keep_alive="24h",
)

task = "guidelines"

embed_model = "avr/sfr-embedding-mistral"
embeddings = OllamaEmbeddings(
    model=embed_model,
    base_url=f"http://{g4}:{PORT}",
)

node_vector_index = None
# node_vector_index = Neo4jVector.from_existing_graph(
#     embeddings,
#     index_name="node_vector_index",
#     search_type="hybrid",
#     # node_label="DOCUMENT",
#     node_label="NODE",
#     text_node_properties=["value"],
#     # text_node_properties=["page_content"],
#     embedding_node_property="embedding",
# )

# graph.query(
#     """
# CREATE VECTOR INDEX relationship_vector_index
# IF NOT EXISTS
# FOR ()-[r:CONNECTED]-() ON (r.embedding)
# OPTIONS {indexConfig: {
#  `vector.dimensions`: 1536,
#  `vector.similarity_function`: 'cosine'
# }}
# """
# )

# relationship_vector_index = Neo4jVector.from_existing_relationship_index(
#     embeddings,
#     index_name="relation_vector_index",
#     search_type="hybrid",
#     text_node_property="value",
# )


# entities = MedicEntities
entities = Entities
parser = JsonOutputParser(pydantic_object=entities)
instructions = parser.get_format_instructions()
entity_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Extrahiere aus der folgenden Frage alle Nomen und Konzepte.",
        ),
        (
            "human",
            """Hier ist die Frage:

            {question}""",
        ),
    ]
)
entity_prompt = entity_prompt.partial(instructions=instructions)

entity_chain = entity_prompt | llm.with_structured_output(entities)

# entitiy_answer = entity_chain.invoke(
#     {"question": "Was ist chronische Herzinsuffizienz"}
# )
# print(entitiy_answer.names)


def backtick(x):
    return f"`{x}`"


# entities = "|".join(map(backtick, NODES))
nodes = "|".join(map(backtick, ["NODE"]))
graph.query(f"DROP INDEX entity IF EXISTS")
graph.query(f"CREATE FULLTEXT INDEX entity FOR (e:{nodes}) ON EACH [e.value]")
graph.query(f"DROP INDEX relations IF EXISTS")
graph.query(
    f"CREATE FULLTEXT INDEX relations FOR ()-[r:CONNECTED]-() ON EACH [r.value]"
)


def generate_full_text_query(input: str) -> str:
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input).split() if el]
    for word in words[:-1]:
        full_text_query += f" {word} AND"
        # full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}"
    # full_text_query += f" {words[-1]}~2"
    return full_text_query.strip()


# Fulltext index query
def structured_retriever(question: str) -> str:
    entities = entity_chain.invoke({"question": question})
    print(entities)
    retrieval_list = list()
    for entity in entities.names:
        full_text_query = generate_full_text_query(entity)
        node_query = """
            CALL db.index.fulltext.queryNodes('entity', $query, {limit:50})
            YIELD node,score 
            CALL { WITH node
            MATCH (node)-[r:!MENTIONS]->(m)
            RETURN node.value + ' - ' + r.value + ' -> ' + m.value as output
            UNION
            WITH node
            MATCH (node)<-[r:!MENTIONS]-(m)
            RETURN m.value + ' - ' + r.value + ' -> ' + node.value as output}
            RETURN output
        """
        node_response = graph.query(
            node_query,
            {"query": full_text_query},
        )
        retrieval_list += [el["output"] for el in node_response if el["output"]]
        relation_query = """
            CALL db.index.fulltext.queryRelationships('relations', $query, {limit:50})
            YIELD relationship as relation,score 
            WITH relation
            MATCH (n)-[relation]->(m)
            RETURN n.value + ' - ' + relation.value + ' -> ' + m.value as output
        """
        relation_response = graph.query(
            relation_query,
            {"query": full_text_query},
        )
        retrieval_list += [el["output"] for el in relation_response if el["output"]]
    ranked_list = rerank(
        embeddings, retrieval_list, question["question"], entities.names
    )
    result = "\n".join(ranked_list[:5])
    print(result)
    return result


# structured_retriever("Ist eine Hyperkaliämie eine Kontraindikation für ACE-Hemmer?")


def unstructured_retriever(question: str):
    unstructured_data = [
        el.page_content for el in node_vector_index.similarity_search(question)
    ]
    return unstructured_data[0:1]


def hybrid_retriever(query: str):
    question = query["question"]
    # print(f"Search query: {question}")
    structured_data = structured_retriever(question)
    unstructured_data = unstructured_retriever(question)
    final_data = f"""Structured data:
    {structured_data}
    Unstructured data:
    {"#Document ". join(unstructured_data)}
    """
    # print(
    #     f"Unstructured data: {'#Document '. join(unstructured_data)[:100], len(unstructured_data)}"
    # )
    # print(f"Final data: {final_data}")
    return final_data


answer_template = """
Im folgenden bekommst Du medizinische Informationen in Form von Tripeln, die von einer klinischen Richtlinie über 
chronische Herzinsuffizienz stammen. 
Beantworte die darunterstehende Frage anhand dieser Tripel.

Tripel: {context}

Frage: {question}
"""

summarize_template = """
Im folgenden bekommst Du medizinische Informationen in Form von Tripeln, die von einer klinischen Richtlinie über 
chronische Herzinsuffizienz stammen. 
Fasse die Tripel zu einem verständlichen Text zusammen.

Tripel: {context}
"""

empty_template = """
Bitte beantworte die folgende medizinische Frage über chronische Herzinsuffizienz.

Frage: {question}
"""

answer_prompt = ChatPromptTemplate.from_template(answer_template)
summarize_prompt = ChatPromptTemplate.from_template(summarize_template)
empty_prompt = ChatPromptTemplate.from_template(empty_template)

answer_chain = (
    RunnableParallel(
        {
            "context": structured_retriever,
            "question": RunnablePassthrough(),
            "language": itemgetter("language"),
        }
    )
    | answer_prompt
    | llm
    | StrOutputParser()
)


summarize_chain = (
    RunnableParallel(
        {
            "context": structured_retriever,
            "question": RunnablePassthrough(),
            "language": itemgetter("language"),
        }
    )
    | summarize_prompt
    | llm
    | StrOutputParser()
)

empty_chain = (
    RunnableParallel(
        {
            "question": RunnablePassthrough(),
            "language": itemgetter("language"),
        }
    )
    | empty_prompt
    | llm
    | StrOutputParser()
)


for i, (q, a) in enumerate(zip(questions1, answers1)):
    if i <= 1:
        continue
    print(i, q, a)
    answer_msg = answer_chain.invoke({"question": q, "language": "german"})
    print(f"1) {answer_msg}")
    # summarize_msg = summarize_chain.invoke({"question": q, "language": "german"})
    # print(f"2) {summarize_msg}")
    empty_msg = empty_chain.invoke({"question": q, "language": "german"})
    print(f"3) {empty_msg}")
    print("-" * 100)
    pass

pass
