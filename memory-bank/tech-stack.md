# 技术栈（实际使用 + 规划）

## 1. 总体原则
- 单人可交付、最少依赖、可维护
- 模块清晰：前端/后端/模型服务/知识库
- 开源优先，国产或中文友好模型优先
- 技术选型以落地与稳定为先

## 2. 当前技术栈（已落地）

### 2.1 前端
- 框架：Vue 3 + Vite
- UI 组件：Element Plus
- 图标：Lucide Icons
- 图表：ECharts（规划中）
- 选择理由：学习曲线平缓、生态成熟、可快速搭建管理端与教学端页面

### 2.2 后端
- 语言与框架：Python 3.11 + FastAPI
- 异步支持：uvicorn ASGI 服务器
- 流式输出：SSE（Server-Sent Events）
- 选择理由：与 AI 模型生态兼容、开发效率高、原生异步与流式支持

### 2.3 大模型与推理服务
- 模型接入：DashScope API（通义千问系列，如 qwen-plus / qwen-turbo）
- 联网搜索：DashScope Generation API `enable_search` + `search_options`（强制搜索、来源返回、角标引用、垂域搜索等）
- 框架：LangChain（模型调用、Chain/Prompt 编排）
- 可选本地模型：Qwen2.5-7B / DeepSeek-7B（通过 Ollama/vLLM 本地部署）
- 选择理由：DashScope 提供稳定中文 API 服务与内置联网搜索能力，LangChain 生态成熟

### 2.4 Embedding 与 Rerank
- Embedding 模型：DashScope text-embedding-v3（1024 维，中文优化）
- Rerank 模型：DashScope gte-rerank（Cross-Encoder 重排序）
- 选择理由：中文效果好，API 接入简单，与 LangChain 无缝集成

### 2.5 知识库与检索
- 向量数据库：ChromaDB（轻量级，适合原型开发与单机部署）
- 混合检索：向量语义检索 + BM25 关键词检索
- 中文分词：jieba（提升 BM25 与去重精度）
- 文档解析：PyPDFLoader / python-docx / Markdown 原生解析
- 可选大模型辅助切分：由 LLM 优化语义边界与标题路径
- 选择理由：ChromaDB 零配置、内置 HNSW 索引；混合检索显著提升召回率

### 2.6 评测
- RAG 评测：RAGAS 框架（faithfulness、answer_relevancy、context_precision、context_recall）
- 选择理由：业界标准 RAG 评测框架，指标全面

### 2.7 数据存储
- 业务数据库：SQLite（零维护，单机够用）
- 知识库元数据：JSON 文件（documents.json / chunks/*.json）
- 选择理由：SQLite 足够支撑毕设规模，后续可平滑升级至 PostgreSQL

### 2.8 部署与运行
- 开发模式：前端 `npm run dev`、后端 `uvicorn --reload`
- 生产部署：Docker Compose（规划中）

## 3. 规划新增技术（工业级工程化升级，对应阶段四主线 P0-1 ~ P0-6，第 10-13 周）

### 3.1 Agent 编排（P0-1）
- 框架：LangGraph（状态机式多节点 Agent）
- 协议：Function Calling（DashScope 原生支持）
- 详见 [memory-bank/agent-spec.md](memory-bank/agent-spec.md)

### 3.2 工具与技能（P0-2）
- MCP（Model Context Protocol，Anthropic 2024-11）+ Python `mcp` SDK
- Agent Skills 标准格式（Anthropic 2025-10）
- 详见 [memory-bank/mcp-server-spec.md](memory-bank/mcp-server-spec.md) 与 [memory-bank/skills-spec.md](memory-bank/skills-spec.md)

### 3.3 评测与可观测（P0-3）
- LangFuse（开源 LLM Trace 平台）
- LLM-as-Judge：评委固定 Qwen-Max
- GitHub Actions（CI 阻断）
- 详见 [memory-bank/evaluation-spec.md](memory-bank/evaluation-spec.md)

### 3.4 业务层 Java 化（P0-4）
- SpringBoot 3 + MyBatis + MySQL 8 + Spring Security + JWT
- Maven 构建
- 详见 [memory-bank/microservice-spec.md](memory-bank/microservice-spec.md)

### 3.5 中间件（P0-5）
- Redis 7 + `redis-py` + `rq`（任务队列）
- Java 侧：`spring-data-redis` + `redisson`
- 详见 [memory-bank/redis-spec.md](memory-bank/redis-spec.md)

### 3.6 分层记忆（P0-6）
- 短期：现有 SQLite + 滑动窗口
- 长期：DashScope text-embedding-v3 + ChromaDB（或 Redis Vector Set）
- 详见 [memory-bank/memory-spec.md](memory-bank/memory-spec.md)

### 3.7 主观题高级评分（与 P0-1 同步实施，第 10 周穿插完成）
- 语义相似度（余弦相似度）+ 大模型判分加权融合
- 多要点拆分评分（按 rubric 关键点逐项匹配）

### 3.8 本地推理（P1 可选）
- Ollama 本地部署 Qwen2.5-7B
- 与 DashScope 多模型路由 + 故障兜底

## 4. 实现条件（与毕设匹配）
- 开发环境：macOS/Windows/Linux 均可，Python 虚拟环境 + Node.js
- 实验平台：本地单机部署为主，通过 DashScope API 接入大模型
- 开发语言：Python（后端）+ JavaScript（前端）
- 数据库：SQLite（默认）/ PostgreSQL（可选）
- 运行时：Python 3.10+，Node.js 18+，Vite 构建
- 涉及硬件：普通笔记本可运行，建议 16GB 内存

## 5. 最简可运行形态（当前 MVP）
- 前端：Vue 3 + Element Plus + Lucide
- 后端：FastAPI + uvicorn
- 模型：DashScope API（通义千问）
- Embedding：DashScope text-embedding-v3
- 向量库：ChromaDB
- 检索：向量 + BM25 混合 + Rerank
- 数据库：SQLite
- 编排：LangChain

## 5.1 工业级升级形态（阶段四主线完成后，答辩演示形态）
- 前端：同上
- 业务层：SpringBoot 3 + MyBatis + MySQL 8 + JWT
- AI 层：FastAPI + LangChain + LangGraph + MCP Server
- 中间件：Redis 7（缓存 / 队列 / 限流）
- 模型：DashScope（主）+ Ollama 本地（兜底）
- 可观测：LangFuse 全链路 Trace
- CI：GitHub Actions + RAGAS + LLM-as-Judge + Golden Set 阻断

## 6. 取舍说明
- 选择 DashScope API 而非本地模型部署，降低硬件门槛，保证开发效率与生成质量
- ChromaDB 替代最初规划的 FAISS，零配置且内置持久化，更适合快速迭代
- LangChain 提供标准化的 RAG 编排能力，便于扩展与维护
- jieba 分词提升中文场景下 BM25 精度，成本极低
- RAGAS 提供标准评测指标，便于论文量化分析
