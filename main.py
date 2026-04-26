import os
import uuid
from datetime import datetime
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import models, schemas
from database import engine, SessionLocal

# ================= INIT =================

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ================= PATHS =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "images")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

BASE_URL = os.getenv(
    "BASE_URL",
    "https://mobileassignment1-production.up.railway.app"
)

# ================= DB =================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================= AUTH =================

@app.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):

    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(400, "Email already exists")

    if not user.email.endswith("@stud.fci-cu.edu.eg"):
        raise HTTPException(400, "Invalid FCI email")

    if user.student_id not in user.email:
        raise HTTPException(400, "Student ID mismatch")

    if user.academic_level not in [None, 1, 2, 3, 4]:
        raise HTTPException(400, "Invalid academic level")

    if len(user.password) < 8 or not any(c.isdigit() for c in user.password):
        raise HTTPException(400, "Weak password")

    if user.password != user.confirm_password:
        raise HTTPException(400, "Passwords do not match")

    new_user = models.User(
        name=user.name,
        gender=user.gender,
        email=user.email,
        student_id=user.student_id,
        academic_level=user.academic_level,
        password=user.password
    )

    db.add(new_user)
    db.commit()

    return {"message": "Signup Success"}


@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):

    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if not db_user or db_user.password != user.password:
        raise HTTPException(400, "Invalid email or password")

    return {
        "message": "Login Success",
        "user_id": db_user.id
    }

# ================= PROFILE =================

@app.get("/profile/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "gender": user.gender,
        "academic_level": user.academic_level,
        "profile_image": user.profile_image
    }


@app.put("/profile/{user_id}")
def update_profile(user_id: int, updated: schemas.UserUpdate, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    if not updated.name.strip():
        raise HTTPException(400, "Name cannot be empty")

    if updated.gender not in [None, "Male", "Female"]:
        raise HTTPException(400, "Invalid gender")

    if updated.academic_level not in [None, 1, 2, 3, 4]:
        raise HTTPException(400, "Invalid academic level")

    if updated.email:
        if not updated.email.endswith("@stud.fci-cu.edu.eg"):
            raise HTTPException(400, "Invalid FCI email")

        existing = db.query(models.User).filter(models.User.email == updated.email).first()
        if existing and existing.id != user_id:
            raise HTTPException(400, "Email already exists")

        user.email = updated.email

    if updated.student_id:
        user.student_id = updated.student_id

    user.name = updated.name
    user.gender = updated.gender
    user.academic_level = updated.academic_level

    db.commit()

    return {"message": "Profile updated"}

# ================= UPLOAD IMAGE =================

@app.post("/profile/{user_id}/upload")
async def upload_image(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    content = await file.read()

    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(400, "Image too large")

    file_extension = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_extension}"

    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    image_url = f"{BASE_URL}/images/{filename}"

    user.profile_image = image_url
    db.commit()

    return {
        "message": "Image uploaded",
        "image_url": image_url
    }

# ================= TASKS =================

@app.post("/tasks")
def add_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):

    if task.priority not in ["Low", "Medium", "High"]:
        raise HTTPException(400, "Invalid priority")

    try:
        datetime.strptime(task.due_date, "%Y-%m-%d")
    except:
        raise HTTPException(400, "Due date must be YYYY-MM-DD")

    new_task = models.Task(**task.dict())

    db.add(new_task)
    db.commit()

    return {"message": "Task added"}


@app.get("/users/{user_id}/tasks", response_model=List[schemas.Task])
def get_tasks(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Task).filter(models.Task.user_id == user_id).all()


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db)):

    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not db_task:
        raise HTTPException(404, "Task not found")

    if task.priority not in ["Low", "Medium", "High"]:
        raise HTTPException(400, "Invalid priority")

    try:
        datetime.strptime(task.due_date, "%Y-%m-%d")
    except:
        raise HTTPException(400, "Due date must be YYYY-MM-DD")

    for key, value in task.dict().items():
        setattr(db_task, key, value)

    db.commit()

    return {"message": "Task updated"}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):

    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not db_task:
        raise HTTPException(404, "Task not found")

    db.delete(db_task)
    db.commit()

    return {"message": "Task deleted"}


@app.patch("/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):

    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not db_task:
        raise HTTPException(404, "Task not found")

    db_task.is_completed = True
    db.commit()

    return {"message": "Task completed"}


@app.patch("/tasks/{task_id}/add-favorite")
def add_favorite(task_id: int, db: Session = Depends(get_db)):

    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(404, "Task not found")

    task.is_favorite = True
    db.commit()

    return {"message": "Added to favorites", "is_favorite": True}


@app.patch("/tasks/{task_id}/remove-favorite")
def remove_favorite(task_id: int, db: Session = Depends(get_db)):

    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(404, "Task not found")

    task.is_favorite = False
    db.commit()

    return {"message": "Removed from favorites", "is_favorite": False}


@app.get("/users/{user_id}/favorites")
def get_favorites(user_id: int, db: Session = Depends(get_db)):

    return db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.is_favorite.is_(True)
    ).all()


@app.get("/tasks/{task_id}/deadline")
def get_deadline(task_id: int, db: Session = Depends(get_db)):

    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(404, "Task not found")

    due_date = datetime.strptime(task.due_date, "%Y-%m-%d")
    now = datetime.now()

    remaining = (due_date.date() - now.date()).days

    return {
        "due_date": task.due_date,
        "today": now.strftime("%Y-%m-%d"),
        "remaining_days": remaining
    }