# src/config.py
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
    DB_URL = os.getenv("DB_URL")

    if not BOT_TOKEN or not ADMIN_ID or not DB_URL:
        raise ValueError("Ошибка: Необходимые переменные окружения (BOT_TOKEN, ADMIN_ID, DB_URL) не найдены.")