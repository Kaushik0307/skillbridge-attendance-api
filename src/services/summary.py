from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.enums import AttendanceStatus
from src.models.models import Attendance, Batch, BatchStudent, Session as SessionModel, User


def _attendance_breakdown_query(db: Session, batch_ids: list[int] | None = None, institution_id: int | None = None):
    query = db.query(Attendance.status, func.count(Attendance.id)).join(
        SessionModel, Attendance.session_id == SessionModel.id
    )
    if batch_ids:
        query = query.filter(SessionModel.batch_id.in_(batch_ids))
    if institution_id:
        query = query.join(Batch, SessionModel.batch_id == Batch.id).filter(Batch.institution_id == institution_id)
    return query.group_by(Attendance.status).all()


def _format_breakdown(rows):
    base = {status.value: 0 for status in AttendanceStatus}
    for status, count in rows:
        base[status.value if hasattr(status, 'value') else status] = count
    return base


def batch_summary(db: Session, batch_id: int):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        return None
    students = db.query(func.count(BatchStudent.id)).filter(BatchStudent.batch_id == batch_id).scalar() or 0
    sessions = db.query(func.count(SessionModel.id)).filter(SessionModel.batch_id == batch_id).scalar() or 0
    breakdown = _format_breakdown(_attendance_breakdown_query(db, batch_ids=[batch_id]))
    return {
        "batch_id": batch.id,
        "batch_name": batch.name,
        "total_students": students,
        "total_sessions": sessions,
        "attendance_breakdown": breakdown,
    }


def institution_summary(db: Session, institution_id: int):
    institution = db.query(User).filter(User.id == institution_id, User.role == "institution").first()
    if not institution:
        return None
    batch_ids = [b.id for b in db.query(Batch).filter(Batch.institution_id == institution_id).all()]
    student_count = (
        db.query(func.count(BatchStudent.id)).join(Batch, BatchStudent.batch_id == Batch.id).filter(Batch.institution_id == institution_id).scalar() or 0
    )
    session_count = db.query(func.count(SessionModel.id)).join(Batch, SessionModel.batch_id == Batch.id).filter(Batch.institution_id == institution_id).scalar() or 0
    breakdown = _format_breakdown(_attendance_breakdown_query(db, institution_id=institution_id))
    return {
        "institution_id": institution.id,
        "institution_name": institution.name,
        "total_batches": len(batch_ids),
        "total_students": student_count,
        "total_sessions": session_count,
        "attendance_breakdown": breakdown,
    }


def programme_summary(db: Session):
    total_institutions = db.query(func.count(User.id)).filter(User.role == "institution").scalar() or 0
    total_batches = db.query(func.count(Batch.id)).scalar() or 0
    total_students = db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0
    total_sessions = db.query(func.count(SessionModel.id)).scalar() or 0
    breakdown = _format_breakdown(db.query(Attendance.status, func.count(Attendance.id)).group_by(Attendance.status).all())
    return {
        "total_institutions": total_institutions,
        "total_batches": total_batches,
        "total_students": total_students,
        "total_sessions": total_sessions,
        "attendance_breakdown": breakdown,
    }
