from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: dict[str, Any], expires_minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    to_encode = {**subject, "iat": int(datetime.now(timezone.utc).timestamp()), "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_monitoring_token(subject: dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.monitoring_token_expire_minutes)
    to_encode = {
        **subject,
        "scope": "monitoring_read",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.monitoring_token_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def decode_monitoring_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.monitoring_token_secret_key, algorithms=[settings.jwt_algorithm])


def safe_decode(token: str, monitoring: bool = False) -> dict[str, Any]:
    try:
        return decode_monitoring_token(token) if monitoring else decode_access_token(token)
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
