# (Новый файл src/database/session.py)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config import settings

# Создаем "движок"
# Он использует DATABASE_URL из .env (который указывает на 'db' в Docker)
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Создаем "фабрику сессий"
# Из нее мы будем получать сессии для запросов к БД
async_session = async_sessionmaker(engine, expire_on_commit=False)