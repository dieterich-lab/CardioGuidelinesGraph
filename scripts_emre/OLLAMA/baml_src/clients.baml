// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview

client<llm> CustomGPT4o {
  provider openai
  options {
    model "gpt-4o"
    api_key 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
  }
}

client<llm> CustomGPT4oMini {
  provider openai
  retry_policy Exponential
  options {
    model "gpt-4o-mini"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> Gemma {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.150:11430/v1"
    model gemma3
    max_tokens 10000
    temperature 0.0
  }
}
client<llm> GemmaG2 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.143:11430/v1"
    model gemma3
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> GemmaG4 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.153:11430/v1"
    model gemma3
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> GemmaG5 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.156:11435/v1"
    model gemma3
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> Llava34bG5 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.156:11435/v1"
    model llava:34b
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> Qwen25vl72bG5 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.156:11435/v1"
    model qwen2.5vl:72b
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> Qwen25vl32bG5 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.156:11435/v1"
    model qwen2.5vl:32b
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> Llama4 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.153:11430/v1"
    model llama4
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> Llama3 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.153:11430/v1"
    model llama3.3:70b
  }
}

client<llm> Qwen4 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.153:11430/v1"
    model qwen3:32b
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> Qwen8b4 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.153:11430/v1"
    model qwen3:latest
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> Qwen8b2 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.143:11430/v1"
    model qwen3:latest
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> Qwen4b2 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.143:11430/v1"
    model qwen3:4b
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> Qwen14b4 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.153:11430/v1"
    model qwen3:14b
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> Qwen14b5 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.156:11430/v1"
    model qwen3:14b
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> Qwen30b4 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.153:11430/v1"
    model qwen3:30b
    max_tokens 100000
    temperature 0.0
  }
}

client<llm> Qwen30b5 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.156:11430/v1"
    model qwen3:30b
    max_tokens 100000
    temperature 0.0
  }
}

client<llm> Qwen32b5 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.156:11430/v1"
    model qwen3:32b
    max_tokens 100000
    temperature 0.0
  }
}


client<llm> Qwen14b3 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.150:11430/v1"
    model qwen3:14b
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> Qwen4b3 {
  provider "openai-generic"
  options {
    base_url "http://10.250.135.150:11430/v1"
    model qwen3:4b
    max_tokens 10000
    temperature 0.0
  }
}

client<llm> CustomHaiku {
  provider anthropic
  retry_policy Constant
  options {
    model "claude-3-haiku-20240307"
    api_key env.ANTHROPIC_API_KEY
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/round-robin
client<llm> CustomFast {
  provider round-robin
  options {
    // This will alternate between the two clients
    strategy [CustomGPT4oMini, CustomHaiku]
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/fallback
client<llm> OpenaiFallback {
  provider fallback
  options {
    // This will try the clients in order until one succeeds
    strategy [CustomGPT4oMini, CustomGPT4oMini]
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/retry
retry_policy Constant {
  max_retries 3
  // Strategy is optional
  strategy {
    type constant_delay
    delay_ms 200
  }
}

retry_policy Exponential {
  max_retries 2
  // Strategy is optional
  strategy {
    type exponential_backoff
    delay_ms 300
    multiplier 1.5
    max_delay_ms 10000
  }
}