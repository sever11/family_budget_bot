import asyncio
import logging
from aiogram import Bot, Dispatcher
from core.config import BOT_TOKEN
from handlers import base, expenses, registration, budget, reports
from core.database import init_db

# Импортируем планировщик и нашу задачу
from core.scheduler import scheduler, send_monthly_reminder 

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # --- НАСТРОЙКА АВТОМАТИЗАЦИИ ---
    # Добавляем задачу: запускать функцию send_monthly_reminder
    # trigger="cron" означает запуск по календарю.
    # day=15, hour=10, minute=0 -> Каждое 15-е число месяца в 10:00 утра
    scheduler.add_job(
        send_monthly_reminder, 
        trigger="cron", 
        hour=10, 
        minute=0, 
        args=[bot]
    )
    
    # ДЛЯ ТЕСТА: отправка каждые 10 секунд (строка ниже раскомментирована правильно)
    # scheduler.add_job(send_monthly_reminder, trigger="interval", seconds=10, args=[bot])

    # Запускаем планировщик
    scheduler.start()
    print("Планировщик задач успешно запущен!")
    # ------------------------------

    dp.include_router(base.router)
    dp.include_router(registration.router)
    dp.include_router(budget.router)
    dp.include_router(reports.router)
    dp.include_router(expenses.router) # Напоминаю: этот роутер всегда в самом конце

    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")