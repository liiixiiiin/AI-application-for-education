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

### 1.4 填空题（fill_in_blank）
```
{
  "type": "fill_in_blank",
  "question": "在关系数据库中，____用于唯一标识表中的每一条记录。",
  "blanks": [
    {"index": 1, "answer": "主键", "alternatives": ["primary key", "主码"]}
  ],
  "analysis": "主键（Primary Key）是关系数据库中用于唯一标识记录的字段或字段组合。"
}
```

### 1.5 简答题（short_answer）
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
  "types": ["single_choice", "true_false", "fill_in_blank", "short_answer"],
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
- 填空题必须包含 `blanks` 数组，每个空位含标准答案与可接受的替代答案。
- 每题均需提供答案与简要解析。

## 4. 生成策略（Few-shot Prompting）
- 系统预置不同难度（简单/中等/困难）的示例题目，教师指定难度后自动嵌入 Prompt。
- Prompt 中补充显式约束指令（如"选项应具有合理干扰性"、"参考答案应包含关键得分点"）。
- 采用结构化输出（JSON Schema）约束生成格式，确保下游程序可直接解析。
- 支持基于选中知识点定向出题，检索范围限定在相关知识点的知识库片段中。
