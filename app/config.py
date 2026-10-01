from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных окружения """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_user: str = "wallet_user"
    postgres_password: str = "wallet_password"
    postgres_db: str = "wallet_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    app_name: str = "Wallet API"
    debug: bool = False

    @property
    def database_url(self) -> str:
        """Формирует асинхронный URL подключения к БД для SQLAlch"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()