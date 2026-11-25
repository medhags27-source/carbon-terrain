import os
import re
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pwdlib import PasswordHash

router = APIRouter(prefix="/auth", tags=["Authentication"])
password_hasher = PasswordHash.recommended()

DB_PATH = Path(__file__).resolve().parent / "users.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)
    return connection


class AuthRequest(BaseModel):
    email: str
    password: str


def validate_email(email):
    return bool(re.fullmatch(
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
        r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+",
        email
    ))


@router.post("/register")
def register(data: AuthRequest):
    email = data.email.strip().lower()
    password = data.password

    if not validate_email(email):
        raise HTTPException(400, "Enter a valid email address.")

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long."
        )

    password_hash = password_hasher.hash(password)

    connection = get_connection()
    try:
        connection.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, password_hash)
        )
        connection.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(409, "An account with this email already exists.")
    finally:
        connection.close()

    return {"success": True, "message": "Account created. You can now sign in."}


@router.post("/login")
def login(data: AuthRequest):
    email = data.email.strip().lower()

    connection = get_connection()
    try:
        user = connection.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            (email,)
        ).fetchone()
    finally:
        connection.close()

    if not user or not password_hasher.verify(data.password, user[0]):
        raise HTTPException(401, "Incorrect email or password.")

    return {"success": True, "message": "Credentials verified."}


