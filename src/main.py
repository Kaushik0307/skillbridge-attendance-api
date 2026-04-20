from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from src.api.routes import router
from src.core.config import settings
from src.db.base import Base
from src.db.session import engine

app = FastAPI(title=settings.app_name)
app.include_router(router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": exc.errors(), "message": "Validation failed"})


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": "Database integrity error"})


@app.get("/")
def health():
    return {"message": "SkillBridge Attendance API is running"}
