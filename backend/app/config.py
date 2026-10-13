import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""
    database_url: str = "sqlite:///./regshift.db"
    upload_dir: str = "./app/uploads"
    max_upload_size_mb: int = 20
    frontend_url: str = "http://localhost:5173"
    app_env: str = "development"
    secret_key: str = "dev-secret-key"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
