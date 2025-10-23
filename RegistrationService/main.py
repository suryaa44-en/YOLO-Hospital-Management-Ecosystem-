from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session
from database import get_session, create_db_and_tables
from models import Patient, Appointment, StatusEnum
import uuid
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/api/v1/patients/register", response_model=Patient)
def register_patient(patient: Patient, session: Session = Depends(get_session)):
    session.add(patient)
    session.commit()
    session.refresh(patient)
    return patient

@app.post("/api/v1/appointments/book", response_model=Appointment)
def book_appointment(appointment: Appointment, session: Session = Depends(get_session)):
    # Simple logic for queue token
    appointment.queue_token = f"{appointment.status}-{uuid.uuid4().hex[:6].upper()}"
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return appointment

@app.get("/api/v1/appointments/{appointment_id}", response_model=Appointment)
def get_appointment(appointment_id: uuid.UUID, session: Session = Depends(get_session)):
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment
