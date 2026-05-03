# MCP Server 规范（P0-2 底层 输出）

## 1. 设计目标

将本系统业务能力按 Model Context Protocol（MCP）标准协议对外暴露为 5 个原子 Tool，使其能被任意 MCP 客户端（Claude Desktop / Cursor / 自研 Agent）发现与调用。

业务工作流封装见 [memory-bank/skills-spec.md](memory-bank/skills-spec.md)；Agent 编排见 [memory-bank/agent-spec.md](memory-bank/agent-spec.md)。

## 2. 协议与传输

- 协议：Model Context Protocol（Anthropic 2024-11 开放标准）
- SDK：`mcp` Python SDK
- Transport：
  - **stdio**（默认）：本地进程对接 Claude Desktop / Cursor / Claude Code
  - **SSE / HTTP**（可选）：网络部署，供远程 MCP 客户端访问
- 内部 Agent（P0-1）通过 stdio transport 直连同进程 MCP Server，避免网络开销

## 3. 五个原子 Tool

### 3.1 `search_kb`
- 用途：课程知识库混合检索（向量 + BM25 + Rerank）
- input_schema：
  ```
  {
    "course_id": "string, required",
    "query": "string, required",
    "top_k": "integer, default 5",
    "filters": {"source_doc_type": ["markdown","pdf","docx"]}
  }
  ```
- output_schema：
  ```
  {
    "results": [
      {"chunk_id","score","content","title_path","source_doc_id","source_doc_name"}
    ]
  }
  ```
- 底层调用：[backend/app/services/knowledge_base.py](backend/app/services/knowledge_base.py)

### 3.2 `lesson_outline`
- 用途：基于检索结果生成章节讲解提纲
- input_schema：
  ```
  {
    "course_id": "string, required",
    "chapter": "string, required",
    "duration_minutes": "integer, default 90",
    "knowledge_points": "string[], optional",
    "context_chunks": "string[] (chunk_ids), optional"
  }
  ```
- output_schema：见 [memory-bank/exercise-generation-spec.md](memory-bank/exercise-generation-spec.md) 与现有 `lesson_plans.py` 输出
- 底层调用：[backend/app/services/lesson_plans.py](backend/app/services/lesson_plans.py)

### 3.3 `generate_exercise`
- 用途：按知识点 / 难度 / 题型生成练习题
- input_schema：
  ```
  {
    "course_id": "string, required",
    "count": "integer, default 5",
    "types": "string[]  // 单选/判断/填空/简答",
    "difficulty": "easy|medium|hard",
    "knowledge_scope": "string[], optional"
  }
  ```
- output_schema：见 [memory-bank/exercise-generation-spec.md](memory-bank/exercise-generation-spec.md) §2.2
- 底层调用：[backend/app/services/exercises.py](backend/app/services/exercises.py)

### 3.4 `grade_answer`
- 用途：单题评测（客观规则 + 主观语义+LLM 加权）
- input_schema：
  ```
  {
    "exercise_id": "string, required",
    "course_id": "string, required",
    "type": "single_choice|true_false|fill_in_blank|short_answer",
    "answer": "string | string[] | boolean"
  }
  ```
- output_schema：见 [memory-bank/exercise-grading-spec.md](memory-bank/exercise-grading-spec.md) §2
- 底层调用：[backend/app/services/exercises.py](backend/app/services/exercises.py)

### 3.5 `get_mastery`
- 用途：查询学生在某课程下所有知识点的掌握度（含薄弱标识）
- input_schema：
  ```
  {
    "student_id": "string, required",
    "course_id": "string, required",
    "weak_threshold": "number, default 0.6"
  }
  ```
- output_schema：
  ```
  {
    "mastery": [
      {"knowledge_point","mastery","attempt_count","is_weak"}
    ]
  }
  ```
- 底层调用：[backend/app/services/knowledge_tracking.py](backend/app/services/knowledge_tracking.py)

## 4. 与现有 `mcp_web_search.py` 的关系

- [backend/app/services/mcp_web_search.py](backend/app/services/mcp_web_search.py) 为 **MCP 客户端**，消费外部 MCP 服务（联网搜索）
- 本规范的 MCP Server 为 **生产侧**，对外暴露本系统能力
- 两者并存，互不干扰

## 5. 启动方式

```
# 本地 stdio 启动（供 Cursor / Claude Desktop 接入）
python -m backend.app.mcp.server

# 网络模式（SSE）
python -m backend.app.mcp.server --transport sse --port 8765
```

## 6. 客户端接入示例

### 6.1 Claude Desktop / Cursor 配置（stdio）
```
{
  "mcpServers": {
    "edu-platform": {
      "command": "python",
      "args": ["-m", "backend.app.mcp.server"],
      "env": {"DASHSCOPE_API_KEY": "sk-..."}
    }
  }
}
```

### 6.2 内部 Agent（P0-1）调用
- LangGraph Agent 在工具执行节点通过 mcp Python SDK 直连 stdio Server
- 每次调用自动附加 LangFuse Trace（详见 [memory-bank/evaluation-spec.md](memory-bank/evaluation-spec.md)）

## 7. 错误处理

| 错误码 | 含义 | Tool 行为 |
|---|---|---|
| `KB_NOT_FOUND` | 课程未上传知识库 | 返回空 results + warning 字段 |
| `INVALID_TYPE` | 题型不支持 | 抛出 ValidationError，由调用方处理 |
| `LLM_TIMEOUT` | 大模型超时 | 重试 1 次后抛 timeout |
| `RATE_LIMITED` | 触发限流 | 抛 RateLimitError，由调用方退避重试 |

错误均按 MCP 协议 `isError: true` 字段返回，避免被误判为正常输出。

## 8. 权限与限流

- stdio 模式：本地信任，无鉴权
- SSE/HTTP 模式：必须配合 API Key Header（`X-API-Key`）
- 限流策略由 [memory-bank/redis-spec.md](memory-bank/redis-spec.md) §5 统一承载（令牌桶）

## 9. 测试

- 单元：每个 Tool 的 input/output schema 校验
- 集成：用 mcp inspector 工具列出 tools 并调用每个 Tool 一次
- 端到端：通过 Cursor / Claude Desktop 实际接入并完成 1 个备课请求

## 10. 与其他规范的关系

- 高层 Skill 调用本 Server 的 Tool：[memory-bank/skills-spec.md](memory-bank/skills-spec.md)
- Agent 工具节点统一走本 Server：[memory-bank/agent-spec.md](memory-bank/agent-spec.md) §6
- 评测与 Trace：[memory-bank/evaluation-spec.md](memory-bank/evaluation-spec.md)
