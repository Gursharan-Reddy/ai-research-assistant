import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AI Research & Knowledge Assistant"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    VECTOR_DB_DIR: str = os.getenv("VECTOR_DB_DIR", "./data/vector_db")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./models/tf_classifier.h5")
    TOKENIZER_PATH: str = os.getenv("TOKENIZER_PATH", "./models/tokenizer.pickle")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/assistant.db")
    UPLOAD_DIR: str = "./data/raw_documents"

    class Config:
        env_file = ".env"

settings = Settings()