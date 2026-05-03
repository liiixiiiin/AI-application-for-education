import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "app.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            creator_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (creator_id) REFERENCES users (id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_points (
            id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            point TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '新对话',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            citations TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_mastery (
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
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS exercise_attempts (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            exercise_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            score REAL NOT NULL,
            knowledge_points TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
        """
    )
    conn.commit()
    conn.close()
