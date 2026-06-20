from keyboards.reply import get_main_menu_kb
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.database import create_family, join_family

router = Router()

class RegState(StatesGroup):
    waiting_for_code = State()

# Кнопки выбора роли
def get_roles_kb(action: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я - Муж 👨", callback_data=f"{action}_husband")],
        [InlineKeyboardButton(text="Я - Жена 👩", callback_data=f"{action}_wife")]
    ])

@router.callback_query(F.data == "create_family")
async def process_create_family(callback: CallbackQuery):
    await callback.message.edit_text("Кем вы будете в этой семье?", reply_markup=get_roles_kb("create"))

@router.callback_query(F.data.startswith("create_"))
async def finish_creation(callback: CallbackQuery):
    await callback.message.answer("Меню управления открыто! 👇", reply_markup=get_main_menu_kb())
    role = "Муж" if "husband" in callback.data else "Жена"
    invite_code = await create_family(callback.from_user.id, role)
    
    await callback.message.edit_text(
        f"✅ Семья успешно создана! Вы записаны как {role}.\n\n"
        f"🔑 **Ваш код приглашения:** `{invite_code}`\n\n"
        f"Передайте этот код вашей второй половинке. "
        f"Она должна запустить бота и нажать «Присоединиться по коду».",
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "join_family")
async def process_join_family(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите код приглашения, который вам прислал партнер:")
    await state.set_state(RegState.waiting_for_code)

@router.message(RegState.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.update_data(code=code)
    await message.answer("Отлично. Теперь выберите вашу роль:", reply_markup=get_roles_kb("join"))
    await state.set_state(None) # Временно снимаем состояние

@router.callback_query(F.data.startswith("join_"))
async def finish_join(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Меню управления открыто! 👇", reply_markup=get_main_menu_kb())
    data = await state.get_data()
    code = data.get("code")
    role = "Муж" if "husband" in callback.data else "Жена"
    
    success = await join_family(callback.from_user.id, code, role)
    if success:
        await callback.message.edit_text(f"✅ Вы успешно присоединились к семье как {role}! Теперь у вас общий бюджет.")
    else:
        await callback.message.edit_text("❌ Неверный код приглашения. Попробуйте еще раз: /start")