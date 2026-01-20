import os
from functools import lru_cache
from typing import Any


def _get_dashscope_key() -> str:
    return os.getenv("DASHSCOPE_API_KEY", "").strip()


def is_dashscope_configured() -> bool:
    return bool(_get_dashscope_key())


@lru_cache
def get_embeddings() -> Any:
    from langchain_community.embeddings import DashScopeEmbeddings

    model = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v3").strip()
    return DashScopeEmbeddings(
        model=model,
        dashscope_api_key=_get_dashscope_key() or None,
    )


@lru_cache
def get_chat_model() -> Any:
    if not is_dashscope_configured():
        return None

    try:
        from langchain_community.chat_models import ChatTongyi
    except Exception:
        from langchain_community.chat_models import ChatDashScope as ChatTongyi

    model = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus").strip() or "qwen-plus"
    temperature = float(os.getenv("DASHSCOPE_TEMPERATURE", "0.3"))
    return ChatTongyi(
        model=model,
        temperature=temperature,
        dashscope_api_key=_get_dashscope_key(),
    )


@lru_cache
def get_reranker() -> Any:
    if not is_dashscope_configured():
        return None
    try:
        from langchain_community.document_compressors import DashScopeRerank
    except Exception:
        return None
    model = os.getenv("DASHSCOPE_RERANK_MODEL", "").strip() or None
    return DashScopeRerank(
        model=model,
        dashscope_api_key=_get_dashscope_key() or None,
    )
