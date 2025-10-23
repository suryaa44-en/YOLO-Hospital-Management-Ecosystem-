import uuid
from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel

class StatusEnum(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    WALK_IN = "WALK_IN"

class Patient(SQLModel, table=True):
    __tablename__ = "patients"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    first_name: str
    last_name: str
    dob: date
    contact_number: str
    address: str
    appointments: List["Appointment"] = Relationship(back_populates="patient")

class Appointment(SQLModel, table=True):
    __tablename__ = "appointments"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_id: uuid.UUID = Field(foreign_key="patients.id")
    doctor_id: str  # Placeholder for now
    appointment_time: datetime
    status: StatusEnum
    queue_token: str
    patient: Optional[Patient] = Relationship(back_populates="appointments")
