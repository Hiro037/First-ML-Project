from typing import Optional

from pydantic import Field, PostgresDsn, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Настройки Базы Данных
    database_name: str = Field(..., env="DATABASE_NAME")
    database_user: str = Field(..., env="DATABASE_USER")
    database_password: str = Field(..., env="DATABASE_PASSWORD")
    database_host: str = Field("localhost", env="DATABASE_HOST")
    database_port: int = Field(5432, env="DATABASE_PORT")  # Меняем тип на int!

    # Полный DSN URL для подключения к БД (вычисляемое поле)
    database_url: Optional[PostgresDsn] = None

    @validator("database_url", pre=True, always=True)
    def assemble_db_connection(cls, v, values) -> str:
        """Собирает DSN строку для подключения к PostgreSQL."""
        if isinstance(v, str):
            return v

        # Убедимся, что все значения получены
        if not all(
            [
                values.get("database_user"),
                values.get("database_password"),
                values.get("database_host"),
                values.get("database_port"),
                values.get("database_name"),
            ]
        ):
            raise ValueError("Missing required database configuration values")

        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("database_user"),
            password=values.get("database_password"),
            host=values.get("database_host"),
            port=values.get("database_port"),  # Теперь port будет int
            path=values.get("database_name") or "",
        )

    # Параметры алгоритма
    price_change_threshold: float = Field(0.01, env="PRICE_CHANGE_THRESHOLD")
    lookback_window_minutes: int = Field(60, env="LOOKBACK_WINDOW_MINUTES")
    beta_recalculation_interval: int = Field(
        86400, env="BETA_RECALCULATION_INTERVAL"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Создаем глобальный экземпляр настроек
settings = Settings()
