from baml_py import ClientRegistry

# IP addresses for different nodes
ip_dict = {
    "g2": "10.250.135.143",
    "g3": "10.250.135.150",
    "g4": "10.250.135.153",
    "g5": "10.250.135.156",
}

# Port mapping for different nodes
port_dict = {
    "g2": 32,
    "g3": 33,
    "g4": 34,
    "g5": 35,
}

# Available Ollama models and their model strings from clients.baml
ollama_models = {
    "Qwen25vl72b": "qwen2.5vl:72b",
    "Qwen25vl32b": "qwen2.5vl:32b",
    "Qwen8b": "qwen3:latest",
    "Qwen4b": "qwen3:4b",
    "Qwen14b": "qwen3:14b",
    "Qwen30b": "qwen3:30b",
    "Qwen32b": "qwen3:32b",
    "Qwen235b": "qwen3:235b",
    "Qwen06b": "qwen3:0.6b",
    "Qwen17b": "qwen3:1.7b",
}

# OpenAI models
openai_models = [
    ("GPT41Nano", "gpt-4.1-nano", "env.KG_GENERATOR_API_KEY_FIRST"),
    ("GPT5", "gpt-5", "env.KG_GENERATOR_API_KEY_FIRST"),
    ("CustomGPT4oMini", "gpt-4o-mini", "env.OPENAI_API_KEY"),
]

# Anthropic models
anthropic_models = [
    ("CustomHaiku", "claude-3-haiku-20240307", "env.ANTHROPIC_API_KEY"),
]


def create_client_registry(
    model_name: str, node: str = None, port: int = None
) -> ClientRegistry:
    """
    Create a ClientRegistry with the specified model as primary.

    Args:
        model_name: Name of the model to use as primary
        node: Node identifier (g2, g3, g4, g5) for Ollama models
        port: Custom port number (overrides default)

    Returns:
        ClientRegistry with the specified model set as primary
    """
    cr = ClientRegistry()
    clients_added = []

    # Add OpenAI models
    for name, model, api_key in openai_models:
        cr.add_llm_client(
            name=name,
            provider="openai",
            options={
                "model": model,
                "api_key": api_key,
                "format": "json",
            },
        )
        clients_added.append(name)

    # Add Anthropic models
    for name, model, api_key in anthropic_models:
        cr.add_llm_client(
            name=name,
            provider="anthropic",
            options={
                "model": model,
                "api_key": api_key,
                "format": "json",
            },
        )
        clients_added.append(name)

    # Determine node and port for Ollama models
    if node and port:
        actual_port = port
        actual_node = node
    elif node:
        actual_port = port_dict.get(node, 34)
        actual_node = node

    # Add Ollama models for the specified node
    base_url = f"http://{ip_dict[node]}:114{actual_port}/v1"

    # Add the requested Ollama model if it exists
    if model_name in ollama_models:
        model_string = ollama_models[model_name]
        max_tokens = 10000
        if "qwen3:32b" in model_string or "qwen3:30b" in model_string:
            max_tokens = 100000
        if "qwen3:14b" in model_string:
            max_tokens = 4000
        cr.add_llm_client(
            name=model_name,
            provider="openai-generic",
            options={
                "base_url": base_url,
                "model": model_string,
                "max_tokens": max_tokens,
                "temperature": 0.0,
                "format": "json",
                "timeout": 600,
                "request_timeout": 600,
            },
        )
        clients_added.append(model_name)

    # Set primary model
    if model_name in clients_added:
        cr.set_primary(model_name)
    else:
        raise ValueError(
            f"Model '{model_name}' not found in available clients: {clients_added}"
        )

    return cr
