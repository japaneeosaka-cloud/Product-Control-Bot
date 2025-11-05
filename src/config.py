# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field

class Settings(BaseSettings):
    """
    Класс настроек проекта, который загружает переменные из .env файла
    и окружения.
    """
    
    # --- Конфигурация Pydantic ---
    model_config = SettingsConfigDict(
        # Указываем, откуда читать переменные
        # env_file=".env", 
        env_file_encoding="utf-8",
        # ИСПРАВЛЕНИЕ: Игнорируем любые переменные в окружении (например, db_url),
        # которые не описаны в этом классе. Это устраняет ошибку "Extra inputs".
        extra='ignore' 
    )

    # --- Bot ---
    BOT_TOKEN: SecretStr
    ADMIN_ID: int

    # --- Redis (для FSM) ---
    REDIS_HOST: str
    REDIS_PORT: int

    # --- PostgreSQL (Переменные, которые вы используете в Docker Compose и .env) ---
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr # Используем SecretStr для пароля
    POSTGRES_DB: str
    POSTGRES_HOST: str 
    POSTGRES_PORT: int

    # --- Итоговый URL для подключения SQLAlchemy ---
    # Переменная в коде - DB_URL. Загружаем ее из DATABASE_URL в .env
    DB_URL: str = Field(validation_alias="DATABASE_URL")

    # Метод, чтобы удобно получать токен в виде строки
    def get_bot_token(self) -> str:
        """Возвращает токен бота в виде строки."""
        return self.BOT_TOKEN.get_secret_value()

    # Метод для получения пароля PostgreSQL (если нужен в коде)
    def get_postgres_password(self) -> str:
        """Возвращает пароль PostgreSQL в виде строки."""
        return self.POSTGRES_PASSWORD.get_secret_value()

# Создаем один-единственный экземпляр настроек
settings = Settings()