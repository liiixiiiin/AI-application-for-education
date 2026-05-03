"""LangGraph Agent 编排层（P0-1）。

设计依据：memory-bank/agent-spec.md
- 状态机：intent_router → planner → tool_executor → reflector → aggregator
- 工具集：search_kb / lesson_outline / generate_exercise / grade_answer / get_mastery / web_search
- 反思维度：json_schema / format_check / kp_match / coverage / time_budget
"""

from .runner import run_agent, stream_agent_events

__all__ = ["run_agent", "stream_agent_events"]
