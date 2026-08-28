import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from pwdlib import PasswordHash

router = APIRouter(prefix="/api/auth", tags=["authentication"])
load_dotenv()
password_hash = PasswordHash.recommended()
database_path = Path(__file__).resolve().parents[1] / "data" / "auth.db"
email_pattern = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _secret() -> str:
    value = os.getenv("ATMOGRAPH_JWT_SECRET")
    if not value or len(value) < 32:
        raise RuntimeError("ATMOGRAPH_JWT_SECRET must contain at least 32 characters")
    return value


def _connection():
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    return connection


def _public_user(row):
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def _token(user):
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user["id"]), "email": user["email"], "iat": now, "exp": now + timedelta(minutes=30)}
    return jwt.encode(payload, _secret(), algorithm="HS256")


def user_from_request(request: Request):
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = jwt.decode(authorization[7:], _secret(), algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from None
    with _connection() as connection:
        user = connection.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return _public_user(user)


@router.post("/register", status_code=201)
def register(body: RegisterRequest):
    name = body.name.strip()
    email = body.email.strip().lower()
    if len(name) < 2 or not email_pattern.match(email) or len(body.password) < 10:
        raise HTTPException(status_code=422, detail="Use a valid name, email and password of at least 10 characters")
    try:
        with _connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users(name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (name, email, password_hash.hash(body.password), datetime.now(timezone.utc).isoformat()),
            )
            user = {"id": cursor.lastrowid, "name": name, "email": email}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="An account with this email already exists") from None
    return {"access_token": _token(user), "token_type": "bearer", "user": user}


@router.post("/login")
def login(body: LoginRequest):
    with _connection() as connection:
        row = connection.execute("SELECT * FROM users WHERE email = ?", (body.email.strip().lower(),)).fetchone()
    if row is None or not password_hash.verify(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    user = _public_user(row)
    return {"access_token": _token(user), "token_type": "bearer", "user": user}


@router.get("/me")
def me(request: Request):
    return user_from_request(request)
