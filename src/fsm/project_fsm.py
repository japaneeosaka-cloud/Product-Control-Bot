# src/fsm/project_fsm.py
from aiogram.fsm.state import StatesGroup, State

# Добавляем get_category
class AddProjectStates(StatesGroup):
    """Состояния для пошагового добавления проекта АДМИНОМ."""
    get_category = State()
    get_title = State()
    get_description = State()
    get_link = State()
    get_photo = State()
    get_document = State() # --- НОВОЕ ---

# Добавляем get_category
class UserAddProjectStates(StatesGroup):
    """Состояния для пошагового добавления проекта ПОЛЬЗОВАТЕЛЕМ."""
    get_category = State()
    get_title = State()
    get_description = State()
    get_link = State()
    get_photo = State()
    get_document = State() # --- НОВОЕ ---