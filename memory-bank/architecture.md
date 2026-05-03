## 文档与文件说明

### 顶层规划
- `memory-bank/design-document.md`：毕设设计文档，定义业务背景、需求、范围、技术原理与风险。
- `memory-bank/tech-stack.md`：技术栈选择与实施条件（已落地 + 规划新增）。
- `memory-bank/implementation-plan.md`：分步实施计划（含阶段四：工业级工程化升级，答辩前 4 周冲刺）。
- `memory-bank/mvp-scope.md`：基础功能清单与扩展功能清单。
- `memory-bank/progress.md`：阶段性进度记录。
- `memory-bank/api-conventions.md`：API 路径风格与资源命名规范。

### 已落地业务规范
- `memory-bank/knowledge-base-guidelines.md`：知识库清洗与切分规则。
- `memory-bank/retrieval-spec.md`：向量化与检索流程规范。
- `memory-bank/rag-qa-spec.md`：RAG 问答协议、对话管理 API（记忆细节迁至 `memory-spec.md`，评测接口迁至 `evaluation-spec.md`）。
- `memory-bank/exercise-generation-spec.md`：练习生成题型规范。
- `memory-bank/exercise-grading-spec.md`：练习评测规则。
- `memory-bank/user-course-spec.md`：基础用户与课程管理规范（业务表迁移至 SpringBoot 后此规范保留为业务契约）。

### 工业级工程化新增规范（阶段四主线，第 10-13 周）
- `memory-bank/agent-spec.md`：LangGraph Agent 状态机、意图识别、工具编排、反思纠错（P0-1）。
- `memory-bank/mcp-server-spec.md`：MCP Server 协议与 5 个原子 Tool（P0-2 底层）。
- `memory-bank/skills-spec.md`：Agent Skills 标准格式与 3 个工作流 Skill（P0-2 上层）。
- `memory-bank/evaluation-spec.md`：三层评测体系 + LangFuse Trace + CI 阻断（P0-3）。
- `memory-bank/microservice-spec.md`：SpringBoot + FastAPI 双服务架构（P0-4）。
- `memory-bank/redis-spec.md`：语义缓存 / 异步队列 / 限流 / 降级（P0-5）。
- `memory-bank/memory-spec.md`：短期 + 长期分层记忆方案（P0-6）。

## 项目结构

- `frontend/`：前端应用，Vue 3 + Vite + Element Plus。
- `backend/`：FastAPI AI 推理服务（含 Agent / RAG / 出题 / 评测 / 知识追踪 / MCP Server）。
- `backend-java/`：SpringBoot 业务服务（计划，阶段四 P0-4）—— 用户 / 课程 / 数据看板。
- `backend/skills/`：Agent Skills 目录（计划，阶段四 P0-2）。
- `data/`：本地数据 / 知识库 / 评测 Golden Set（`data/evaluation/`）。

## 当前实现

### 后端（FastAPI）
- 入口：`backend/app/main.py`
- 模块：
  - `backend/app/db.py`：SQLite 初始化与连接
  - `backend/app/schemas.py`：Pydantic 数据模型
  - `backend/app/auth.py`：密码哈希、会话 token、角色校验
  - `backend/app/routers/auth.py`：注册/登录 API
  - `backend/app/routers/courses.py`：课程创建与查询 API
  - `backend/app/routers/knowledge_base.py`：知识库文档上传、管理（查看/修改/删除/检索）、网页解析 API
  - `backend/app/routers/rag_qa.py`：RAG 问答 API（含流式 SSE 输出与 RAGAS 评测）
  - `backend/app/routers/exercises.py`：练习生成与评测 API（评测后自动记录作答并更新知识点掌握度）
  - `backend/app/routers/lesson_plans.py`：教师备课 API（章节知识讲解提纲自动生成）
  - `backend/app/routers/knowledge_tracking.py`：知识追踪与个性化推荐 API（掌握度查询/推荐练习/作答历史）
  - `backend/app/routers/agents.py`：LangGraph Agent 入口（`/api/v1/agents/run` + SSE `/run/stream`）
  - `backend/app/services/knowledge_base.py`：知识库文档存储、内容更新、网页解析、向量检索与可选大模型辅助切分
  - `backend/app/services/langchain_client.py`：DashScope Embeddings/Chat 模型封装
  - `backend/app/services/model_client.py`：外部模型 API 适配（可选）
  - `backend/app/services/rag_qa.py`：RAG 问答逻辑（LangChain + DashScope，含流式输出与联网搜索）
  - `backend/app/services/rag_evaluation.py`：RAGAS 评测逻辑（指标计算与评估）
  - `backend/app/services/rag_utils.py`：RAG 工具函数（混合检索、BM25、jieba 分词等）
  - `backend/app/services/exercises.py`：练习生成与评测逻辑（LangChain + DashScope），评测结果包含 knowledge_points
  - `backend/app/services/lesson_plans.py`：讲解提纲生成逻辑（检索课程资料 → 组装备课 Prompt → 输出教学目标/重点难点/课堂流程/实训任务/考核建议）
  - `backend/app/services/knowledge_tracking.py`：知识追踪服务（EMA 掌握度更新、薄弱知识点识别、个性化推荐练习生成、作答记录）
  - `backend/app/services/mcp_web_search.py`：MCP 网页搜索服务
  - `backend/app/services/memory_store.py`：对话记忆存储服务（对话 CRUD、消息持久化、历史加载）
  - `backend/app/routers/conversations.py`：对话管理 API（创建/列表/详情/删除/更新标题）
  - `backend/app/agents/`：LangGraph Agent 编排层（P0-1 已落地）
    - `intents.py`：7 个意图标签 + Skill 默认映射
    - `state.py`：`AgentState` TypedDict（共享状态、超时与重试预算）
    - `llm.py`：节点共用 LLM 调用（结构化 JSON + 自动修复）
    - `tools/registry.py`：6 个 Tool 适配器（`search_kb`/`lesson_outline`/`generate_exercise`/`grade_answer`/`get_mastery`/`web_search`），Pydantic 校验入参，包装现有 service
    - `nodes/intent_router.py`：意图识别（LLM 优先 + 规则兜底）
    - `nodes/planner.py`：任务拆解（每个 Intent 预设 Skill 步骤序列；mixed 走 LLM 自由拆解）
    - `nodes/tool_executor.py`：工具调用（≤2 次重试、step 间依赖回填、软超时记录）
    - `nodes/reflector.py`：反思纠错（json_schema / format_check / kp_match / coverage / grade_consistency / time_budget）
    - `nodes/aggregator.py`：按意图组装结构化最终响应，并把 qa 答案写入会话记忆
    - `graph.py`：LangGraph `StateGraph` 编织（intent_router → planner → tool_executor↺ → reflector → aggregator，反思失败 ≤1 次回 planner）
    - `runner.py`：对外 `run_agent` 同步入口 + `stream_agent_events` SSE 流式入口

### 前端（Vue 3 + Vite + Element Plus）
- 入口：`frontend/index.html` / `frontend/src/main.js`
- 路由：`frontend/src/router/index.js`
- 页面：
  - `frontend/src/pages/Login.vue`：注册与登录
  - `frontend/src/pages/Courses.vue`：课程列表与角色展示
  - `frontend/src/pages/CreateCourse.vue`：教师课程创建
  - `frontend/src/pages/KnowledgeBaseUpload.vue`：知识库上传、管理（查看/修改/删除/检索）页面
  - `frontend/src/pages/RagQa.vue`：RAG 问答页面（聊天式多轮对话，支持流式输出、联网搜索来源展示、对话管理与 RAGAS 评测模式）
  - `frontend/src/pages/LessonOutline.vue`：教师端章节知识讲解提纲生成页面
  - `frontend/src/pages/ExerciseGeneration.vue`：练习生成表单与结果页面
  - `frontend/src/pages/ExerciseGrading.vue`：练习评测提交与结果页面
  - `frontend/src/pages/ExerciseSession.vue`：沉浸式做题页面（全屏模式、计时、即时评测、练习总结）
  - `frontend/src/pages/PersonalizedExercise.vue`：个性化练习页面（知识点掌握度展示、薄弱项识别、推荐练习生成）
- API：`frontend/src/services/api.js`
- 会话：`frontend/src/stores/session.js`
- 样式：`frontend/src/assets/base.css`

### 数据库（SQLite）
- `users`：`id`/`name`/`email`/`role`/`password_hash`/`password_salt`/`created_at`
- `courses`：`id`/`title`/`description`/`creator_id`/`created_at`
- `sessions`：`token`/`user_id`/`created_at`
- `knowledge_points`：`id`/`course_id`/`point`/`created_at`
- `conversations`：`id`/`user_id`/`course_id`/`title`/`created_at`/`updated_at`（对话会话）
- `messages`：`id`/`conversation_id`/`role`/`content`/`citations`/`created_at`（对话消息）
- `knowledge_mastery`：`id`/`student_id`/`course_id`/`knowledge_point`/`mastery`(REAL)/`attempt_count`(INTEGER)/`updated_at`（知识点掌握度，UNIQUE(student_id, course_id, knowledge_point)）
- `exercise_attempts`：`id`/`student_id`/`exercise_id`/`course_id`/`score`(REAL)/`knowledge_points`(TEXT, JSON)/`created_at`（作答记录）

### 知识库存储
- 知识库索引：`data/knowledge-base/indexes/{课程名}/`
  - `documents.json`：文档元数据
  - `chunks/*.json`：切分后的文本片段
  - `chroma/`：ChromaDB 向量索引

## 知识库样本
- 已有课程：大模型（多文档 PDF）、地理（网页解析）
- 样本文档：`data/knowledge-base/sample-course/course-outline.md`、`data/knowledge-base/sample-course/lecture-notes.md`

## 已实现扩展模块
- 知识追踪与个性化推荐（EMA 掌握度更新 + 薄弱知识点识别 + 大模型生成针对性练习）
- 教师备课辅助（章节知识讲解提纲自动生成）
- 多轮对话记忆（方案 C，滑动窗口，详见 `rag-qa-spec.md`）
- 联网搜索（DashScope `enable_search` + 角标引用）
- 填空题题型支持（多空位 + 替代答案）

## 工业级工程化（阶段四主线，第 10-13 周，答辩前完成）
七个占位模块，详见对应 spec 与 [memory-bank/implementation-plan.md](memory-bank/implementation-plan.md) 阶段四：

| 模块 | 文档 | 状态 |
|---|---|---|
| Agent 编排层（LangGraph 状态机） | [agent-spec.md](memory-bank/agent-spec.md) | ✅ P0-1 已落地（`backend/app/agents/`） |
| MCP Server（5 个原子 Tool） | [mcp-server-spec.md](memory-bank/mcp-server-spec.md) | 🔲 P0-2 计划中 |
| Agent Skills（3 个高层工作流） | [skills-spec.md](memory-bank/skills-spec.md) | 🔲 P0-2 计划中 |
| 评测体系 + LangFuse Trace + CI 阻断 | [evaluation-spec.md](memory-bank/evaluation-spec.md) | 🔲 P0-3 计划中 |
| SpringBoot + FastAPI 双服务架构 | [microservice-spec.md](memory-bank/microservice-spec.md) | 🔲 P0-4 计划中 |
| Redis 中间件（缓存 / 队列 / 限流 / 降级） | [redis-spec.md](memory-bank/redis-spec.md) | 🔲 P0-5 计划中 |
| 分层记忆（短期滑窗 + 长期向量化） | [memory-spec.md](memory-bank/memory-spec.md) | 🔲 P0-6 计划中 |

## 数据库（升级方向）
- 业务库：SQLite（当前） → MySQL 8（阶段四主线 P0-4，由 SpringBoot 承载）
- 向量库：ChromaDB（不变）
- 中间件：新增 Redis 7（P0-5）
- 长期记忆向量：ChromaDB 复用 或 Redis Vector Set（P0-6，详见 `memory-spec.md`）
