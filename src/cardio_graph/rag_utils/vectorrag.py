# from langchain_ollama import OllamaEmbeddings, ChatOllama
import re
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from cardio_graph.extraction_utils.langchain_replacement import (
    SimpleRetrievalQA,
    ChatOllama,
    OllamaEmbeddings,
)

# from langchain.chains.retrieval_qa.base import RetrievalQA


ollama_host_ip = "10.250.135.153:11430"
md_path = "/prj/doctoral_letters/guide/data2/guidelines/esc_ccs.md"  # replace with your markdown file path


def create_vr_faiss_index(md_path, ollama_host_ip):
    loader = UnstructuredMarkdownLoader(md_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)

    embedding_model = OllamaEmbeddings(
        model="mxbai-embed-large:335m",
        base_url=ollama_host_ip,
    )

    vectorstore = FAISS.from_documents(docs, embedding_model)
    vectorstore.save_local(
        folder_path="/home/ecalik/CardioGuidelineGraph/src/cardio_graph/data",
        index_name="faiss_index_esc_ccs_new",
    )


def initialize_vector_rag(ollama_host_ip, folder_path):
    embedding = OllamaEmbeddings(
        model="mxbai-embed-large:335m", base_url=ollama_host_ip
    )
    vectorstore = FAISS.load_local(
        embeddings=lambda text: embedding.embed_query(text),
        folder_path=folder_path,
        allow_dangerous_deserialization=True,
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity", search_kwargs={"k": 3}
    )

    chat = ChatOllama(model="qwen3:14b", base_url=ollama_host_ip)

    qa_chain = SimpleRetrievalQA(
        llm=chat,
        retriever=retriever,
    )
    return qa_chain


def v_rag_query(prompt, qa_chain):
    result = qa_chain.invoke({"query": prompt})
    return result


def v_rag_wrapper(queries, qa_chain):
    results = []
    for prompt in queries:
        result = v_rag_query(prompt, qa_chain)
        results.append(result)
    return results


def strip_thinking(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def print_v_rag_result(result):
    print(f"\n--- Question---\n")
    print(result["query"])
    print("\n--- Answer ---\n")
    print(strip_thinking(result["result"]))

    print("\n--- Source Chunks ---\n")
    for doc in result["source_documents"]:
        print(doc.page_content)
        print("---")


def print_v_rag_list(result_list):
    for item in result_list:
        print("\n" + "-" * 50 + "\n")
        print_v_rag_result(item)
        print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    # qa_chain = initialize_vector_rag(ollama_host_ip)
    # list = []
    # questions = [
    #     "How did the ISCHEMIA-EXTEND follow-up influence the interpretation of invasive strategy outcomes, especially in patients with multivessel disease?"
    # ]

    # for question in questions:
    #     list.append(v_rag_query(question, qa_chain))
    # print_v_rag_list(list)
    create_vr_faiss_index(
        md_path="/prj/doctoral_letters/guide/data/guidelines/markdown/esc_ccs.md",
        ollama_host_ip="10.250.135.156:11430",
    )
