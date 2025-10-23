from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from database import get_session, create_db_and_tables, engine
from models import Patient, Appointment, StatusEnum, User, RoleEnum
import uuid
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from jose import JWTError, jwt
from security import verify_password, create_access_token, get_password_hash, SECRET_KEY, ALGORITHM
from datetime import timedelta
from pydantic import BaseModel
from models import generate_patient_uid


class Token(BaseModel):
    access_token: str
    token_type: str


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_index():
    return FileResponse('static/login.html')

@app.get("/dashboard")
async def read_dashboard():
    return FileResponse('static/index.html')


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    with Session(engine) as session:
        statement = select(User).where(User.username == "reception")
        user = session.exec(statement).first()
        if not user:
            hashed_password = get_password_hash("password")
            reception_user = User(username="reception", hashed_password=hashed_password, role=RoleEnum.RECEPTION)
            session.add(reception_user)
            session.commit()


async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        statement = select(User).where(User.username == username)
        user = session.exec(statement).first()
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/v1/patients/register", response_model=Patient)
def register_patient(patient: Patient, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    patient.patient_uid = generate_patient_uid()
    session.add(patient)
    session.commit()
    session.refresh(patient)
    return patient

@app.post("/api/v1/appointments/book", response_model=Appointment)
def book_appointment(appointment: Appointment, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    appointment.queue_token = f"{appointment.status}-{uuid.uuid4().hex[:6].upper()}"
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return appointment

@app.get("/api/v1/appointments/{appointment_id}", response_model=Appointment)
def get_appointment(appointment_id: uuid.UUID, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment
