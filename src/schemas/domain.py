from datetime import date, datetime, time
from pydantic import BaseModel, Field
from src.models.enums import AttendanceStatus


class CreateBatchRequest(BaseModel):
    name: str = Field(..., min_length=2)
    institution_id: int
    trainer_ids: list[int] = Field(default_factory=list)


class InviteResponse(BaseModel):
    invite_token: str
    expires_at: datetime


class JoinBatchRequest(BaseModel):
    token: str


class CreateSessionRequest(BaseModel):
    batch_id: int
    title: str = Field(..., min_length=2)
    date: date
    start_time: time
    end_time: time


class MarkAttendanceRequest(BaseModel):
    session_id: int
    status: AttendanceStatus


class AttendanceItem(BaseModel):
    student_id: int
    student_name: str
    status: AttendanceStatus
    marked_at: datetime


class BatchSummaryResponse(BaseModel):
    batch_id: int
    batch_name: str
    total_students: int
    total_sessions: int
    attendance_breakdown: dict[str, int]


class InstitutionSummaryResponse(BaseModel):
    institution_id: int
    institution_name: str
    total_batches: int
    total_students: int
    total_sessions: int
    attendance_breakdown: dict[str, int]


class ProgrammeSummaryResponse(BaseModel):
    total_institutions: int
    total_batches: int
    total_students: int
    total_sessions: int
    attendance_breakdown: dict[str, int]
