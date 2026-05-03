# 功能清单（MVP + 扩展）

## 一、基础功能（MVP，已完成）

- 账号体系：注册 / 登录 / 三角色（管理员 / 教师 / 学生）
- 课程管理：教师创建、三角色查看
- 知识库管理：PDF / Word / Markdown / 网页 URL 上传，查看 / 编辑 / 删除 / 检索
- RAG 问答：基于课程知识库问答，支持流式输出、引用来源
- 练习生成：单选 / 判断 / 填空 / 简答；附标准答案与知识点；简答含评分标准；支持基于知识点定向出题
- 练习评测：客观题规则匹配、给出建议
- 基础统计：用户数、练习次数、正确率

## 二、已完成扩展功能

- 多轮对话记忆（方案 C，滑动窗口持久化）
- 联网搜索（DashScope `enable_search` + 角标引用）
- 混合检索 + DashScope Rerank
- 大模型辅助语义切分
- RAGAS 评测接口
- 知识追踪与个性化推荐（EMA + 薄弱识别 + 推荐生成）
- 教师备课辅助（章节讲解提纲）

## 三、待完成扩展功能

- 主观题高级评分（语义相似度 + 大模型判分加权融合 + 多要点拆分）
- 学情分析（错题聚合、知识点掌握趋势、班级统计）
- 管理端数据看板（ECharts）

## 四、工业级工程化升级（阶段四主线，第 10-13 周，答辩前冲刺）

每项详见对应 spec：

| 编号 | 项 | 设计依据 |
|---|---|---|
| P0-1 | LangGraph Agent（意图识别 + 任务拆解 + 工具调用 + 反思纠错） | [agent-spec.md](memory-bank/agent-spec.md) |
| P0-2 | MCP Server（5 原子 Tool）+ Agent Skills（3 工作流） | [mcp-server-spec.md](memory-bank/mcp-server-spec.md) / [skills-spec.md](memory-bank/skills-spec.md) |
| P0-3 | 三层评测（RAGAS + LLM-Judge + Golden Set）+ LangFuse Trace + CI 阻断 | [evaluation-spec.md](memory-bank/evaluation-spec.md) |
| P0-4 | SpringBoot + FastAPI 双服务微服务架构 | [microservice-spec.md](memory-bank/microservice-spec.md) |
| P0-5 | Redis（语义缓存 / 异步队列 / 限流 / 降级） | [redis-spec.md](memory-bank/redis-spec.md) |
| P0-6 | 短期 + 长期分层记忆 | [memory-spec.md](memory-bank/memory-spec.md) |
| P1 | Ollama 本地推理 + 模型路由（可选） | 不独立 spec |

## 五、其他延伸方向（不在当前路线，仅备查）

- 高级知识追踪模型（DKT / AKT）
- 知识图谱 GraphRAG
- 多模态（公式 OCR / 图理解 / 语音转写）
- LoRA 微调
- 联邦学习 / 差分隐私
