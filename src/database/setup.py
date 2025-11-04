# src/database/setup.py
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from typing import AsyncGenerator

# (ИСПРАВЛЕНО) Импортируем 'settings' из нашего нового config.py
from src.config import settings 
from src.database.models import Base, User, Category 

# Настройка логгера
logger = logging.getLogger(__name__)

# Асинхронный движок
# (ИСПРАВЛЕНО) Используем 'settings.DB_URL'
engine = create_async_engine(settings.DB_URL, echo=False)

# Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def init_db():
    """Создает все таблицы в базе данных."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База данных инициализирована и таблицы созданы.")

async def get_session() -> AsyncGenerator[AsyncSession, None]: 
    """Генератор для получения сессии."""
    async with AsyncSessionLocal() as session:
        yield session

async def ensure_admin_exists(admin_id: int):
    """Проверяет и создает запись для администратора."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.user_id == admin_id)
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()
        
        if not admin:
            new_admin = User(user_id=admin_id, username="admin_user", is_admin=True)
            session.add(new_admin)
            await session.commit()
            logger.info(f"Администратор с ID {admin_id} добавлен.")
        else:
            # (ДОБАВЛЕНО) Убедимся, что у существующего юзера есть права
            if not admin.is_admin:
                admin.is_admin = True
                await session.commit()
                logger.info(f"Пользователю {admin_id} выданы права администратора.")


async def ensure_default_categories(session_maker: async_sessionmaker[AsyncSession]):
    """Создает стандартные IT-категории, если их нет."""
    default_categories = [
        "Backend (Python)", 
        "Frontend (JS/TS)", 
        "Mobile Development", 
        "DevOps/Cloud", 
        "UI/UX Design", 
        "QA/Testing", 
        "Data Science"
    ]
    
    async with session_maker() as session:
        # Используем session.begin() для автоматического коммита или отката
        async with session.begin():
            categories_added = 0
            for name in default_categories:
                # Проверяем наличие категории
                stmt = select(Category).where(Category.name == name)
                existing_category = await session.scalar(stmt)
                
                if not existing_category:
                    new_category = Category(name=name)
                    session.add(new_category)
                    categories_added += 1
            
            if categories_added > 0:
                logger.info(f"Добавлено {categories_added} стандартных категорий.")
            else:
                logger.info("Стандартные категории уже существуют.")