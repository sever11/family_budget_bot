import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter

from utils.cbr_api import get_usd_rate
from core.database import get_user, get_carryover, save_monthly_budget

router = Router()

class BudgetFSM(StatesGroup):
    waiting_for_usd = State()
    waiting_for_rate = State()

@router.message(Command("set_budget"))
@router.message(F.text.contains("Бюджет"), StateFilter("*"))
async def cmd_set_budget(message: Message, state: FSMContext):
    await state.clear() # Сбрасываем зависание машины состояний
    
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала создайте семью командой /start")
        return

    await state.update_data(family_id=user[1])
    await message.answer("💵 Введите планируемую сумму дохода на этот месяц **в долларах (USD)**:")
    await state.set_state(BudgetFSM.waiting_for_usd)

@router.message(BudgetFSM.waiting_for_usd)
async def process_usd_amount(message: Message, state: FSMContext):
    try:
        usd_amount = float(message.text.replace(',', '.'))
    except ValueError:
        await message.answer("Пожалуйста, введите число (например, 3000)")
        return

    # Получаем актуальный курс
    cbr_rate = get_usd_rate()
    await state.update_data(usd_amount=usd_amount, cbr_rate=cbr_rate)

    # Предлагаем выбор курса
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Использовать курс ЦБ ({cbr_rate:.2f} ₽)", callback_data="use_cbr_rate")]
    ])
    
    await message.answer(
        f"Текущий официальный курс: **{cbr_rate:.2f} ₽**\n\n"
        f"Введите ваш собственный курс (по которому меняли) текстом, ИЛИ нажмите кнопку ниже:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(BudgetFSM.waiting_for_rate)

async def finalize_budget(message_or_call, state: FSMContext, rate: float):
    """Общая функция расчета математики"""
    data = await state.get_data()
    usd = data['usd_amount']
    family_id = data['family_id']
    
    # 1. Получаем текущий период (например, '2026-06')
    now = datetime.datetime.now()
    period = now.strftime('%Y-%m')
    
    # 2. Вычисляем остаток с прошлого месяца
    carryover = await get_carryover(family_id, period)
    
    # 3. Применяем формулу: Бюджет = (Доход * Курс) + Остаток
    base_rub = usd * rate
    planned_rub = base_rub + carryover
    
    # 4. Сохраняем в БД
    await save_monthly_budget(family_id, period, usd, rate, planned_rub, carryover)
    
    # 5. Формируем красивый ответ
    text = (
        f"📊 **Бюджет на {now.strftime('%B %Y')} успешно установлен!**\n\n"
        f"💵 Доход: {usd} USD\n"
        f"💱 Примененный курс: {rate:.2f} ₽\n"
        f"💰 Базовый бюджет: {base_rub:,.2f} ₽\n"
    )
    
    if carryover != 0:
        sign = "+" if carryover > 0 else ""
        text += f"🔄 Остаток с прошлого месяца: {sign}{carryover:,.2f} ₽\n"
        
    text += f"\n✅ **ИТОГО ДОСТУПНО: {planned_rub:,.2f} ₽**"

    if isinstance(message_or_call, Message):
        await message_or_call.answer(text, parse_mode="Markdown")
    else:
        await message_or_call.message.edit_text(text, parse_mode="Markdown")
        
    await state.clear()

@router.callback_query(F.data == "use_cbr_rate", BudgetFSM.waiting_for_rate)
async def process_cbr_rate(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await finalize_budget(callback, state, data['cbr_rate'])

@router.message(BudgetFSM.waiting_for_rate)
async def process_custom_rate(message: Message, state: FSMContext):
    try:
        custom_rate = float(message.text.replace(',', '.'))
        await finalize_budget(message, state, custom_rate)
    except ValueError:
        await message.answer("Пожалуйста, введите число (например, 94.5)")