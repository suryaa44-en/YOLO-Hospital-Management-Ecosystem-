import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, DESCENDING
from dotenv import load_dotenv
from typing import Optional
import asyncio
from models import User, Patient, Appointment, Vitals, Queue, Doctor, RoleEnum, generate_patient_uid
from security import get_password_hash

load_dotenv()

# MongoDB Cloud Atlas connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://username:password@cluster.mongodb.net/hospital_management?retryWrites=true&w=majority")
DATABASE_NAME = os.getenv("DATABASE_NAME", "hospital_management")

# Global client instance
client: Optional[AsyncIOMotorClient] = None
database = None

async def get_database():
    """Get database instance"""
    global database
    if database is None:
        await connect_to_mongo()
    return database

async def connect_to_mongo():
    """Create database connection"""
    global client, database
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        database = client[DATABASE_NAME]
        
        # Test the connection
        await client.admin.command('ping')
        print("Successfully connected to MongoDB Cloud Atlas!")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    global client
    if client:
        client.close()

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Users collection indexes
        await database.users.create_indexes([
            IndexModel([("username", ASCENDING)], unique=True),
            IndexModel([("role", ASCENDING)]),
            IndexModel([("is_active", ASCENDING)])
        ])
        
        # Patients collection indexes
        await database.patients.create_indexes([
            IndexModel([("patient_uid", ASCENDING)], unique=True),
            IndexModel([("contact_number", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)])
        ])
        
        # Appointments collection indexes
        await database.appointments.create_indexes([
            IndexModel([("patient_uid", ASCENDING)]),
            IndexModel([("doctor_id", ASCENDING)]),
            IndexModel([("appointment_time", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("queue_token", ASCENDING)], unique=True),
            IndexModel([("created_at", DESCENDING)])
        ])
        
        # Vitals collection indexes
        await database.vitals.create_indexes([
            IndexModel([("patient_uid", ASCENDING)]),
            IndexModel([("recorded_by", ASCENDING)]),
            IndexModel([("recorded_at", DESCENDING)])
        ])
        
        # Queue collection indexes
        await database.queue.create_indexes([
            IndexModel([("doctor_id", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("priority", ASCENDING)]),
            IndexModel([("queue_number", ASCENDING)]),
            IndexModel([("created_at", ASCENDING)])
        ])
        
        # Doctors collection indexes
        await database.doctors.create_indexes([
            IndexModel([("doctor_id", ASCENDING)], unique=True),
            IndexModel([("specialization", ASCENDING)]),
            IndexModel([("department", ASCENDING)]),
            IndexModel([("is_available", ASCENDING)])
        ])
        
        print("Database indexes created successfully!")
        
    except Exception as e:
        print(f"Error creating indexes: {e}")

async def initialize_default_data():
    """Initialize default users and data"""
    try:
        # Create default users for each role
        users_to_create = [
            {
                "username": "reception",
                "password": "reception123",
                "role": RoleEnum.RECEPTION,
                "full_name": "Reception Staff"
            },
            {
                "username": "nurse",
                "password": "nurse123",
                "role": RoleEnum.NURSE,
                "full_name": "Nurse Staff"
            },
            {
                "username": "doctor",
                "password": "doctor123",
                "role": RoleEnum.DOCTOR,
                "full_name": "Dr. Smith"
            }
        ]
        
        for user_data in users_to_create:
            existing_user = await database.users.find_one({"username": user_data["username"]})
            if not existing_user:
                user = User(
                    username=user_data["username"],
                    hashed_password=get_password_hash(user_data["password"]),
                    role=user_data["role"]
                )
                await database.users.insert_one(user.dict(by_alias=True))
                print(f"Created {user_data['role']} user: {user_data['username']}")
        
        # Check if any doctors exist, if not create a sample doctor
        doctor_count = await database.doctors.count_documents({})
        if doctor_count == 0:
            sample_doctor = Doctor(
                doctor_id="DOC001",
                name="Dr. John Smith",
                specialization="General Medicine",
                department="Internal Medicine",
                working_hours={
                    "monday": {"start": "09:00", "end": "17:00"},
                    "tuesday": {"start": "09:00", "end": "17:00"},
                    "wednesday": {"start": "09:00", "end": "17:00"},
                    "thursday": {"start": "09:00", "end": "17:00"},
                    "friday": {"start": "09:00", "end": "17:00"}
                }
            )
            await database.doctors.insert_one(sample_doctor.dict(by_alias=True))
            print("Sample doctor created!")
            
    except Exception as e:
        print(f"Error initializing default data: {e}")

# Collection getters
def get_users_collection():
    return database.users

def get_patients_collection():
    return database.patients

def get_appointments_collection():
    return database.appointments

def get_vitals_collection():
    return database.vitals

def get_queue_collection():
    return database.queue

def get_doctors_collection():
    return database.doctors
