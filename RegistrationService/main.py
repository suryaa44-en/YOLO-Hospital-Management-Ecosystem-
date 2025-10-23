from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from database import (
    get_database, connect_to_mongo, close_mongo_connection, 
    get_users_collection, get_patients_collection, get_appointments_collection,
    get_vitals_collection, get_queue_collection, get_doctors_collection,
    initialize_default_data
)
from models import (
    Patient, Appointment, Vitals, Queue, Doctor, User, 
    StatusEnum, RoleEnum, PriorityEnum, generate_patient_uid
)
import uuid
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from jose import JWTError, jwt
from security import verify_password, create_access_token, get_password_hash, SECRET_KEY, ALGORITHM
from config import MONGODB_URL, DATABASE_NAME
from datetime import timedelta, datetime
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from bson import ObjectId
import asyncio


class Token(BaseModel):
    access_token: str
    token_type: str

class VitalsInput(BaseModel):
    patient_uid: int
    temperature: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    notes: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None

class QueueUpdate(BaseModel):
    status: StatusEnum
    estimated_wait_time: Optional[int] = None

class AppointmentCreate(BaseModel):
    patient_uid: int
    doctor_id: str
    appointment_time: datetime
    status: StatusEnum = StatusEnum.PENDING
    priority: PriorityEnum = PriorityEnum.MEDIUM
    is_online_booking: bool = False
    is_walk_in: bool = False
    is_kiosk_registration: bool = False
    notes: Optional[str] = None

app = FastAPI(title="Hospital Management System", version="2.0.0")

# CORS middleware for mobile/tablet support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/login.html')

@app.get("/dashboard")
async def read_dashboard():
    return FileResponse('static/index.html')

@app.get("/vitals")
async def read_vitals():
    return FileResponse('static/vitals.html')

@app.get("/queue")
async def read_queue():
    return FileResponse('static/queue.html')

@app.on_event("startup")
async def on_startup():
    await connect_to_mongo()
    await initialize_default_data()

@app.on_event("shutdown")
async def on_shutdown():
    await close_mongo_connection()


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        users_collection = get_users_collection()
        user_data = await users_collection.find_one({"username": username})
        if user_data is None:
            raise credentials_exception
        
        # Convert to User model
        user = User(**user_data)
        return user
    except JWTError:
        raise credentials_exception

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    users_collection = get_users_collection()
    user_data = await users_collection.find_one({"username": form_data.username})
    
    if not user_data or not verify_password(form_data.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user_data["username"], "role": user_data["role"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Patient Management
@app.post("/api/v1/patients/register", response_model=Patient)
async def register_patient(patient: Patient, current_user: User = Depends(get_current_user)):
    try:
        # Generate unique patient UID
        patients_collection = get_patients_collection()
        
        # Ensure patient_uid is unique
        while True:
    patient.patient_uid = generate_patient_uid()
            existing = await patients_collection.find_one({"patient_uid": patient.patient_uid})
            if not existing:
                break
        
        # Convert date string to date object if needed
        if isinstance(patient.dob, str):
            from datetime import datetime
            patient.dob = datetime.strptime(patient.dob, "%Y-%m-%d").date()
        
        patient_dict = patient.dict(by_alias=True)
        result = await patients_collection.insert_one(patient_dict)
        patient_dict["_id"] = result.inserted_id
        
        print(f"✅ Patient registered: {patient.first_name} {patient.last_name} (ID: {patient.patient_uid})")
        return Patient(**patient_dict)
    except Exception as e:
        print(f"❌ Error registering patient: {e}")
        raise HTTPException(status_code=500, detail=f"Error registering patient: {str(e)}")

@app.get("/api/v1/patients", response_model=List[Patient])
async def get_all_patients(current_user: User = Depends(get_current_user)):
    """Get all patients - for reception staff"""
    if current_user.role != RoleEnum.RECEPTION:
        raise HTTPException(status_code=403, detail="Only reception staff can view all patients")
    
    try:
        patients_collection = get_patients_collection()
        patients_cursor = patients_collection.find({}).sort("created_at", -1)
        patients_list = await patients_cursor.to_list(length=100)
        return [Patient(**patient) for patient in patients_list]
    except Exception as e:
        print(f"❌ Error getting patients: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting patients: {str(e)}")

@app.get("/api/v1/patients/{patient_uid}", response_model=Patient)
async def get_patient(patient_uid: int, current_user: User = Depends(get_current_user)):
    patients_collection = get_patients_collection()
    patient_data = await patients_collection.find_one({"patient_uid": patient_uid})
    if not patient_data:
        raise HTTPException(status_code=404, detail="Patient not found")
    return Patient(**patient_data)

# Appointment Management
@app.post("/api/v1/appointments/book", response_model=Appointment)
async def book_appointment(appointment_data: AppointmentCreate, current_user: User = Depends(get_current_user)):
    try:
        appointments_collection = get_appointments_collection()
        
        # Generate queue token
        queue_token = f"{appointment_data.status}-{uuid.uuid4().hex[:6].upper()}"
        
        appointment = Appointment(
            patient_uid=appointment_data.patient_uid,
            doctor_id=appointment_data.doctor_id,
            appointment_time=appointment_data.appointment_time,
            status=appointment_data.status,
            queue_token=queue_token,
            priority=appointment_data.priority,
            is_online_booking=appointment_data.is_online_booking,
            is_walk_in=appointment_data.is_walk_in,
            is_kiosk_registration=appointment_data.is_kiosk_registration,
            notes=appointment_data.notes
        )
        
        appointment_dict = appointment.dict(by_alias=True)
        result = await appointments_collection.insert_one(appointment_dict)
        appointment_dict["_id"] = result.inserted_id
        
        # Add to queue if not online booking
        if not appointment_data.is_online_booking:
            await add_to_queue(appointment_dict["_id"], appointment_data.patient_uid, 
                              appointment_data.doctor_id, appointment_data.priority)
        
        print(f"✅ Appointment booked: Patient {appointment_data.patient_uid} with Doctor {appointment_data.doctor_id}")
        return Appointment(**appointment_dict)
    except Exception as e:
        print(f"❌ Error booking appointment: {e}")
        raise HTTPException(status_code=500, detail=f"Error booking appointment: {str(e)}")

@app.get("/api/v1/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str, current_user: User = Depends(get_current_user)):
    appointments_collection = get_appointments_collection()
    appointment_data = await appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if not appointment_data:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return Appointment(**appointment_data)

# Vitals Management (New Feature)
@app.post("/api/v1/vitals/record", response_model=Vitals)
async def record_vitals(vitals_data: VitalsInput, current_user: User = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.NURSE, RoleEnum.DOCTOR]:
        raise HTTPException(status_code=403, detail="Only nurses and doctors can record vitals")
    
    vitals = Vitals(
        patient_uid=vitals_data.patient_uid,
        recorded_by=current_user.username,
        temperature=vitals_data.temperature,
        blood_pressure_systolic=vitals_data.blood_pressure_systolic,
        blood_pressure_diastolic=vitals_data.blood_pressure_diastolic,
        heart_rate=vitals_data.heart_rate,
        respiratory_rate=vitals_data.respiratory_rate,
        oxygen_saturation=vitals_data.oxygen_saturation,
        weight=vitals_data.weight,
        height=vitals_data.height,
        notes=vitals_data.notes,
        device_info=vitals_data.device_info
    )
    
    vitals_collection = get_vitals_collection()
    vitals_dict = vitals.dict(by_alias=True)
    result = await vitals_collection.insert_one(vitals_dict)
    vitals_dict["_id"] = result.inserted_id
    return Vitals(**vitals_dict)

@app.get("/api/v1/vitals/patient/{patient_uid}", response_model=List[Vitals])
async def get_patient_vitals(patient_uid: int, current_user: User = Depends(get_current_user)):
    vitals_collection = get_vitals_collection()
    vitals_cursor = vitals_collection.find({"patient_uid": patient_uid}).sort("recorded_at", -1)
    vitals_list = await vitals_cursor.to_list(length=100)
    return [Vitals(**vitals) for vitals in vitals_list]

# Queue Management (New Feature)
async def add_to_queue(appointment_id: ObjectId, patient_uid: int, doctor_id: str, priority: PriorityEnum):
    try:
        queue_collection = get_queue_collection()
        
        # Get next queue number for this doctor
        last_queue = await queue_collection.find_one(
            {"doctor_id": doctor_id}, 
            sort=[("queue_number", -1)]
        )
        next_queue_number = (last_queue["queue_number"] + 1) if last_queue else 1
        
        queue_item = Queue(
            appointment_id=appointment_id,
            patient_uid=patient_uid,
            doctor_id=doctor_id,
            queue_number=next_queue_number,
            status=StatusEnum.PENDING,
            priority=priority
        )
        
        queue_dict = queue_item.dict(by_alias=True)
        await queue_collection.insert_one(queue_dict)
        print(f"✅ Added to queue: Patient {patient_uid} - Queue #{next_queue_number} for Doctor {doctor_id}")
    except Exception as e:
        print(f"❌ Error adding to queue: {e}")

@app.get("/api/v1/queue/doctor/{doctor_id}", response_model=List[Queue])
async def get_doctor_queue(doctor_id: str, current_user: User = Depends(get_current_user)):
    queue_collection = get_queue_collection()
    queue_cursor = queue_collection.find({"doctor_id": doctor_id}).sort("queue_number", 1)
    queue_list = await queue_cursor.to_list(length=100)
    return [Queue(**queue_item) for queue_item in queue_list]

@app.put("/api/v1/queue/{queue_id}/update")
async def update_queue_status(queue_id: str, update_data: QueueUpdate, current_user: User = Depends(get_current_user)):
    queue_collection = get_queue_collection()
    
    update_dict = {"status": update_data.status, "updated_at": datetime.utcnow()}
    if update_data.estimated_wait_time:
        update_dict["estimated_wait_time"] = update_data.estimated_wait_time
    
    if update_data.status == StatusEnum.IN_PROGRESS:
        update_dict["called_at"] = datetime.utcnow()
    elif update_data.status == StatusEnum.COMPLETED:
        update_dict["served_at"] = datetime.utcnow()
    
    result = await queue_collection.update_one(
        {"_id": ObjectId(queue_id)}, 
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    return {"message": "Queue status updated successfully"}

# Doctor Management
@app.get("/api/v1/doctors", response_model=List[Doctor])
async def get_doctors(current_user: User = Depends(get_current_user)):
    doctors_collection = get_doctors_collection()
    doctors_cursor = doctors_collection.find({"is_available": True})
    doctors_list = await doctors_cursor.to_list(length=100)
    return [Doctor(**doctor) for doctor in doctors_list]

@app.get("/api/v1/doctors/{doctor_id}", response_model=Doctor)
async def get_doctor(doctor_id: str, current_user: User = Depends(get_current_user)):
    doctors_collection = get_doctors_collection()
    doctor_data = await doctors_collection.find_one({"doctor_id": doctor_id})
    if not doctor_data:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return Doctor(**doctor_data)

# Doctor Queue Printing
@app.get("/api/v1/doctors/{doctor_id}/queue/print")
async def print_doctor_queue(doctor_id: str, current_user: User = Depends(get_current_user)):
    try:
        queue_collection = get_queue_collection()
        patients_collection = get_patients_collection()
        appointments_collection = get_appointments_collection()
        
        # Get queue for this doctor
        queue_cursor = queue_collection.find({"doctor_id": doctor_id}).sort("queue_number", 1)
        queue_list = await queue_cursor.to_list(length=100)
        
        # Get patient details for each queue item
        queue_with_patients = []
        for queue_item in queue_list:
            patient_data = await patients_collection.find_one({"patient_uid": queue_item["patient_uid"]})
            appointment_data = await appointments_collection.find_one({"_id": queue_item["appointment_id"]})
            
            queue_with_patients.append({
                "queue_number": queue_item["queue_number"],
                "patient_uid": queue_item["patient_uid"],
                "patient_name": f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}" if patient_data else "Unknown",
                "status": queue_item["status"],
                "priority": queue_item["priority"],
                "appointment_time": appointment_data.get("appointment_time") if appointment_data else None,
                "created_at": queue_item["created_at"]
            })
        
        print(f"📋 Doctor {doctor_id} Queue Print:")
        for item in queue_with_patients:
            print(f"  #{item['queue_number']}: {item['patient_name']} (ID: {item['patient_uid']}) - {item['status']} - {item['priority']}")
        
        return {
            "doctor_id": doctor_id,
            "queue": queue_with_patients,
            "total_patients": len(queue_with_patients),
            "printed_at": datetime.utcnow()
        }
    except Exception as e:
        print(f"❌ Error printing doctor queue: {e}")
        raise HTTPException(status_code=500, detail=f"Error printing doctor queue: {str(e)}")

# Dashboard Statistics
@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    try:
        patients_collection = get_patients_collection()
        appointments_collection = get_appointments_collection()
        queue_collection = get_queue_collection()
        
        total_patients = await patients_collection.count_documents({})
        today_appointments = await appointments_collection.count_documents({
            "appointment_time": {
                "$gte": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                "$lt": datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
            }
        })
        pending_queue = await queue_collection.count_documents({"status": StatusEnum.PENDING})
        
        return {
            "total_patients": total_patients,
            "today_appointments": today_appointments,
            "pending_queue": pending_queue
        }
    except Exception as e:
        print(f"❌ Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting dashboard stats: {str(e)}")
