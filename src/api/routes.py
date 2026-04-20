from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_monitoring_user, require_roles
from src.core.config import settings
from src.core.security import create_access_token, create_monitoring_token, hash_password, verify_password
from src.db.session import get_db
from src.models.enums import UserRole
from src.models.models import Attendance, Batch, BatchInvite, BatchStudent, BatchTrainer, Session as SessionModel, User
from src.schemas.auth import LoginRequest, MessageResponse, MonitoringTokenRequest, SignupRequest, TokenResponse
from src.schemas.domain import (
    AttendanceItem,
    BatchSummaryResponse,
    CreateBatchRequest,
    CreateSessionRequest,
    InstitutionSummaryResponse,
    InviteResponse,
    JoinBatchRequest,
    MarkAttendanceRequest,
    ProgrammeSummaryResponse,
)
from src.services.summary import batch_summary, institution_summary, programme_summary

router = APIRouter()


def _user_payload(user: User):
    return {"user_id": user.id, "role": user.role.value}


@router.post("/auth/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=422, detail="Email already registered")

    if payload.role != UserRole.institution and payload.institution_id is not None:
        institution = db.query(User).filter(User.id == payload.institution_id, User.role == UserRole.institution).first()
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        institution_id=payload.institution_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(_user_payload(user)))


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(_user_payload(user)))


@router.post("/auth/monitoring-token", response_model=TokenResponse)
def monitoring_token(
    payload: MonitoringTokenRequest,
    current_user: User = Depends(require_roles(UserRole.monitoring_officer)),
):
    if payload.key != settings.monitoring_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return TokenResponse(access_token=create_monitoring_token(_user_payload(current_user)))


@router.post("/batches", response_model=MessageResponse)
def create_batch(
    payload: CreateBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.trainer, UserRole.institution)),
):
    institution = db.query(User).filter(User.id == payload.institution_id, User.role == UserRole.institution).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    if current_user.role == UserRole.institution and current_user.id != payload.institution_id:
        raise HTTPException(status_code=403, detail="Institution can only create its own batches")

    batch = Batch(name=payload.name, institution_id=payload.institution_id)
    db.add(batch)
    db.commit()
    db.refresh(batch)

    trainer_ids = set(payload.trainer_ids)
    if current_user.role == UserRole.trainer:
        trainer_ids.add(current_user.id)

    for trainer_id in trainer_ids:
        trainer = db.query(User).filter(User.id == trainer_id, User.role == UserRole.trainer).first()
        if not trainer:
            raise HTTPException(status_code=404, detail=f"Trainer {trainer_id} not found")
        db.add(BatchTrainer(batch_id=batch.id, trainer_id=trainer_id))

    db.commit()
    return MessageResponse(message=f"Batch {batch.id} created successfully")


@router.post("/batches/{batch_id}/invite", response_model=InviteResponse)
def create_invite(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.trainer)),
):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    assignment = db.query(BatchTrainer).filter(BatchTrainer.batch_id == batch_id, BatchTrainer.trainer_id == current_user.id).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="Trainer not assigned to this batch")

    expires_at = datetime.now(timezone.utc) + timedelta(days=2)
    invite = BatchInvite(
        batch_id=batch_id,
        token=secrets.token_urlsafe(24),
        created_by=current_user.id,
        expires_at=expires_at,
        used=False,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return InviteResponse(invite_token=invite.token, expires_at=invite.expires_at)


@router.post("/batches/join", response_model=MessageResponse)
def join_batch(
    payload: JoinBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
):
    invite = db.query(BatchInvite).filter(BatchInvite.token == payload.token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite token not found")
    if invite.used:
        raise HTTPException(status_code=403, detail="Invite already used")
    if invite.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invite expired")

    link = BatchStudent(batch_id=invite.batch_id, student_id=current_user.id)
    db.add(link)
    invite.used = True
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=403, detail="Student already enrolled in this batch")
    return MessageResponse(message="Joined batch successfully")


@router.post("/sessions", response_model=MessageResponse)
def create_session(
    payload: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.trainer)),
):
    batch = db.query(Batch).filter(Batch.id == payload.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    assignment = db.query(BatchTrainer).filter(BatchTrainer.batch_id == payload.batch_id, BatchTrainer.trainer_id == current_user.id).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="Trainer not assigned to this batch")
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=422, detail="end_time must be after start_time")

    session_obj = SessionModel(
        batch_id=payload.batch_id,
        trainer_id=current_user.id,
        title=payload.title,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return MessageResponse(message=f"Session {session_obj.id} created successfully")


@router.post("/attendance/mark", response_model=MessageResponse)
def mark_attendance(
    payload: MarkAttendanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
):
    session_obj = db.query(SessionModel).filter(SessionModel.id == payload.session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    enrolled = db.query(BatchStudent).filter(
        BatchStudent.batch_id == session_obj.batch_id,
        BatchStudent.student_id == current_user.id,
    ).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="Student is not enrolled in this batch")

    now = datetime.now()
    if session_obj.date != now.date() or not (session_obj.start_time <= now.time() <= session_obj.end_time):
        raise HTTPException(status_code=403, detail="Attendance can only be marked for an active session")

    existing = db.query(Attendance).filter(Attendance.session_id == payload.session_id, Attendance.student_id == current_user.id).first()
    if existing:
        existing.status = payload.status
        existing.marked_at = datetime.utcnow()
    else:
        db.add(Attendance(session_id=payload.session_id, student_id=current_user.id, status=payload.status))
    db.commit()
    return MessageResponse(message="Attendance marked successfully")


@router.get("/sessions/{session_id}/attendance", response_model=list[AttendanceItem])
def get_session_attendance(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.trainer)),
):
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_obj.trainer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Trainer can only view their own session attendance")

    rows = db.query(Attendance, User).join(User, Attendance.student_id == User.id).filter(Attendance.session_id == session_id).all()
    return [AttendanceItem(student_id=u.id, student_name=u.name, status=a.status, marked_at=a.marked_at) for a, u in rows]


@router.get("/batches/{batch_id}/summary", response_model=BatchSummaryResponse)
def get_batch_summary(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.institution)),
):
    summary = batch_summary(db, batch_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Batch not found")
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if batch.institution_id != current_user.id:
        raise HTTPException(status_code=403, detail="Institution can only view its own batches")
    return summary


@router.get("/institutions/{institution_id}/summary", response_model=InstitutionSummaryResponse)
def get_institution_summary(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.programme_manager)),
):
    summary = institution_summary(db, institution_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Institution not found")
    return summary


@router.get("/programme/summary", response_model=ProgrammeSummaryResponse)
def get_programme_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.programme_manager)),
):
    return programme_summary(db)


@router.get("/monitoring/attendance")
def monitoring_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_monitoring_user),
):
    rows = db.query(Attendance, User, SessionModel).join(User, Attendance.student_id == User.id).join(SessionModel, Attendance.session_id == SessionModel.id).all()
    return [
        {
            "attendance_id": a.id,
            "session_id": s.id,
            "session_title": s.title,
            "student_id": u.id,
            "student_name": u.name,
            "status": a.status.value,
            "marked_at": a.marked_at.isoformat(),
        }
        for a, u, s in rows
    ]


@router.api_route("/monitoring/attendance", methods=["POST", "PUT", "PATCH", "DELETE"])
def monitoring_not_allowed():
    return Response(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
