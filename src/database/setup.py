# src/database/setup.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from src.config import Config
# Обновленный импорт: добавили Category
from src.database.models import Base, User, Category 
from typing import AsyncGenerator

# Асинхронный движок
engine = create_async_engine(Config.DB_URL, echo=False)

# Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def init_db():
    """Создает все таблицы в базе данных."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("База данных инициализирована и таблицы созданы.")

# Эта функция нам больше не нужна для хэндлеров, но пусть будет
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
            print(f"Администратор с ID {admin_id} добавлен.")

# --- НОВАЯ ФУНКЦИЯ ДЛЯ КАТЕГОРИЙ (ЭКСПОРТИРУЕТСЯ) ---
async def ensure_default_categories(session_maker: async_sessionmaker[AsyncSession]):
    """Создает стандартные IT-категории, если их нет."""
    default_categories = ["Backend (Python)", "Frontend (JS/TS)", "Mobile Development", "DevOps/Cloud", "UI/UX Design", "QA/Testing", "Data Science"]
    
    async with session_maker() as session:
        async with session.begin():
            categories_added = 0
            for name in default_categories:
                stmt = select(Category).where(Category.name == name)
                existing_category = await session.scalar(stmt)
                
                if not existing_category:
                    new_category = Category(name=name)
                    session.add(new_category)
                    categories_added += 1
            
            if categories_added > 0:
                 print(f"Добавлено {categories_added} стандартных категорий.")
            else:
                 print("Стандартные категории уже существуют.")