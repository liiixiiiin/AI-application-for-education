# 练习生成规范（Step 6 输出）

## 1. 题型与数据结构

### 1.1 通用字段
```
{
  "exercise_id": "ex_001",
  "course_id": "course_001",
  "type": "single_choice",
  "question": "...",
  "knowledge_points": ["主键", "外键"],
  "source_chunks": ["chunk_042"],
  "difficulty": "easy"
}
```

### 1.2 单选题（single_choice）
```
{
  "type": "single_choice",
  "options": [
    {"key": "A", "text": "..."},
    {"key": "B", "text": "..."},
    {"key": "C", "text": "..."},
    {"key": "D", "text": "..."}
  ],
  "answer": "B",
  "analysis": "..."
}
```

### 1.3 判断题（true_false）
```
{
  "type": "true_false",
  "answer": true,
  "analysis": "..."
}
```

### 1.4 简答题（short_answer）
```
{
  "type": "short_answer",
  "answer": "...",
  "rubric": [
    {"point": "说明主键用于唯一标识记录", "score": 2},
    {"point": "说明外键建立表间引用关系", "score": 2}
  ]
}
```

## 2. 生成输入与输出

### 2.1 生成输入
```
{
  "course_id": "course_001",
  "count": 5,
  "types": ["single_choice", "true_false", "short_answer"],
  "difficulty": "easy",
  "knowledge_scope": ["主键", "外键"]
}
```

### 2.2 生成输出
```
{
  "generated": [
    {
      "exercise_id": "ex_001",
      "type": "single_choice",
      "question": "...",
      "options": [
        {"key": "A", "text": "..."},
        {"key": "B", "text": "..."},
        {"key": "C", "text": "..."},
        {"key": "D", "text": "..."}
      ],
      "answer": "B",
      "analysis": "...",
      "knowledge_points": ["主键"],
      "source_chunks": ["chunk_042"],
      "difficulty": "easy"
    }
  ]
}
```

## 3. 生成约束
- 题目必须来自检索到的知识点，`source_chunks` 必填。
- 简答题必须包含评分标准 `rubric`。
- 每题均需提供答案与简要解析。
