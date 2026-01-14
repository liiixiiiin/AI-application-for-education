# 练习评测规范（Step 7 输出）

## 1. 学生提交格式
```
{
  "exercise_id": "ex_001",
  "course_id": "course_001",
  "type": "single_choice",
  "answer": "B"
}
```

## 2. 评测输出格式
```
{
  "exercise_id": "ex_001",
  "correct": true,
  "score": 1,
  "feedback": "回答正确。",
  "suggestion": ""
}
```

## 3. 判定规则
- 单选题：答案与标准答案一致则正确。
- 判断题：true/false 与标准答案一致则正确。
- 简答题：按评分标准 `rubric` 匹配关键点，可给出部分得分。

## 4. 评测约束
- 输出必须包含 `correct`、`score`、`feedback` 字段。
- `score` 取值区间 0–1（便于统计正确率），部分得分可使用小数。
- 简答题需返回 `suggestion`（缺失点提示或改进建议）。

## 5. 辅助字段（可选）
```
{
  "matched_points": ["说明主键用于唯一标识记录"],
  "missing_points": ["说明外键建立表间引用关系"]
}
```
