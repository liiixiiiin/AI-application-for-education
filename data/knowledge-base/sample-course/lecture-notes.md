# 讲义节选：SQL 基础查询（示例）

## 1. SELECT 与 WHERE
SELECT 语句用于从表中查询数据，WHERE 用于过滤条件。常见条件包括等于、不等于、范围与模糊匹配。

示例：
SELECT name, score FROM students WHERE score >= 60;

## 2. 排序与分页
ORDER BY 用于排序，LIMIT 用于限制返回行数，常见于分页场景。

示例：
SELECT name, score FROM students ORDER BY score DESC LIMIT 10;

## 3. 聚合函数与分组
聚合函数包括 COUNT、SUM、AVG、MAX、MIN。与 GROUP BY 结合可得到分组统计结果。

示例：
SELECT class_id, AVG(score) FROM students GROUP BY class_id;

## 4. 常见错误
- 忘记在 GROUP BY 中包含非聚合字段
- 混用 WHERE 与 HAVING 的作用范围
