from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: Optional[str] = None
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "inboundshield"
    MYSQL_USER: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None

    APP_ENV: str = "development"
    SECRET_KEY: str = "inboundshield_super_secure_secret_key_2026"
    UPLOAD_DIR: str = "uploads"
    FIXTURES_DIR: str = "fixtures"
    VISION_PROVIDER: str = "hybrid"  # "hybrid", "gemini", or "mock"
    GEMINI_API_KEY: Optional[str] = None

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.MYSQL_USER and self.MYSQL_PASSWORD:
            return (
                f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
                f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            )
        # Default fallback to SQLite for reliable standalone local execution & tests
        return "sqlite:///./inboundshield.db"


settings = Settings()
