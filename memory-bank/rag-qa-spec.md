# RAG 问答最小闭环规范（Step 5 输出）

## 1. 输入与输出协议

### 1.1 问答输入
```
{
  "course_id": "course_001",
  "question": "主键和外键的作用是什么？",
  "top_k": 5
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
  ]
}
```

## 2. 生成约束
- 仅基于检索结果生成答案，不引入外部知识。
- 若检索结果为空，回答需返回“未找到相关资料”的提示。
- 引用字段 `citations` 必须包含可追溯片段信息。

## 3. 评价指标（最小）
- 引用字段存在且可回溯到检索结果。
- 答案与引用内容语义一致。
