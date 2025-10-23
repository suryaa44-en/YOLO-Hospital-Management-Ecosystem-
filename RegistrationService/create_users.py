import asyncio
from database import connect_to_mongo, get_users_collection
from models import User, RoleEnum
from security import get_password_hash

async def create_users():
    """Create default users manually"""
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        
        users_collection = get_users_collection()
        
        # Check if users already exist
        existing_reception = await users_collection.find_one({"username": "reception"})
        existing_nurse = await users_collection.find_one({"username": "nurse"})
        existing_doctor = await users_collection.find_one({"username": "doctor"})
        
        # Create users if they don't exist
        if not existing_reception:
            reception_user = User(
                username="reception",
                hashed_password=get_password_hash("reception123"),
                role=RoleEnum.RECEPTION
            )
            await users_collection.insert_one(reception_user.dict(by_alias=True))
            print("✅ Created reception user")
        else:
            print("ℹ️ Reception user already exists")
            
        if not existing_nurse:
            nurse_user = User(
                username="nurse",
                hashed_password=get_password_hash("nurse123"),
                role=RoleEnum.NURSE
            )
            await users_collection.insert_one(nurse_user.dict(by_alias=True))
            print("✅ Created nurse user")
        else:
            print("ℹ️ Nurse user already exists")
            
        if not existing_doctor:
            doctor_user = User(
                username="doctor",
                hashed_password=get_password_hash("doctor123"),
                role=RoleEnum.DOCTOR
            )
            await users_collection.insert_one(doctor_user.dict(by_alias=True))
            print("✅ Created doctor user")
        else:
            print("ℹ️ Doctor user already exists")
            
        # List all users
        print("\n📋 All users in database:")
        async for user in users_collection.find({}):
            print(f"  - Username: {user['username']}, Role: {user['role']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_users())
