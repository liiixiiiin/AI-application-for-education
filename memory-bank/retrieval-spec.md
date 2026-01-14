# 向量化与检索流程规范（Step 4 输出）

## 1. 输入与输出格式

### 1.1 文档输入（清洗后）
```
{
  "course_id": "course_001",
  "source_doc_id": "doc_001",
  "source_doc_name": "course-outline.md",
  "source_doc_type": "markdown",
  "content": "..."
}
```

### 1.2 切分输出（片段）
```
{
  "chunk_id": "chunk_001",
  "course_id": "course_001",
  "source_doc_id": "doc_001",
  "title_path": "课程大纲 > 第 1 章：关系模型与数据表",
  "content": "...",
  "order_index": 3,
  "char_count": 214
}
```

### 1.3 向量化输出
```
{
  "chunk_id": "chunk_001",
  "embedding": [0.012, -0.034, ...],
  "dim": 768
}
```

### 1.4 检索输入
```
{
  "course_id": "course_001",
  "query": "主键和外键的作用是什么？",
  "top_k": 5,
  "filters": {
    "source_doc_type": ["markdown", "pdf", "docx"]
  }
}
```

### 1.5 检索输出
```
{
  "query": "主键和外键的作用是什么？",
  "results": [
    {
      "chunk_id": "chunk_042",
      "score": 0.82,
      "content": "...",
      "title_path": "课程大纲 > 第 1 章：关系模型与数据表",
      "source_doc_id": "doc_001"
    }
  ]
}
```

## 2. 基础检索策略
- 相似度检索 Top-k，默认 `top_k = 5`。
- 可选重排序：在检索结果基础上进行 rerank（先不强制启用）。
- 过滤条件按课程与文档类型生效。

## 3. 文档类型兼容
- 最低要求：支持 PDF / Word / Markdown 任意组合输入。
- 建议统一输出为纯文本后进入切分流程。

## 4. 约束与日志
- 每次检索记录 `query`、`top_k`、`course_id`、返回数量。
- 若无命中，返回空数组并记录原因（如无索引/过滤过严）。
