import time, os, requests

# from langchain_community.graphs import Neo4jGraph
# from langchain_neo4j import Neo4jVector

# rom langchain.chains import GraphCypherQAChain
# from langchain_ollama import OllamaEmbeddings, ChatOllama
from neo4j import GraphDatabase
from typing import List, Optional

from clients import create_client_registry
from query_copy import (
    ExactLogicOneHop,
    pretty_print_triples,
    entities_to_list,
    ExactLogicOneHopMultithreadedWrapper,
    UnReificator,
    pretty_print_logic_analysis,
)
from cardio_graph.rag_utils.vectorrag import (
    initialize_vector_rag,
    v_rag_query,
    print_v_rag_list,
    strip_thinking,
)
from cardio_graph.extraction_utils.langchain_replacement import (
    ChatOllama,
    OllamaEmbeddings,
    Neo4jGraph,
    Neo4jHybridVectorStore,
)
from cardio_graph.baml_client.sync_client import b
from baml_py import ClientRegistry
from dataclasses import dataclass


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

diagnostic_basics = [
    "According to the 2024 ESC CCS guidelines, what is the stepwise diagnostic algorithm (Steps 1–4) for individuals with suspected CCS?",
    "How is the Risk-Factor–weighted Clinical Likelihood (RF-CL) model constructed and what thresholds define very low, low, moderate, and high likelihood of obstructive CAD?",
    "When is coronary artery calcium scoring (CACS) recommended to reclassify low pre-test likelihood, and how should results alter downstream testing?",
    "In which pre-test likelihood ranges is CCTA preferred over functional imaging, and when is functional imaging recommended first-line?",
    "What are the indications for invasive coronary angiography (ICA) as the first diagnostic test, and what clinical features trigger this choice?",
]

diagnostic_advanced = [
    "What are the recommended cut-offs and roles for FFR, iFR, and QFR in assessing intermediate epicardial stenoses during ICA?",
    "How should non-invasive testing for microvascular dysfunction be performed (e.g., PET/CMR quantification of MBF/MFR) and how are abnormal thresholds defined?",
    "What is the recommended protocol for invasive vasomotor testing (e.g., acetylcholine) to diagnose epicardial vasospasm vs microvascular spasm?",
    "How should exercise ECG be used today in suspected CCS, and what are its main limitations and recommended use cases?",
    "How is 'high risk of adverse events' defined across modalities (e.g., Duke Treadmill Score, ischaemia on SPECT/PET/CMR, CCTA anatomy, FFR-CT), and how does this affect management?",
]

pharmacologic_therapy = [
    "What is the recommended strategy to select first-line antianginal/anti-ischaemic drugs and when should combination therapy be initiated?",
    "When is ivabradine indicated in CCS (including LVEF thresholds and clinical context), and when is it not recommended or contraindicated?",
    "What are the recommendations for aspirin vs clopidogrel monotherapy in CCS with and without prior MI/PCI, and after CABG?",
    "How should DAPT duration be tailored after elective PCI in CCS, including adjustments for high bleeding risk (ARC-HBR) and complex PCI?",
    "When is extended intensified antithrombotic therapy (e.g., low-dose rivaroxaban plus aspirin) recommended, and in which patient profiles should it be avoided?",
]

lipid_glucose_inflammation = [
    "What LDL-C targets and treatment sequence (high-intensity statin → ezetimibe → PCSK9 inhibitor) are recommended for CCS, and how do risk categories modify goals?",
    "When should SGLT2 inhibitors and/or GLP-1 receptor agonists be used in CCS patients (with diabetes, obesity, HF) for event reduction?",
    "What is the role of anti-inflammatory therapy (e.g., low-dose colchicine) in CCS, and in which phenotypes is it recommended or discouraged?",
    "How should antithrombotic therapy be managed in CCS patients with AF undergoing PCI (OAC alone vs OAC plus antiplatelet, and for how long)?",
    "Which patients with obstructive CAD should be referred for revascularization to reduce events or improve symptoms, and how should PCI vs CABG be selected (including SYNTAX/LM/multivessel considerations)?",
]

special_populations = [
    "How are ANOCA/INOCA endotypes (microvascular angina vs vasospastic angina) defined diagnostically, and what is the stepwise treatment for each?",
    "What specific considerations apply to CCS management in older adults (frailty, polypharmacy, dosing, procedural risk)?",
    "What sex-specific differences in CCS presentation, diagnostics, and therapy should guide decision-making in women?",
    "How should therapy be adapted in high bleeding-risk CCS patients (risk tools, antithrombotic minimization strategies, PPIs)?",
    "What are guideline recommendations for CCS with chronic kidney disease regarding imaging choices, contrast exposure, and drug dosing?",
]

follow_up_and_refractory = [
    "How should CCS be managed in the presence of heart failure (HFrEF/HFmrEF/HFpEF), including viability assessment and revascularization considerations?",
    "What is recommended for CCS patients with atrial fibrillation beyond peri-PCI management (rate/rhythm control interactions and anticoagulation long term)?",
    "When is screening for CAD in asymptomatic individuals appropriate, and what modalities (CACS/CCTA) are recommended for which risk strata?",
    "What is the recommended structure of long-term follow-up for established CCS (visit frequency, triggers for re-testing, adherence strategies, digital health)?",
    "How should recurrent or refractory angina be evaluated and treated after prior PCI/CABG, including approaches to ISR, graft failure, and non-obstructive causes?",
]

easy_questions = [
    # Paragraph 1 (Revascularization overview)
    "What is meant by revascularization in the context of chronic coronary syndromes, and which two procedures does it include?",
    # Paragraph 2 (Indication / ISCHEMIA context)
    "What did the ISCHEMIA trial show regarding the benefit of an initial invasive strategy compared with an initial conservative strategy in CCS patients with moderate or severe inducible ischaemia?",
    # Paragraph 3 (MI endpoints and long-term outcomes)
    "Why is the use of ‘any myocardial infarction’ as an endpoint problematic when evaluating the benefits of revascularization?",
]

medium_questions = [
    # Paragraph 1
    "According to the paragraph, how do CABG and PCI differ in their impact on survival compared with optimal medical therapy, and in which patient populations is CABG shown to be superior?",
    # Paragraph 2
    "How do the results of the ISCHEMIA trial and the CLARIFY registry together inform the initial management strategy for chronic coronary syndrome patients without left main disease or severe LV dysfunction?",
    # Paragraph 3
    "What trade-off between spontaneous myocardial infarction and procedural myocardial infarction is described when comparing an initial invasive strategy with a conservative strategy?",
]

hard_questions = [
    # Paragraph 1
    "Why must the survival benefit data for CABG be interpreted cautiously in modern clinical practice, and how do disease-modifying therapies such as ACE inhibitors, ARBs, and statins affect this interpretation?",
    # Paragraph 2
    "How can the apparent lack of overall survival benefit with routine revascularization be reconciled with the observed reductions in spontaneous myocardial infarction and improvements in angina-related health status reported in ISCHEMIA, ORBITA 2, and subsequent meta-analyses?",
    # Paragraph 3
    "How do the ISCHEMIA-EXTEND results and recent meta-analyses complicate the interpretation of cardiovascular versus all-cause mortality benefits associated with revascularization?",
]

patient_case_questions = [
    # Paragraph 1
    (
        "A 67-year-old man with diabetes mellitus, reduced left ventricular ejection fraction, "
        "and angiographically confirmed three-vessel coronary artery disease presents with stable "
        "exertional angina despite optimal medical therapy. Coronary anatomy shows high lesion complexity. "
        "Based on the evidence summarized, which revascularization strategy would be preferred, "
        "what factors support this decision, and which ongoing controversies should be discussed?"
    ),
    # Paragraph 2
    (
        "A 62-year-old woman with chronic coronary syndrome has moderate inducible ischaemia on stress testing, "
        "no left main coronary disease, and a left ventricular ejection fraction of 55%. She remains symptomatic "
        "despite optimized antianginal therapy. Based on the evidence summarized, how should the role of "
        "revascularization be discussed, including expected benefits, risks, and uncertainties?"
    ),
    # Paragraph 3
    (
        "A 69-year-old man with preserved left ventricular ejection fraction and multivessel coronary artery disease "
        "including ≥70% proximal LAD stenosis is treated initially with guideline-directed medical therapy. "
        "How would you assess the long-term benefits and risks of an early invasive strategy with respect to "
        "spontaneous myocardial infarction, procedural myocardial infarction, cardiovascular mortality, "
        "and all-cause mortality?"
    ),
]
# Additional questions for paragraph 4.4.2 (Ischaemic HFrEF, viability, and revascularization)

easy_questions += [
    "What is meant by myocardial viability in the context of ischaemic heart failure, and how does it differ from scarred myocardium?"
]

medium_questions += [
    "What did the STICH trial demonstrate about the long-term effects of CABG plus guideline-directed medical therapy compared with medical therapy alone in patients with LVEF ≤35%?"
]

hard_questions += [
    "How do the results of STICH, PARR-2, and REVIVED-BCIS2 collectively challenge the traditional concept that revascularization of viable myocardium necessarily improves left ventricular function and survival in ischaemic HFrEF?"
]

patient_case_questions += [
    (
        "A 61-year-old man with ischaemic cardiomyopathy (LVEF 30%), multivessel coronary artery disease, "
        "and evidence of myocardial viability on cardiac imaging is being evaluated for revascularization. "
        "Based on the evidence summarized in this paragraph, how would you weigh CABG versus PCI versus "
        "continued guideline-directed medical therapy, including expected effects on survival, myocardial infarction, "
        "stroke risk, symptom relief, and the relevance of myocardial viability testing?"
    )
]

# Additional questions for ESC Guidelines 3471 (viability assessment, STICH vs REVIVED-BCIS2 comparison)

easy_questions += [
    "Which major differences in patient characteristics and trial design distinguish the REVIVED-BCIS2 trial from the STICH trial?"
]

medium_questions += [
    "Why might the older age, lower burden of multivessel disease, higher use of modern heart failure therapies, and shorter follow-up in REVIVED-BCIS2 explain the lack of survival benefit with PCI?"
]

hard_questions += [
    "Why do heterogeneous definitions and measurement methods of myocardial viability limit the ability to draw firm conclusions about its role in guiding revascularization decisions in ischaemic HFrEF?"
]

patient_case_questions += [
    (
        "A 68-year-old patient with ischaemic heart failure with reduced ejection fraction is being evaluated "
        "by a multidisciplinary heart team. Imaging shows regions of partially viable myocardium that do not "
        "clearly align with technically feasible target vessels for revascularization. Based on the evidence "
        "summarized in this paragraph, how should myocardial viability assessment be interpreted, and how should "
        "an integrative management strategy involving imaging, heart failure, arrhythmia, and revascularization "
        "specialists be structured?"
    )
]

all_questions = [
    easy_questions,
    medium_questions,
    hard_questions,
    patient_case_questions,
]


array = [free_text_questions, patient_cases]
abstract_batch = [
    diagnostic_basics,
    diagnostic_advanced,
    pharmacologic_therapy,
    lipid_glucose_inflammation,
    special_populations,
    follow_up_and_refractory,
]

prompt = "Did the ISCHEMIA trial include patients with left main disease or LVEF <35%?"
array = [[prompt]]
list = [prompt]
dome_frage = "What should we do with a LVEF of 10%"


def initialize(
    model,
    node,
    ollama_host_llm,
    URI,
    AUTH,
    INDEX_NAME,
    vectorrag=True,
    faiss_folder_path=None,
):
    os.environ.setdefault("OLLAMA_HOST", ollama_host_llm)
    cr = create_client_registry(model_name=model, node=node, port=30)
    embedding = OllamaEmbeddings(
        model="mxbai-embed-large:latest",
        base_url=ollama_host_llm,
    )
    vectorstore = Neo4jHybridVectorStore(
        url=URI,
        username=AUTH[0],
        password=AUTH[1],
        embedding=embedding,
        index_name=INDEX_NAME,
        node_label="Node",
        text_node_property="value",
        search_type="hybrid",  # Optional, allows combining keyword + vector
    )

    qa_chain = None
    if vectorrag:
        qa_chain = initialize_vector_rag(ollama_host_llm, faiss_folder_path)
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
    questions,
    output_path,
    file_names,
    model,
    node,
    ollama_host_llm,
    URI,
    AUTH,
    INDEX_NAME,
):
    """
    Wrapper function to initialize components, process lists of questions, and log timing information.
    """
    os.environ["OLLAMA_HOST"] = ollama_host_llm
    time_list = []
    total_start = time.perf_counter()
    qa_chain, vectorstore, cr = initialize(
        model, node, ollama_host_llm, URI, AUTH, INDEX_NAME, vectorrag=False
    )
    iter_start = time.perf_counter()
    kg_results = {}
    for idx, question in enumerate(questions):
        results = hybrid_search_graph(question, cr, vectorstore)
        statements = UnReificator(results[1])
        answer = b.Interpreter(
            results[0], question, statements, results[2], {"client_registry": cr}
        )
        kg_results[question] = answer
    final_output_path = f"{output_path}/{file_names}_{idx+1}.txt"
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
    question_batches,
    model,
    node,
    ollama_host_llm,
    faiss_folder_path,
    URI,
    AUTH,
    INDEX_NAME,
    output_dir,
    file_name="nonamegiven",
):
    """
    Wrapper function to initialize components, process arrays of questions, and log timing information.
    """
    time_list = []
    total_start = time.perf_counter()
    qa_chain, vectorstore, cr = initialize(
        model,
        node,
        ollama_host_llm,
        URI,
        AUTH,
        INDEX_NAME,
        vectorrag=True,
        faiss_folder_path=faiss_folder_path,
    )
    for idx, questions in enumerate(question_batches):
        iter_start = time.perf_counter()
        kg, v, baseline = kg_v_baseline_chain(questions, qa_chain, vectorstore, cr)
        output_path = f"{output_dir}/{file_name}_{idx+1}.txt"
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


def search_dev1_dev2(list, model, node, ollama_host_llm):
    hybrid_search_graph_wrapper(
        questions=list,
        output_path="/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/RAG_ouput/dev1_hybrid_search",
        file_names="dev1_hybrid_search",
        model=model,
        node=node,
        ollama_host_llm=ollama_host_llm,
        URI="bolt://neo4j-dev1.internal:7687",
        AUTH=("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"),
        INDEX_NAME="embed_dev1",
    )
    hybrid_search_graph_wrapper(
        questions=list,
        output_path="/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/RAG_ouput/dev2_hybrid_search",
        file_names="dev2_hybrid_search",
        model=model,
        node=node,
        ollama_host_llm=ollama_host_llm,
        URI="bolt://neo4j-dev2.internal:7687",
        AUTH=("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"),
        INDEX_NAME="node_vector_index",
    )
    return


if __name__ == "__main__":
    # Example usage:
    # array = [free_text_questions, patient_cases]
    kg_v_baseline_wrapper(
        question_batches=all_questions,
        model="Qwen14b",
        node="g5",
        ollama_host_llm="10.250.135.156:11430",
        faiss_folder_path="/home/ecalik/CardioGuidelineGraph/src/cardio_graph/data/new_faiss/",
        URI="bolt://neo4j-dev3.internal:7687",
        AUTH=("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"),
        INDEX_NAME="embed_dev1",
        output_dir="/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/RAG_ouput/dev3_hybrid_search",
        file_name="test2026",
    )
    # hybrid_search_graph_wrapper(
    #     questions=[prompt],
    #     output_path="/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/RAG_ouput/dev3_hybrid_search",
    #     file_names="dev3_hybrid_search",
    #     model="Qwen14b",
    #     node="g4",
    #     ollama_host_llm="10.250.135.153:11430",
    #     URI="bolt://neo4j-dev3.internal:7687",
    #     AUTH=("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"),
    #     INDEX_NAME="embed_dev1",
    # )
    # hybrid_search_graph_wrapper(
    #     questions=free_text_questions,
    #     output_path="/home/ecalik/CardioGuidelineGraph/src/cardio_graph/outputs/RAG_ouput/dev2_hybrid_search",
    #     file_names="dev2_hybrid_search",
    #     model="Qwen14b",
    #     node="g5",
    #     ollama_host_llm="10.250.135.156:11430",
    #     URI="bolt://neo4j-dev2.internal:7687",
    #     AUTH=("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"),
    #     INDEX_NAME="node_vector_index",
    # )
