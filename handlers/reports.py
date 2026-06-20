import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from core.database import get_user, get_user_stats, get_family_stats, get_budget_info

router = Router()

def get_stats_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Мои расходы", callback_data="stats_mine")],
        [InlineKeyboardButton(text="👥 Общий бюджет семьи", callback_data="stats_family")]
    ])

@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика") # <--- ДОБАВИТЬ ЭТУ СТРОКУ
async def cmd_stats(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала создайте семью командой /start")
        return
        
    await message.answer("📊 Выберите тип отчета за текущий месяц:", reply_markup=get_stats_kb())

@router.callback_query(F.data.startswith("stats_"))
async def process_stats(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    family_id = user[1]
    
    now = datetime.datetime.now()
    period = now.strftime('%Y-%m')
    month_name = now.strftime('%B %Y')

    if callback.data == "stats_mine":
        # Отчет только по своим тратам
        stats = await get_user_stats(callback.from_user.id, period)
        title = f"👤 **Мои расходы ({month_name}):**\n\n"
    else:
        # Отчет по всей семье
        stats = await get_family_stats(family_id, period)
        title = f"👥 **Семейные расходы ({month_name}):**\n\n"

    if not stats:
        await callback.message.edit_text(title + "Трат в этом месяце пока нет. 🤷‍♂️", parse_mode="Markdown")
        return

    # Формируем текст с категориями
    total_spent = 0
    text = title
    for category, amount in stats:
        text += f"▪️ {category}: {amount:,.0f} ₽\n"
        total_spent += amount

    text += f"\n📉 **Всего потрачено: {total_spent:,.0f} ₽**"

    # Если смотрим семейный бюджет, добавляем сравнение с лимитом
    if callback.data == "stats_family":
        budget = await get_budget_info(family_id, period)
        if budget > 0:
            left = budget - total_spent
            if left >= 0:
                text += f"\n🟢 **Остаток бюджета: {left:,.0f} ₽**"
            else:
                text += f"\n🔴 **ПЕРЕРАСХОД: {abs(left):,.0f} ₽**"
        else:
            text += "\n\n*(Бюджет на этот месяц не установлен. Введите /set_budget)*"

    # Добавляем кнопку "Назад"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к выбору", callback_data="stats_back")]
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "stats_back")
async def back_to_stats_menu(callback: CallbackQuery):
    await callback.message.edit_text("📊 Выберите тип отчета за текущий месяц:", reply_markup=get_stats_kb())