import sys

from ollama import Client

LLAMA4_HOST = "http://10.250.135.153:11430"


def get_ollama_response(prompt, model="qwen3:32b", temperature=0.0):
    """Get a response from Ollama LLM."""
    client = Client(host=LLAMA4_HOST, headers={"x-some-header": "some-value"})

    response = client.chat(
        model=model,
        options={"temperature": temperature},
        messages=[
            {"role": "user", "content": prompt},
        ],
    )

    return response["message"]["content"]


def main():
    """Main function to run Ollama interaction."""
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "give me the first 10 fibonacci numbers"

    print(f"Sending prompt to Ollama: '{prompt}'")
    print("\nResponse:")
    print(get_ollama_response(prompt))


if __name__ == "__main__":
    main()
