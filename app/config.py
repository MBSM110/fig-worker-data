from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_CORE_URL: str
    COIN_GECKO_ID: str
    DAYS_TO_FETCH: int
    COINGECKO_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()