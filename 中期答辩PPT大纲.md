# 基于 AI 大模型的教学实训智能辅助系统的设计与实现

**本科毕业设计 中期答辩**

> 全篇共 14 页（含封面与致谢），与 `中期答辩PPT.pptx` 保持一一对齐。

---

## 第 1 页：封面

- **题目**：基于 AI 大模型的教学实训智能辅助系统的设计与实现
- **学生姓名**：李鑫
- **学号**：2207020422
- **指导教师**：XXX
- **学院 / 专业**：计算机科学与技术学院
- **答辩日期**：2026 年 X 月 X 日
- **答辩类型**：本科毕业设计 · 中期答辩

---

## 第 2 页：选题背景

布局：左侧两张政策原文截图作为权威背书，右侧用 STAR 方法的 S（时代背景）+ T（行业痛点）展开。

**S — 时代背景  ·  AI + 教育上升为国家战略**

- 教育数字化已上升为国家战略：教育部《教育数字化战略行动》、国务院《人工智能 +》行动意见明确要求推动 AI 与教育教学深度融合，智慧教育新形态加速到来
- 高校实训教学是计算机类专业人才培养的关键环节，但当前实训教学方式智能化程度普遍偏低、与产业需求衔接不足、教学资源更新缓慢，亟需借助大模型与 RAG 技术实现深度变革

**T — 行业痛点  ·  实训教学的四大顽疾**

| 序号 | 痛点 | 现状 |
|---|---|---|
| ① 备课负担重 | 章节素材整理、题目设计耗时数小时 |
| ② 题库更新慢 | 考核内容陈旧、难以紧跟课程与产业演进 |
| ③ 个性化缺位 | 一对多教学难以兼顾学生差异化需求 |
| ④ 数据成孤岛 | 教与学过程数据分散、难以形成反馈闭环 |

**金句横幅（页脚）**：当政策春风遇上技术成熟期，正是智能教学辅助系统落地的最佳窗口

---

## 第 3 页：研究目标 — 针对痛点的系统性对策

布局：顶部一句总体目标横幅 → 中部"痛点（红）→ 对策（绿）"4 列上下对比 → 底部一行图片占位（系统体现） → 收尾金句横幅。

**总体目标**

构建教师 / 学生 / 管理三端一体的 AI 教学辅助系统，针对四大痛点提供 **RAG · 知识追踪 · 个性化推荐**三位一体的系统性对策。

**痛点 → 对策 一一对应**

| 痛点 | 对策 | 系统体现 |
|---|---|---|
| ① 备课负担重 | **教师备课辅助** | 章节讲解提纲自动生成（教学目标 / 重难点 / 课堂流程） |
| ② 题库更新慢 | **智能出题** | 按知识点定向生成 4 种题型（单选 / 判断 / 填空 / 简答） |
| ③ 个性化缺位 | **知识追踪 + 推荐** | EMA 动态更新掌握度，识别薄弱知识点并推送针对性练习 |
| ④ 数据成孤岛 | **数据闭环** | 练习 → 评估 → EMA 更新，作答数据自动驱动推荐 |

**收尾金句**：痛点逐一被对策接住 — 形成可量化、可落地、可持续演进的智能教学闭环

> 注：原大纲中的"用户角色与功能用例"页已与本页合并，三端目标在本页通过"系统体现"列体现。

---

## 第 4 页：系统总体架构与技术栈（目标架构）

布局：7 层模块化分层架构 + 1 条横跨全栈的"可观测与评测"侧条，每层左侧色彩标签 + 右侧多个 block（每个 block：标题 + 一句技术副标题）。底部一行数据闭环 + 工业级亮点。

**顶部 5 大特性 标签条**

> AI 原生架构  ·  双服务微服务  ·  Agent + MCP + Skills 三层暴露  ·  全链路可观测  ·  数据闭环

**7 层架构 + 技术栈**

| 层 | 包含的 Block |
|---|---|
| **① 用户层 / User** | 教师 · 学生 · 管理员 · 浏览器（Chrome / Edge）· RBAC 权限（三角色控制） |
| **② 展示层 / Presentation** | Vue 3（组合式 API）· Vite（极速构建）· Element Plus（UI 组件库）· Lucide（图标）· Pinia（状态管理）· ECharts（图表）· SSE 流式渲染 |
| **③ 网关层 / Gateway** | Nginx（反向代理 + 路径路由）· JWT（统一鉴权）· 令牌桶限流（用户级 + 全局） |
| **④ 业务层 / Business（双服务微服务）** | **SpringBoot 3 业务服务**：auth · users · courses · stats（MyBatis + Spring Security + JWT） ⇄ **FastAPI AI 服务**：agents · rag_qa · exercises · lesson_plans · knowledge_tracking · conversations · knowledge_base |
| **⑤ Agent 编排层 / Orchestration** | **LangGraph** 状态机（意图识别 → 任务拆解 → 工具调用 → 反思纠错） · **Agent Skills**（prepare-class / personalized-practice / grade-essay）· **MCP Server**（5 个原子 Tool：search_kb / lesson_outline / generate_exercise / grade_answer / get_mastery） · LangChain Pipeline · Function Calling |
| **⑥ 中间件层 / Middleware** | **Redis**：语义缓存（GPTCache 思路）· 异步任务队列（RQ：kb_index / batch_exercise / eval / summarize）· 令牌桶限流 · 降级标志 · 长期记忆向量（可选） |
| **⑦ AI 模型层 / Models** | **DashScope**：Qwen-Plus（对话生成）· Qwen-Turbo（快速响应）· Qwen-Max（评委 LLM-as-Judge）· text-embedding-v3（向量化 1024 维）· gte-rerank（Cross-Encoder 重排）· enable_search（联网搜索）  ·  **Ollama**：Qwen2.5-7B（本地兜底） |
| **⑧ 数据层 / Data** | **MySQL 8**（业务 8 张表）· **ChromaDB**（向量索引 HNSW）· **Redis 7**（缓存 / 队列 / 限流）· `conversation_summaries`（长期记忆）· 文件系统（原文 / 切片 / Golden Set） |

**横跨全栈：可观测与评测层（侧条）**

> **LangFuse 全链路 Trace**（Agent 节点 / 工具调用 / LLM 调用 三层可视化）  ·  **RAGAS**（4 指标）  ·  **LLM-as-Judge**（Qwen-Max 评委 + 4 套 rubric）  ·  **Golden Set**（100 QA + 50 题 + 30 Agent 任务）  ·  **GitHub Actions CI**（指标退化阻断 PR）

**底部数据闭环说明**

> 学习闭环：学生作答 → `exercise_attempts` → EMA 平滑 → `knowledge_mastery` → 薄弱识别 → 个性化推荐 → 推送学生
>
> 质量闭环：每次代码改动 → CI 跑 Golden Set → RAGAS + LLM-Judge 打分 → 退化 >5% 阻断合并 → 持续保证系统质量不退化

**架构特点（讲点）**

- **AI 原生架构（AI-Native Architecture）**：将 LLM 不确定性通过 Agent 状态机 + 反思纠错 + 评测体系转化为工程确定性
- **双服务微服务**：Java 业务层（事务 / 权限 / 审计的强项） ⇄ Python AI 层（LLM / RAG / Agent 生态的强项），各扬其长
- **能力三层暴露**：MCP 协议（原子能力，可被任意客户端调用）+ Agent Skills（高层工作流，菜谱级封装）+ LangGraph（决策大脑），命中工业界主流 Agent 范式
- **流式优先**：SSE 流式推送，首字延迟 < 1 秒，支持中途打断
- **全链路可观测**：LangFuse Trace 打通 Agent / 工具 / LLM 三层，多维归因分析
- **数据 + 质量双闭环**：学习闭环驱动个性化；质量闭环保证持续不退化
- **模型可替换**：DashScope 主链路 + Ollama 本地兜底，模型不可达时自动降级

**当前已落地范围（中期答辩前）**

- 业务层：FastAPI 单服务（7 个 AI 模块路由）
- 数据层：SQLite 8 表 + ChromaDB（HNSW）
- 编排层：LangChain Pipeline + Prompt 工程 + JSON Schema 结构化输出
- AI 模型层：DashScope 全套（Qwen + text-embedding-v3 + gte-rerank）
- 用户层 / 展示层：三角色 RBAC + Vue 3 全栈

> **阶段四目标架构（第 10-13 周渐进推进，本页用浅色 / 标注呈现）**：网关层 Nginx · Agent 编排 LangGraph + MCP + Skills · 中间件 Redis · AI 模型层 Ollama 兜底 · 业务层 SpringBoot 双服务化 · 可观测与评测层 LangFuse + RAGAS + LLM-Judge + Golden Set + CI Gate

> 说明：本页展示的是**目标架构（阶段四工业级升级完成形态）**，对应阶段四 P0-1 ~ P0-6 共 6 项主线工作的端到端落地形态。

---

## 第 5 页：核心数据库设计与技术亮点

布局：上半 8 表网格（按颜色分 3 组）→ 下半左 ER 关系图（自动生成自 `db.py`）+ 下半右 5 个技术亮点 → 底部数据闭环说明。

**8 张核心数据表（按业务分 3 组着色）**

| 分组 | 表名 | 关键字段 | 业务作用 |
|---|---|---|---|
| 基础数据（蓝） | `users` | id / name / email / role / password_hash | 三角色用户（管理员 / 教师 / 学生） |
| 基础数据 | `sessions` | token / user_id / created_at | 登录态管理 |
| 基础数据 | `courses` | id / title / description / creator_id | 课程基本信息 |
| 基础数据 | `knowledge_points` | id / course_id / point | 课程知识点（自动 + 手动维护） |
| 对话（绿） | `conversations` | id / user_id / course_id / title | 多轮对话会话 |
| 对话 | `messages` | id / conversation_id / role / content / **citations (JSON)** | 对话消息（含引用） |
| 知识追踪（橙） | `knowledge_mastery` ★ | student_id / course_id / knowledge_point / **mastery (REAL)** / attempt_count | EMA 掌握度向量 |
| 知识追踪 | `exercise_attempts` ★ | student_id / exercise_id / **score (REAL)** / **knowledge_points (JSON)** | 作答记录 · 闭环数据 |

**ER 关系示意图（自动生成）**

由 `scripts/export_er_diagram.py` 解析 `backend/app/db.py` 自动生成，输出 `data/er-diagram/er.svg / er.png`，已嵌入 PPT 左下方。

**5 个技术亮点**

| Tag | 说明 |
|---|---|
| **HNSW** | ChromaDB 默认 HNSW 向量索引（`hnsw:space=cosine`）— 高维近似最近邻 O(log n)，千万级片段下毫秒级召回 |
| **UPSERT** | `knowledge_mastery` 复合 UNIQUE `(student_id, course_id, knowledge_point)` — 配合事务保证掌握度记录唯一不重复 |
| **EMA** | α = 0.3 指数平滑：`mastery_new = α · score + (1-α) · old_mastery` — 新作答影响 30%、历史保留 70%，平滑抗抖动 |
| **JSON-in-TEXT** | `messages.citations` / `exercise_attempts.knowledge_points` — TEXT 存 JSON 数组，schema 灵活、应用层按需解码 |
| **BM25 + RRF** | jieba 分词 + `rank_bm25.BM25Okapi` 倒排索引 + RRF (Reciprocal Rank Fusion) 与向量检索结果融合，解决专有名词与缩写不敏感 |

**数据闭环（页脚一行）**

> 学生作答 → `exercise_attempts` 写入 → EMA 平滑更新 `knowledge_mastery` → 识别薄弱知识点 → 个性化推荐 → 推送学生

---

## 第 6 页：用户登录与角色管理

布局：上方一行承接说明；中部 左 登录认证流程图 + 右 三角色 RBAC 权限矩阵；下方 4 点安全设计要点；底部 演示截图占位符 + 金句横幅。

**承接第 5 页**

> 基于第 5 页设计的 `users` + `sessions` 表，实现一套统一的用户认证体系与三角色 RBAC 权限路由控制，支撑后续教师 / 学生 / 管理三端业务的安全访问。

**登录注册流程（左侧流程图）**

```
注册：邮箱 + 密码 + 角色 (teacher / student / admin)
    ↓
PBKDF2-HMAC-SHA256（10 万次迭代）+ 16 字节随机 salt
    ↓
INSERT users (password_hash, password_salt 分字段存储)
─────────────────────────────────────────────────────
登录：邮箱查询 users → 同 salt + 算法重新 hash → 比对 password_hash
    ↓
生成 session token → INSERT sessions
    ↓
前端 localStorage 存 token → 后续请求 Authorization: Bearer xxx
    ↓
后端 require_user 依赖注入校验 token → 注入当前 user 上下文
```

**三角色 RBAC 权限矩阵（右侧表）**

| 角色 | 可访问路由（前端 `router.beforeEach` 守卫） | 主要业务能力 |
|---|---|---|
| **教师 (teacher)** | `/courses` · `/courses/new` · `/knowledge-base` · `/lesson-outline` · `/exercises` | 知识库管理 / 课程创建 / 备课 / 出题 / 学情分析 |
| **学生 (student)** | `/courses` · `/qa` · `/exercises/session` · `/personalized` | RAG 问答 / 完成练习 / 查看掌握度 / 个性化推荐 |
| **管理员 (admin)** | `/admin` · `/knowledge-base` · `/courses` | 用户管理 / 课程管理 / 数据看板 / 全局知识库 |

**安全设计要点（4 点紧凑卡片）**

- **PBKDF2-HMAC-SHA256 + 10 万次迭代**：NIST 推荐的密码哈希算法，抗暴力破解
- **每用户独立 16 字节随机 salt**：彻底防止彩虹表攻击
- **`password_hash` / `password_salt` 分字段存储**：单字段泄露不可还原
- **双层路由守卫**：前端 `router.beforeEach`（UX 体验）+ 后端 `require_user` 依赖注入（安全核心）

**演示截图（占位符）**

| # | 截图 | 操作步骤 / 截取范围 |
|---|---|---|
| 1 | 登录 / 注册页（左右分栏品牌设计） | `/login` `Login.vue`，含 Tab 切换"账户登录 / 新用户注册" + feature badges（RAG 增强问答 / 自动练习生成 / 实时学情分析） |

**底部 banner**

> 一套统一的 PBKDF2 + 三角色 RBAC 认证体系，支撑教师 / 学生 / 管理三端的安全访问

---

## 第 7 页：教师侧功能总览

布局：上半 任务书要求 → 系统实现映射 表格；下半 三大核心模块卡片。

**任务书要求 → 系统实现映射**

| 任务书要求 | 系统实现模块 | 状态 |
|---|---|---|
| 基于课程大纲和本地知识库自动生成章节知识讲解提纲 | 模块 2：教师备课辅助 | ✓ |
| 基于课程大纲和本地知识库自动生成基础实训练习 | 模块 2：备课中"基础实训任务"字段 | ✓ |
| 按知识点自动生成练习题与测试题 | 模块 3：智能出题 | ✓ |
| 提供参考答案 | 模块 3：每题附标准答案 + 评分标准 | ✓ |

**三大核心模块（详见后续 3 页）**

| 编号 | 模块名 | 一句话 |
|---|---|---|
| ① | **知识库管理 + RAG 问答** | 上传 PDF / Word / Markdown / URL → 自动解析切分 → 向量化入库 → 混合检索 + 重排 + 流式问答 |
| ② | **教师备课辅助** | 输入：课程 + 章节 + 课时 + 知识点；输出：6 大模块结构化讲解提纲 |
| ③ | **智能出题** | 题型：单选 / 判断 / 填空 / 简答；按章节 + 知识点 + 难度三维定向；标准答案 + 知识点标签 + 评分标准 |

---

## 第 8 页：模块 1 — 知识库管理与 RAG 问答

布局：上半 离线知识库构建 pipeline + 在线问答 pipeline；中部 一行核心特性；下半 3 张演示截图（已截）。

**RAG Pipeline · 离线知识库构建**

```
文档上传 (PDF / Word / MD / URL)
    ↓
解析 (PyPDFLoader / python-docx / Markdown / 网页正文提取)
    ↓
切分 (规则切分 ⇄ LLM 辅助语义切分，超长回退)
    ↓
jieba 中文分词
    ↓
Embedding (DashScope text-embedding-v3, 1024 维)
    ↓
ChromaDB (HNSW 索引，按课程隔离持久化)
```

**RAG Pipeline · 在线问答检索增强**

```
用户提问
    ↓
查询改写 + jieba 分词
    ↓
混合检索（并行召回）
    ├── 向量召回 (ChromaDB Top-K)
    └── BM25 召回 (Top-K)
    ↓
融合去重 (RRF) → DashScope gte-rerank 重排序 (Cross-Encoder)
    ↓
Top-N 上下文 + 对话历史滑窗 10 条 + 联网搜索结果
    ↓
Prompt 拼装 → Qwen-Plus 流式生成
    ↓
SSE 推送前端 → 解析引用角标 [1][2] → 展示来源卡片
```

**核心特性（一行紧凑标签）**

> ✓ BM25 + 向量混合检索   ✓ Cross-Encoder 重排   ✓ 滑窗 10 条多轮记忆   ✓ DashScope 联网搜索   ✓ SSE 流式（首字 < 1s）   ✓ RAGAS 评测

**三张演示截图**

| # | 截图 | 操作步骤 | 截取范围 |
|---|---|---|---|
| 1 | 知识库上传与文档管理 | `/knowledge-base` `KnowledgeBaseUpload.vue`，上传 1 份 PDF | 已上传文档列表 + 切片数 + 处理状态 |
| 2 | 知识库检索与召回结果 | `/knowledge-base/search` `KnowledgeBaseSearch.vue`，输入"什么是 RAG" | 混合检索结果 + rerank 分数 + 来源片段 |
| 3 | RAG 多轮问答（含引用） | `/qa` `RagQa.vue`，提问"对比 BM25 与向量检索" | 含 [1][2] 引用 + 联网来源 + 流式生成中的对话气泡 |

---

## 第 9 页：模块 2 — 教师备课辅助（章节讲解提纲）

布局：左 1/3 输入参数 + 生成流程；右 2/3 6 大输出模块（2×3 网格）；底部 4 张演示截图（已截）。

**输入参数**

| 参数 | 示例 |
|---|---|
| 课程 | 大模型应用开发 |
| 章节 | 第 3 章 RAG 检索增强生成 |
| 课时 | 90 分钟 |
| 知识点 | 向量检索 / BM25 / Rerank |

**生成流程**

> ① 检索知识库 Top-N 片段 → ② 拼装 Prompt + Few-shot → ③ Qwen-Plus 调用 → ④ 6 大模块结构化输出 → ⑤ 教师审核 / 微调 / 导出

**6 大模块结构化输出（2×3 网格）**

| # | 模块 | 内容 |
|---|---|---|
| ① | 教学目标 | 可量化、可达成的学习成果 |
| ② | 重点难点 | 核心知识点 + 易错环节标注 |
| ③ | 课堂流程 | 导入 → 讲解 → 演示 → 实训 → 总结 |
| ④ | 基础实训任务 | 任务驱动 + 步骤指导 + 验收标准 |
| ⑤ | 考核建议 | 提问 + 实训提交 + 简答评分 |
| ⑥ | 知识来源 | 知识库片段引用 [1][2][3] 含页码 |

**关键技术（讲点）**

- **检索阶段**：基于章节标题与知识点做混合检索，获取 Top-N 相关片段
- **生成阶段**：JSON Schema 约束输出结构，Few-shot 示例引导生成质量
- **知识来源回填**：将检索到的片段元信息（文档名 / 页码）写入输出，便于教师溯源核对

**核心价值（页脚 banner）**

> 备课时间：从"几小时整理素材" → "10 秒生成 + 微调"，输出可直接用于实训课堂

---

## 第 10 页：模块 3 — 智能出题

布局：上半 4 题型卡片；中部 生成流程 pipeline；下半 一行 Prompt 工程要点 + 3 张演示截图（已截）。

**支持 4 种题型**

| 题型 | 字段结构 | 评测方式 |
|---|---|---|
| 单选题 (single_choice) | stem + options[4] + answer | 选项精确匹配 |
| 判断题 (true_false) | stem + answer (bool) | 布尔值匹配 |
| 填空题 ★ (fill_in_blank) | stem + blanks[多空 + 替代答案] | 逐空 + alternatives + 忽略大小写 |
| 简答题 (short_answer) | stem + reference_answer + rubric | 关键词 + 语义相似度（规划） |

**生成流程**

```
教师选参数（课程 · 题型 · 数量 · 难度 · 知识点）
    ↓
按知识点检索知识库 Top-N 片段
    ↓
组装 Prompt（JSON Schema + Few-shot 示例）
    ↓
Qwen-Plus 调用
    ↓
后端校验 + 知识点回填
    ↓
持久化 + 前端列表展示
```

**Prompt 工程要点（一行紧凑）**

> JSON Schema 结构化输出 · Few-shot 示例 · 难度指令 · 知识点定向 · 检索片段防幻觉

**填空题特色实现**

- `blanks` 数组结构：`[{index, answer, alternatives: ["同义词1", "同义词2"]}]`
- 评测时逐空匹配 + 替代答案匹配 + 忽略大小写，提升评分宽容度

**三张演示截图**

| # | 截图 | 操作步骤 |
|---|---|---|
| 1 | 出题表单 | `/exercises` `ExerciseGeneration.vue`，选课程→题型(混合)→数量(10)→难度(中)→勾选 3 个知识点 |
| 2 | 生成结果列表 | 点"开始生成" → 4 种题型混合的题目列表（题干 + 题型徽章 + 难度标签） |
| 3 | 题目详情 + 答案 | 点列表中任一题 → 弹窗 / 详情：题干 + 选项 / 填空 + 标准答案 + 知识点标签 + 评分标准 |

---

## 第 11 页：Agent 编排层 — LangGraph 多智能体 + MCP + Skills 三层暴露

布局：上半 三层能力暴露架构图（自底向上：MCP Server 原子能力 → Agent Skills 工作流 → LangGraph 决策大脑）；中部 LangGraph 状态机流程图 + 多智能体协作示意；下半 5 个 MCP 工具表 + 一行核心特性 + 落地说明。

**承接第 4 页**

> 第 4 页架构图中的「⑤ Agent 编排层」放大展开 — 这一层是把"LLM 的不确定性"转化为"工程确定性"的核心引擎，也是阶段四 P0-3 项工业级升级的主线工作。

**设计思想 · 能力的三层暴露（命中工业界主流 Agent 范式）**

将系统能力按照"原子化 → 流程化 → 智能化"分三层暴露，既保证灵活组合，又支持高层封装与自主决策。

| 层 | 抽象 | 角色 | 系统体现 |
|---|---|---|---|
| **③ LangGraph** | 决策大脑 | 智能体编排（多 Agent 协作） | 状态机：意图识别 → 任务拆解 → 工具调用 → 反思纠错 |
| **② Agent Skills** | 工作流（菜谱级） | 高层场景封装 | `prepare-class` / `personalized-practice` / `grade-essay` |
| **① MCP Server** | 原子能力（协议级） | 工具底座（任意客户端可用） | 5 个 Tool：`search_kb` / `lesson_outline` / `generate_exercise` / `grade_answer` / `get_mastery` |

> 类比：**MCP = 食材  ·  Skills = 菜谱  ·  LangGraph = 主厨** — 三层职责清晰、各司其职

**LangGraph 状态机（5 节点 + 反思回边）**

```
[用户输入]
    ↓
[① 意图识别 Node]  Qwen-Plus 判定任务类型（备课 / 出题 / 答疑 / 评测 / 推荐）
    ↓
[② 任务拆解 Node]  把高层目标拆成原子步骤（DAG）
    ↓
[③ 工具调用 Node]  Function Calling → 路由到 MCP Tool / Skill / 子 Agent
    ↓                                                     ↑
[④ 反思纠错 Node]  Schema 校验 + LLM-as-Judge ──失败重试──┘
    ↓
[⑤ 输出聚合 Node]  SSE 流式推送前端
```

**多智能体协作 · 典型场景：学生提问 → 个性化推荐闭环**

| Agent | 角色 | 主要工具 |
|---|---|---|
| **检索 Agent** | 从知识库召回相关片段 | `search_kb`（BM25 + 向量混合 + Rerank） |
| **答疑 Agent** | 基于片段生成答案 + 引用回填 | Qwen-Plus 流式 + 角标 [1][2] |
| **学情 Agent** | 拉取学生知识点掌握度 | `get_mastery`（EMA 平滑后向量） |
| **推荐 Agent** | 识别薄弱点 + 定向出题 | `generate_exercise`（按薄弱知识点） |
| **反思 Agent** | 校验输出 + 触发重试 | LLM-as-Judge + JSON Schema |

**MCP Server 原子工具（5 个，标准协议暴露）**

| Tool | 输入 | 输出 | 业务作用 |
|---|---|---|---|
| `search_kb` | query + course_id + top_k | 片段列表 + 引用元信息 | 知识库混合检索 |
| `lesson_outline` | 课程 + 章节 + 知识点 + 课时 | 6 大模块结构化讲解提纲 | 教师备课 |
| `generate_exercise` | 题型 + 难度 + 知识点 + 数量 | 4 类题目 JSON 数组 | 智能出题 |
| `grade_answer` | 题目 + 学生答案 + rubric | 得分 + 评语 + 知识点反馈 | 主观题评分 |
| `get_mastery` | student_id + course_id | 知识点 → 掌握度 [0,1] | 学情分析 / 推荐 |

**Agent Skills（3 个高层工作流，菜谱级封装）**

| Skill | 串联工具链 | 面向场景 |
|---|---|---|
| `prepare-class` | `search_kb` → `lesson_outline` | 教师"一键备课" |
| `personalized-practice` | `get_mastery` → `generate_exercise` | 学生"个性化练习" |
| `grade-essay` | `grade_answer` ×N → 聚合反馈 | 主观题"批量批改" |

**核心特性（一行紧凑标签）**

> ✓ 状态机可视化   ✓ 反思纠错自愈   ✓ MCP 标准协议（Claude Desktop / Cursor 等可直接调用）   ✓ Skills 菜谱级封装   ✓ 多 Agent 异步协作   ✓ LangFuse 全链路 Trace

**落地说明**

- **当前已落地（中期答辩前）**：LangChain Pipeline + Function Calling + JSON Schema 结构化输出（已支撑教师侧三大模块）
- **阶段四升级（W11 ~ W12）**：迁移到 LangGraph 状态机 + 部署 MCP Server（5 个 Tool）+ 抽象 3 个 Agent Skills，对应任务清单 P0-3 项

**核心价值（页脚 banner）**

> 用 **MCP** 标准化原子能力 · 用 **Skills** 封装常用工作流 · 用 **LangGraph** 做智能决策 — 把 LLM 的不确定性转化为工程的确定性

---

## 第 12 页：进度对照与阶段性总结

布局：左 65% 进度对照表 + 完成度量化指标卡片；右 35% 阶段性核心成果列表（已完成 / 超额完成 / 结论）。

**进度对照（对照任务书 16 周安排）**

| 周次 | 任务书安排 | 实际完成情况 | 状态 |
|---|---|---|---|
| 第 1-2 周 | 文献调研 / 开题 / 外文翻译 | 完成开题报告、文献综述、2 篇外文翻译 | ✓ |
| 第 3-5 周 | 需求分析 / 概要设计 / 详细设计 / 数据库设计 | 完成 6 层架构设计、8 张核心数据表设计、API 规范定义 | ✓ |
| 第 6-8 周 | 教师侧功能模块编码实现 | 完成知识库管理 + 备课提纲 + 智能出题三大模块 | ✓ |
| **第 9 周** | **中期检查** | **当前阶段** | ★ |
| 第 10-12 周 | 学生侧 / 管理侧功能模块 | 已提前完成知识追踪与个性化推荐闭环 | ● 部分完成 |
| 第 13-14 周 | 代码测试 / 论文撰写 / 查重 | 待开始 | □ |
| 第 15-16 周 | PPT 制作 / 预答辩 / 正式答辩 | 进行中 | □ |

**完成度量化指标（卡片）**

| 维度 | 数据 |
|---|---|
| 后端 router 模块数 | 9（auth / courses / knowledge_base / rag_qa / exercises / conversations / lesson_plans / knowledge_tracking / agents） |
| 后端 service 模块数 | 11 |
| 前端页面数 | 11 |
| 数据库表数 | 8 |
| 已支持题型 | 4（单选 / 判断 / 填空 / 简答） |
| 已实现 RAGAS 指标 | 4（faithfulness / answer_relevancy / context_precision / context_recall） |

**阶段性核心成果**

- **已完成**
  - 教师侧 3 大模块全部完成；任务书教师侧目标 100% 达成
- **超额完成（不在原计划内）**
  - 混合检索（BM25 + 向量）+ Rerank 重排序
  - 多轮对话记忆（滑动窗口 + 持久化）
  - 联网搜索（DashScope `enable_search` + 角标引用）
  - 填空题题型支持（多空位 + 替代答案）
  - 大模型辅助语义切分
  - RAGAS 评测接口
  - 知识追踪 + 个性化推荐闭环（原属第 10-12 周计划）
- **结论**
  - 进度严格符合任务书要求且部分超前，可保质保量完成毕业设计

---

## 第 13 页：剩余工作计划（第 9 周 → 第 16 周）

布局：左 8 项工作清单；右 W9 ~ W16 甘特图（每条彩色 bar 对应左侧编号）；底部一行金句横幅 + 一行论文对位小字。

**后续 8 周工作安排**

| # | 待完成模块 | 核心内容 | 预计周次 |
|---|---|---|---|
| ① | 主观题高级评分 | **LLM-as-Judge（Qwen-Max 评委）** + 语义相似度加权融合，5 组样本验证 | W9 ~ W10 |
| ② | 学情分析 | 错题聚合、班级统计、薄弱知识点识别 + ECharts 可视化 | W10 ~ W11 |
| ③ | 管理端数据看板 | 多维图表：练习参与人数 / 正确率 / 知识点掌握分布 | W10 ~ W11 |
| ④ | **评测体系 + 可观测性（亮点）** | **Golden Set（100 QA + 50 题）+ RAGAS 4 指标 + LangFuse 全链路 Trace** | W11 ~ W12 |
| ⑤ | 系统稳定性 + 性能优化 | 异常处理、SSE 重连、Redis 缓存加速、并发与压力测试 | W12 ~ W13 |
| ⑥ | 系统测试 | 功能测试 + 性能测试 + 用户测试 + CI 自动回归 | W13 ~ W14 |
| ⑦ | 论文撰写与查重 | 毕业设计论文（含评测实验章节）+ 学校查重 | W13 ~ W15 |
| ⑧ | PPT + 预答辩 + 修改 | 正式答辩材料整理 | W15 ~ W16 |

**收尾金句（页脚 banner）**

> 任务书剩余项 + 论文按周推进；评测 / 可观测性作为论文核心实验章节，提供量化数据支撑

**论文对位说明（金句下方一行小字）**

> 第 ④ 项「评测体系 + 可观测性」对应论文中「系统评测」章节，提供 Golden Set 上的量化对比数据，让"系统能用"升级为"系统好用、可衡量"。

> 注：原大纲中的"风险与应对"和"保障措施"两节已删除，本页只展示后续工作清单 + 甘特图 + 论文对位说明。

---

## 第 14 页：致谢

**衷心感谢**

- 鸣谢指导教师 **XXX 老师**，在选题方向、技术路线选择与项目推进中的悉心指导
- 感谢计算机科学与技术学院全体老师的悉心教诲
- 感谢同学们在开发过程中的讨论与协助
- 感谢家人对学业的长期支持

**请各位答辩老师批评指正！**

李鑫  ·  2026 年

---

## 附录：与原大纲的差异说明（备查）

| 变更 | 说明 |
|---|---|
| 总页数 13 → 12 | 删除原"用户角色与功能用例"页，三端目标合并到"研究目标"的"系统体现"列 |
| 架构 + 技术栈 合并 | 原第 5、6 页合并为"系统总体架构与技术栈"一页，技术栈以 block 形式嵌入 6 层架构 |
| 数据库页加技术亮点 | 增加 5 个技术亮点（HNSW / UPSERT / EMA / JSON-in-TEXT / BM25+RRF）；EMA α 修正为 0.3（与代码 `EMA_ALPHA = 0.3` 一致） |
| 第 11 页删风险/保障 | 删除"风险与应对""保障措施"两节，只保留后续工作清单 + 甘特图 + 一句话总结 |
| 章节序号 | 全部不带"一、二、..."前缀，与 PPT 实际标题保持一致 |
| 表情符号 | 已替换为简单符号（★ ◆ ✓ ① ② 等），不再使用 💡📷📥📋🔧🎯🛡️🎓📚📝🚀📈🔄 等花哨 emoji |
| 总页数 12 → 13 | 新增第 6 页"用户登录与角色管理"，承接 `users` / `sessions` 表，介绍 PBKDF2-HMAC-SHA256 哈希 + 三角色 RBAC + 双层路由守卫 |
| 第 12 页剩余工作扩展 | 由 7 项增至 8 项，加入第 ④ 项"评测体系 + 可观测性"作为工业级亮点（包装为论文实验章节），并加论文对位小字，避免老师质疑做不完 |
| 第 4 页底部加范围说明 | 明确"当前已落地"vs"阶段四目标"两块，避免老师误以为目标架构都已经做完 |
| 总页数 13 → 14 | 新增第 11 页"Agent 编排层 — LangGraph 多智能体 + MCP + Skills 三层暴露"，作为第 4 页架构图中「⑤ Agent 编排层」的放大展开页，原 11/12/13 页顺延为 12/13/14 页 |
| 第 11 页核心内容 | ① 三层能力暴露设计（MCP 原子能力 / Skills 菜谱 / LangGraph 决策大脑） + ② LangGraph 5 节点状态机（含反思回边） + ③ 多智能体协作场景表（检索 / 答疑 / 学情 / 推荐 / 反思 5 个 Agent） + ④ 5 个 MCP Tool 工具表 + ⑤ 3 个 Agent Skills 封装 + ⑥ 当前已落地 vs 阶段四升级范围 |
