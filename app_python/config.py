from pydantic_settings import BaseSettings


class Config(BaseSettings):
    SERVICE_TITLE: str = "devops-info-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_DESCRIPTION: str = "DevOps course info service"
    SERVICE_FRAMEWORK: str = "FastAPI"

    HOST: str = "0.0.0.0"
    PORT: int = 5000

    class Config:
        env_file = ".env"


settings = Config()
