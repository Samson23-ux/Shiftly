from dotenv import load_dotenv

load_dotenv(override=True)


class Config:
    ENVIRONMENT: str = "dev"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "shiftly"
    DATABASE_USER: str = "postgres"
    DATABASE_HOST: str = "localhost"
    DATABASE_PASSWORD: str = "postgres"
