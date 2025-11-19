"""
Authentication and RBAC for FastAPI backend.
Roles: admin, teacher, student
Simple JWT-based auth for prototype.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import jwt
import time
from datetime import timedelta
from .database import get_session
from .models import RefreshToken
from sqlmodel import select

# Secret for JWT (in production, use env var)
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

# Dummy user store for prototype
USERS = {
    "admin": {"username": "admin", "password": "adminpass", "role": "admin"},
    "teacher": {"username": "teacher", "password": "teacherpass", "role": "teacher", "teacher_id": "t1"},
    "student": {"username": "student", "password": "studentpass", "role": "student", "student_id": "s1"},
    "student2": {"username": "student2", "password": "student2pass", "role": "student", "student_id": "s2"},
}

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenWithRefresh(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class User(BaseModel):
    username: str
    role: str
    student_id: Optional[str] = None
    teacher_id: Optional[str] = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def authenticate_user(username: str, password: str) -> Optional[User]:
    user = USERS.get(username)
    if user and user["password"] == password:
        return User(username=user["username"], role=user["role"], student_id=user.get("student_id"), teacher_id=user.get("teacher_id"))
    return None

def create_access_token(data: dict, expires_delta: int = 3600):
    to_encode = data.copy()
    to_encode.update({"exp": int(time.time()) + expires_delta})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: int = 60 * 60 * 24 * 7):
    # default: 7 days
    to_encode = data.copy()
    # include a random identifier so each refresh token is unique even if called in the same second
    import uuid
    to_encode.update({"exp": int(time.time()) + expires_delta, "jti": str(uuid.uuid4())})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # persist refresh token for revocation/rotation support
    try:
        # ensure DB tables exist (handles cases where DB was created before RefreshToken model)
        from .database import init_db
        init_db()
        from datetime import datetime
        rt = RefreshToken(token=token, username=data.get('sub'), created_at=datetime.utcnow().isoformat(), expires_at=str(int(time.time()) + expires_delta), revoked=False)
        with get_session() as sess:
            sess.add(rt)
            sess.commit()
    except Exception:
        pass
    return token

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        student_id = payload.get("student_id")
        teacher_id = payload.get("teacher_id")
        if username is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return User(username=username, role=role, student_id=student_id, teacher_id=teacher_id)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_refresh_token(token: str) -> Optional[dict]:
    # Strict verification: decode and confirm presence/non-revoked state in DB.
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    # require DB confirmation; if DB access fails, treat as invalid to avoid insecure fallback.
    try:
        with get_session() as sess:
            # prefer non-revoked matching tokens; if multiple rows exist with the same token
            # (possible in this prototype when tokens are deterministic), ensure we pick a non-revoked one.
            row = sess.exec(select(RefreshToken).where((RefreshToken.token == token) & (RefreshToken.revoked == False))).first()
            if not row:
                return None
    except Exception:
        return None
    return payload


def revoke_refresh_token(token: str):
    try:
        with get_session() as sess:
            rows = sess.exec(select(RefreshToken).where(RefreshToken.token == token)).all()
            for row in rows:
                row.revoked = True
                sess.add(row)
            if rows:
                sess.commit()
    except Exception:
        pass

def require_role(required_role: str):
    def role_checker(user: User = Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker
