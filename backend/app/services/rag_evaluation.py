import math
from typing import Any

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from .knowledge_base import get_course_title, search_documents
from .langchain_client import get_chat_model, get_embeddings, is_dashscope_configured
from .rag_qa import build_answer_from_results

_METRIC_REGISTRY = {
    "faithfulness": faithfulness,
    "answer_relevancy": answer_relevancy,
    "context_precision": context_precision,
    "context_recall": context_recall,
}


def _to_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _result_to_dict(result: Any) -> dict[str, float]:
    if hasattr(result, "to_pandas"):
        df = result.to_pandas()
        if hasattr(df, "to_dict"):
            records = df.to_dict(orient="records")
            if records:
                output: dict[str, float] = {}
                for key, value in records[0].items():
                    parsed = _to_float(value)
                    if parsed is not None:
                        output[key] = parsed
                return output
    if hasattr(result, "scores"):
        output: dict[str, float] = {}
        for key, value in result.scores.items():
            parsed = _to_float(value)
            if parsed is not None:
                output[key] = parsed
        return output
    try:
        output: dict[str, float] = {}
        for key, value in dict(result).items():
            parsed = _to_float(value)
            if parsed is not None:
                output[key] = parsed
        return output
    except Exception:
        return {}


def _select_metrics(metric_names: list[str] | None, has_ground_truth: bool) -> list[Any]:
    if metric_names:
        selected = []
        for name in metric_names:
            metric = _METRIC_REGISTRY.get(name)
            if not metric:
                raise ValueError(f"Unsupported metric: {name}")
            if name in {"context_precision", "context_recall"} and not has_ground_truth:
                raise ValueError(f"Metric {name} requires ground_truth")
            selected.append(metric)
        return selected
    if has_ground_truth:
        return [faithfulness, answer_relevancy, context_precision, context_recall]
    return [faithfulness, answer_relevancy]


def evaluate_rag_response(
    course_id: str,
    question: str,
    top_k: int,
    answer: str | None = None,
    ground_truth: str | None = None,
    metrics: list[str] | None = None,
) -> dict[str, Any]:
    if not is_dashscope_configured():
        raise ValueError("DashScope API key is not configured.")

    llm = get_chat_model()
    embeddings = get_embeddings()
    if not llm or not embeddings:
        raise ValueError("RAGAS requires LLM and embedding models.")

    results = search_documents(course_id, question, top_k)
    course_name = get_course_title(course_id)
    payload = build_answer_from_results(
        question,
        results,
        course_name=course_name,
        answer_override=answer,
    )
    contexts = payload["contexts"]
    if not contexts:
        raise ValueError("No contexts found for evaluation.")

    dataset_payload: dict[str, list[Any]] = {
        "question": [question],
        "answer": [payload["answer"]],
        "contexts": [contexts],
    }
    if ground_truth is not None:
        dataset_payload["ground_truth"] = [ground_truth]

    dataset = Dataset.from_dict(dataset_payload)
    metric_objects = _select_metrics(metrics, ground_truth is not None)
    result = evaluate(dataset, metrics=metric_objects, llm=llm, embeddings=embeddings)
    scores = _result_to_dict(result)

    return {
        "answer": payload["answer"],
        "contexts": contexts,
        "citations": payload["citations"],
        "scores": scores,
        "metrics": [metric.name for metric in metric_objects],
    }
