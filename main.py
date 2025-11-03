# main.py
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from src.config import Config
from src.handlers.user_handlers import router, admin_router
# Убедитесь, что этот импорт теперь верен
from src.database.setup import init_db, ensure_admin_exists, AsyncSessionLocal, ensure_default_categories 

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout
)

async def main():
    # 1. Инициализация Базы Данных
    await init_db()
    
    # 2. Убедиться, что администратор добавлен в БД
    await ensure_admin_exists(Config.ADMIN_ID)
    
    # 3. Добавление стандартных категорий
    await ensure_default_categories(AsyncSessionLocal)
    
    # 4. Инициализация Бота
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Инициализация Диспетчера
    dp = Dispatcher()
    
    # 5. Регистрация роутеров
    dp.include_router(admin_router) 
    dp.include_router(router)
    
    # 6. Запуск бота
    logging.info("Starting bot in Long Polling mode...")
    await bot.delete_webhook(drop_pending_updates=True) 
    
    # ПЕРЕДАЕМ ЗАВИСИМОСТЬ ПРИ ЗАПУСКЕ ПОЛЛИНГА
    await dp.start_polling(
        bot, 
        session_maker=AsyncSessionLocal 
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped manually.")
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")