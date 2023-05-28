from pydantic import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: Optional[str]
    DATABASE_URL: Optional[str]
    MAIL_USERNAME: Optional[str]
    MAIL_PASSWORD: Optional[str]
    MAIL_FROM: Optional[str]
    MAIL_PORT: Optional[str]
    MAIL_SERVER: Optional[str]
    SERVER_HOST: Optional[str]
    DAYS_TO_VERIFY_EMAIL: Optional[int]
    ENCRYPTION_KEY: Optional[str]
    TEST_PASSWORD: Optional[str]
    TOKEN_EXPIRE_DAYS: Optional[int]
    RESET_PASSWORD_EXPIRE_HOURS: Optional[int]


# Settings is a singleton
@lru_cache()
def get_settings():
    return Settings()
