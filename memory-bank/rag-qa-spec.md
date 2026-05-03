# RAG 问答规范（Step 5 输出）

## 1. 输入与输出协议

### 1.1 问答输入
```
{
  "course_id": "course_001",
  "question": "主键和外键的作用是什么？",
  "top_k": 5,
  "conversation_id": "conv_001"  // 可选，不传则自动进入最近对话或创建新对话
}
```

### 1.2 检索输出（内部）
```
{
  "query": "主键和外键的作用是什么？",
  "results": [
    {
      "chunk_id": "chunk_042",
      "score": 0.82,
      "content": "...",
      "title_path": "课程大纲 > 第 1 章：关系模型与数据表",
      "source_doc_id": "doc_001",
      "source_doc_name": "course-outline.md"
    }
  ]
}
```

### 1.3 问答输出
```
{
  "answer": "主键用于唯一标识表中的记录，外键用于建立表之间的引用关系...",
  "citations": [
    {
      "chunk_id": "chunk_042",
      "source_doc_id": "doc_001",
      "source_doc_name": "course-outline.md",
      "title_path": "课程大纲 > 第 1 章：关系模型与数据表",
      "excerpt": "主键与外键的作用..."
    }
  ],
  "conversation_id": "conv_001"
}
```

## 2. 生成约束
- 优先基于检索结果生成答案；检索结果为空时，模型依据自身知识回答。
- 检索结果为空时，回答前自动附加 disclaimer 提示，区分两种情况：
  - 课程尚未上传知识库：提示"该课程尚未上传知识库资料，以下回答基于模型自身知识，仅供参考。"
  - 知识库存在但未命中：提示"未在课程知识库中检索到直接相关的资料，以下回答基于模型自身知识，仅供参考。"
- 联网搜索模式下，即使本地检索为空仍可结合联网结果正常回答。
- 引用字段 `citations` 必须包含可追溯片段信息；无检索结果时为空数组。
- 多轮对话中，模型需结合对话历史理解追问与指代消解。

## 2.5 联网搜索

### 2.5.1 概述
前端提供"联网"开关，开启后模型可基于 DashScope 联网搜索获取实时信息（如天气、股价、新闻等），弥补训练数据的时效性限制。联网搜索与本地知识库检索可同时生效：本地检索资料作为上下文，联网搜索补充实时信息。

### 2.5.2 调用方式
使用 DashScope Generation API 的 `enable_search` 参数，配合 `search_options` 控制搜索行为：
- `forced_search: true`：强制联网搜索，不由模型自行判断是否需要联网
- `enable_source: true`：返回搜索来源（标题、URL、站点名）
- `enable_citation: true`：模型回复中自动插入角标引用（如 `[1]`、`[2]`）
- `citation_format: "[<number>]"`：角标格式
- `prepend_search_result: true`：搜索来源在首个流式 chunk 中提前返回

### 2.5.3 SSE 事件协议
联网搜索模式下，流式响应新增一个 SSE 事件类型：
```
event: web_sources
data: {"sources": [{"title": "...", "url": "...", "site_name": "...", "index": 1}, ...]}
```
`done` 事件的 payload 中也包含 `web_sources` 字段（与上述格式相同），前端以 `done` 事件中的数据为最终值。

### 2.5.4 支持的模型
qwen-plus、qwen-max、qwen-turbo、qwen-flash 等千问系列模型均支持联网搜索。

### 2.5.5 前端交互
- 联网来源以可折叠区域展示在助手消息下方（Globe 图标 + "N 条联网来源"标题）。
- 每条来源为可点击的卡片链接，展示序号、标题、站点名，点击可在新窗口打开原始网页。

## 3. 评价指标（最小）
- 引用字段存在且可回溯到检索结果。
- 答案与引用内容语义一致。

> 评测接口与 RAGAS / LLM-as-Judge / Golden Set 的完整规范已迁移至 [evaluation-spec.md](memory-bank/evaluation-spec.md)。

## 4. 记忆管理（多轮对话）

> 短期记忆细节（注入策略、标题生成、持久化、向后兼容）以及长期记忆方案已迁移至 [memory-spec.md](memory-bank/memory-spec.md)。本节仅保留交互模式与对话数据/接口契约。

### 4.1 交互模式：方案 C（折中模式）
- 每个用户在每门课程下可拥有多个对话。
- 进入问答页面时**自动进入最近活跃的对话**，无需手动选择。
- 提供「新建对话」按钮，用户需要切换话题时才创建新对话。
- 首次使用时自动创建第一个对话，对用户无感知。

### 4.2 对话数据结构
```
// 对话会话
{
  "id": "conv_001",
  "user_id": "user_001",
  "course_id": "course_001",
  "title": "主键与外键",
  "created_at": "2026-03-24T10:00:00Z",
  "updated_at": "2026-03-24T10:05:00Z"
}

// 对话消息
{
  "id": "msg_001",
  "conversation_id": "conv_001",
  "role": "user",       // "user" | "assistant"
  "content": "主键和外键的作用是什么？",
  "citations": [],       // assistant 消息附带引用
  "created_at": "2026-03-24T10:00:00Z"
}
```

### 4.3 对话管理 API
- `POST /api/v1/conversations`：创建新对话（需 `course_id`）
- `GET /api/v1/conversations?course_id=xxx`：列出用户在某课程下的对话列表
- `GET /api/v1/conversations/{id}`：获取对话详情（含消息列表）
- `DELETE /api/v1/conversations/{id}`：删除对话及其所有消息
- `PATCH /api/v1/conversations/{id}`：更新对话标题
