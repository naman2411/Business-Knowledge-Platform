from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")
    openai_api_key: str | None = None
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "bkp"
    jwt_secret: str = "please_change_me"
    jwt_expire_minutes: int = 60
    allowed_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:8010", "http://localhost:8010"]
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    file_storage_dir: str = r"C:\Users\NAMAN GOYAl\bkp-mongo-starter\data\files"
settings = Settings()
