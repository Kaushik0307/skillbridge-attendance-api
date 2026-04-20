import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import os
from datetime import date, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test_skillbridge.db"
os.environ["JWT_SECRET_KEY"] = "test-standard-secret"
os.environ["MONITORING_TOKEN_SECRET_KEY"] = "test-monitoring-secret"
os.environ["MONITORING_API_KEY"] = "test-monitoring-api-key"

from src.db.base import Base
from src.db.session import get_db
from src.main import app
from src.models.enums import UserRole
from src.models.models import Batch, BatchStudent, BatchTrainer, Session as SessionModel, User
from src.core.security import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_skillbridge.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    institution = User(name="Institution A", email="inst@test.com", hashed_password=hash_password("Password123!"), role=UserRole.institution)
    db.add(institution)
    db.commit(); db.refresh(institution)

    trainer = User(name="Trainer A", email="trainer@test.com", hashed_password=hash_password("Password123!"), role=UserRole.trainer, institution_id=institution.id)
    student = User(name="Student A", email="student@test.com", hashed_password=hash_password("Password123!"), role=UserRole.student, institution_id=institution.id)
    pm = User(name="PM A", email="pm@test.com", hashed_password=hash_password("Password123!"), role=UserRole.programme_manager)
    mo = User(name="MO A", email="mo@test.com", hashed_password=hash_password("Password123!"), role=UserRole.monitoring_officer)
    db.add_all([trainer, student, pm, mo])
    db.commit(); db.refresh(trainer); db.refresh(student)

    batch = Batch(name="Batch Test", institution_id=institution.id)
    db.add(batch)
    db.commit(); db.refresh(batch)

    db.add(BatchTrainer(batch_id=batch.id, trainer_id=trainer.id))
    db.add(BatchStudent(batch_id=batch.id, student_id=student.id))
    db.commit()

    active_session = SessionModel(
        batch_id=batch.id,
        trainer_id=trainer.id,
        title="Active Session",
        date=date.today(),
        start_time=time(0, 0),
        end_time=time(23, 59),
    )
    db.add(active_session)
    db.commit()
    db.close()

    def override_get_db():
        test_db = TestingSessionLocal()
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    return TestClient(app)


def login(client, email, password="Password123!"):
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]
