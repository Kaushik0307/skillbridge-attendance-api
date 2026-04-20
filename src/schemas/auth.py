from pydantic import BaseModel, EmailStr, Field
from src.models.enums import UserRole


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole
    institution_id: int | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class MonitoringTokenRequest(BaseModel):
    key: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str
