from datetime import date, datetime, time, timedelta, timezone

from src.core.config import settings
from src.core.security import hash_password
from src.db.base import Base
from src.db.session import SessionLocal, engine
from src.models.enums import AttendanceStatus, UserRole
from src.models.models import Attendance, Batch, BatchStudent, BatchTrainer, Session as SessionModel, User


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).first():
            print("Seed skipped: data already exists")
            return

        password = hash_password(settings.seed_default_password)

        institutions = [
            User(
                name="North Skill Institute",
                email="institution1@skillbridgeapp.com",
                hashed_password=password,
                role=UserRole.institution,
            ),
            User(
                name="South Skill Institute",
                email="institution2@skillbridgeapp.com",
                hashed_password=password,
                role=UserRole.institution,
            ),
        ]
        db.add_all(institutions)
        db.commit()
        for inst in institutions:
            db.refresh(inst)

        trainers = []
        for idx in range(4):
            inst = institutions[idx % 2]
            trainers.append(
                User(
                    name=f"Trainer {idx+1}",
                    email=f"trainer{idx+1}@skillbridgeapp.com",
                    hashed_password=password,
                    role=UserRole.trainer,
                    institution_id=inst.id,
                )
            )
        db.add_all(trainers)

        students = []
        for idx in range(15):
            inst = institutions[idx % 2]
            students.append(
                User(
                    name=f"Student {idx+1}",
                    email=f"student{idx+1}@skillbridgeapp.com",
                    hashed_password=password,
                    role=UserRole.student,
                    institution_id=inst.id,
                )
            )

        programme_manager = User(
            name="Programme Manager",
            email="pm@skillbridgeapp.com",
            hashed_password=password,
            role=UserRole.programme_manager,
        )
        monitoring = User(
            name="Monitoring Officer",
            email="monitor@skillbridgeapp.com",
            hashed_password=password,
            role=UserRole.monitoring_officer,
        )
        db.add_all(students + [programme_manager, monitoring])
        db.commit()

        trainers = db.query(User).filter(User.role == UserRole.trainer).all()
        students = db.query(User).filter(User.role == UserRole.student).all()

        batches = [
            Batch(name="Batch Alpha", institution_id=institutions[0].id),
            Batch(name="Batch Beta", institution_id=institutions[0].id),
            Batch(name="Batch Gamma", institution_id=institutions[1].id),
        ]
        db.add_all(batches)
        db.commit()
        for batch in batches:
            db.refresh(batch)

        assignments = [
            BatchTrainer(batch_id=batches[0].id, trainer_id=trainers[0].id),
            BatchTrainer(batch_id=batches[0].id, trainer_id=trainers[1].id),
            BatchTrainer(batch_id=batches[1].id, trainer_id=trainers[1].id),
            BatchTrainer(batch_id=batches[2].id, trainer_id=trainers[2].id),
            BatchTrainer(batch_id=batches[2].id, trainer_id=trainers[3].id),
        ]
        db.add_all(assignments)

        for idx, student in enumerate(students):
            batch = batches[idx % 3]
            db.add(BatchStudent(batch_id=batch.id, student_id=student.id))
        db.commit()

        today = date.today()
        sessions = []
        for idx in range(8):
            batch = batches[idx % 3]
            trainer = trainers[idx % 4]
            session_date = today if idx == 0 else today - timedelta(days=(idx % 4) + 1)
            start = time(0, 0) if idx == 0 else time(9, 0)
            end = time(23, 59) if idx == 0 else time(11, 0)
            sessions.append(
                SessionModel(
                    batch_id=batch.id,
                    trainer_id=trainer.id,
                    title=f"Session {idx+1}",
                    date=session_date,
                    start_time=start,
                    end_time=end,
                )
            )
        db.add_all(sessions)
        db.commit()
        for session in sessions:
            db.refresh(session)

        enrollment_rows = db.query(BatchStudent).all()
        for idx, row in enumerate(enrollment_rows):
            batch_sessions = [s for s in sessions if s.batch_id == row.batch_id]
            for s in batch_sessions[:2]:
                status = [AttendanceStatus.present, AttendanceStatus.absent, AttendanceStatus.late][
                    (idx + s.id) % 3
                ]
                db.add(
                    Attendance(
                        session_id=s.id,
                        student_id=row.student_id,
                        status=status,
                        marked_at=datetime.now(timezone.utc),
                    )
                )
        db.commit()
        print("Seed completed successfully")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()