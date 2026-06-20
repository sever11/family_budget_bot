from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from core.database import get_user
from keyboards.reply import get_main_menu_kb # <--- Импортируем наше меню
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.database import update_reminder_day

router = Router()

class ReminderFSM(StatesGroup):
    waiting_for_day = State()

@router.message(Command("set_reminder"))
async def cmd_set_reminder(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("📅 Введите число месяца (от 1 до 31), когда вам нужно присылать напоминания:")
    await state.set_state(ReminderFSM.waiting_for_day)

@router.message(ReminderFSM.waiting_for_day)
async def process_reminder_day(message: Message, state: FSMContext):
    try:
        day = int(message.text)
        if day < 1 or day > 31:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число от 1 до 31.")
        return

    user = await get_user(message.from_user.id)
    family_id = user[1]
    
    # Обновляем в базе
    await update_reminder_day(family_id, day)
    await message.answer(f"✅ Готово! Теперь напоминания будут приходить {day}-го числа каждого месяца.")
    await state.clear()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_user(message.from_user.id)
    
    if user:
        await message.answer(
            "С возвращением! Главное меню открыто внизу экрана 👇",
            reply_markup=get_main_menu_kb() # <--- Выдаем меню
        )
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать новую семью", callback_data="create_family")],
            [InlineKeyboardButton(text="🔗 Присоединиться по коду", callback_data="join_family")]
        ])
        await message.answer(
            "Привет! Я бот для учета семейного бюджета. 💸\n"
            "Для начала работы нужно создать семью или присоединиться к уже существующей.",
            reply_markup=kb
        )

# Реакция на кнопку "Помощь"
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    await message.answer(
        "💡 **Как пользоваться ботом:**\n\n"
        "1️⃣ **Ввод трат:** Просто отправьте цифру (например, `450` или `1200 продукты`).\n"
        "2️⃣ **Бюджет:** Нажмите кнопку внизу, чтобы установить лимит на месяц.\n"
        "3️⃣ **Статистика:** Показывает остатки и траты по категориям.\n\n"
        "_Меню всегда доступно внизу экрана!_",
        parse_mode="Markdown"
    )

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_user(message.from_user.id)
    
    if user:
        # Пользователь уже зарегистрирован
        await message.answer(
            f"С возвращением! 🚀\n"
            "Напишите сумму расхода (например, 500) или настройте бюджет командой /set_budget."
        )
    else:
        # Пользователя нет в базе - предлагаем регистрацию
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать новую семью", callback_data="create_family")],
            [InlineKeyboardButton(text="🔗 Присоединиться по коду", callback_data="join_family")]
        ])
        await message.answer(
            "Привет! Я бот для учета семейного бюджета. 💸\n"
            "Для начала работы нужно создать семью или присоединиться к уже существующей.",
            reply_markup=kb
        )