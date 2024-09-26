import os
from operator import itemgetter
from typing import List

from graph_utils import MyNeo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_ollama import ChatOllama, OllamaEmbeddings
from pydantic import BaseModel, Field
from questions import *
from rerank import rerank
from templates import NODES

os.environ["NEO4J_URI"] = f"bolt+s://neo4j-wft-inf.dieterichlab.org:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"

graph = MyNeo4jGraph()

graph.refresh_schema()
# print(f"Schema:")
# print(graph.schema)


# model = "mistral-nemo"
model = "mixtral:8x7b"
# model = "mistral:v0.3"
port = "11435"
# llm = OllamaFunctions(
#     model=model,
#     base_url=f"http://10.250.135.153:{port}",
#     format="json",
#     temperature=0,
# )
llm = ChatOllama(
    model=model,
    base_url=f"http://10.250.135.153:{port}",
    format="json",
    temperature=0,
)

embed_model = "avr/sfr-embedding-mistral"
embeddings = OllamaEmbeddings(
    model=embed_model,
    base_url=f"http://10.250.135.153:{port}",
)

node_vector_index = Neo4jVector.from_existing_graph(
    embeddings,
    index_name="node_vector_index",
    search_type="hybrid",
    node_label="DOCUMENT",
    text_node_properties=["page_content"],
    embedding_node_property="embedding",
)

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


# Extract entities from text
class MedicEntities(BaseModel):
    names: List[str] = Field(
        ...,
        description="Alle medizinischen, anatomischen, technischen und laborwissenschaftlichen Konzepte, die im Text vorkommen.",
    )


structured_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Extrahiere medizinische, anatomische, laborwissenschaftliche Konzepte aus dem Text.",
            # "Beispiele hierfür sind: HFrEF, ACE-Hemmer, chronische Herzinsuffizienz usw.",
        ),
        (
            "human",
            "Benutze das vorgegebene Format um Informationen aus der folgenden Eingabe zu extrahieren: {question}",
        ),
    ]
)

entity_chain = structured_prompt | llm.with_structured_output(MedicEntities)

# entitiy_answer = entity_chain.invoke(
#     {"question": "Was ist chronische Herzinsuffizienz"}
# )
# print(entitiy_answer.names)


def backtick(x):
    return f"`{x}`"


entities = "|".join(map(backtick, NODES))
graph.query(f"DROP INDEX entity IF EXISTS")
graph.query(f"CREATE FULLTEXT INDEX entity FOR (e:{entities}) ON EACH [e.value]")
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
    """
    Collects the neighborhood of entities mentioned
    in the question
    """
    # result = ""
    # entities = entity_chain.invoke(question)
    entities = entity_chain.invoke({"question": question})
    # print(f"Entities: {entities.names}")
    retrieval_list = list()
    for entity in entities.names:
        full_text_query = generate_full_text_query(entity)
        node_query = """
            CALL db.index.fulltext.queryNodes('entity', $query, {limit:5})
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
            CALL db.index.fulltext.queryRelationships('relations', $query, {limit:5})
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
    ranked_list = rerank(entities.names, retrieval_list, question["question"])
    result = "\n".join(ranked_list[:10])
    # print(result)
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


structured_template = """Im folgenden bekommst Du Tripel, die von einer klinischen Richtlinie über 
chronische Herzinsuffizienz stammen. Beantworte die darunterstehende Frage anhand dieser Tripel.

WICHTIG: 
* Benutze ausschließlich den Inhalt der gegebenen Tripel.
* Wenn der Kontext nicht genügend Information bietet, dann sage unbedingt, 
dass Du keine Aussage treffen kannst.
* Antworte auf Deutsch.

Tripel: {context}

Frage: {question}
"""

summarize_template = """Im folgenden siehst Du Tripel, die von einer klinischen Richtlinie über 
chronische Herzinsuffizienz stammen. Fasse die Tripel zu einem verständlichen Text zusammen.

WICHTIG: 
* Benutze ausschließlich den Inhalt der gegebenen Tripel.
* Antworte auf Deutsch.

Tripel: {context}
"""

answer_template = """Im folgenden siehst Du Tripel, die von einer klinischen Richtlinie über 
chronische Herzinsuffizienz stammen. Darunter siehst Du eine Frage zu der Richtlinie.
Beantworte die darunterstehende Frage anhand dieser Information.

WICHTIG: 
* Benutze ausschließlich den Inhalt aus der Zusammenfassung.
* Wenn der Kontext nicht genügend Information bietet, dann sage unbedingt, 
dass Du keine Aussage treffen kannst.
* Antworte auf Deutsch.

Tripel: {context}

Frage: {question}
"""

empty_template = """Bitte beantworte die folgende Frage aus einer einer klinischen Richtlinie über 
chronische Herzinsuffizienz.

Frage: {question}
"""

structured_prompt = ChatPromptTemplate.from_template(structured_template)
summarize_prompt = ChatPromptTemplate.from_template(summarize_template)
answer_prompt = ChatPromptTemplate.from_template(answer_template)
empty_prompt = ChatPromptTemplate.from_template(empty_template)


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

structured_chain = (
    RunnableParallel(
        {
            "context": structured_retriever,
            "question": RunnablePassthrough(),
            "language": itemgetter("language"),
        }
    )
    | structured_prompt
    | llm
    | StrOutputParser()
)

retriever_chain = (
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

summarize_answer_chain = (
    {
        "context": retriever_chain,
        "question": RunnablePassthrough(),
        "language": itemgetter("language"),
    }
    | answer_prompt
    | llm
    | StrOutputParser()
)

# chains = [structured_chain, summarize_chain, empty_chain, summarize_answer_chain]

for i, (q, a) in enumerate(zip(questions1, answers1)):
    # if i == 0:
    #     continue
    print(q, a)
    structured_answer = structured_chain.invoke({"question": q, "language": "german"})
    summarize_answer = summarize_chain.invoke({"question": q, "language": "german"})
    empty_answer = empty_chain.invoke({"question": q, "language": "german"})
    summarize_answer_answer = summarize_answer_chain.invoke(
        {"question": q, "language": "german"}
    )
    pass

# answer = chain.invoke(
#     {
#         "question": "Welche Auswirkungen hat sie auf den Menschen?",
#         "chat_history": [("Was ist chronische Herzinsuffizienz", answer)],
#         "language": "german",
#     }
# )

pass
