from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import requests

from cardio_graph_core.extraction.clients import (
    ollama_model_fallbacks,
    resolve_ollama_base_url,
)


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


def _extract_content_from_response(body: Dict[str, Any]) -> str:
    # Ollama /api/chat shape
    message = body.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content

    # OpenAI-compatible /v1/chat/completions shape
    choices = body.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        msg = first.get("message") if isinstance(first, dict) else None
        if isinstance(msg, dict):
            content = msg.get("content")
            if isinstance(content, str):
                return content

    raise RuntimeError("LLM response missing chat content")


def _discover_ollama_models(api_base_v1: str, timeout: int) -> List[str]:
    tags_url = (
        api_base_v1[:-3] + "/api/tags"
        if api_base_v1.endswith("/v1")
        else api_base_v1 + "/api/tags"
    )
    try:
        response = requests.get(tags_url, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        models = payload.get("models", []) if isinstance(payload, dict) else []
        names = []
        for model in models:
            if not isinstance(model, dict):
                continue
            name = model.get("name")
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
        return names
    except Exception:
        return []


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
        payload, _ = self.generate_json_with_debug(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return payload

    def generate_json_with_debug(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        api_base = resolve_ollama_base_url(self.node, self.port)
        model_candidates = ollama_model_fallbacks(self.model_name)
        discovered_models = _discover_ollama_models(
            api_base, timeout=min(self.timeout, 20)
        )
        if discovered_models:
            # Prefer qwen-family models, then any other discovered models.
            qwen = [m for m in discovered_models if "qwen" in m.lower()]
            others = [m for m in discovered_models if m not in qwen]
            for candidate in qwen + others:
                if candidate not in model_candidates:
                    model_candidates.append(candidate)

        base_payload = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        attempts = []
        for model_id in model_candidates:
            attempts.append(
                (
                    "openai_v1_json",
                    f"{api_base}/chat/completions",
                    {
                        **base_payload,
                        "model": model_id,
                        "response_format": {"type": "json_object"},
                    },
                )
            )
            attempts.append(
                (
                    "openai_v1_text",
                    f"{api_base}/chat/completions",
                    {**base_payload, "model": model_id},
                )
            )

        errors = []
        for mode, url, payload in attempts:
            debug: Dict[str, Any] = {
                "mode": mode,
                "url": url,
                "model": payload.get("model"),
                "temperature": payload.get("temperature"),
                "max_tokens": payload.get("max_tokens"),
            }
            response = None
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                )
                debug["http_status"] = response.status_code
                raw_text = response.text
                debug["raw_response_preview"] = raw_text[:4000]
                response.raise_for_status()
                body = response.json()
                content = _extract_content_from_response(body)
                debug["raw_content_preview"] = str(content)[:4000]
                parsed = _extract_json(content)
                debug["parsed_keys"] = (
                    sorted(parsed.keys()) if isinstance(parsed, dict) else []
                )
                return parsed, debug
            except Exception as exc:
                debug["error"] = str(exc)
                if response is not None:
                    if response.status_code == 404 and re.search(
                        r"model .* not found", response.text, flags=re.IGNORECASE
                    ):
                        debug["retry_reason"] = "model_not_found"
                errors.append(debug)

        raise RuntimeError(
            "LLM JSON generation failed; attempts="
            + json.dumps(errors, ensure_ascii=False)
        )
