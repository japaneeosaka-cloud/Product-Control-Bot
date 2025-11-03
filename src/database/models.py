# src/database/models.py
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column

# Базовый класс для моделей (должен быть определен здесь, а не импортирован)
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Связь с проектами
    projects: Mapped[list["PortfolioItem"]] = relationship(back_populates="creator")
    
    def __repr__(self):
        return f"<User(id={self.user_id}, username='{self.username}')>"

class Category(Base):
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    # Связь с проектами
    items: Mapped[list["PortfolioItem"]] = relationship(back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class PortfolioItem(Base):
    __tablename__ = 'portfolio_items'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # --- ИЗМЕНЕНИЕ: Поля для файлов ---
    photo_file_id: Mapped[str | None] = mapped_column(String, nullable=True) # Было telegram_file_id
    document_file_id: Mapped[str | None] = mapped_column(String, nullable=True) # --- НОВОЕ ПОЛЕ ---
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    
    link: Mapped[str | None] = mapped_column(String, nullable=True) 
    
    # СИСТЕМА МОДЕРАЦИИ: Проект одобрен?
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # КЛЮЧЕВОЕ ПОЛЕ: ID пользователя, который добавил проект
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'), nullable=False)
    creator: Mapped["User"] = relationship(back_populates="projects")
    
    # КАТЕГОРИЗАЦИЯ
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'), nullable=False)
    category: Mapped["Category"] = relationship(back_populates="items")
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, title='{self.title}', approved={self.is_approved})>"