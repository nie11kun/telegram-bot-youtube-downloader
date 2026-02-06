import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    BOT_TOKEN: str
    INS_ACCOUNT: Optional[str] = None
    TEMP_DIR: str = "temp_downloads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    DEFAULT_TIMEOUT: int = 600

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

# Ensure temp directory exists
os.makedirs(settings.TEMP_DIR, exist_ok=True)
