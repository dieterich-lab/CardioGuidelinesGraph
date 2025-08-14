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
from vectorrag import (
    initialize_vector_rag,
    v_rag_query,
    print_v_rag_list,
    strip_thinking,
)
from baml_client.sync_client import b
from baml_py import ClientRegistry


URI = "bolt://neo4j-dev2.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")
INDEX_NAME = "node_vector_index"
ollama_host_llm = "10.250.135.153:11430"  # gpu g4
model = "Qwen14b4"  # gpu g4
# ollama_host_llm = "10.250.135.150:11430" #gpu g3
# model = "Qwen4b3" #gpu g3
# output_path = "/prj/doctoral_letters/guide/outputs2/baml_output/evaluation.txt"
# prompt = "Which treatment is reccomended for CCS Patients with angina pectoris"
# questions = [prompt]

# questions = [
#     "What was the primary finding of the ISCHEMIA trial regarding invasive versus conservative strategies in CCS patients without left main disease or severely reduced LVEF?",
#     "What were the key symptomatic and prognostic benefits of the invasive strategy as reported in ISCHEMIA and ORBITA 2?"
# ]

# 10 Yes/No Questions
# yes_no_questions = [
#     "Did the ISCHEMIA trial show a significant benefit of an initial invasive strategy over a conservative strategy for the primary endpoint?",
#     "Is an initial conservative medical strategy generally preferred in CCS patients with moderate or severe inducible ischaemia and no left main disease or reduced LVEF?",
#     "Did patients in the invasive arm of the ISCHEMIA trial experience greater improvement in angina-related health status?",
#     "Was there a higher rate of spontaneous myocardial infarction in the conservative strategy group in the ISCHEMIA trial?",
#     "Did the ORBITA 2 trial show a benefit of PCI over placebo in reducing angina symptoms in patients with objective evidence of ischaemia?",
#     "Did extended follow-up in ISCHEMIA-EXTEND show a significant reduction in cardiovascular mortality with an initial invasive strategy?",
#     "Was the benefit of revascularization in ISCHEMIA-EXTEND most marked in patients with multivessel disease?",
#     "Did meta-analyses consistently show greater freedom from anginal symptoms with revascularization compared to GDMT alone?",
#     "Did the ISCHEMIA trial include patients with left main disease or LVEF <35%?",
#     "Did a post hoc analysis of ISCHEMIA show a higher risk of events with greater CAD severity?"
# ]

# 10 Free Text Questions
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

# 10 Patient Cases with Questions
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


# node_vector_index = Neo4jVector.from_existing_graph(
#     url=URI,
#     username=AUTH[0],
#     password=AUTH[1],
#     embedding=embedding,
#     index_name="node_vector_index",           # Name of your Neo4j VECTOR index
#     node_label="Node",                        # Label of the nodes to embed
#     text_node_properties=["value"],           # Which properties to embed
#     embedding_node_property="embedding",      # Where to store the vector
#     search_type="hybrid",                     # Optional, allows combining keyword + vector
# )


# remember to remove the index from all rdf:statement nodes
def initalize():
    cr = ClientRegistry()
    cr.set_primary(model)
    embedding = OllamaEmbeddings(
        model="mxbai-embed-large:335m",
        base_url=ollama_host_llm,
    )
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


def kg_v_baseline_chain(questions, qa_chain, vectorstore, cr):

    q_and_a_KG_RAG = {}
    q_and_a_V_RAG = []
    q_and_a_baseline = {}
    for prompt in questions:
        entities = b.EntityExtractor(prompt, {"client_registry": cr})
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
        print("--------------------------------------------------")
        # print(type(results[2]))
        # pretty_print_logic_analysis(results[2])
        print("BAML Client Interpreter...")
        statements = UnReificator(results[1])
        q_and_a_KG_RAG[prompt] = b.Interpreter(
            results[0], prompt, statements, results[2], {"client_registry": cr}
        )
        q_and_a_V_RAG.append(v_rag_query(prompt, qa_chain))
        q_and_a_baseline[prompt] = b.QuestionWithoutContext(
            prompt, {"client_registry": cr}
        )
    return q_and_a_KG_RAG, q_and_a_V_RAG, q_and_a_baseline


def file_three_llm(q_and_a_KG_RAG, q_and_a_V_RAG, q_and_a_baseline, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for (quKG, anKG), itemVRAG, (quBASE, anBASE) in zip(
            q_and_a_KG_RAG.items(), q_and_a_V_RAG, q_and_a_baseline.items()
        ):
            f.write("Q: " + quKG.strip() + "\n")
            f.write("KG A: " + str(anKG).strip() + "\n")
            f.write("V A: " + strip_thinking(itemVRAG["result"]) + "\n")
            f.write("B A: " + str(anBASE).strip() + "\n\n")


if __name__ == "__main__":
    time_list = []
    total_start = time.perf_counter()
    qa_chain, vectorstore, cr = initalize()
    for idx, questions in enumerate(array):
        iter_start = time.perf_counter()

        kg, v, baseline = kg_v_baseline_chain(questions, qa_chain, vectorstore, cr)
        output_path = (
            f"/prj/doctoral_letters/guide/outputs2/baml_output/tester2_{idx+1}.txt"
        )
        file_three_llm(kg, v, baseline, output_path)
        iter_end = time.perf_counter()
        time_list.append(
            f"Batch {idx+1} processed in {iter_end - iter_start:.2f} seconds"
        )

    total_end = time.perf_counter()
    for time_info in time_list:
        print(time_info)
    print(f"Total time: {total_end - total_start:.2f} seconds")

    # q_and_a_KG_RAG = {}
    # q_and_a_V_RAG = []
    # q_and_a_baseline = {}
    # for prompt in questions:
    #     entities = b.EntityExtractor(prompt)
    #     entity_list = entities_to_list(entities)
    #     queryable_nodes = []
    #     for entity in entity_list:
    #         result = vectorstore.similarity_search_with_score(entity, k=5)
    #         for doc, score in result:
    #             if score >=0.8:
    #                 queryable_nodes.append(doc.page_content)
    #             print("Content:", doc.page_content)
    #             print("Score:", score)
    #             print("Element ID:", doc.metadata.get("element_id", "N/A"))
    #             print("-" * 60)
    #         print("-" * 60)
    #     print(queryable_nodes, sep="\n")
    #     entities_corrected = b.EntityCorrector(" ".join(queryable_nodes), entities)

    #     queryable_nodes = entities_to_list(entities_corrected)
    #     results = ExactLogicOneHopMultithreadedWrapper(queryable_nodes, printing=False)
    #     print("--------------------------------------------------")
    #     # print(type(results[2]))
    #     # pretty_print_logic_analysis(results[2])
    #     print("BAML Client Interpreter...")
    #     statements = UnReificator(results[1])
    #     q_and_a_KG_RAG[prompt]=b.Interpreter(results[0], prompt, statements, results[2])
    #     q_and_a_V_RAG.append(v_rag_query(prompt, qa_chain))
    #     q_and_a_baseline[prompt] = b.QuestionWithoutContext(prompt)
    # # print(q_and_a_KG_RAG)
    # # print_v_rag_list(q_and_a_V_RAG)
    # # print(q_and_a_baseline)
    # with open(output_path, "w", encoding="utf-8") as f:
    #     for (quKG, anKG), itemVRAG , (quBASE, anBASE) in zip(q_and_a_KG_RAG.items(), q_and_a_V_RAG, q_and_a_baseline.items()):
    #         f.write("Q: " + quKG.strip() + "\n")
    #         f.write("KG A: " + str(anKG).strip() + "\n")
    #         f.write("V A: " + strip_thinking(itemVRAG['result']) + "\n")
    #         f.write("B A: " + str(anBASE).strip() + "\n\n")
