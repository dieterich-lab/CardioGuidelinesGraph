import time
from langchain_neo4j import Neo4jVector, Neo4jGraph, GraphCypherQAChain
from langchain_ollama import OllamaEmbeddings, ChatOllama
from neo4j import GraphDatabase
from query_copy import (
    ExactLogicOneHop,
    pretty_print_triples,
    entities_to_list,
    ExactLogicOneHopMultithreadedWrapper,
    UnReificator,
    pretty_print_logic_analysis,
)
from rag_utils.vectorrag import (
    initialize_vector_rag,
    v_rag_query,
    print_v_rag_list,
    strip_thinking,
)
from cardio_graph.baml_client.sync_client import b
from baml_py import ClientRegistry


URI = "bolt://neo4j-dev2.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")
INDEX_NAME = "node_vector_index"
ollama_host_llm = "10.250.135.153:11430"  # gpu g4
model = "Qwen14b4"  # gpu g4

free_text_questions = [
    "What did the ISCHEMIA trial conclude regarding the benefit of an initial invasive strategy versus conservative strategy in terms of primary endpoints?",
    "How did angina-related health status differ between invasive and conservative strategies in the ISCHEMIA trial?",
    "What did the ORBITA 2 trial demonstrate about PCI in patients with minimal or no antianginal therapy?",
    "What were the outcomes regarding spontaneous MI in patients managed conservatively in the ISCHEMIA trial?",
    "What does the CLARIFY registry suggest about the natural history of angina symptoms in CCS patients?",
    "What were the cardiovascular mortality outcomes after 7 years in ISCHEMIA-EXTEND?",
    "How did multivessel disease influence outcomes in ISCHEMIA-EXTEND?",
    "What complications arise in interpreting the endpoint of 'any myocardial infarction'?",
    "What differences were noted across meta-analyses examining revascularization versus GDMT?",
    "How does the severity of CAD relate to patient outcomes in ISCHEMIA according to post hoc analysis?",
]

patient_cases = [
    "A 62-year-old male with stable angina and moderate inducible ischaemia on stress testing, no left main disease, and LVEF of 60%. Should initial conservative medical therapy be considered?",
    "A 58-year-old female with CCS and persistent angina despite antianginal therapy. Would she potentially benefit from revascularization?",
    "A 70-year-old male with multivessel CAD (≥70 percent stenosis on CCTA) is being considered for an invasive strategy. Does evidence suggest a mortality benefit in this subgroup?",
    "A 65-year-old patient randomized to medical therapy in a trial like ISCHEMIA later suffers a spontaneous MI. Is this consistent with findings from the ISCHEMIA trial?",
    "A 55-year-old with stable angina is on no antianginal medication but has documented ischaemia. Would PCI likely improve symptoms?",
    "A 68-year-old CCS patient asks whether revascularization reduces all-cause mortality. What does long-term ISCHEMIA follow-up suggest?",
    "A 72-year-old patient wants to know the risks of procedural MI with early invasive management. Is the risk increased according to ISCHEMIA data?",
    "A 60-year-old with CCS asks whether non-cardiac mortality is increased with invasive strategy. What did ISCHEMIA-EXTEND show?",
    "A 66-year-old patient has proximal LAD stenosis ≥70%. Does this increase their risk of adverse outcomes according to ISCHEMIA?",
    "A 64-year-old patient with resolved angina asks if they still need revascularization. What does the CLARIFY registry suggest?",
]
array = [free_text_questions, patient_cases]

prompt = "Did the ISCHEMIA trial include patients with left main disease or LVEF <35%?"
array = [[prompt]]
list = [prompt]


def initialize(model, ollama_host_llm, URI, AUTH, INDEX_NAME, vectorrag=True):
    cr = ClientRegistry()
    cr.set_primary(model)
    embedding = OllamaEmbeddings(
        model="mxbai-embed-large:335m",
        base_url=ollama_host_llm,
    )
    if vectorrag:
        qa_chain = initialize_vector_rag(ollama_host_llm)
    vectorstore = Neo4jVector(
        url=URI,
        username=AUTH[0],
        password=AUTH[1],
        embedding=embedding,
        index_name=INDEX_NAME,
        node_label="Node",
        text_node_property="value",
        search_type="hybrid",  # Optional, allows combining keyword + vector
    )
    return qa_chain, vectorstore, cr


def hybrid_search_graph(question, cr, vectorstore):
    entities = b.EntityExtractor(question, {"client_registry": cr})
    entity_list = entities_to_list(entities)
    queryable_nodes = []
    for entity in entity_list:
        result = vectorstore.similarity_search_with_score(entity, k=5)
        for doc, score in result:
            if score >= 0.8:
                queryable_nodes.append(doc.page_content)
            print("Content:", doc.page_content)
            print("Score:", score)
            print("Element ID:", doc.metadata.get("element_id", "N/A"))
            print("-" * 60)
        print("-" * 60)
    print(queryable_nodes, sep="\n")
    entities_corrected = b.EntityCorrector(
        " ".join(queryable_nodes), entities, {"client_registry": cr}
    )
    true_given_nodes = entities_to_list(entities_corrected)
    results = ExactLogicOneHopMultithreadedWrapper(
        true_given_nodes, queryable_nodes, printing=False
    )
    return results


def hybrid_search_graph_wrapper(
    questions, output_path, model, ollama_host_llm, URI, AUTH, INDEX_NAME
):
    """
    Wrapper function to initialize components, process lists of questions, and log timing information.
    """
    time_list = []
    total_start = time.perf_counter()
    qa_chain, vectorstore, cr = initialize(
        model, ollama_host_llm, URI, AUTH, INDEX_NAME, vectorrag=False
    )
    iter_start = time.perf_counter()
    kg_results = {}
    for idx, question in enumerate(questions):
        results = hybrid_search_graph(question, cr, vectorstore)
        # You may want to process results further here
        kg_results[question] = results
    final_output_path = f"{output_path}/tester2_{idx+1}.txt"
    file_kg_results(kg_results, final_output_path)
    iter_end = time.perf_counter()
    time_list.append(f"Batch {idx+1} processed in {iter_end - iter_start:.2f} seconds")

    total_end = time.perf_counter()
    for time_info in time_list:
        print(time_info)
    print(f"Total time: {total_end - total_start:.2f} seconds")
    return


def kg_v_baseline_chain(questions, qa_chain, vectorstore, cr):
    q_and_a_KG_RAG = {}
    q_and_a_V_RAG = []
    q_and_a_baseline = {}
    for question in questions:
        results = hybrid_search_graph(question, cr, vectorstore)
        print("--------------------------------------------------")
        print("BAML Client Interpreter...")
        statements = UnReificator(results[1])
        q_and_a_KG_RAG[question] = b.Interpreter(
            results[0], question, statements, results[2], {"client_registry": cr}
        )
        q_and_a_V_RAG.append(v_rag_query(question, qa_chain))
        q_and_a_baseline[question] = b.QuestionWithoutContext(
            question, {"client_registry": cr}
        )
    return q_and_a_KG_RAG, q_and_a_V_RAG, q_and_a_baseline


def file_kg_results(q_and_a_KG_RAG, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for quKG, anKG in q_and_a_KG_RAG.items():
            f.write("Question: " + quKG.strip() + "\n")
            f.write("KgAnswer: " + str(anKG).strip() + "\n")


def file_three_llm(q_and_a_KG_RAG, q_and_a_V_RAG, q_and_a_baseline, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for (quKG, anKG), itemVRAG, (quBASE, anBASE) in zip(
            q_and_a_KG_RAG.items(), q_and_a_V_RAG, q_and_a_baseline.items()
        ):
            f.write("Q: " + quKG.strip() + "\n")
            f.write("KG A: " + str(anKG).strip() + "\n")
            f.write("V A: " + strip_thinking(itemVRAG["result"]) + "\n")
            f.write("B A: " + str(anBASE).strip() + "\n\n")


def kg_v_baseline_wrapper(
    question_batches, model, ollama_host_llm, URI, AUTH, INDEX_NAME, output_dir
):
    """
    Wrapper function to initialize components, process arrays of questions, and log timing information.
    """
    time_list = []
    total_start = time.perf_counter()
    qa_chain, vectorstore, cr = initialize(
        model, ollama_host_llm, URI, AUTH, INDEX_NAME, vectorrag=True
    )
    for idx, questions in enumerate(question_batches):
        iter_start = time.perf_counter()
        kg, v, baseline = kg_v_baseline_chain(questions, qa_chain, vectorstore, cr)
        output_path = f"{output_dir}/tester2_{idx+1}.txt"
        file_three_llm(kg, v, baseline, output_path)
        iter_end = time.perf_counter()
        time_list.append(
            f"Batch {idx+1} processed in {iter_end - iter_start:.2f} seconds"
        )

    total_end = time.perf_counter()
    for time_info in time_list:
        print(time_info)
    print(f"Total time: {total_end - total_start:.2f} seconds")
    return


if __name__ == "__main__":
    # Example usage:
    # array = [free_text_questions, patient_cases]
    kg_v_baseline_wrapper(
        array,
        model,
        ollama_host_llm,
        URI,
        AUTH,
        INDEX_NAME,
        "/prj/doctoral_letters/guide/outputs2/baml_output",
    )
