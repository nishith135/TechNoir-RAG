"""
JWT-based authentication: register, login, and token verification.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.database import get_connection

# ─── Config ────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


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
def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
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
    if len(req.username) < 2 or len(req.username) > 50:
        raise HTTPException(status_code=400, detail="Username must be between 2 and 50 characters.")
    if len(req.password) < 6 or len(req.password) > 72:
        raise HTTPException(status_code=400, detail="Password must be between 6 and 72 characters.")

    conn = get_connection()
    try:
        # Check unique constraints
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ? OR username = ?",
            (req.email, req.username),
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Email or username already exists.")

        hashed = _hash_password(req.password)
        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (req.username, req.email, hashed),
        )
        conn.commit()
    finally:
        conn.close()

    token = _create_token({"sub": req.email, "username": req.username})
    return TokenResponse(access_token=token, username=req.username, email=req.email)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (req.email,)).fetchone()
    finally:
        conn.close()

    if not row or not _verify_password(req.password, row["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = _create_token({"sub": row["email"], "username": row["username"]})
    return TokenResponse(access_token=token, username=row["username"], email=row["email"])


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)):
    return UserResponse(username=user["username"], email=user["email"])
