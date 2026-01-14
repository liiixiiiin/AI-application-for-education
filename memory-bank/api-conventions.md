# API 路径与资源命名规范（Step 2 输出）

## 1. 基本风格
- 基础前缀：`/api/v1`
- 资源使用复数名词（如 `courses`、`users`）
- 路径使用 `kebab-case`
- 通过 HTTP 方法表达动作（GET/POST/PUT/PATCH/DELETE）

## 2. 资源与路径示例
- 用户与认证
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `GET /api/v1/users/{userId}`
- 课程
  - `POST /api/v1/courses`
  - `GET /api/v1/courses`
  - `GET /api/v1/courses/{courseId}`
- 知识库文档
  - `POST /api/v1/courses/{courseId}/documents`
  - `GET /api/v1/courses/{courseId}/documents`
- RAG 问答
  - `POST /api/v1/courses/{courseId}/qa`
- 练习生成与评测
  - `POST /api/v1/courses/{courseId}/exercises/generate`
  - `POST /api/v1/courses/{courseId}/exercises/grade`
- 基础统计
  - `GET /api/v1/stats/overview`

## 3. 命名与字段约定
- 资源主键统一使用 `id`
- 课程关联字段使用 `course_id`
- 角色字段使用 `role`，取值：`admin`/`teacher`/`student`
- 时间字段统一使用 ISO 8601 字符串（`created_at`/`updated_at`）

## 4. 错误与响应
- 成功响应：`{ "data": ..., "meta": ... }`
- 失败响应：`{ "error": { "code": "...", "message": "..." } }`
- 错误码使用 `SCREAMING_SNAKE_CASE`
