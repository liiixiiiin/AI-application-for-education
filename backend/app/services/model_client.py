import json
import os
import urllib.request
from typing import Any


MODEL_API_URL = os.getenv("MODEL_API_URL", "").strip()
MODEL_API_KEY = os.getenv("MODEL_API_KEY", "").strip()
MODEL_API_MODEL = os.getenv("MODEL_API_MODEL", "gpt-4o-mini").strip()
MODEL_API_MODE = os.getenv("MODEL_API_MODE", "openai").strip().lower()


def is_configured() -> bool:
    return bool(MODEL_API_URL)


def _build_request_body(messages: list[dict[str, str]], temperature: float) -> dict[str, Any]:
    if MODEL_API_MODE == "openai":
        return {
            "model": MODEL_API_MODEL,
            "messages": messages,
            "temperature": temperature,
        }
    prompt = "\n".join([item["content"] for item in messages if item.get("content")])
    return {"prompt": prompt, "temperature": temperature}


def _extract_text(payload: dict[str, Any]) -> str | None:
    if MODEL_API_MODE == "openai":
        choices = payload.get("choices") or []
        if not choices:
            return None
        message = choices[0].get("message") or {}
        return message.get("content")

    for key in ("text", "answer", "content", "result"):
        if key in payload:
            return payload.get(key)
    return None


def generate_text(messages: list[dict[str, str]], temperature: float = 0.3) -> str | None:
    if not is_configured():
        return None

    data = json.dumps(_build_request_body(messages, temperature)).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if MODEL_API_KEY:
        headers["Authorization"] = f"Bearer {MODEL_API_KEY}"

    request = urllib.request.Request(MODEL_API_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    text = _extract_text(payload)
    return text.strip() if isinstance(text, str) else None


def parse_json_payload(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    if not cleaned:
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
