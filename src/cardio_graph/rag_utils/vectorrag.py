from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains.retrieval_qa.base import RetrievalQA
import re
ollama_host_llm = "10.250.135.153:11430"
md_path = "/prj/doctoral_letters/guide/data2/guidelines/esc_ccs.md"  # replace with your markdown file path
# loader = UnstructuredMarkdownLoader(md_path)
# documents = loader.load()

# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
# docs = text_splitter.split_documents(documents)

# embedding_model = OllamaEmbeddings(model="mxbai-embed-large:335m",base_url=ollama_host_llm,)

# vectorstore = FAISS.from_documents(docs, embedding_model)
# vectorstore.save_local("faiss_index_esc_ccs") 

def initialize_vector_rag(ollama_host_llm):
    vectorstore = FAISS.load_local("faiss_index_esc_ccs", OllamaEmbeddings(model="mxbai-embed-large:335m", base_url=ollama_host_llm), allow_dangerous_deserialization=True)

    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    chat = ChatOllama(model="qwen3:14b",base_url=ollama_host_llm)

    qa_chain = RetrievalQA.from_chain_type(
        llm=chat,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
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
    print(result['query'])
    print("\n--- Answer ---\n")
    print(strip_thinking(result['result']))

    print("\n--- Source Chunks ---\n")
    for doc in result['source_documents']:
        print(doc.page_content)
        print("---")

def print_v_rag_list(result_list):
    for item in result_list:
        print("\n" + "-"*50 + "\n")
        print_v_rag_result(item)
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    qa_chain = initialize_vector_rag(ollama_host_llm)
    list = []
    questions = [
        "How did the ISCHEMIA-EXTEND follow-up influence the interpretation of invasive strategy outcomes, especially in patients with multivessel disease?"
    ]
    
    for question in questions:
        list.append(v_rag_query(question, qa_chain))
    print_v_rag_list(list)
