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

# Available Ollama models and their configurations from clients.baml
ollama_models = [
    # Gemma models
    ("Gemma", "gemma3", "g3"),
    ("GemmaG2", "gemma3", "g2"),
    ("GemmaG4", "gemma3", "g4"),
    ("GemmaG5", "gemma3", "g5"),
    # Llava models
    ("Llava34bG5", "llava:34b", "g5"),
    # Qwen models
    ("Qwen32b5_35", "qwen3:32b", "g5"),
    ("Qwen32b5_36", "qwen3:32b", "g5"),
    ("Qwen25vl72bG5", "qwen2.5vl:72b", "g5"),
    ("Qwen25vl32bG5", "qwen2.5vl:32b", "g5"),
    ("Qwen8bG4_37", "qwen3:latest", "g4"),
    ("Qwen4", "qwen3:32b", "g4"),
    ("Qwen8b4", "qwen3:latest", "g4"),
    ("Qwen8b2", "qwen3:latest", "g2"),
    ("Qwen4b2", "qwen3:4b", "g2"),
    ("Qwen14b4", "qwen3:14b", "g4"),
    ("Qwen14b5", "qwen3:14b", "g5"),
    ("Qwen30b4", "qwen3:30b", "g4"),
    ("Qwen30b5", "qwen3:30b", "g5"),
    ("Qwen32b5", "qwen3:32b", "g5"),
    ("Qwen14b3", "qwen3:14b", "g3"),
    ("Qwen4b3", "qwen3:4b", "g3"),
    # Llama models
    ("Llama4", "llama4", "g4"),
    ("Llama3", "llama3.3:70b", "g4"),
]

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
            },
        )
        clients_added.append(name)

    # Determine node and port for Ollama models
    if node and port:
        actual_port = port
        actual_node = node
    elif node:
        actual_port = port_dict.get(node, 30)
        actual_node = node
    else:
        # Try to infer from model name
        for ollama_name, _, model_node in ollama_models:
            if ollama_name.lower() == model_name.lower():
                actual_node = model_node
                actual_port = port_dict.get(model_node, 30)
                break
        else:
            # Default fallback
            actual_node = "g5"
            actual_port = 35

    # Add Ollama models for the specified node
    base_url = f"http://{ip_dict[actual_node]}:114{actual_port}/v1"

    for name, model, model_node in ollama_models:
        if model_node == actual_node:
            cr.add_llm_client(
                name=name,
                provider="openai-generic",
                options={
                    "base_url": base_url,
                    "model": model,
                    "max_tokens": (
                        10000
                        if "qwen3:32b" not in model and "qwen3:30b" not in model
                        else 100000
                    ),
                    "temperature": 0.0,
                },
            )
            clients_added.append(name)

    # Set primary model
    if model_name in clients_added:
        cr.set_primary(model_name)
    else:
        raise ValueError(
            f"Model '{model_name}' not found in available clients: {clients_added}"
        )

    return cr
