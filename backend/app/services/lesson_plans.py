import json
import os

from langchain_core.messages import HumanMessage, SystemMessage

from ..utils import generate_id, now_iso
from .knowledge_base import generate_knowledge_points, search_documents
from .langchain_client import get_chat_model, is_dashscope_configured
from .model_client import parse_json_payload


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_OUTLINE_ROOT = os.path.join(_PROJECT_ROOT, "data", "teaching-outlines")


def _ensure_course_outline_dir(course_id: str) -> str:
    path = os.path.join(_OUTLINE_ROOT, course_id)
    os.makedirs(path, exist_ok=True)
    return path


def _iter_outline_files(course_id: str) -> list[str]:
    dir_path = os.path.join(_OUTLINE_ROOT, course_id)
    if not os.path.exists(dir_path):
        return []
    return [
        os.path.join(dir_path, filename)
        for filename in os.listdir(dir_path)
        if filename.endswith(".json")
    ]


def _load_outline_file(file_path: str) -> dict | None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def save_lesson_outline(course_id: str, outline: dict, created_by: str | None = None) -> dict:
    outline_id = outline.get("outline_id") or generate_id("outline")
    dir_path = _ensure_course_outline_dir(course_id)
    file_path = os.path.join(dir_path, f"{outline_id}.json")
    created_at = outline.get("created_at") or now_iso()

    payload = {
        **outline,
        "outline_id": outline_id,
        "course_id": course_id,
        "created_by": created_by,
        "created_at": created_at,
        "updated_at": outline.get("updated_at"),
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return payload


def list_lesson_outlines(course_id: str) -> list[dict]:
    outlines = []
    for file_path in _iter_outline_files(course_id):
        data = _load_outline_file(file_path)
        if not data:
            continue
        outline_id = data.get("outline_id") or os.path.splitext(os.path.basename(file_path))[0]
        outlines.append(
            {
                "outline_id": outline_id,
                "title": data.get("title") or f"讲解提纲 {outline_id}",
                "chapter_title": data.get("chapter_title") or "",
                "duration_minutes": data.get("duration_minutes") or 0,
                "created_at": data.get("created_at") or now_iso(),
                "knowledge_count": len(data.get("key_points") or data.get("knowledge_points") or []),
            }
        )
    return sorted(outlines, key=lambda item: item["created_at"], reverse=True)


def get_lesson_outline(course_id: str, outline_id: str) -> dict | None:
    file_path = os.path.join(_OUTLINE_ROOT, course_id, f"{outline_id}.json")
    if not os.path.exists(file_path):
        return None
    data = _load_outline_file(file_path)
    if not data:
        return None
    return _normalize_saved_outline(data)


def delete_lesson_outline(course_id: str, outline_id: str) -> bool:
    file_path = os.path.join(_OUTLINE_ROOT, course_id, f"{outline_id}.json")
    if not os.path.exists(file_path):
        return False
    try:
        os.remove(file_path)
        return True
    except OSError:
        return False


def _normalize_saved_outline(data: dict) -> dict:
    source_chunks = data.get("source_chunks") or []
    citations = data.get("citations") or []
    if source_chunks and isinstance(source_chunks[0], dict) and not citations:
        citations = source_chunks
        source_chunks = [item.get("chunk_id") for item in citations if item.get("chunk_id")]

    teaching_flow = data.get("teaching_flow")
    if not teaching_flow and isinstance(data.get("teaching_steps"), list):
        teaching_flow = [
            {
                "stage": item.get("title") or "教学环节",
                "minutes": item.get("duration_minutes") or 5,
                "teacher_activity": item.get("content") or "组织讲解与引导",
                "student_activity": "参与讨论、记录要点并完成课堂任务。",
                "content_focus": item.get("content") or item.get("title") or "章节重点",
            }
            for item in data["teaching_steps"]
            if isinstance(item, dict)
        ]

    return {
        **data,
        "teaching_flow": teaching_flow or [],
        "practice_tasks": data.get("practice_tasks") or [],
        "assessment_suggestions": data.get("assessment_suggestions") or data.get("after_class_suggestions") or [],
        "source_chunks": source_chunks,
        "citations": citations,
    }


def generate_lesson_outline(
    course_id: str,
    chapter_title: str,
    duration_minutes: int,
    knowledge_scope: list[str] | None = None,
    audience_level: str = "基础",
    include_practice: bool = True,
) -> dict:
    knowledge_points = [item.strip() for item in (knowledge_scope or []) if item and item.strip()]
    if not knowledge_points:
        knowledge_points = generate_knowledge_points(course_id, limit=8)
    if not knowledge_points:
        knowledge_points = [chapter_title]

    query = " ".join([chapter_title, *knowledge_points[:6]])
    results = search_documents(course_id, query, top_k=8)
    citations = [_build_citation(result) for result in results]

    fallback = _build_fallback_outline(
        course_id=course_id,
        chapter_title=chapter_title,
        duration_minutes=duration_minutes,
        knowledge_points=knowledge_points,
        results=results,
        include_practice=include_practice,
    )

    if is_dashscope_configured() and results:
        model_payload = _generate_outline_with_model(
            chapter_title=chapter_title,
            duration_minutes=duration_minutes,
            knowledge_points=knowledge_points,
            audience_level=audience_level,
            include_practice=include_practice,
            results=results,
        )
        if model_payload:
            _apply_model_payload(fallback, model_payload)

    fallback["teaching_flow"] = _normalize_flow_minutes(
        fallback.get("teaching_flow", []),
        duration_minutes,
    )
    fallback["citations"] = citations
    fallback["source_chunks"] = [item["chunk_id"] for item in citations]
    return fallback


def _build_citation(result: dict) -> dict:
    content = result.get("content") or ""
    return {
        "chunk_id": result.get("chunk_id") or generate_id("chunk"),
        "source_doc_id": result.get("source_doc_id") or "",
        "source_doc_name": result.get("source_doc_name") or "未知文档",
        "title_path": result.get("title_path") or "",
        "excerpt": content[:180],
        "score": result.get("score"),
        "rerank_score": result.get("rerank_score"),
        "bm25_score": result.get("bm25_score"),
        "hybrid_score": result.get("hybrid_score"),
    }


def _build_fallback_outline(
    course_id: str,
    chapter_title: str,
    duration_minutes: int,
    knowledge_points: list[str],
    results: list[dict],
    include_practice: bool,
) -> dict:
    key_points = knowledge_points[:6] or [chapter_title]
    difficult_points = key_points[:3]
    intro = max(5, round(duration_minutes * 0.15))
    concept = max(10, round(duration_minutes * 0.35))
    demo = max(10, round(duration_minutes * 0.30))
    summary = max(5, duration_minutes - intro - concept - demo)

    return {
        "title": f"{chapter_title}讲解提纲",
        "course_id": course_id,
        "chapter_title": chapter_title,
        "duration_minutes": duration_minutes,
        "objectives": [
            f"理解{chapter_title}的核心概念与基本作用。",
            "能够结合课程资料解释关键知识点之间的关系。",
            "能够完成与本章节相关的基础实训任务。",
        ],
        "key_points": key_points,
        "difficult_points": difficult_points,
        "teaching_flow": [
            {
                "stage": "导入与目标说明",
                "minutes": intro,
                "teacher_activity": "结合课程背景说明本节学习目标与应用场景。",
                "student_activity": "回顾已有知识，明确本节学习任务。",
                "content_focus": chapter_title,
            },
            {
                "stage": "核心概念讲解",
                "minutes": concept,
                "teacher_activity": "围绕知识库检索片段讲解关键概念、定义与关系。",
                "student_activity": "记录重点概念，回答教师提出的理解性问题。",
                "content_focus": "、".join(key_points[:4]),
            },
            {
                "stage": "案例演示与实训引导",
                "minutes": demo,
                "teacher_activity": "通过示例演示知识点的实际应用，并布置基础实训任务。",
                "student_activity": "跟随示例完成操作或分析，尝试独立解决小任务。",
                "content_focus": "基础实训",
            },
            {
                "stage": "总结与巩固",
                "minutes": summary,
                "teacher_activity": "归纳本节重点与易错点，说明课后巩固方向。",
                "student_activity": "完成随堂小结，记录仍不清楚的问题。",
                "content_focus": "知识巩固",
            },
        ],
        "practice_tasks": _build_practice_tasks(key_points, include_practice),
        "assessment_suggestions": [
            "使用单选题和判断题检查学生对核心概念的掌握情况。",
            "使用填空题考查关键术语与定义记忆。",
            "使用简答题要求学生说明知识点作用并结合实训场景举例。",
        ],
        "source_chunks": [result.get("chunk_id") for result in results if result.get("chunk_id")],
        "citations": [],
    }


def _build_practice_tasks(knowledge_points: list[str], include_practice: bool) -> list[str]:
    if not include_practice:
        return []
    selected = knowledge_points[:3] or ["本章节核心知识点"]
    return [
        f"围绕“{point}”完成一个基础练习，并说明操作或判断依据。"
        for point in selected
    ]


def _generate_outline_with_model(
    chapter_title: str,
    duration_minutes: int,
    knowledge_points: list[str],
    audience_level: str,
    include_practice: bool,
    results: list[dict],
) -> dict | None:
    llm = get_chat_model()
    if not llm:
        return None

    context = "\n\n".join(
        f"[{idx}] {item.get('title_path', '')}\n{item.get('content', '')}"
        for idx, item in enumerate(results, start=1)
    )
    system_prompt = (
        "你是高校实训课程教师备课助手。请严格依据给定课程资料生成章节知识讲解提纲，"
        "内容应服务教师备课，结构清晰、可直接用于课堂讲解。"
        "只返回严格 JSON，不要包含 Markdown 或多余解释。"
    )
    user_prompt = (
        f"章节名称：{chapter_title}\n"
        f"课时长度：{duration_minutes} 分钟\n"
        f"学生基础：{audience_level}\n"
        f"知识点范围：{', '.join(knowledge_points)}\n"
        f"是否包含基础实训任务：{include_practice}\n\n"
        f"课程资料：\n{context}\n\n"
        "请返回 JSON 字段：title, objectives(array), key_points(array), "
        "difficult_points(array), teaching_flow(array), practice_tasks(array), "
        "assessment_suggestions(array)。teaching_flow 每项必须包含 "
        "stage, minutes, teacher_activity, student_activity, content_focus。"
        "minutes 总和应尽量接近课时长度。"
        "practice_tasks、key_points、difficult_points 中的每一项都必须是可直接展示的中文字符串，"
        "不要返回对象、嵌套 JSON 或字典结构。"
    )
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        text = getattr(response, "content", str(response))
        payload = parse_json_payload(text)
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def _apply_model_payload(outline: dict, payload: dict) -> None:
    for key in ["title", "objectives", "key_points", "difficult_points", "practice_tasks", "assessment_suggestions"]:
        value = payload.get(key)
        if isinstance(value, str) and key == "title" and value.strip():
            outline[key] = value.strip()
        elif isinstance(value, list) and value:
            outline[key] = [_stringify_list_item(item) for item in value if _stringify_list_item(item)]

    flow = payload.get("teaching_flow")
    if isinstance(flow, list) and flow:
        normalized_flow = []
        for item in flow:
            if not isinstance(item, dict):
                continue
            normalized_flow.append(
                {
                    "stage": str(item.get("stage") or "教学环节").strip(),
                    "minutes": int(item.get("minutes") or 5),
                    "teacher_activity": str(item.get("teacher_activity") or "组织讲解与引导").strip(),
                    "student_activity": str(item.get("student_activity") or "参与学习与练习").strip(),
                    "content_focus": str(item.get("content_focus") or "章节重点").strip(),
                }
            )
        if normalized_flow:
            outline["teaching_flow"] = normalized_flow


def _stringify_list_item(item: object) -> str:
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        name = str(item.get("name") or item.get("title") or item.get("task") or "").strip()
        description = str(item.get("description") or item.get("content") or "").strip()
        duration = item.get("duration_minutes") or item.get("minutes")
        output = str(item.get("output_format") or item.get("output") or "").strip()
        parts = []
        if name:
            parts.append(name)
        if description:
            parts.append(description)
        if duration:
            parts.append(f"建议用时 {duration} 分钟")
        if output:
            parts.append(f"产出形式：{output}")
        if parts:
            return "；".join(parts)
    return str(item).strip()


def _normalize_flow_minutes(flow: list[dict], target_minutes: int) -> list[dict]:
    if not flow:
        return flow

    normalized = []
    for item in flow:
        if not isinstance(item, dict):
            continue
        minutes = item.get("minutes")
        try:
            minutes = int(minutes)
        except (TypeError, ValueError):
            minutes = 0
        normalized.append({**item, "minutes": max(1, minutes)})

    if not normalized:
        return flow

    current_total = sum(item["minutes"] for item in normalized)
    if current_total <= 0:
        even = max(1, target_minutes // len(normalized))
        for item in normalized:
            item["minutes"] = even
        current_total = sum(item["minutes"] for item in normalized)

    diff = target_minutes - current_total
    if diff == 0:
        return normalized

    # Put the final adjustment on the longest stage first, then spread any remainder.
    sorted_indexes = sorted(
        range(len(normalized)),
        key=lambda index: normalized[index]["minutes"],
        reverse=True,
    )
    while diff != 0 and sorted_indexes:
        changed = False
        for index in sorted_indexes:
            if diff == 0:
                break
            step = 1 if diff > 0 else -1
            if normalized[index]["minutes"] + step < 1:
                continue
            normalized[index]["minutes"] += step
            diff -= step
            changed = True
        if not changed:
            break
    return normalized
