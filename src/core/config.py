from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SkillBridge Attendance API"
    environment: str = "development"
    debug: bool = True

    database_url: str = "sqlite:///./skillbridge.db"
    jwt_secret_key: str = "change-me-standard-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    monitoring_api_key: str = "monitoring-key-123"
    monitoring_token_secret_key: str = "change-me-monitoring-secret"
    monitoring_token_expire_minutes: int = 60

    seed_default_password: str = "Password123!"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
