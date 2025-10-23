import asyncio
from database import connect_to_mongo, get_users_collection

async def check_users():
    """Check what users exist in the database"""
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        
        users_collection = get_users_collection()
        
        print("📋 Users in database:")
        user_count = 0
        async for user in users_collection.find({}):
            user_count += 1
            print(f"  {user_count}. Username: {user['username']}")
            print(f"     Role: {user['role']}")
            print(f"     Active: {user.get('is_active', True)}")
            print(f"     Created: {user.get('created_at', 'Unknown')}")
            print()
            
        if user_count == 0:
            print("❌ No users found in database!")
        else:
            print(f"✅ Found {user_count} users")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_users())
