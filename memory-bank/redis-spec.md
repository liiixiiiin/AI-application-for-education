# Redis 中间件规范（P0-5 输出）

## 1. 设计目标

引入 Redis 作为系统中间件层，承载三大用途：
- **语义缓存**：减少重复 LLM 调用，降低延迟与成本
- **异步任务队列**：耗时操作（解析 / 切分 / 向量化 / 批量出题）解耦
- **令牌桶限流**：保护 DashScope API 配额、防止恶意刷接口

并提供降级策略：DashScope 不可用时切换至本地推理路径。

## 2. 部署形态

- 开发：单机 Redis（Docker Compose 起一个 `redis:7` 容器即可）
- 生产：Redis 6+/7+ 单实例（毕设规模），主从可选
- 客户端库：
  - Python：`redis-py` + `rq`（任务队列）
  - Java：`spring-data-redis` + `redisson`（限流可用 Redisson 限速器）

## 3. Key 命名约定

统一前缀分隔风格：`{namespace}:{primary_key}[:{secondary}]`

| Key 模式 | 用途 | TTL |
|---|---|---|
| `emb:{md5(text)}` | 文本 → embedding 缓存 | 30 天 |
| `retr:{course_id}:{md5(query)}:{kb_version}` | RAG 检索结果缓存 | 7 天 |
| `qa:{course_id}:{md5(query)}:{kb_version}` | RAG 问答语义缓存 | 24 小时 |
| `mastery:{student_id}:{course_id}` | 学生掌握度热缓存 | 1 小时 |
| `kp:{course_id}` | 课程知识点列表 | 1 小时 |
| `task:{task_id}` | 异步任务状态 | 7 天 |
| `task:queue:{type}` | RQ 任务队列（kb_index / batch_exercise / eval） | 永久 |
| `rl:user:{user_id}` | 用户级令牌桶 | 滑动窗口 |
| `rl:global:{api_name}` | 全局令牌桶 | 滑动窗口 |
| `lock:{resource_id}` | 分布式锁（如重建索引） | 60s 自动过期 |

`kb_version`：每次知识库变更（上传 / 编辑 / 删除文档）+1，作为缓存失效信号；存储于 `kb_version:{course_id}`。

## 4. 语义缓存策略

### 4.1 RAG 问答语义缓存
- 命中流程：
  1. 计算 query embedding
  2. 在 `qa:*` 命名空间内查最近的语义邻居（用 RedisSearch + Vector Set，或退化为 hash key 精确匹配）
  3. 余弦相似度 ≥ 0.92 → 命中，直接返回缓存答案
  4. 未命中 → 走完整 RAG 链路，结果写回缓存
- 失效条件：
  - `kb_version` 变化 → 该课程下所有 `qa:{course_id}:*` 失效
  - TTL 到期
- 回退策略：缓存读写失败时不影响主链路（fail-open）

### 4.2 Embedding 缓存
- 同一文本（精确 hash 匹配）直接返回缓存向量
- 用于：知识库切片重复内容、用户重复 query

### 4.3 检索结果缓存
- 仅缓存命中 chunk 列表（不含 LLM 生成结果）
- 适合：相似 query 频繁、RAG 链路开销主要在检索而非生成

### 4.4 缓存命中率监控
- 命中/未命中计数写入 LangFuse Tag
- 详见 [memory-bank/evaluation-spec.md](memory-bank/evaluation-spec.md) §7

## 5. 异步任务队列

### 5.1 适用任务
| 任务类型 | 队列名 | 典型耗时 |
|---|---|---|
| 知识库文档解析 + 切分 + 向量化 | `task:queue:kb_index` | 数十秒 - 分钟 |
| 教师批量出题（>10 题） | `task:queue:batch_exercise` | 10-30 秒 |
| RAGAS / Golden Set 评测 | `task:queue:eval` | 分钟级 |
| 长对话摘要压缩 | `task:queue:summarize` | 数秒 |

### 5.2 协议
- 提交：`POST /api/v1/tasks` → 返回 `task_id`
- 查询：`GET /api/v1/tasks/{task_id}` → `{status, progress, result, error}`
- 状态机：`pending` → `running` → `succeeded` / `failed`
- 进度上报：worker 每完成一个 step 写 `task:{task_id}.progress` 字段

### 5.3 实现
- Python 端：`rq` 库 + worker 进程（独立部署）
- 前端体验：提交后轮询任务状态，进度条展示

## 6. 限流（令牌桶）

### 6.1 用户级
- Key：`rl:user:{user_id}`
- 规则：每用户每分钟最多 30 次 LLM 调用
- 触发后返回 429 + `Retry-After` 头

### 6.2 全局级
- Key：`rl:global:llm`
- 规则：全系统每秒最多 10 次 DashScope 调用（配合付费计划阈值）
- 优先用 Redisson Token Bucket 或 Lua 脚本原子实现

### 6.3 限流接入位置
- FastAPI：路由依赖 `Depends(rate_limit_user)`
- SpringBoot：`@RateLimit` 注解（自定义 AOP）
- MCP Tool 调用层：包装内部限流（避免单 Tool 高频压垮 LLM）

## 7. 降级策略

### 7.1 DashScope 不可达
- 检测：连续 3 次请求 5xx 或超时
- 动作：写入 `flag:dashscope_down` Redis Key（TTL 30s）
- 后续请求：路由到 Ollama 本地模型（P1 可选项；未实现时降级为返回缓存或友好错误）

### 7.2 缓存层故障
- Redis 不可达 → 缓存 fail-open（直接走主链路），日志告警
- 不允许因为缓存挂掉导致主功能不可用

### 7.3 限流触发
- 用户触发：返回 429 + 提示稍后再试
- 全局触发：放入异步队列延后处理，前端显示"系统繁忙，已加入处理队列"

## 8. 接入点（按现有代码标注）

| 现有文件 | 接入动作 |
|---|---|
| [backend/app/services/rag_qa.py](backend/app/services/rag_qa.py) | 入口加语义缓存检查；出口写回 |
| [backend/app/services/rag_utils.py](backend/app/services/rag_utils.py) | 检索结果缓存 + embedding 缓存 |
| [backend/app/services/knowledge_base.py](backend/app/services/knowledge_base.py) | 文档处理任务投递到 `kb_index` 队列；维护 `kb_version` |
| [backend/app/services/exercises.py](backend/app/services/exercises.py) | 批量出题投递到 `batch_exercise` 队列 |
| [backend/app/services/knowledge_tracking.py](backend/app/services/knowledge_tracking.py) | 掌握度查询走 `mastery:*` 缓存 |
| [backend/app/routers/](backend/app/routers/) 全部 | 添加用户级限流依赖 |
| MCP Tool 层（P0-2） | LLM 调用前检查全局限流 |

## 9. 监控指标（接入 LangFuse）

- 各类 Cache 命中率（每小时聚合）
- 任务队列深度 / 平均执行时长
- 限流命中数（按用户、全局分别）
- 降级事件计数

## 10. 测试

| 类别 | 用例 |
|---|---|
| 单元 | 缓存读写、TTL 生效、kb_version 失效 |
| 并发 | 同 query 并发 100 次，预期仅 1 次穿透到 LLM |
| 限流 | 单用户 1 分钟内 31 次调用，最后一次返回 429 |
| 降级 | mock DashScope 不可达，确认 flag 写入 + 路由到兜底 |
| 队列 | 投递 10 个 kb_index 任务，验证状态机正确 |

## 11. 与其他规范的关系

- 任务队列接口对接：[memory-bank/api-conventions.md](memory-bank/api-conventions.md)
- 缓存命中率上报：[memory-bank/evaluation-spec.md](memory-bank/evaluation-spec.md) §7
- 微服务两侧共用：[memory-bank/microservice-spec.md](memory-bank/microservice-spec.md) §6
- 长期记忆向量存储中可选用 Redis Vector Set：[memory-bank/memory-spec.md](memory-bank/memory-spec.md)
