# src/callbacks/project_cb.py
from aiogram.filters.callback_data import CallbackData

class ProjectCallback(CallbackData, prefix="proj"):
    """Callback-фабрика для навигации и управления проектами."""
    action: str  # 'next', 'prev', 'delete', 'approve', 'reject'
    item_id: int # ID проекта
    current_index: int # Текущий индекс в списке для навигации
    category_id: int # ID текущей категории (0 для "Все")

class CategoryCallback(CallbackData, prefix="cat"):
    """Callback-фабрика для выбора категории."""
    category_id: int # ID категории (0 для "Показать все")