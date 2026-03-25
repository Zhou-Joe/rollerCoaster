from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Roller Coaster Simulator"
    app_version: str = "0.1.0"
    debug: bool = True

    # File storage
    projects_dir: str = "projects"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()