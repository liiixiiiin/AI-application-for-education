"""Agent 节点共用的 LLM 调用辅助。

封装：
- 结构化 JSON 调用（带一次自动修复）
- 兼容 DashScope 未配置时的降级（节点根据返回 None 走规则路径）
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..services.langchain_client import get_chat_model, is_dashscope_configured
from ..services.model_client import parse_json_payload

logger = logging.getLogger(__name__)


def llm_available() -> bool:
    return is_dashscope_configured()


def call_json(
    system_prompt: str,
    user_prompt: str,
    *,
    repair_on_error: bool = True,
) -> dict[str, Any] | None:
    """调用 LLM 返回严格 JSON；解析失败时自动调用一次修复。"""

    llm = get_chat_model()
    if not llm:
        return None
    try:
        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        text = getattr(response, "content", str(response))
    except Exception:
        logger.exception("LLM call failed")
        return None
    if not text:
        return None
    payload = parse_json_payload(text)
    if isinstance(payload, dict):
        return payload

    if not repair_on_error:
        return None

    repair_prompt = (
        "你刚才返回的内容不是合法 JSON。请仅基于刚才的语义重新输出严格 JSON，"
        "不要添加任何解释。原始内容：\n" + str(text)
    )
    try:
        repaired = llm.invoke(
            [
                SystemMessage(content="你是 JSON 修复助手，只输出严格 JSON。"),
                HumanMessage(content=repair_prompt),
            ]
        )
        repaired_text = getattr(repaired, "content", str(repaired))
        payload = parse_json_payload(repaired_text)
        if isinstance(payload, dict):
            return payload
    except Exception:
        logger.exception("LLM repair call failed")
    return None


def call_text(system_prompt: str, user_prompt: str) -> str | None:
    """调用 LLM 返回纯文本（用于 qa 综述、聚合摘要等）。"""

    llm = get_chat_model()
    if not llm:
        return None
    try:
        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        text = getattr(response, "content", str(response))
        return str(text).strip() if text else None
    except Exception:
        logger.exception("LLM call_text failed")
        return None


def safe_json_dumps(value: Any, max_len: int = 800) -> str:
    """把任意结构序列化为短 JSON 字符串，避免污染 prompt。"""

    try:
        text = json.dumps(value, ensure_ascii=False)
    except TypeError:
        text = str(value)
    if len(text) > max_len:
        return text[:max_len] + "...(已截断)"
    return text
