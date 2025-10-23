from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from database_simple import (
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
    await initialize_default_data()

@app.on_event("shutdown")
async def on_shutdown():
    pass

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
        user_data = users_collection.get(username)
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
    user_data = users_collection.get(form_data.username)
    
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
    # Generate unique patient UID
    patients_collection = get_patients_collection()
    
    # Ensure patient_uid is unique
    while True:
        patient.patient_uid = generate_patient_uid()
        if patient.patient_uid not in patients_collection:
            break
    
    patient_dict = patient.dict(by_alias=True)
    patients_collection[patient.patient_uid] = patient_dict
    return Patient(**patient_dict)

@app.get("/api/v1/patients/{patient_uid}", response_model=Patient)
async def get_patient(patient_uid: int, current_user: User = Depends(get_current_user)):
    patients_collection = get_patients_collection()
    patient_data = patients_collection.get(patient_uid)
    if not patient_data:
        raise HTTPException(status_code=404, detail="Patient not found")
    return Patient(**patient_data)

# Appointment Management
@app.post("/api/v1/appointments/book", response_model=Appointment)
async def book_appointment(appointment_data: AppointmentCreate, current_user: User = Depends(get_current_user)):
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
    appointment_id = str(uuid.uuid4())
    appointments_collection[appointment_id] = appointment_dict
    
    return Appointment(**appointment_dict)

@app.get("/api/v1/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str, current_user: User = Depends(get_current_user)):
    appointments_collection = get_appointments_collection()
    appointment_data = appointments_collection.get(appointment_id)
    if not appointment_data:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return Appointment(**appointment_data)

# Vitals Management
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
    vitals_id = str(uuid.uuid4())
    vitals_collection[vitals_id] = vitals_dict
    return Vitals(**vitals_dict)

@app.get("/api/v1/vitals/patient/{patient_uid}", response_model=List[Vitals])
async def get_patient_vitals(patient_uid: int, current_user: User = Depends(get_current_user)):
    vitals_collection = get_vitals_collection()
    vitals_list = [Vitals(**vitals) for vitals in vitals_collection.values() 
                   if vitals.get("patient_uid") == patient_uid]
    return vitals_list

# Dashboard Statistics
@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    patients_collection = get_patients_collection()
    appointments_collection = get_appointments_collection()
    queue_collection = get_queue_collection()
    
    total_patients = len(patients_collection)
    today_appointments = len([a for a in appointments_collection.values() 
                             if a.get("appointment_time", "").startswith(str(datetime.now().date()))])
    pending_queue = len([q for q in queue_collection.values() 
                        if q.get("status") == "PENDING"])
    
    return {
        "total_patients": total_patients,
        "today_appointments": today_appointments,
        "pending_queue": pending_queue
    }
