from langchain_ollama import ChatOllama

model = "mistral-nemo"
# model = "mistral:v0.3"
port = "11435"
llm = ChatOllama(
    model=model,
    base_url=f"http://10.250.135.153:{port}",
    # format="json",
    # temperature=0.1,
)
