"""
JWT-based authentication: register, login, and token verification.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.config import AUTH_OPTIONAL, LOCAL_MODE
from backend.database import get_connection

# ─── Config ────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if LOCAL_MODE:
        import logging
        logging.getLogger(__name__).warning("SECRET_KEY not set. Using local development fallback secret.")
        SECRET_KEY = "technoir-local-dev-secret-key-change-in-production"
    else:
        raise ValueError("SECRET_KEY environment variable must be set!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


# ─── Schemas ───────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    email: str


class UserResponse(BaseModel):
    username: str
    email: str


# ─── Helpers ───────────────────────────────────────────────────
import re
import time
from collections import defaultdict

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_AUTH_ATTEMPTS: Dict[str, List[float]] = defaultdict(list)


def _validate_email(email: str) -> str:
    cleaned = (email or "").strip().lower()
    if not cleaned or not EMAIL_REGEX.match(cleaned):
        raise HTTPException(status_code=400, detail="Invalid email address format.")
    return cleaned


def _check_rate_limit(key: str, max_attempts: int = 15, window_seconds: float = 60.0):
    now = time.time()
    attempts = _AUTH_ATTEMPTS[key]
    # Prune attempts outside window
    recent = [t for t in attempts if now - t < window_seconds]
    if len(recent) >= max_attempts:
        raise HTTPException(
            status_code=429,
            detail="Too many authentication attempts. Please try again later.",
        )
    recent.append(now)
    _AUTH_ATTEMPTS[key] = recent


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    if credentials is None:
        if AUTH_OPTIONAL:
            return {"email": "local@technoir.rag", "username": "local_user"}
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub", "")
        username: str = payload.get("username", "")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        return {"email": email, "username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


# ─── Routes ────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    req_email = _validate_email(req.email)
    _check_rate_limit(f"reg:{req_email}")

    if len(req.username) < 2 or len(req.username) > 50:
        raise HTTPException(status_code=400, detail="Username must be between 2 and 50 characters.")
    if len(req.password) < 6 or len(req.password) > 72:
        raise HTTPException(status_code=400, detail="Password must be between 6 and 72 characters.")

    conn = get_connection()
    try:
        # Check unique constraints
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ? OR username = ?",
            (req_email, req.username),
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Email or username already exists.")

        hashed = _hash_password(req.password)
        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (req.username, req_email, hashed),
        )
        conn.commit()
    finally:
        conn.close()

    token = _create_token({"sub": req_email, "username": req.username})
    return TokenResponse(access_token=token, username=req.username, email=req_email)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    req_email = _validate_email(req.email)
    _check_rate_limit(f"login:{req_email}")

    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (req_email,)).fetchone()
    finally:
        conn.close()

    if not row or not _verify_password(req.password, row["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = _create_token({"sub": row["email"], "username": row["username"]})
    return TokenResponse(access_token=token, username=row["username"], email=row["email"])


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)):
    return UserResponse(username=user["username"], email=user["email"])
