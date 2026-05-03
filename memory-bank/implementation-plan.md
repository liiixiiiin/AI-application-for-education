# 实施计划

## 总体节奏（16 周毕设）

- 第 1-2 周：调研开题 ✅
- 第 3-5 周：需求分析与架构设计 ✅
- 第 6-8 周：教师侧编码（MVP 主体） ✅
- **第 9 周：中期检查 🟡（当前阶段）**
- **第 10-13 周：阶段四 工业级工程化升级 + 剩余扩展模块（4 周冲刺）**
- **第 14-15 周：阶段五 系统测试 + 论文撰写 + 预答辩**
- **第 16 周：论文修改 + 正式答辩**

工业级升级**必须在答辩前完成**，作为答辩与简历投递的核心亮点。

> 进度详情见 [progress.md](memory-bank/progress.md)；MVP 与扩展功能清单见 [mvp-scope.md](memory-bank/mvp-scope.md)。

---

## 阶段一：需求分析与架构设计 ✅
- 需求范围与不做项 → [mvp-scope.md](memory-bank/mvp-scope.md)
- 项目结构与 API 命名规范 → [api-conventions.md](memory-bank/api-conventions.md)

## 阶段二：知识库构建与 RAG Pipeline ✅
- 知识库切分规则 → [knowledge-base-guidelines.md](memory-bank/knowledge-base-guidelines.md)
- 向量化与混合检索 → [retrieval-spec.md](memory-bank/retrieval-spec.md)
- RAG 问答最小闭环 + SSE 流式输出 → [rag-qa-spec.md](memory-bank/rag-qa-spec.md)

## 阶段三：智能出题、评测与用户管理 ✅
- 题型与生成规范 → [exercise-generation-spec.md](memory-bank/exercise-generation-spec.md)
- 评测规则 → [exercise-grading-spec.md](memory-bank/exercise-grading-spec.md)
- 用户与课程管理 → [user-course-spec.md](memory-bank/user-course-spec.md)
- 多轮对话记忆（方案 C） → [rag-qa-spec.md](memory-bank/rag-qa-spec.md) §4
- 知识追踪与个性化推荐（EMA + 薄弱识别 + 推荐生成）
- 教师备课辅助（章节讲解提纲）

---

## 阶段四：工业级工程化升级 + 剩余扩展模块（第 10-13 周，4 周冲刺）

> 这是答辩前的核心冲刺阶段。工业级升级 6 项（P0-1 ~ P0-6）为主线；剩余 3 个扩展模块（主观题评分 / 学情分析 / 数据看板）穿插完成。每一步对应一份 spec 文档。

### 4.1 周次甘特

| 周次 | 主线（工业级 P0） | 副线（剩余扩展模块） |
|---|---|---|
| **第 10 周** | P0-1 LangGraph Agent 重构 | 主观题高级评分（接入 grade_answer 工具时同步落地） |
| **第 11 周** | P0-2 MCP Server + Agent Skills 双层 | （工业级主线满载） |
| **第 12 周** | P0-3 评测体系 + LangFuse Trace + CI 阻断 | 学情分析（基于评测产出的统计数据自然延伸） |
| **第 13 周** | P0-4 SpringBoot + P0-5 Redis + P0-6 分层记忆 | 管理端数据看板（SpringBoot stats 接口 + 前端 ECharts） |

### 4.2 工业级主线（P0-1 ~ P0-6）

#### 步骤 P0-1：LangGraph Agent 重构 🔲（第 10 周）
- 设计依据：[agent-spec.md](memory-bank/agent-spec.md)
- 产出：`backend/app/agents/`（状态机节点 / 工具适配 / 反思器）
- 替换：原 `agents.py` 路由占位 → 真实 Agent 入口
- 验证：30 条 Agent Golden Set 任务成功率 ≥90%、意图识别命中率 ≥90%

#### 步骤 P0-2：MCP Server + Agent Skills 双层 🔲（第 11 周）
- 设计依据：[mcp-server-spec.md](memory-bank/mcp-server-spec.md) + [skills-spec.md](memory-bank/skills-spec.md)
- 产出：
  - `backend/app/mcp/server.py`（MCP Server 入口，5 个原子 Tool）
  - `backend/skills/{prepare-class,personalized-practice,grade-essay}/SKILL.md`
- 验证：mcp inspector 列出 5 个 Tool 并各调用一次成功；Cursor / Claude Desktop 实际接入完成 1 次备课请求

#### 步骤 P0-3：评测体系 + LangFuse Trace 🔲（第 12 周）
- 设计依据：[evaluation-spec.md](memory-bank/evaluation-spec.md)
- 产出：
  - Golden Set：100 QA + 50 题 + 30 Agent 任务（`data/evaluation/golden-set/`）
  - 4 套 rubric（`data/evaluation/rubrics/`）
  - 评测脚本 `scripts/run_evaluation.py`
  - LangFuse 装饰器接入核心 service
  - GitHub Actions workflow `.github/workflows/evaluation.yml`
- 验证：CI 在故意制造退化的 PR 上能阻断；LangFuse 控制台可看到三层 Trace

#### 步骤 P0-4：SpringBoot 业务层独立 🔲（第 13 周上半）
- 设计依据：[microservice-spec.md](memory-bank/microservice-spec.md)
- 产出：
  - `backend-java/`（SpringBoot 3 + MyBatis + MySQL + Spring Security + JWT）
  - 迁移 auth / users / courses / stats 四个模块
  - SQLite → MySQL 数据迁移脚本
  - Nginx 反向代理（或 Vite proxy）
- 验证：登录 → 创建课程 → RAG 问答 → 评测全链路通；JWT 双服务透传 OK

#### 步骤 P0-5：Redis 中间件层 🔲（第 13 周下半，可与 P0-4 并行）
- 设计依据：[redis-spec.md](memory-bank/redis-spec.md)
- 产出：语义缓存 + 4 类异步任务队列 + 用户级和全局令牌桶限流 + DashScope 故障降级标志
- 验证：100 次重复 query 仅 1 次穿透 LLM；单用户 1 分钟 31 次调用第 31 次 429；mock DashScope 故障 flag 写入

#### 步骤 P0-6：分层记忆 🔲（第 13 周收尾）
- 设计依据：[memory-spec.md](memory-bank/memory-spec.md)
- 产出：`conversation_summaries` 表 + 向量索引 + 摘要触发 worker + 长期记忆召回注入
- 验证：25 条对话触发摘要写入；同主题新对话能召回历史摘要；跨用户严格隔离

#### 步骤 P1（可选）：本地推理 + 模型路由 🔲
- Ollama 跑 Qwen2.5-7B + DashScope 故障兜底；不写独立 spec
- 时间紧时砍

### 4.3 副线（剩余扩展模块）

#### 主观题高级评分 🔲（第 10 周穿插）
- 实施依据：[exercise-grading-spec.md](memory-bank/exercise-grading-spec.md) §3.2
- 与 P0-1 同步：`grade_answer` 工具内部从规则匹配升级为"语义相似度 + 大模型判分加权融合 + 多要点拆分"
- 验证：5 组不同质量答案，评分梯度合理

#### 学情分析 🔲（第 12 周穿插）
- 错题聚合 / 知识点掌握趋势 / 班级层面统计
- 数据源：`exercise_attempts` + `knowledge_mastery` + 评测体系产出
- 验证：30 条模拟答题记录可正确生成统计报告

#### 管理端数据看板 🔲（第 13 周穿插）
- 后端聚合：由 P0-4 的 SpringBoot `stats` 模块承载
- 前端 ECharts：参与人数 / 正确率 / 知识点掌握分布
- 验证：模拟数据下图表展示完整

### 4.4 工作量估算

| 步骤 | 工时 | 关键依赖 |
|---|---|---|
| P0-1 LangGraph Agent + 主观题评分 | 6-8 天 | 现有 service 层稳定 |
| P0-2 MCP + Skills | 5-6 天 | P0-1 工具适配层就绪 |
| P0-3 评测 + Trace + 学情分析 | 5-6 天 | Golden Set 标注（人工 1.5 天） |
| P0-4 SpringBoot + 数据看板 | 6-7 天 | MySQL 部署 |
| P0-5 Redis | 3-4 天 | Redis 部署，可与 P0-4 并行 |
| P0-6 分层记忆 | 2-3 天 | P0-5 异步队列就绪 |
| 合计 | 27-34 天 ≈ **4 周** | 单人 30-40 h/周 |

### 4.5 风险与降级

若 4 周吃紧，按以下顺序保留 / 砍除：

| 优先级 | 项 | 砍除影响 |
|---|---|---|
| 🟢 必保 | P0-1 / P0-2 / P0-3 / P0-4 | 命中 JD 关键词最广，简历核心 |
| 🟡 优先保 | 主观题评分 / 学情分析 | 任务书要求 |
| 🟠 可降级 | P0-5 Redis 限流（保缓存与队列） | 影响小 |
| 🟠 可降级 | 数据看板（仅留接口，前端用静态数据） | 影响中 |
| 🔴 可砍 | P0-6 分层记忆 / P1 Ollama | 答辩后再补 |

---

## 阶段五：系统测试 + 论文 + 答辩（第 14-16 周）

### 第 14 周：系统测试 + 论文初稿
- 端到端测试：完整流程跑 30 个用户场景，覆盖三角色
- 评测结果归档：跑全 Golden Set，把指标写入论文
- 论文初稿：架构图 / 关键技术 / 评测数据 / 截图素材

### 第 15 周：论文修改 + PPT + 预答辩
- 论文查重 + 修改
- 答辩 PPT 制作（沿用并升级 [中期答辩PPT大纲.md](中期答辩PPT大纲.md)）
- 参加预答辩，记录改进点

### 第 16 周：最终修改 + 正式答辩
- 论文最终修改
- 答辩演示脚本与彩排
- 正式答辩
