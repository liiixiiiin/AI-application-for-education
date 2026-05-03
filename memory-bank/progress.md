# 进度记录

## 阶段一：需求分析与架构设计 ✅
- 项目目录结构：`frontend/` + `backend/` + `data/`
- 输出：[mvp-scope.md](memory-bank/mvp-scope.md) / [api-conventions.md](memory-bank/api-conventions.md)

## 阶段二：知识库构建与 RAG Pipeline ✅
- 知识库上传与切分（规则 + 大模型辅助 + 超长回退）
- 混合检索（向量 + BM25 + jieba）+ DashScope Rerank
- 知识库管理（查看 / 编辑 / 删除 / 检索 / 网页 URL 解析）
- RAG 问答最小闭环 + SSE 流式输出 + RAGAS 评测接口
- 输出规范：[knowledge-base-guidelines.md](memory-bank/knowledge-base-guidelines.md) / [retrieval-spec.md](memory-bank/retrieval-spec.md) / [rag-qa-spec.md](memory-bank/rag-qa-spec.md)

## 阶段三：智能出题、评测与用户管理 ✅
- 出题：单选 / 判断 / 填空（多空位 + 替代答案）/ 简答
- 评测：客观题规则匹配 + 简答评分标准
- 用户与课程：注册 / 登录 / 三角色 / 课程 CRUD
- 全流程联调：登录 → 上传 → 问答 → 生成 → 评测
- 多轮对话记忆（方案 C）：`conversations` / `messages` 表 + 滑动窗口注入 Prompt
- 联网搜索：DashScope `enable_search` + `search_options` + 角标引用 + 来源卡片
- 输出规范：[exercise-generation-spec.md](memory-bank/exercise-generation-spec.md) / [exercise-grading-spec.md](memory-bank/exercise-grading-spec.md) / [user-course-spec.md](memory-bank/user-course-spec.md)

## 阶段三扩展（已完成额外优化）
- 课程知识点管理：自动生成 + 手动增删改查 + 基于知识点定向出题
- 知识追踪与个性化推荐：EMA 掌握度 + 薄弱识别 + 推荐练习生成
- 教师备课辅助：章节讲解提纲（教学目标 / 重难点 / 课堂流程 / 实训任务 / 考核建议 / 知识来源）

## 阶段四：工业级工程化升级 + 剩余扩展模块（第 10-13 周，规划中）

> 答辩前的核心冲刺；详细周次甘特与工时见 [implementation-plan.md](memory-bank/implementation-plan.md) §4。

工业级主线（必须在答辩前完成）：
- ✅ P0-1：LangGraph Agent 重构（[agent-spec.md](memory-bank/agent-spec.md)）—— 第 10 周
  - 状态机已落地：`backend/app/agents/`（`intent_router → planner → tool_executor↺ → reflector → aggregator`）
  - 6 个 Tool 适配现有 service：`search_kb` / `lesson_outline` / `generate_exercise` / `grade_answer` / `get_mastery` / `web_search`
  - 接入 6 反思维度（`json_schema` / `format_check` / `kp_match` / `coverage` / `grade_consistency` / `time_budget`），失败 ≤1 次回 planner
  - HTTP 入口：`POST /api/v1/agents/run`（同步）+ `POST /api/v1/agents/run/stream`（SSE：run_start / intent / plan / tool_start / tool_end / reflect / done）
  - 烟测：`scripts/test_agent.py` 6 条用例 → 意图命中 6/6、工具命中 6/6、成功 6/6（无 LLM 时降级到规则路由依然可用）
- 🔲 P0-2：MCP Server + Agent Skills 双层（[mcp-server-spec.md](memory-bank/mcp-server-spec.md) / [skills-spec.md](memory-bank/skills-spec.md)）—— 第 11 周
- 🔲 P0-3：评测体系 + LangFuse Trace + CI 阻断（[evaluation-spec.md](memory-bank/evaluation-spec.md)）—— 第 12 周
- 🔲 P0-4：SpringBoot 业务层独立（[microservice-spec.md](memory-bank/microservice-spec.md)）—— 第 13 周上半
- 🔲 P0-5：Redis 中间件层（[redis-spec.md](memory-bank/redis-spec.md)）—— 第 13 周下半
- 🔲 P0-6：分层记忆方案（[memory-spec.md](memory-bank/memory-spec.md)）—— 第 13 周收尾
- 🔲 P1（可选）：Ollama 本地推理 + 模型路由

副线（剩余扩展模块，穿插完成）：
- 🔲 主观题高级评分（与 P0-1 同步）
- 🔲 学情分析（与 P0-3 同步）
- 🔲 管理端数据看板（与 P0-4 同步）

## 阶段五：系统测试 + 论文 + 答辩（第 14-16 周）
- 🔲 第 14 周：系统测试 + 论文初稿
- 🔲 第 15 周：论文修改 + PPT + 预答辩
- 🔲 第 16 周：最终修改 + 正式答辩

---

## 文档重构记录（2026-04）
- 新增 7 份 spec：agent / mcp-server / skills / evaluation / microservice / redis / memory
- 删除迁移内容：
  - `rag-qa-spec.md` §4 RAGAS 接口 → `evaluation-spec.md`
  - `rag-qa-spec.md` §5.4-5.7 → `memory-spec.md`
  - `tech-stack.md` 已实现的"知识追踪 / 个性化推荐"占位
  - `architecture.md` 旧的"待实现模块（规划）"
  - `design-document.md` 第 11 章"进度安排（10 周）"（统一由本文承载）
  - `implementation-plan.md` "已完成的额外优化"段落（统一由本文承载）
  - `mvp-scope.md` 废弃可选项与已完成清单去重
- 单一信息源原则确立：进度 → progress.md；阶段计划 → implementation-plan.md；评测 → evaluation-spec.md；记忆细节 → memory-spec.md
