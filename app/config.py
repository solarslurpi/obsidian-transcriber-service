from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Obsidian Transcriber Service"
    ALLOWED_ORIGINS: list = ["*"]
    PORT: int = 8082


settings = Settings()