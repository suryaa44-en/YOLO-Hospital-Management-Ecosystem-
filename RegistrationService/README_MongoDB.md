# Hospital Management System - MongoDB Cloud Atlas Version

## Overview
This is a comprehensive hospital management system built with FastAPI and MongoDB Cloud Atlas. It includes patient registration, appointment booking, vitals recording, queue management, and real-time dashboard features.

## New Features Added

### 1. Patient Vitals Recording
- **Mobile/Tablet Support**: Optimized interface for nurses to record vitals on mobile devices
- **Comprehensive Vitals**: Temperature, blood pressure, heart rate, respiratory rate, oxygen saturation, weight, height
- **Device Tracking**: Records device information for audit trails
- **Vitals History**: View complete vitals history for each patient

### 2. Digital Queue Management
- **Real-time Queue**: Live queue management with status updates
- **Priority Management**: Support for different priority levels (LOW, MEDIUM, HIGH, URGENT)
- **Wait Time Estimation**: Automatic wait time calculations
- **Status Tracking**: PENDING → IN_PROGRESS → COMPLETED workflow

### 3. Enhanced Appointment System
- **Online Booking**: Support for online appointment booking
- **Walk-in Management**: Handle walk-in patients efficiently
- **Kiosk Registration**: Support for kiosk-based patient registration
- **Appointment Types**: Different appointment types with proper tracking

### 4. Dashboard Analytics
- **Real-time Statistics**: Total patients, today's appointments, pending queue
- **Visual Dashboard**: Clean, modern interface with statistics cards
- **Auto-refresh**: Real-time updates for queue management

## Setup Instructions

### 1. MongoDB Cloud Atlas Setup

1. **Create MongoDB Atlas Account**:
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Create a free account
   - Create a new cluster (M0 Sandbox is free)

2. **Get Connection String**:
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password
   - Replace `<dbname>` with your database name

3. **Configure Environment**:
   ```bash
   # Create .env file
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/hospital_management?retryWrites=true&w=majority
   DATABASE_NAME=hospital_management
   SECRET_KEY=your-secret-key-here
   ```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Authentication
- `POST /token` - Login and get access token

### Patient Management
- `POST /api/v1/patients/register` - Register new patient
- `GET /api/v1/patients/{patient_uid}` - Get patient details

### Appointment Management
- `POST /api/v1/appointments/book` - Book appointment
- `GET /api/v1/appointments/{appointment_id}` - Get appointment details

### Vitals Management (New)
- `POST /api/v1/vitals/record` - Record patient vitals
- `GET /api/v1/vitals/patient/{patient_uid}` - Get patient vitals history

### Queue Management (New)
- `GET /api/v1/queue/doctor/{doctor_id}` - Get doctor's queue
- `PUT /api/v1/queue/{queue_id}/update` - Update queue status

### Doctor Management
- `GET /api/v1/doctors` - Get all doctors
- `GET /api/v1/doctors/{doctor_id}` - Get doctor details

### Dashboard
- `GET /api/v1/dashboard/stats` - Get dashboard statistics

## User Interfaces

### 1. Main Dashboard (`/dashboard`)
- Patient registration
- Appointment booking
- Status checking
- Dashboard statistics

### 2. Vitals Recording (`/vitals`)
- Mobile-optimized vitals recording
- Device information tracking
- Vitals history viewing

### 3. Queue Management (`/queue`)
- Real-time queue monitoring
- Status updates
- Wait time management

## Database Collections

### Collections Created:
- `users` - System users (doctors, nurses, reception)
- `patients` - Patient information
- `appointments` - Appointment records
- `vitals` - Patient vitals records
- `queue` - Queue management
- `doctors` - Doctor information

### Indexes:
- Unique indexes on patient_uid, username, doctor_id
- Performance indexes on frequently queried fields
- Compound indexes for complex queries

## Security Features

- JWT-based authentication
- Role-based access control
- Password hashing with bcrypt
- CORS support for mobile/tablet access

## Mobile/Tablet Support

- Responsive design for all interfaces
- Touch-friendly controls
- Device information tracking
- Offline-capable forms (with sync when online)

## Production Considerations

1. **Environment Variables**: Set proper SECRET_KEY and MONGODB_URL
2. **CORS Configuration**: Update CORS settings for production domains
3. **Database Security**: Use proper MongoDB Atlas security settings
4. **SSL/TLS**: Ensure HTTPS in production
5. **Monitoring**: Set up MongoDB Atlas monitoring and alerts

## Default Credentials

- **Username**: reception
- **Password**: password

## Features Summary

✅ **Patient Registration**: Complete patient management system
✅ **Appointment Booking**: Online, walk-in, and kiosk registration
✅ **Vitals Recording**: Mobile-optimized vitals recording system
✅ **Queue Management**: Real-time digital queue system
✅ **Dashboard Analytics**: Comprehensive statistics and monitoring
✅ **Mobile Support**: Responsive design for tablets and mobile devices
✅ **MongoDB Cloud Atlas**: Scalable cloud database
✅ **Real-time Updates**: Live queue and status updates
✅ **Audit Trails**: Complete tracking of all operations
✅ **Role-based Access**: Different access levels for different user types

This system addresses all the requirements mentioned:
- Manual vitals recording → Automated mobile/tablet vitals recording
- Appointment management → Comprehensive online/offline appointment system
- Queue management → Digital queue with real-time updates
- Data synchronization → Cloud-based system with automatic sync
