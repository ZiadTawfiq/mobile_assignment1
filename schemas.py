from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    gender: Optional[str] = None
    email: str
    student_id: str
    academic_level: Optional[int] = None
    password: str
    confirm_password: str
    
class UserLogin(BaseModel):
    email: str
    password: str

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: str
    priority: str
    user_id: int


class UserUpdate(BaseModel):
    name: str
    gender: Optional[str] = None
    academic_level: Optional[int] = None
    email: Optional[str] = None
    student_id: Optional[str] = None


