"""LangGraph 状态机编织（agent-spec §2）。

```
START → intent_router → planner → tool_executor ↺ → reflector
                                                    ├─ pass → aggregator → END
                                                    └─ fail (≤replan) → planner
```
"""

from __future__ import annotations

import logging
from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from .nodes import (
    aggregator_node,
    intent_router_node,
    planner_node,
    reflector_node,
    tool_executor_node,
)
from .state import AgentState, time_exhausted

logger = logging.getLogger(__name__)

MAX_PLAN_REPLAN = 1


def _route_after_executor(state: AgentState) -> str:
    """工具循环出口：plan 还有剩余且未超时 → 继续 tool_executor，否则进入 reflector。"""

    plan = state.get("plan") or []
    cursor = int(state.get("cursor") or 0)
    if cursor < len(plan) and not time_exhausted(state):
        return "tool_executor"
    return "reflector"


def _route_after_reflector(state: AgentState) -> str:
    history = state.get("reflect_history") or []
    if not history:
        return "aggregator"
    last = history[-1]
    if last.get("pass_"):
        return "aggregator"
    plan_attempts = int(state.get("plan_attempts") or 0)
    if plan_attempts > MAX_PLAN_REPLAN:
        return "aggregator"
    return "planner"


@lru_cache(maxsize=1)
def get_agent_graph():
    """构建并缓存 LangGraph 编译产物。"""

    graph = StateGraph(AgentState)

    graph.add_node("intent_router", intent_router_node)
    graph.add_node("planner", planner_node)
    graph.add_node("tool_executor", tool_executor_node)
    graph.add_node("reflector", reflector_node)
    graph.add_node("aggregator", aggregator_node)

    graph.add_edge(START, "intent_router")
    graph.add_edge("intent_router", "planner")
    graph.add_edge("planner", "tool_executor")

    graph.add_conditional_edges(
        "tool_executor",
        _route_after_executor,
        {"tool_executor": "tool_executor", "reflector": "reflector"},
    )

    graph.add_conditional_edges(
        "reflector",
        _route_after_reflector,
        {"planner": "planner", "aggregator": "aggregator"},
    )

    graph.add_edge("aggregator", END)

    compiled = graph.compile()
    logger.info("LangGraph agent compiled with %s nodes", len(graph.nodes))
    return compiled
