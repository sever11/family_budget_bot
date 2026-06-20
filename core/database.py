import aiosqlite
import random
import string

DB_NAME = "budget.db"

def generate_invite_code():
    """Генерирует случайный код из 6 символов"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS families (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invite_code TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                tg_id INTEGER PRIMARY KEY,
                family_id INTEGER,
                role TEXT,
                FOREIGN KEY (family_id) REFERENCES families(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS monthly_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id INTEGER,
                period TEXT NOT NULL, 
                income_usd REAL NOT NULL,
                exchange_rate REAL NOT NULL,
                planned_rub REAL NOT NULL,
                carryover_rub REAL NOT NULL DEFAULT 0.0,
                FOREIGN KEY (family_id) REFERENCES families(id),
                UNIQUE (family_id, period)
            )
        """)
        await db.commit()
        
        try:
            await db.execute("ALTER TABLE families ADD COLUMN reminder_day INTEGER DEFAULT 15")
        except aiosqlite.OperationalError:
            pass # Если колонка уже есть, Питон просто пойдет дальше
            
        await db.commit()

async def get_user(tg_id: int):
    """Проверяет, зарегистрирован ли пользователь"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)) as cursor:
            return await cursor.fetchone()

async def create_family(tg_id: int, role: str):
    """Создает семью и добавляет туда пользователя"""
    invite_code = generate_invite_code()
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("INSERT INTO families (invite_code) VALUES (?)", (invite_code,))
        family_id = cursor.lastrowid
        await db.execute("INSERT INTO users (tg_id, family_id, role) VALUES (?, ?, ?)", (tg_id, family_id, role))
        await db.commit()
    return invite_code

async def join_family(tg_id: int, invite_code: str, role: str):
    """Присоединяет пользователя к семье по коду"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id FROM families WHERE invite_code = ?", (invite_code,)) as cursor:
            family = await cursor.fetchone()
            if not family:
                return False # Код не найден
            
            family_id = family[0]
            await db.execute("INSERT INTO users (tg_id, family_id, role) VALUES (?, ?, ?)", (tg_id, family_id, role))
            await db.commit()
            return True

async def add_expense(user_id: int, amount: float, category: str, subcategory: str = None, comment: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO expenses (user_id, amount, category, subcategory, comment) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, subcategory, comment)
        )
        await db.commit()

        import datetime

async def get_carryover(family_id: int, current_period: str) -> float:
    """Вычисляет переходящий остаток с прошлого месяца."""
    # Получаем предыдущий месяц (примитивная логика для примера)
    year, month = map(int, current_period.split('-'))
    if month == 1:
        prev_period = f"{year - 1}-12"
    else:
        prev_period = f"{year}-{month - 1:02d}"

    async with aiosqlite.connect(DB_NAME) as db:
        # Ищем бюджет прошлого месяца
        async with db.execute("SELECT planned_rub FROM monthly_balances WHERE family_id = ? AND period = ?", (family_id, prev_period)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return 0.0 # Если прошлого месяца нет, остаток 0
            
            planned_rub = row[0]
            
        # Считаем все траты семьи за прошлый месяц
        async with db.execute("""
            SELECT SUM(amount) FROM expenses 
            JOIN users ON expenses.user_id = users.tg_id 
            WHERE users.family_id = ? AND strftime('%Y-%m', expenses.created_at) = ?
        """, (family_id, prev_period)) as cursor:
            exp_row = await cursor.fetchone()
            spent = exp_row[0] if exp_row[0] else 0.0
            
        return planned_rub - spent # Остаток = Бюджет минус Траты

async def save_monthly_budget(family_id: int, period: str, usd: float, rate: float, planned_rub: float, carryover: float):
    """Сохраняет бюджет на текущий месяц (обновляет, если уже есть)."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO monthly_balances (family_id, period, income_usd, exchange_rate, planned_rub, carryover_rub)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(family_id, period) DO UPDATE SET
                income_usd=excluded.income_usd,
                exchange_rate=excluded.exchange_rate,
                planned_rub=excluded.planned_rub,
                carryover_rub=excluded.carryover_rub
        """, (family_id, period, usd, rate, planned_rub, carryover))
        await db.commit()

async def get_user_stats(user_id: int, period: str):
    """Получает статистику трат конкретного пользователя за месяц по категориям."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT category, SUM(amount) 
            FROM expenses 
            WHERE user_id = ? AND strftime('%Y-%m', created_at) = ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
        """, (user_id, period)) as cursor:
            return await cursor.fetchall()

async def get_family_stats(family_id: int, period: str):
    """Получает общие траты всей семьи за месяц по категориям."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT e.category, SUM(e.amount) 
            FROM expenses e
            JOIN users u ON e.user_id = u.tg_id
            WHERE u.family_id = ? AND strftime('%Y-%m', e.created_at) = ?
            GROUP BY e.category
            ORDER BY SUM(e.amount) DESC
        """, (family_id, period)) as cursor:
            return await cursor.fetchall()

async def get_budget_info(family_id: int, period: str):
    """Получает информацию о бюджете на текущий месяц."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT planned_rub FROM monthly_balances 
            WHERE family_id = ? AND period = ?
        """, (family_id, period)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0.0
        
async def update_reminder_day(family_id: int, day: int):
    """Обновляет день напоминания для семьи."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE families SET reminder_day = ? WHERE id = ?", (day, family_id))
        await db.commit()

async def get_users_by_reminder_day(day: int):
    """Ищет всех пользователей, чья семья выбрала этот день для напоминаний."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT u.tg_id FROM users u
            JOIN families f ON u.family_id = f.id
            WHERE f.reminder_day = ?
        """, (day,)) as cursor:
            return await cursor.fetchall()
        
    async def delete_last_expense(family_id: int) -> bool:
    
     async with aiosqlite.connect(DB_NAME) as db:
        # Сначала находим ID последней записи для этой семьи
        async with db.execute("""
            SELECT id FROM expenses 
            WHERE family_id = ? 
            ORDER BY timestamp DESC LIMIT 1
        """, (family_id,)) as cursor:
            row = await cursor.fetchone()
            
        if row:
            expense_id = row[0]
            # Удаляем этот расход
            await db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            await db.commit()
            return True
        return False