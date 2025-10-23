import uuid
import random
from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel

class RoleEnum(str, Enum):
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    RECEPTION = "RECEPTION"

class StatusEnum(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    WALK_IN = "WALK_IN"

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: RoleEnum

def generate_patient_uid():
    return random.randint(100_000_000_00, 999_999_999_99)

class Patient(SQLModel, table=True):
    __tablename__ = "patients"
    id: int = Field(primary_key=True)
    patient_uid: int = Field(unique=True, index=True)
    first_name: str
    last_name: str
    dob: date
    contact_number: str
    address: str
    appointments: List["Appointment"] = Relationship(back_populates="patient")

class Appointment(SQLModel, table=True):
    __tablename__ = "appointments"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_uid: int = Field(foreign_key="patients.patient_uid")
    doctor_id: str
    appointment_time: datetime
    status: StatusEnum
    queue_token: str
    patient: Optional[Patient] = Relationship(back_populates="appointments")
