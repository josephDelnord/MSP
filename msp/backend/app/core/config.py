from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Mikrotik Provisioning Manager"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Database
    DATABASE_URL: str = "postgresql://msp:msp_password@localhost:5432/msp_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Mikrotik defaults
    MIKROTIK_DEFAULT_PORT_API: int = 8728
    MIKROTIK_DEFAULT_PORT_SSH: int = 22
    MIKROTIK_DEFAULT_PORT_API_SSL: int = 8729
    MIKROTIK_DEFAULT_USERNAME: str = "admin"
    MIKROTIK_DEFAULT_PASSWORD: str = ""
    MIKROTIK_DEFAULT_IP: str = "192.168.88.1"

    # Templates directory
    TEMPLATES_DIR: str = "/app/templates"

    # Notification defaults
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "msp@localhost"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
