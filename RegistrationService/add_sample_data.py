import asyncio
from database import connect_to_mongo, get_doctors_collection, get_patients_collection
from models import Doctor, Patient
from datetime import datetime, date

async def add_sample_data():
    """Add sample doctors and patients for testing"""
    try:
        await connect_to_mongo()
        
        doctors_collection = get_doctors_collection()
        patients_collection = get_patients_collection()
        
        # Add sample doctors
        sample_doctors = [
            {
                "doctor_id": "DOC001",
                "name": "Dr. John Smith",
                "specialization": "General Medicine",
                "department": "Internal Medicine",
                "is_available": True,
                "working_hours": {
                    "monday": {"start": "09:00", "end": "17:00"},
                    "tuesday": {"start": "09:00", "end": "17:00"},
                    "wednesday": {"start": "09:00", "end": "17:00"},
                    "thursday": {"start": "09:00", "end": "17:00"},
                    "friday": {"start": "09:00", "end": "17:00"}
                },
                "created_at": datetime.utcnow()
            },
            {
                "doctor_id": "DOC002",
                "name": "Dr. Sarah Johnson",
                "specialization": "Cardiology",
                "department": "Cardiology",
                "is_available": True,
                "working_hours": {
                    "monday": {"start": "08:00", "end": "16:00"},
                    "tuesday": {"start": "08:00", "end": "16:00"},
                    "wednesday": {"start": "08:00", "end": "16:00"},
                    "thursday": {"start": "08:00", "end": "16:00"},
                    "friday": {"start": "08:00", "end": "16:00"}
                },
                "created_at": datetime.utcnow()
            },
            {
                "doctor_id": "DOC003",
                "name": "Dr. Michael Brown",
                "specialization": "Pediatrics",
                "department": "Pediatrics",
                "is_available": True,
                "working_hours": {
                    "monday": {"start": "10:00", "end": "18:00"},
                    "tuesday": {"start": "10:00", "end": "18:00"},
                    "wednesday": {"start": "10:00", "end": "18:00"},
                    "thursday": {"start": "10:00", "end": "18:00"},
                    "friday": {"start": "10:00", "end": "18:00"}
                },
                "created_at": datetime.utcnow()
            }
        ]
        
        for doctor_data in sample_doctors:
            existing_doctor = await doctors_collection.find_one({"doctor_id": doctor_data["doctor_id"]})
            if not existing_doctor:
                await doctors_collection.insert_one(doctor_data)
                print(f"✅ Created doctor: {doctor_data['name']} ({doctor_data['doctor_id']})")
            else:
                print(f"ℹ️ Doctor {doctor_data['name']} already exists")
        
        # Add sample patients
        sample_patients = [
            {
                "patient_uid": 10000000001,
                "first_name": "Alice",
                "last_name": "Johnson",
                "dob": date(1990, 5, 15),
                "contact_number": "+1-555-0101",
                "address": "123 Main St, City, State",
                "emergency_contact": "+1-555-0102",
                "medical_history": ["Hypertension"],
                "allergies": ["Penicillin"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "patient_uid": 10000000002,
                "first_name": "Bob",
                "last_name": "Smith",
                "dob": date(1985, 8, 22),
                "contact_number": "+1-555-0201",
                "address": "456 Oak Ave, City, State",
                "emergency_contact": "+1-555-0202",
                "medical_history": ["Diabetes Type 2"],
                "allergies": ["Shellfish"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "patient_uid": 10000000003,
                "first_name": "Carol",
                "last_name": "Davis",
                "dob": date(1992, 12, 3),
                "contact_number": "+1-555-0301",
                "address": "789 Pine St, City, State",
                "emergency_contact": "+1-555-0302",
                "medical_history": [],
                "allergies": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        for patient_data in sample_patients:
            existing_patient = await patients_collection.find_one({"patient_uid": patient_data["patient_uid"]})
            if not existing_patient:
                await patients_collection.insert_one(patient_data)
                print(f"✅ Created patient: {patient_data['first_name']} {patient_data['last_name']} (ID: {patient_data['patient_uid']})")
            else:
                print(f"ℹ️ Patient {patient_data['first_name']} {patient_data['last_name']} already exists")
        
        print("\n🎉 Sample data added successfully!")
        print("📋 Available doctors:")
        async for doctor in doctors_collection.find({}):
            print(f"  - {doctor['name']} ({doctor['doctor_id']}) - {doctor['specialization']}")
        
        print("\n📋 Available patients:")
        async for patient in patients_collection.find({}):
            print(f"  - {patient['first_name']} {patient['last_name']} (ID: {patient['patient_uid']})")
            
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")

if __name__ == "__main__":
    asyncio.run(add_sample_data())
