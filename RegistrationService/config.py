import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Cloud Atlas Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://username:password@cluster.mongodb.net/hospital_management?retryWrites=true&w=majority")
DATABASE_NAME = os.getenv("DATABASE_NAME", "hospital_management")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Application Settings
APP_NAME = "Hospital Management System"
VERSION = "2.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
