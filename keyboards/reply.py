from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_kb() -> ReplyKeyboardMarkup:
    """Создает постоянное нижнее меню."""
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="💵 Бюджет")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True, # Делает кнопки компактными
        is_persistent=True    # Оставляет клавиатуру открытой
    )
    return kb