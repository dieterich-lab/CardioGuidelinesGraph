from langchain_ollama import ChatOllama

from .parser import args

model_dict = {
    "nemo": "mistral-nemo",
    "8x22b": "mixtral:8x22b",
    "v03": "mistral:v0.3",
    "large": "mistral-large",
    "70b": "llama3.1:70b",
}
model = model_dict[args.model]

ip_dict = {
    "g4": "10.250.135.153",
    "g2": "10.250.135.143",
    "g3": "10.250.135.150",
    "g5": "10.250.135.156",
}

llm = ChatOllama(
    model=model,
    temperature=0,
    keep_alive="24h",
    base_url=f"http://{ip_dict[args.gpu]}:114{args.port}",
    num_ctx=2048,
    num_predict=-1,
)
