from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    # Assembled Database URL
    DATABASE_URL: Optional[str] = None

    @model_validator(mode='before')
    def assemble_db_connection(cls, v):
        if isinstance(v, dict):
            v['DATABASE_URL'] = (
                f"postgresql+asyncpg://{v.get('DB_USER')}:{v.get('DB_PASSWORD')}"
                f"@{v.get('DB_HOST')}:{v.get('DB_PORT')}/{v.get('DB_NAME')}"
            )
        return v

    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
