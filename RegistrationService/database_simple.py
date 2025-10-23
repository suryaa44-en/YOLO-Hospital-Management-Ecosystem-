# Simple in-memory database for testing
from typing import Dict, List, Any
import asyncio
from datetime import datetime
from models import User, Patient, Appointment, Vitals, Queue, Doctor, RoleEnum
from security import get_password_hash

# In-memory storage
users_db: Dict[str, Dict] = {}
patients_db: Dict[int, Dict] = {}
appointments_db: Dict[str, Dict] = {}
vitals_db: Dict[str, Dict] = {}
queue_db: Dict[str, Dict] = {}
doctors_db: Dict[str, Dict] = {}

# Initialize with default users
def initialize_default_users():
    """Initialize default users for testing"""
    default_users = [
        {
            "username": "reception",
            "password": "reception123",
            "role": "RECEPTION",
            "full_name": "Reception Staff"
        },
        {
            "username": "nurse",
            "password": "nurse123",
            "role": "NURSE",
            "full_name": "Nurse Staff"
        },
        {
            "username": "doctor",
            "password": "doctor123",
            "role": "DOCTOR",
            "full_name": "Dr. Smith"
        }
    ]
    
    for user_data in default_users:
        if user_data["username"] not in users_db:
            users_db[user_data["username"]] = {
                "username": user_data["username"],
                "hashed_password": get_password_hash(user_data["password"]),
                "role": user_data["role"],
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            print(f"Created {user_data['role']} user: {user_data['username']}")

# Initialize default data
initialize_default_users()

# Collection getters
def get_users_collection():
    return users_db

def get_patients_collection():
    return patients_db

def get_appointments_collection():
    return appointments_db

def get_vitals_collection():
    return vitals_db

def get_queue_collection():
    return queue_db

def get_doctors_collection():
    return doctors_db

# Simple database operations
async def connect_to_mongo():
    """Mock connection for testing"""
    print("Connected to in-memory database for testing!")
    return True

async def initialize_default_data():
    """Initialize default data"""
    print("Default data initialized!")
    return True

async def close_mongo_connection():
    """Mock close connection"""
    print("Connection closed!")
    return True
