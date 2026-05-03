"""Agent 工具适配层。

将 backend/app/services/ 下既有业务函数包装为统一的 Tool 对象，
供 LangGraph 状态机调用。P0-2 完成 MCP Server 后，此层将切换到
通过 MCP 协议调用同一组工具，对外接口保持不变。
"""

from .registry import (
    REGISTRY,
    ToolSpec,
    get_tool,
    list_tool_specs,
    summarize_result,
)

__all__ = [
    "REGISTRY",
    "ToolSpec",
    "get_tool",
    "list_tool_specs",
    "summarize_result",
]
