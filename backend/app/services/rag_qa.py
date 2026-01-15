from typing import Any

from .knowledge_base import search_documents


def answer_question(course_id: str, question: str, top_k: int) -> dict[str, Any]:
    results = search_documents(course_id, question, top_k)
    citations = []
    for result in results:
        content = result.get("content", "")
        citations.append(
            {
                "chunk_id": result.get("chunk_id", ""),
                "source_doc_id": result.get("source_doc_id", ""),
                "source_doc_name": result.get("source_doc_name", "unknown"),
                "title_path": result.get("title_path", ""),
                "excerpt": content[:120] if content else "",
            }
        )

    if not citations:
        answer = "未找到相关资料，请确认课程知识库已上传。"
    else:
        answer = "（占位）基于检索到的资料生成回答，待接入模型后替换。"

    return {"answer": answer, "citations": citations}
