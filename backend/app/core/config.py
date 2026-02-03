from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hospital QKD" # Default value prevents crash
    MONGODB_URL: str
    DB_NAME: str = "hospital_db"
    SECRET_KEY: str = "secret"

    class Config:
        # This tells it to look for .env in the backend root
        env_file = ".env"
        extra = "ignore" # Prevents crashing if .env has extra fields

settings = Settings()