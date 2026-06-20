import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
import aiosqlite
from core.database import get_users_by_reminder_day
from core.database import DB_NAME

# Создаем асинхронный планировщик
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

async def send_monthly_reminder(bot: Bot):
    today = datetime.datetime.now().day
    users = await get_users_by_reminder_day(today)
    for user in users:
        tg_id = user[0]
        try:
            await bot.send_message(
                chat_id=tg_id,
                text=f"🚨 **Напоминание!**\n\n"
                     f"Сегодня {today}-е число — время обязательных платежей. "
                     f"Не забудьте внести их в бот!",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка отправки {tg_id}: {e}")
            
    """Функция, которая будет отправлять напоминание об ипотеке."""
    async with aiosqlite.connect(DB_NAME) as db:
        # Достаем ID всех пользователей из базы данных
        async with db.execute("SELECT tg_id FROM users") as cursor:
            users = await cursor.fetchall()
            
    # Отправляем сообщение каждому пользователю
    for user in users:
        tg_id = user[0]
        try:
            await bot.send_message(
                chat_id=tg_id,
                text="🚨 **Напоминание об обязательных платежах!**\n\n"
                     "Сегодня время оплатить ипотеку/аренду и парковку. "
                     "Не забудьте внести эти расходы в бот!",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {tg_id}: {e}")