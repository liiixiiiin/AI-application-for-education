## 文档与文件说明

- `memory-bank/design-document.md`：毕设设计文档，定义业务背景、需求、范围与风险。
- `memory-bank/tech-stack.md`：技术栈选择与实施条件，作为开发与部署依据。
- `memory-bank/implementation-plan.md`：分步实施计划与测试要求，指导开发节奏。
- `memory-bank/mvp-scope.md`：MVP 基础功能清单与不做项，约束单人实现范围。
- `memory-bank/progress.md`：阶段性进度记录，便于接力开发与复盘。
- `memory-bank/api-conventions.md`：API 路径风格与资源命名规范，作为后端接口约束。
- `memory-bank/knowledge-base-guidelines.md`：知识库清洗与切分规则、样本文档位置。
- `memory-bank/retrieval-spec.md`：向量化与检索流程规范（输入输出与策略）。
- `memory-bank/rag-qa-spec.md`：RAG 问答最小闭环协议与引用字段规范。
- `memory-bank/exercise-generation-spec.md`：练习生成题型与输入输出规范。
- `memory-bank/exercise-grading-spec.md`：练习评测提交格式与判定规则规范。
- `memory-bank/user-course-spec.md`：基础用户与课程管理规范（角色、数据结构、API、页面）。

## 项目结构（Step 2）

- `frontend/`：前端应用（教师/学生/管理端界面）。
- `backend/`：后端 API 与业务逻辑。
- `model-service/`：模型服务与 RAG 管线。
- `data/`：本地数据与知识库样本存放目录。

## 当前实现（Step 9）

### 后端（FastAPI）
- 入口：`backend/app/main.py`
- 模块：
  - `backend/app/db.py`：SQLite 初始化与连接
  - `backend/app/auth.py`：密码哈希、会话 token、角色校验
  - `backend/app/routers/auth.py`：注册/登录 API
  - `backend/app/routers/courses.py`：课程创建与查询 API
  - `backend/app/routers/knowledge_base.py`：知识库文档上传、管理（查看/修改/删除/检索）API
- `backend/app/routers/rag_qa.py`：RAG 问答 API（含流式输出）
  - `backend/app/routers/exercises.py`：练习生成与评测 API
  - `backend/app/services/knowledge_base.py`：知识库文档存储、内容更新、网页解析、向量检索与可选大模型辅助切分
  - `backend/app/services/langchain_client.py`：DashScope Embeddings/Chat 模型封装
  - `backend/app/services/model_client.py`：外部模型 API 适配（可选）
- `backend/app/services/rag_qa.py`：RAG 问答逻辑（LangChain + DashScope，含流式输出）
  - `backend/app/services/rag_evaluation.py`：RAGAS 评测逻辑（指标计算与评估）
  - `backend/app/services/exercises.py`：练习生成与评测逻辑（LangChain + DashScope）

### 前端（Vue + Vite）
- 入口：`frontend/index.html` / `frontend/src/main.js`
- 路由：`frontend/src/router/index.js`
- 页面：
  - `frontend/src/pages/Login.vue`：注册与登录
  - `frontend/src/pages/Courses.vue`：课程列表与角色展示
  - `frontend/src/pages/CreateCourse.vue`：教师课程创建
  - `frontend/src/pages/KnowledgeBaseUpload.vue`：知识库上传、管理（查看/修改/删除/检索）页面
- `frontend/src/pages/RagQa.vue`：RAG 问答页面（支持流式输出）
  - `frontend/src/pages/ExerciseGeneration.vue`：练习生成表单与结果占位页面
  - `frontend/src/pages/ExerciseGrading.vue`：练习评测提交与结果占位页面
- API：`frontend/src/services/api.js`
- 会话：`frontend/src/stores/session.js`
- 样式：`frontend/src/assets/base.css`

### 数据库（SQLite）
- `users`：`id`/`name`/`email`/`role`/`password_hash`/`password_salt`/`created_at`
- `courses`：`id`/`title`/`description`/`creator_id`/`created_at`
- `sessions`：`token`/`user_id`/`created_at`
## 知识库样本（Step 3）

- 示例课程：数据库基础（多文档）。
- 样本文档：`data/knowledge-base/sample-course/course-outline.md`、`data/knowledge-base/sample-course/lecture-notes.md`。
