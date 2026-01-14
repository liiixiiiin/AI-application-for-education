# 基础用户与课程管理规范（Step 8 输出）

## 1. 角色与权限（最小）
- 管理员：admin
- 教师：teacher
- 学生：student

最小能力：
- 三角色均可注册与登录。
- 三角色均可查看课程列表与课程详情。
- 仅教师可创建课程。

## 2. 用户数据结构（最小）
```
{
  "id": "user_001",
  "name": "张三",
  "email": "user@example.com",
  "role": "teacher",
  "created_at": "2026-01-01T10:00:00Z"
}
```

## 3. 课程数据结构（最小）
```
{
  "id": "course_001",
  "title": "数据库基础",
  "description": "关系模型与 SQL 基础",
  "creator_id": "user_001",
  "created_at": "2026-01-01T10:10:00Z"
}
```

## 4. API（与命名规范一致）
- 注册：`POST /api/v1/auth/register`
- 登录：`POST /api/v1/auth/login`
- 课程创建：`POST /api/v1/courses`（仅教师）
- 课程列表：`GET /api/v1/courses`
- 课程详情：`GET /api/v1/courses/{courseId}`

## 5. 最小页面需求
- 登录页（所有角色）
- 课程列表页（所有角色）
- 课程创建页（教师）

## 6. 测试用例（手动）
- 创建管理员/教师/学生三种账号，均可注册与登录。
- 三角色登录后均可看到课程列表。
- 只有教师账号可创建课程。
