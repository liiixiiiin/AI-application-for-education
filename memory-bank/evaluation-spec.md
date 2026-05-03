# 评测与可观测性规范（P0-3 输出）

## 1. 设计目标

将"评测"从一次性脚本升级为可持续运行的质量保证机制：
- 每次代码改动自动跑回归
- 全链路 Trace 可视化定位失败
- 不达标自动阻断 PR 合并
- 论文与简历提供量化数据支撑

替代并迁移：原 [memory-bank/rag-qa-spec.md](memory-bank/rag-qa-spec.md) §4 RAGAS 评测接口已迁移至本文。

## 2. 三层评测体系

### 2.1 第一层 RAGAS 自动化指标
- 测对象：RAG 链路（检索质量 + 生成忠实度）
- 指标：`faithfulness` / `answer_relevancy` / `context_precision` / `context_recall`
- 评估对象：Golden Set 中的 100 条 QA
- 执行方式：批量跑全集，结果落盘

### 2.2 第二层 LLM-as-Judge 多维主观评分
- 测对象：RAGAS 测不到的主观质量（题目 / Agent / 简答）
- 评委模型：**Qwen-Max（DashScope）**，与被评测模型解耦避免自评偏差
- 输出：1-5 分 + 文本理由
- 评分依据：rubric（详见 §4）

### 2.3 第三层 Golden Set 回归
- 测对象：版本退化检测
- 规模：
  - **100 条金标 QA**（覆盖问答全场景）
  - **50 道金标题目**（4 题型按比例）
  - **30 条 Agent 端到端任务**（覆盖所有意图标签与 Skill）
- 阈值：与 baseline（主分支最近成功一次）对比，关键指标退化 >5% 阻断

## 3. Golden Set 数据规范

### 3.1 目录结构
```
data/evaluation/
├── golden-set/
│   ├── qa.jsonl              # 100 条
│   ├── exercises.jsonl       # 50 条
│   └── agent-tasks.jsonl     # 30 条
├── rubrics/
│   ├── exercise-quality.yaml
│   ├── agent-trace.yaml
│   ├── essay-grading.yaml
│   └── reflect-validity.yaml
└── runs/
    └── {timestamp}/
        ├── metrics.json
        ├── traces/
        └── report.md
```

### 3.2 QA 金标格式
```
{
  "id": "qa_001",
  "course_id": "ai-app",
  "question": "RAG 中 Rerank 的作用是什么？",
  "ground_truth": "对初步检索结果用 Cross-Encoder 重排序，提升 Top-K 的语义精度。",
  "expected_chunks": ["chunk_042", "chunk_058"],
  "tags": ["RAG","Rerank","中等"]
}
```

### 3.3 题目金标格式
```
{
  "id": "ex_001",
  "course_id": "ai-app",
  "type": "single_choice",
  "knowledge_points": ["主键","外键"],
  "expected_difficulty": "easy",
  "min_quality_score": 4.0,
  "must_have_fields": ["question","options","answer","analysis","source_chunks"]
}
```

### 3.4 Agent 任务金标格式
```
{
  "id": "agent_001",
  "user_input": "帮我准备 RAG 那一章的课，90 分钟",
  "course_id": "ai-app",
  "expected_intent": "lesson_plan",
  "expected_skill": "prepare-class",
  "expected_tools": ["search_kb","lesson_outline","generate_exercise"],
  "min_quality_score": 4.0,
  "must_contain": ["教学目标","重点难点","实训任务","知识来源"]
}
```

### 3.5 数据构造流程
1. 用 Qwen-Max 在已有知识库上批量生成候选（QA 200 条 / 题 100 道 / Agent 任务 60 条）
2. 人工筛选保留高质量样本至目标规模
3. 标注 `ground_truth` / `expected_*` / `min_quality_score` 字段
4. 持续扩充：用户在 RAG 问答页点踩的样本进入待标注队列

## 4. Rubric 设计（4 套）

### 4.1 `exercise-quality.yaml`（出题质量）
- `knowledge_match`：题目是否真考察指定知识点（1-5）
- `difficulty_align`：难度是否与标注一致（1-5）
- `distractor_quality`：选项干扰性是否合理（1-5）
- `analysis_clarity`：解析是否清晰可懂（1-5）

### 4.2 `agent-trace.yaml`（Agent 执行）
- `intent_correct`：意图识别是否正确（0/1）
- `tool_sequence`：工具调用顺序是否符合预期（0-1）
- `tool_args_valid`：工具参数是否合理（1-5）
- `final_quality`：最终输出整体质量（1-5）

### 4.3 `essay-grading.yaml`（简答评分）
- `score_consistency`：总分与各要点之和是否一致（0/1）
- `rubric_alignment`：是否按 rubric 关键点逐一评估（1-5）
- `feedback_specificity`：缺失要点说明是否具体（1-5）

### 4.4 `reflect-validity.yaml`（反思有效性）
- `error_detected`：反思能否检测到注入的故意缺陷（0/1）
- `correction_correct`：纠正后的输出是否真的解决了问题（0/1）

## 5. LangFuse 全链路 Trace

### 5.1 接入方式
- 安装：`pip install langfuse`
- 在每个核心 service 顶部用装饰器：
  ```python
  from langfuse.decorators import observe
  
  @observe(name="rag_qa_pipeline")
  async def rag_qa(...): ...
  ```

### 5.2 装饰器接入位置
| 文件 | trace 命名 | 层级 |
|---|---|---|
| [backend/app/services/rag_qa.py](backend/app/services/rag_qa.py) | `rag_qa_pipeline` | RAG 链路 |
| [backend/app/services/rag_utils.py](backend/app/services/rag_utils.py) | `hybrid_retrieve` | 检索 |
| [backend/app/services/exercises.py](backend/app/services/exercises.py) | `exercise_generate` / `exercise_grade` | 出题/评分 |
| [backend/app/services/lesson_plans.py](backend/app/services/lesson_plans.py) | `lesson_outline` | 备课 |
| [backend/app/services/knowledge_tracking.py](backend/app/services/knowledge_tracking.py) | `mastery_update` | 知识追踪 |
| Agent 节点（P0-1） | `agent_intent` / `agent_plan` / `agent_reflect` | Agent |
| MCP Tool 包装层（P0-2） | `mcp_tool:<name>` | 工具调用 |

### 5.3 Trace 三层结构
```
Trace Root (用户请求)
├── Agent 节点（intent / plan / reflect）
│   └── 工具调用（mcp_tool:*）
│       └── LLM 调用（Qwen-Plus / Qwen-Max）
└── 共享：token 数 / 延迟 / 成本 / 用户标签
```

### 5.4 LangFuse 配置
- 自部署或 SaaS 二选一（毕设建议 SaaS 免费版即可）
- 环境变量：`LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST`

## 6. CI 阻断机制

### 6.1 触发
- GitHub Actions：`on: pull_request`
- 路径过滤：`backend/**` / `data/evaluation/**` 改动才触发

### 6.2 流水线
```
Checkout → 安装依赖 → 跑评测脚本 → 对比 baseline → 生成报告 → 失败时评论 PR + 阻断
```

### 6.3 评测脚本
- 入口：`scripts/run_evaluation.py`
- 顺序：RAGAS（QA 集）→ LLM-Judge（题目/Agent/简答）→ Golden Set 一致性校验
- 输出：`data/evaluation/runs/{timestamp}/metrics.json` + `report.md`

### 6.4 阈值（硬阻断条件）
| 指标 | 阈值 |
|---|---|
| 任一 RAGAS 指标退化 | > 5% |
| Agent 任务成功率 | < 90% |
| 题目质量平均分 | < 4.0 |
| 简答评分一致性 | < 95% |

不达任一阈值即阻断 PR 合并；GitHub PR 评论附 `report.md` 链接，标注退化项与原因。

### 6.5 baseline 维护
- main 分支每次成功合并自动更新 `data/evaluation/baseline/metrics.json`
- 紧急回退情况下可手动指定 baseline commit

## 7. 性能与成本指标（来自 LangFuse 聚合）

| 指标 | 目标 | 用途 |
|---|---|---|
| p50 / p95 端到端延迟 | p95 < 8s | 用户体验 |
| 单次请求平均 token | < 4000 | 成本控制 |
| 缓存命中率（来自 Redis） | > 30% | 优化效果验证 |
| Agent 平均工具调用数 | 1.5 - 4 | 编排合理性 |
| 反思触发率 / 重试率 | 监控波动 | Agent 稳定性 |

## 8. 输入输出协议（同步评测接口）

### 8.1 单次评测（在线触发）
```
POST /api/v1/evaluations/run
{
  "type": "rag_qa | exercise | agent",
  "course_id": "...",
  "input": {...},
  "ground_truth": "...",
  "metrics": ["faithfulness","answer_relevancy",...]
}
```

### 8.2 评测结果
```
{
  "run_id": "eval_xxx",
  "scores": {...},
  "rubric_scores": {...},
  "trace_id": "lf_xxx",
  "passed": true,
  "details": [...]
}
```

### 8.3 批量评测（离线）
- 仅在 CI / 命令行运行：`python scripts/run_evaluation.py --suite all`

## 9. 与其他规范的关系

- Agent 任务集来源：[memory-bank/agent-spec.md](memory-bank/agent-spec.md)
- 题目质量评估输入：[memory-bank/exercise-generation-spec.md](memory-bank/exercise-generation-spec.md)
- 简答评分输入：[memory-bank/exercise-grading-spec.md](memory-bank/exercise-grading-spec.md)
- Trace 三层与缓存命中率指标：[memory-bank/redis-spec.md](memory-bank/redis-spec.md)
