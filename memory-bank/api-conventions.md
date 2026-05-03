# API 路径与资源命名规范（Step 2 输出）

## 1. 基本风格
- 基础前缀：`/api/v1`
- 资源使用复数名词（如 `courses`、`users`）
- 路径使用 `kebab-case`
- 通过 HTTP 方法表达动作（GET/POST/PUT/PATCH/DELETE）

## 2. 资源与路径示例
- 用户与认证
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `GET /api/v1/users/{userId}`
- 课程
  - `POST /api/v1/courses`
  - `GET /api/v1/courses`
  - `GET /api/v1/courses/{courseId}`
- 知识库文档
  - `POST /api/v1/courses/{courseId}/documents`
  - `GET /api/v1/courses/{courseId}/documents`
- RAG 问答
  - `POST /api/v1/courses/{courseId}/qa`（支持 `use_web_search` 参数开启联网搜索）
  - `POST /api/v1/courses/{courseId}/qa/stream`（流式 SSE，联网搜索时额外返回 `web_sources` 事件）
- 练习生成与评测
  - `POST /api/v1/courses/{courseId}/exercises/generate`
  - `POST /api/v1/courses/{courseId}/exercises/grade`
- 教师备课
  - `POST /api/v1/courses/{courseId}/lesson-outlines/generate`
- 对话管理
  - `POST /api/v1/conversations`：创建对话（需 `course_id`）
  - `GET /api/v1/conversations?course_id=xxx`：列出用户在某课程下的对话
  - `GET /api/v1/conversations/{conversationId}`：获取对话详情（含消息列表）
  - `DELETE /api/v1/conversations/{conversationId}`：删除对话
  - `PATCH /api/v1/conversations/{conversationId}`：更新对话标题
- 知识追踪与个性化推荐
  - `GET /api/v1/knowledge-state?course_id=xxx`：获取当前用户在某课程下的知识点掌握度
  - `POST /api/v1/recommended-exercises`：基于薄弱知识点生成个性化推荐练习
  - `GET /api/v1/exercise-attempts?course_id=xxx`：获取当前用户的作答历史
- 基础统计
  - `GET /api/v1/stats/overview`

### 阶段四新增接口（工业级升级）

- Agent 编排（详见 [agent-spec.md](memory-bank/agent-spec.md)）
  - `POST /api/v1/agents/run`：发起一次 Agent 任务，支持 stream
  - `GET /api/v1/agents/runs/{runId}`：查询某次 Agent 执行详情（含工具序列与 trace_id）
- 异步任务（详见 [redis-spec.md](memory-bank/redis-spec.md) §5.2）
  - `POST /api/v1/tasks`：投递异步任务（`type` ∈ `kb_index | batch_exercise | eval | summarize`）
  - `GET /api/v1/tasks/{taskId}`：查询任务状态、进度、结果
- 评测（详见 [evaluation-spec.md](memory-bank/evaluation-spec.md) §8）
  - `POST /api/v1/evaluations/run`：在线触发单条评测
  - `GET /api/v1/evaluations/{runId}`：查询评测结果
- 长期记忆（详见 [memory-spec.md](memory-bank/memory-spec.md) §6）
  - `DELETE /api/v1/memory/long-term?course_id=xxx`：清空当前用户长期记忆（用户可主动清空）
- MCP Server（不走 REST，详见 [mcp-server-spec.md](memory-bank/mcp-server-spec.md) §5）
  - 启动入口：`python -m backend.app.mcp.server [--transport stdio|sse]`

## 3. 命名与字段约定
- 资源主键统一使用 `id`
- 课程关联字段使用 `course_id`
- 角色字段使用 `role`，取值：`admin`/`teacher`/`student`
- 时间字段统一使用 ISO 8601 字符串（`created_at`/`updated_at`）

## 4. 错误与响应
- 成功响应：`{ "data": ..., "meta": ... }`
- 失败响应：`{ "error": { "code": "...", "message": "..." } }`
- 错误码使用 `SCREAMING_SNAKE_CASE`
- 限流响应：HTTP 429 + `Retry-After` 头（详见 [redis-spec.md](memory-bank/redis-spec.md) §6）

## 5. 服务路由（阶段四 P0-4 微服务化后）
- 路径前缀不变；由 Nginx 按前缀路由：
  - `/api/v1/auth/*`、`/api/v1/users/*`、`/api/v1/courses/*`、`/api/v1/stats/*` → SpringBoot 业务服务
  - 其余（agents / qa / exercises / lesson-outlines / knowledge-state 等）→ FastAPI AI 服务
- 鉴权：所有接口要求 `Authorization: Bearer <JWT>` Header（公开接口除外）
- 详见 [microservice-spec.md](memory-bank/microservice-spec.md) §5
