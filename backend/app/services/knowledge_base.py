from collections import defaultdict
from typing import List

from ..utils import generate_id, now_iso


_DOCUMENT_STORE: dict[str, list[dict]] = defaultdict(list)


def list_documents(course_id: str) -> list[dict]:
    return list(_DOCUMENT_STORE.get(course_id, []))


def store_documents(course_id: str, documents: List[dict]) -> list[dict]:
    stored: list[dict] = []
    for doc in documents:
        stored.append(
            {
                "id": generate_id("doc"),
                "name": doc["name"],
                "doc_type": doc["doc_type"],
                "status": "indexed",
                "created_at": now_iso(),
            }
        )
    _DOCUMENT_STORE[course_id].extend(stored)
    return stored


def search_documents(
    course_id: str,
    query: str,
    top_k: int,
    filters: dict | None = None,
) -> list[dict]:
    _ = course_id, filters
    return []
