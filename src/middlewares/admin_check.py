# src/middlewares/admin_check.py
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from src.config import Config # Импортируем наш конфиг

class AdminMiddleware(BaseMiddleware):
    """
    Мидлварь для проверки, является ли пользователь администратором,
    сравнивая его ID с ADMIN_ID из конфига.
    """
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Awaitable[Any]:
        
        # Проверяем, что ID пользователя совпадает с ID админа из .env
        if event.from_user.id != Config.ADMIN_ID:
            # Если нет - вежливо отвечаем и прекращаем обработку
            await event.answer("⛔️ У вас нет доступа к этой команде.")
            return
        
        # Если ID совпал - продолжаем выполнение хэндлера
        return await handler(event, data)