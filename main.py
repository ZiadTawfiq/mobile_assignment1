from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import models, schemas
from database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ================= DB =================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ================= Auth =================
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

# ================= Profile =================
@app.get("/profile/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    return user


@app.put("/profile/{user_id}")
def update_profile(user_id: int, updated: schemas.UserUpdate, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    user.name = updated.name
    user.gender = updated.gender
    user.academic_level = updated.academic_level

    db.commit()

    return {"message": "Profile updated"}


@app.post("/profile/{user_id}/upload")
def upload_image(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    file_path = f"images/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    user.profile_image = file_path
    db.commit()

    return {"message": "Image uploaded"}

# ================= Tasks =================
@app.post("/tasks")
def add_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):

    # validate priority
    if task.priority not in ["Low", "Medium", "High"]:
        raise HTTPException(400, "Invalid priority")

    # validate due date
    try:
        datetime.strptime(task.due_date, "%Y-%m-%d")
    except:
        raise HTTPException(400, "Due date must be YYYY-MM-DD")

    new_task = models.Task(**task.dict())

    db.add(new_task)
    db.commit()

    return {"message": "Task added"}


@app.get("/tasks/{user_id}")
def get_tasks(user_id: int, db: Session = Depends(get_db)):

    return db.query(models.Task).filter(models.Task.user_id == user_id).all()


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db)):

    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not db_task:
        raise HTTPException(404, "Task not found")

    # validate priority
    if task.priority not in ["Low", "Medium", "High"]:
        raise HTTPException(400, "Invalid priority")

    # validate due date
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

