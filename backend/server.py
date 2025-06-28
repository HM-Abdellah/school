from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os
from typing import List, Optional
from datetime import datetime, time, date
import uuid
import jwt
from dotenv import load_dotenv
from bson import ObjectId
import json

# Custom JSON encoder to handle ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

load_dotenv()

app = FastAPI(title="Attendance Management System")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client.attendance_system

# Collections
teachers_collection = db.teachers
classes_collection = db.classes
students_collection = db.students
attendance_collection = db.attendance

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable

# Models
class Teacher(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: str
    hashed_password: str

class TeacherCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str

class TeacherLogin(BaseModel):
    username: str
    password: str

class Student(BaseModel):
    id: str
    full_name: str
    class_id: str

class Class(BaseModel):
    id: str
    name: str
    level: str  # Common Core, 1st Baccalaureate, 2nd Baccalaureate
    stream: str  # Science, Arts
    teacher_id: str
    students: List[str]  # List of student IDs

class AttendanceRecord(BaseModel):
    id: str
    class_id: str
    student_id: str
    date: str
    session: str  # "morning" or "afternoon"
    status: str  # "present" or "absent"
    recorded_at: datetime
    recorded_by: str  # teacher_id

class AttendanceSubmission(BaseModel):
    class_id: str
    date: str
    session: str
    attendance_data: List[dict]  # [{"student_id": "xxx", "status": "present"}]

# Helper Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        teacher_id = payload.get("teacher_id")
        if teacher_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return teacher_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Initialize Sample Data
async def init_sample_data():
    # Check if data already exists
    if await teachers_collection.count_documents({}) > 0:
        return
    
    # Sample Teachers
    teachers = [
        {
            "id": str(uuid.uuid4()),
            "username": "teacher1",
            "email": "teacher1@school.com",
            "full_name": "Sarah Johnson",
            "hashed_password": get_password_hash("password123")
        },
        {
            "id": str(uuid.uuid4()),
            "username": "teacher2",
            "email": "teacher2@school.com",
            "full_name": "Michael Smith",
            "hashed_password": get_password_hash("password123")
        }
    ]
    
    await teachers_collection.insert_many(teachers)
    
    # Sample Classes
    classes = [
        {
            "id": str(uuid.uuid4()),
            "name": "Mathematics - Common Core",
            "level": "Common Core",
            "stream": "General",
            "teacher_id": teachers[0]["id"],
            "students": []
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Physics - 1st Baccalaureate Science",
            "level": "1st Baccalaureate",
            "stream": "Science",
            "teacher_id": teachers[0]["id"],
            "students": []
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Literature - 2nd Baccalaureate Arts",
            "level": "2nd Baccalaureate",
            "stream": "Arts",
            "teacher_id": teachers[1]["id"],
            "students": []
        }
    ]
    
    await classes_collection.insert_many(classes)
    
    # Sample Students for each class
    for class_doc in classes:
        students = []
        for i in range(25):  # 25 students per class
            student = {
                "id": str(uuid.uuid4()),
                "full_name": f"Student {i+1} {class_doc['level'][:3]}",
                "class_id": class_doc["id"]
            }
            students.append(student)
        
        await students_collection.insert_many(students)
        
        # Update class with student IDs
        student_ids = [s["id"] for s in students]
        await classes_collection.update_one(
            {"id": class_doc["id"]},
            {"$set": {"students": student_ids}}
        )

# API Routes
@app.on_event("startup")
async def startup_event():
    await init_sample_data()

@app.post("/api/auth/login")
async def login(teacher_data: TeacherLogin):
    teacher = await teachers_collection.find_one({"username": teacher_data.username})
    if not teacher or not verify_password(teacher_data.password, teacher["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"teacher_id": teacher["id"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "teacher": {
            "id": teacher["id"],
            "username": teacher["username"],
            "full_name": teacher["full_name"],
            "email": teacher["email"]
        }
    }

@app.get("/api/teacher/profile")
async def get_teacher_profile(teacher_id: str = Depends(verify_token)):
    teacher = await teachers_collection.find_one({"id": teacher_id})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return {
        "id": teacher["id"],
        "username": teacher["username"],
        "full_name": teacher["full_name"],
        "email": teacher["email"]
    }

@app.get("/api/classes")
async def get_teacher_classes(teacher_id: str = Depends(verify_token)):
    cursor = classes_collection.find({"teacher_id": teacher_id})
    classes = await cursor.to_list(100)
    
    # Convert ObjectId to string
    for cls in classes:
        if "_id" in cls:
            cls["_id"] = str(cls["_id"])
    
    return classes

@app.get("/api/classes/{class_id}/students")
async def get_class_students(class_id: str, teacher_id: str = Depends(verify_token)):
    # Verify teacher owns this class
    class_doc = await classes_collection.find_one({"id": class_id, "teacher_id": teacher_id})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found or access denied")
    
    cursor = students_collection.find({"class_id": class_id})
    students = await cursor.to_list(100)
    
    # Convert ObjectId to string
    for student in students:
        if "_id" in student:
            student["_id"] = str(student["_id"])
    
    return students

@app.get("/api/classes/{class_id}/attendance")
async def get_class_attendance(
    class_id: str,
    date: str,
    session: str,
    teacher_id: str = Depends(verify_token)
):
    # Verify teacher owns this class
    class_doc = await classes_collection.find_one({"id": class_id, "teacher_id": teacher_id})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found or access denied")
    
    cursor = attendance_collection.find({
        "class_id": class_id,
        "date": date,
        "session": session
    })
    attendance_records = await cursor.to_list(100)
    
    # Convert ObjectId to string
    for record in attendance_records:
        if "_id" in record:
            record["_id"] = str(record["_id"])
    
    return attendance_records

@app.post("/api/classes/{class_id}/attendance")
async def submit_attendance(
    class_id: str,
    submission: AttendanceSubmission,
    teacher_id: str = Depends(verify_token)
):
    # Verify teacher owns this class
    class_doc = await classes_collection.find_one({"id": class_id, "teacher_id": teacher_id})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found or access denied")
    
    # Check if attendance already submitted for this session
    existing = await attendance_collection.find_one({
        "class_id": class_id,
        "date": submission.date,
        "session": submission.session
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already submitted for this session")
    
    # Create attendance records
    attendance_records = []
    for record in submission.attendance_data:
        attendance_record = {
            "id": str(uuid.uuid4()),
            "class_id": class_id,
            "student_id": record["student_id"],
            "date": submission.date,
            "session": submission.session,
            "status": record["status"],
            "recorded_at": datetime.now(),
            "recorded_by": teacher_id
        }
        attendance_records.append(attendance_record)
    
    await attendance_collection.insert_many(attendance_records)
    
    return {"message": "Attendance submitted successfully", "records_count": len(attendance_records)}

@app.get("/api/classes/{class_id}")
async def get_class_details(class_id: str, teacher_id: str = Depends(verify_token)):
    class_doc = await classes_collection.find_one({"id": class_id, "teacher_id": teacher_id})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found or access denied")
    
    return class_doc

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)