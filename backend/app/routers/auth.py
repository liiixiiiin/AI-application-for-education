from fastapi import APIRouter, HTTPException, Depends

from ..auth import ALLOWED_ROLES, create_password_hash, create_session, hash_password, require_user
from ..db import get_connection
from ..schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from ..utils import generate_id, now_iso


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _row_to_user(row) -> UserResponse:
    return UserResponse(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        role=row["role"],
        created_at=row["created_at"],
    )


@router.post("/register", response_model=dict)
def register(payload: RegisterRequest) -> dict:
    if payload.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (payload.email,),
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash, password_salt = create_password_hash(payload.password)
    user_id = generate_id("user")
    conn.execute(
        """
        INSERT INTO users (id, name, email, role, password_hash, password_salt, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            payload.name,
            payload.email,
            payload.role,
            password_hash,
            password_salt,
            now_iso(),
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    token = create_session(user_id)
    response = AuthResponse(token=token, user=_row_to_user(row))
    return {"data": response.model_dump(), "meta": {}}


@router.post("/login", response_model=dict)
def login(payload: LoginRequest) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (payload.email,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    expected = hash_password(payload.password, row["password_salt"])
    if expected != row["password_hash"]:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_session(row["id"])
    response = AuthResponse(token=token, user=_row_to_user(row))
    return {"data": response.model_dump(), "meta": {}}


@router.patch("/me/role", response_model=dict)
def update_my_role(payload: dict, user: dict = Depends(require_user)) -> dict:
    new_role = payload.get("role")
    if new_role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    conn = get_connection()
    conn.execute(
        "UPDATE users SET role = ? WHERE id = ?",
        (new_role, user["id"]),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    conn.close()

    return {"data": _row_to_user(row).model_dump(), "meta": {}}
