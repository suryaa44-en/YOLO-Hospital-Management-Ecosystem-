from sqlmodel import create_engine, SQLModel, Session, select
from dotenv import load_dotenv
import os
from sqlalchemy import inspect, text

from models import Patient, generate_patient_uid

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    _ensure_patient_uid_column()


def _ensure_patient_uid_column():
    inspector = inspect(engine)
    if "patients" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("patients")}
    if "patient_uid" in columns:
        return

    # Add column without constraints first so existing rows can be backfilled.
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE patients ADD COLUMN patient_uid BIGINT"))

    with Session(engine) as session:
        patients = session.exec(select(Patient)).all()
        used_ids = set()
        for patient in patients:
            uid = generate_patient_uid()
            # Ensure generated UID stays unique within the batch before committing.
            while uid in used_ids:
                uid = generate_patient_uid()
            patient.patient_uid = uid
            used_ids.add(uid)
        session.commit()

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE patients ALTER COLUMN patient_uid SET NOT NULL"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_patients_patient_uid ON patients(patient_uid)"))
