import hashlib
import secrets
from typing import Optional

from fastapi import Header, HTTPException

from .db import get_connection
from .utils import generate_id, now_iso


ALLOWED_ROLES = {"admin", "teacher", "student"}


def hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        100_000,
    )
    return digest.hex()


def create_password_hash(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    return hash_password(password, salt), salt


def create_session(user_id: str) -> str:
    token = generate_id("token")
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
        (token, user_id, now_iso()),
    )
    conn.commit()
    conn.close()
    return token


def get_user_by_token(token: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT users.id, users.name, users.email, users.role, users.created_at
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = ?
        """,
        (token,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def require_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")
    token = authorization.split(" ", 1)[1].strip()
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    return user


def require_teacher(user: dict) -> None:
    if user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Teacher role required")
