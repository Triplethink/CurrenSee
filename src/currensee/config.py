from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenExchangeRates API Configuration
    oe_api_key: str
    oe_api_base_url: str = 'https://openexchangerates.org/api'

    storage_base_path: str = str(Path(__file__).parent.parent.parent.parent / 'data')
    stage_dir: str = 'stage/exchange-rates/daily'
    db_path: str = 'data/exchange_rates.db'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
    )


def get_settings() -> Settings:
    return Settings()
