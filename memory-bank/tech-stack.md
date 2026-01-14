# 毕设软件技术栈推荐（最简单但最健壮）

## 1. 总体原则
- 单人可交付、最少依赖、可维护
- 模块清晰：前端/后端/模型服务/知识库
- 开源优先，国产或中文友好模型优先
- 赛题要求仅作参考，技术选型以落地与稳定为先

## 2. 推荐技术栈（精简可落地）
### 2.1 前端
- 框架：Vue 3 + Vite
- UI 组件：Element Plus
- 图表：ECharts
- 选择理由：学习曲线平缓、生态成熟、可快速搭建管理端与教学端页面

### 2.2 后端
- 语言与框架：Python + FastAPI
- 任务队列（可选）：Celery + Redis
- 选择理由：与AI模型生态兼容、开发效率高、API 性能稳定

### 2.3 模型与推理服务
- 开源模型（中文友好）：Qwen2.5-7B-Instruct / DeepSeek-7B / Yi-6B
- 推理方式：本地推理（llama.cpp）或本地 API 服务（如 Ollama/vLLM）
- 选择理由：可本地部署、中文效果好、与 RAG 适配稳定

### 2.4 知识库与检索
- 向量数据库：FAISS（本地轻量）
- 文本切分与嵌入：Sentence-Transformers
- 选择理由：无需复杂部署，单机可运行，性能稳定

### 2.5 数据存储
- 业务数据库：SQLite（单机）或 PostgreSQL（扩展时）
- 选择理由：SQLite 够用且零维护，后续可平滑升级

### 2.6 部署与运行
- 方式：Docker Compose 一键启动
- 选择理由：环境一致，易于打包交付

## 3. 实现条件（与毕设匹配）
- 开发环境：macOS/Windows/Linux 均可，Python 虚拟环境 + Node.js
- 实验平台：本地单机部署为主，可选接入外部模型 API 做对比
- 开发语言：Python（后端）+ TypeScript/JavaScript（前端）
- 数据库：SQLite（默认）/ PostgreSQL（可选）
- 编译器/运行时：Python 3.10+，Node.js 18+，Vite 构建
- 涉及硬件：建议 16GB 内存；CPU 可运行，GPU 可提速

## 4. 最简可运行形态（MVP）
- 前端：Vue 3 + Element Plus
- 后端：FastAPI
- 模型：Qwen2.5 + llama.cpp
- 向量库：FAISS
- 数据库：SQLite
- 部署：Docker Compose

## 5. 取舍说明
- 选择国产/中文友好本地模型与 FAISS，避免云依赖，符合赛题“本地知识库+开源模型”要求
- SQLite 降低复杂度，满足单人毕设规模
- Vue 3 + Element Plus 快速搭建教师/学生/管理三端界面
