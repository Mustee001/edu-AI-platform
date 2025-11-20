from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str
    name: str
    grade: int
    class_id: Optional[int] = None


class Lesson(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: str
    subject: Optional[str] = None
    prompt: Optional[str] = None
    source: Optional[str] = None


class Assignment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str
    item_id: str
    assigned_at: Optional[str] = None


class StudentResponse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str
    item_id: str
    answer: Optional[str] = None
    correct: Optional[bool] = None
    submitted_at: Optional[str] = None


class Classroom(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    teacher_id: Optional[str] = None


class RefreshToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str
    username: Optional[str] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    revoked: Optional[bool] = False
