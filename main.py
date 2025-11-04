# main.py
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

# 1. (ИЗМЕНЕНО) Импортируем 'settings' из нового config.py
from src.config import settings 

# 2. (ИЗМЕНЕНО) Импортируем 'engine' для корректного закрытия
from src.database.setup import (
    init_db, 
    ensure_admin_exists, 
    AsyncSessionLocal, 
    ensure_default_categories,
    engine  # <--- ДОБАВЬ ЭТОТ ИМПОРТ (из твоего файла сессии/setup)
)
from src.handlers.user_handlers import router, admin_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting bot configuration...")
    
    # 1. Инициализация Базы Данных
    await init_db()
    logger.info("Database initialized.")
    
    # 2. Убедиться, что администратор добавлен в БД
    # (ИЗМЕНЕНО) Используем settings.ADMIN_ID
    await ensure_admin_exists(settings.ADMIN_ID)
    logger.info(f"Admin user {settings.ADMIN_ID} checked.")
    
    # 3. Добавление стандартных категорий
    await ensure_default_categories(AsyncSessionLocal)
    logger.info("Default categories checked.")
    
    # 4. Инициализация Redis для FSM
    # (ДОБАВЛЕНО)
    redis_client = Redis(host="redis", port=6379) # 'redis' - это имя сервиса из docker-compose
    storage = RedisStorage(redis=redis_client)
    logger.info("Redis storage initialized.")
    
    # 5. Инициализация Бота
    # (ИЗМЕНЕНО) Используем settings.get_bot_token()
    bot = Bot(
        token=settings.get_bot_token(), 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # 6. Инициализация Диспетчера
    # (ИЗМЕНЕНО) Передаем storage (Redis) в Диспетчер
    dp = Dispatcher(storage=storage)
    
    # 7. Регистрация роутеров
    dp.include_router(admin_router)
    dp.include_router(router)
    logger.info("Routers included.")
    
    # 8. Запуск бота
    logger.info("Starting bot in Long Polling mode...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    # (ДОБАВЛЕНО) Блок try...finally для корректного закрытия ресурсов
    try:
        # Передаем сессию БД (как у тебя и было)
        await dp.start_polling(
            bot,
            session_maker=AsyncSessionLocal
        )
    finally:
        logger.info("Stopping bot...")
        # Корректно закрываем соединения
        await dp.storage.close()  # Закрывает соединение с Redis
        await bot.session.close()
        await engine.dispose()    # Закрывает пул соединений с PostgreSQL
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually (KeyboardInterrupt).")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)