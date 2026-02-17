from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

import requests

from cardio_graph_core.extraction.clients import ip_dict, ollama_models


def _base_url(node: str, port: int) -> str:
    host = ip_dict.get(node, node)
    if port >= 1000:
        return f"http://{host}:{port}/v1"
    return f"http://{host}:114{port}/v1"


def _model_id(model_name: str) -> str:
    return ollama_models.get(model_name, model_name)


def _extract_json(text: str) -> Dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            return json.loads(stripped[start : end + 1])
        raise


@dataclass
class LLMBridge:
    model_name: str
    node: str
    port: int
    timeout: int = 180

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        payload = {
            "model": _model_id(self.model_name),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        response = requests.post(
            f"{_base_url(self.node, self.port)}/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        return _extract_json(content)
