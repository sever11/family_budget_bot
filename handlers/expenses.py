import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.database import add_expense

from keyboards.inline import (
    get_main_categories_kb, 
    get_child_categories_kb, 
    CategoryCB, 
    ChildSubCB, 
    ActionCB
)

router = Router()

# Создаем класс состояний, чтобы бот запомнил сумму и текст
class ExpenseFSM(StatesGroup):
    waiting_for_category = State()

# Регулярное выражение: ищет число (целое или с точкой/запятой) в начале строки, 
# а всё остальное считает комментарием
EXPENSE_PATTERN = re.compile(r"^(\d+[.,]?\d*)\s*(.*)$")


# --- 1. ПАРСИНГ СООБЩЕНИЯ ---
# Фильтр срабатывает, если текст сообщения подходит под регулярку (начинается с цифры)
@router.message(F.text.regexp(EXPENSE_PATTERN))
async def parse_expense(message: Message, state: FSMContext):
    # Извлекаем сумму и комментарий
    match = EXPENSE_PATTERN.match(message.text)
    amount_str = match.group(1).replace(",", ".") # Меняем запятую на точку для Python
    amount = float(amount_str)
    comment = match.group(2).strip()

    # Сохраняем данные в оперативную память (FSM)
    await state.update_data(amount=amount, comment=comment)
    await state.set_state(ExpenseFSM.waiting_for_category)

    # Формируем ответ
    text = f"💰 **Сумма:** {amount} руб.\n"
    if comment:
        text += f"📝 **Заметка:** {comment}\n"
    text += "\nВыберите категорию трат:"

    # Отправляем меню
    await message.reply(text, reply_markup=get_main_categories_kb(), parse_mode="Markdown")


# --- 2. ОБРАБОТКА НАЖАТИЯ НА ОБЫЧНУЮ КАТЕГОРИЮ ---
@router.callback_query(CategoryCB.filter(), ExpenseFSM.waiting_for_category)
async def process_main_category(callback: CallbackQuery, callback_data: CategoryCB, state: FSMContext):
    # Достаем сохраненные сумму и комментарий
    data = await state.get_data()
    amount = data.get("amount")
    comment = data.get("comment")
    category = callback_data.name

    # --- 2. ОБРАБОТКА НАЖАТИЯ НА ОБЫЧНУЮ КАТЕГОРИЮ ---
@router.callback_query(CategoryCB.filter(), ExpenseFSM.waiting_for_category)
async def process_main_category(callback: CallbackQuery, callback_data: CategoryCB, state: FSMContext):
    # Достаем сохраненные сумму и комментарий
    data = await state.get_data()
    amount = data.get("amount")
    comment = data.get("comment")
    category = callback_data.name

    # TODO: Здесь будет код записи в базу данных SQL

    await callback.message.edit_text(
        f"✅ Успешно записано!\n"
        f"**Сумма:** {amount} руб.\n"
        f"**Категория:** {category}\n"
        f"**Заметка:** {comment if comment else '—'}",
        parse_mode="Markdown"
    )
    # Очищаем состояние
    await state.clear()


# --- 3. НАЖАТИЕ НА "РЕБЕНОК" (ОТКРЫТИЕ ПОДМЕНЮ) ---
@router.callback_query(ActionCB.filter(F.action == "child_menu"), ExpenseFSM.waiting_for_category)
async def open_child_menu(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=get_child_categories_kb())


# --- 4. НАЖАТИЕ НА ПОДКАТЕГОРИЮ РЕБЕНКА ---
@router.callback_query(ChildSubCB.filter(), ExpenseFSM.waiting_for_category)
async def process_child_category(callback: CallbackQuery, callback_data: ChildSubCB, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount")
    comment = data.get("comment")
    subcategory = callback_data.name
    user_id = callback.from_user.id

    # Запись в базу данных (основная категория 'Ребенок', плюс подкатегория)
    await add_expense(user_id=user_id, amount=amount, category="👶 Ребенок", subcategory=subcategory, comment=comment)

    await callback.message.edit_text(
        f"✅ Успешно записано!\n"
        f"**Сумма:** {amount} руб.\n"
        f"**Категория:** 👶 Ребенок ➔ {subcategory}\n"
        f"**Заметка:** {comment if comment else '—'}",
        parse_mode="Markdown"
    )
    await state.clear()

    # --- 2. ОБРАБОТКА НАЖАТИЯ НА ОБЫЧНУЮ КАТЕГОРИЮ ---
@router.callback_query(CategoryCB.filter(), ExpenseFSM.waiting_for_category)
async def process_main_category(callback: CallbackQuery, callback_data: CategoryCB, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount")
    comment = data.get("comment")
    category = callback_data.name
    user_id = callback.from_user.id

    # Запись в базу данных
    await add_expense(user_id=user_id, amount=amount, category=category, comment=comment)

    await callback.message.edit_text(
        f"✅ Успешно записано!\n"
        f"**Сумма:** {amount} руб.\n"
        f"**Категория:** {category}\n"
        f"**Заметка:** {comment if comment else '—'}",
        parse_mode="Markdown"
    )
    await state.clear()


# --- 5. КНОПКИ УПРАВЛЕНИЯ (ОТМЕНА И НАЗАД) ---
@router.callback_query(ActionCB.filter(F.action == "back_to_main"), ExpenseFSM.waiting_for_category)
async def back_to_main_menu(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=get_main_categories_kb())

@router.callback_query(ActionCB.filter(F.action == "cancel"))
async def cancel_expense(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Ввод расхода отменен.")