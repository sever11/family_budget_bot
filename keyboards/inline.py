from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

# --- Фабрики коллбеков (структура данных, которые возвращает кнопка) ---
class CategoryCB(CallbackData, prefix="cat"):
    name: str

class ChildSubCB(CallbackData, prefix="child"):
    name: str

class ActionCB(CallbackData, prefix="act"):
    action: str

# --- Основная клавиатура категорий ---
def get_main_categories_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Список основных категорий (без ребенка)
    categories = [
        "🛒 Продукты", "🚕 Такси", 
        "💊 Аптека", "🚬 Табак",
        "🐾 Животные", "🏋️ Спорт",
        "🚗 Авто", "🛠 Ремонт",
        "🍷 Вечеринки", "📱 Подписки",
        "🏠 Жилье и Кредиты", "🛍 Разное"
    ]
    
    # Добавляем кнопки в билдер
    for cat in categories:
        builder.button(text=cat, callback_data=CategoryCB(name=cat))
        
    # Кнопка для ребенка (отдельный action, так как открывает подменю)
    builder.button(text="👶 Ребенок (Выбрать)", callback_data=ActionCB(action="child_menu"))
    
    # Кнопка отмены
    builder.button(text="❌ Отмена", callback_data=ActionCB(action="cancel"))
    
    # Настраиваем сетку (Grid): по 2 кнопки в ряд, последние две кнопки (ребенок и отмена) — по 1 в ряд
    builder.adjust(2, 2, 2, 2, 2, 2, 1, 1)
    return builder.as_markup()

# --- Клавиатура подкатегорий для ребенка ---
def get_child_categories_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    subcategories = [
        "Детсад/Кружки", "Игрушки/Книги", 
        "Одежда/Обувь", "Питание/Сладости", 
        "Здоровье"
    ]
    
    for sub in subcategories:
        builder.button(text=sub, callback_data=ChildSubCB(name=sub))
        
    builder.button(text="🔙 Назад", callback_data=ActionCB(action="back_to_main"))
    builder.button(text="❌ Отмена", callback_data=ActionCB(action="cancel"))
    
    # Сетка: 2-2-1-1-1
    builder.adjust(2, 2, 1, 1, 1)
    return builder.as_markup()