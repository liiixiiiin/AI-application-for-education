-- Auto-generated from backend/app/db.py
-- DO NOT EDIT BY HAND

-- users: 用户账号 / 三角色（teacher / student / admin）
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  role TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  password_salt TEXT NOT NULL,
  created_at TEXT NOT NULL
);

-- courses: 课程信息 / 基本元数据
CREATE TABLE courses (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  creator_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (creator_id) REFERENCES users (id)
);

-- sessions: 登录会话 / token 管理
CREATE TABLE sessions (
  token TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

-- knowledge_points: 课程知识点（自动 + 手动）
CREATE TABLE knowledge_points (
  id TEXT PRIMARY KEY,
  course_id TEXT NOT NULL,
  point TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (course_id) REFERENCES courses (id)
);

-- conversations: RAG 多轮对话会话
CREATE TABLE conversations (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  course_id TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT '新对话',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id),
  FOREIGN KEY (course_id) REFERENCES courses (id)
);

-- messages: 对话消息（含引用 JSON）
CREATE TABLE messages (
  id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  citations TEXT DEFAULT '[]',
  created_at TEXT NOT NULL,
  FOREIGN KEY (conversation_id) REFERENCES conversations (id)
);

-- knowledge_mastery: EMA 知识掌握度（知识追踪 ⭐）
CREATE TABLE knowledge_mastery (
  id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  course_id TEXT NOT NULL,
  knowledge_point TEXT NOT NULL,
  mastery REAL NOT NULL DEFAULT 0.5,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (student_id) REFERENCES users (id),
  FOREIGN KEY (course_id) REFERENCES courses (id),
  UNIQUE (student_id, course_id, knowledge_point)
);

-- exercise_attempts: 学生作答记录（数据闭环 ⭐）
CREATE TABLE exercise_attempts (
  id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  exercise_id TEXT NOT NULL,
  course_id TEXT NOT NULL,
  score REAL NOT NULL,
  knowledge_points TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  FOREIGN KEY (student_id) REFERENCES users (id),
  FOREIGN KEY (course_id) REFERENCES courses (id)
);
