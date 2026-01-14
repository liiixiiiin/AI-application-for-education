import secrets
from datetime import datetime, timezone


def generate_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(8)}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
