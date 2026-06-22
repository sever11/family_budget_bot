from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.database import get_categories # Проверьте правильность пути импорта!

# Теперь функция асинхронная (async) и принимает family_id
async def get_main_categories_kb(family_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Достаем категории семьи из базы
    categories = await get_categories(family_id)
    
    # Если база пустая (семья только создана), даем базовый набор
    if not categories:
        categories = ["🛒 Продукты", "🚗 Авто", "🏠 ЖКХ", "🛍 Разное"]
        
    # Создаем кнопки из списка
    for cat in categories:
        # Убедитесь, что ваш CategoryCB принимает параметр name
        builder.button(text=cat, callback_data=CategoryCB(name=cat))
        
    # Добавляем системные кнопки в конец
    builder.button(text="➕ Добавить категорию", callback_data="add_custom_category")
    builder.button(text="❌ Отмена", callback_data="cancel")
    
    # Выстраиваем кнопки по 2 в ряд
    builder.adjust(2)
    return builder.as_markup()