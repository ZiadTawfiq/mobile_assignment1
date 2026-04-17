from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    gender = Column(String)  
    email = Column(String, unique=True)
    student_id = Column(String)
    academic_level = Column(Integer)
    password = Column(String)
    profile_image = Column(String)
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    due_date = Column(String, nullable=False)
    priority = Column(String)
    is_completed = Column(Boolean, default=False)
    user_id = Column(Integer)