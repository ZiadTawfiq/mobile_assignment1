from __future__ import annotations

from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    gender: str | None = None
    email: str
    student_id: str
    academic_level: int | None = None
    password: str
    confirm_password: str
    
class UserLogin(BaseModel):
    email: str
    password: str

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: str
    priority: str
    user_id: int