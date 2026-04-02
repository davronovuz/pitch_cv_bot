import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.config import ADMINS
from loader import dp, user_db
from keyboards.default.default_keyboard import menu_admin, menu_ichki_plan

logger = logging.getLogger(__name__)

CATEGORIES = [
    "IT", "Savdo", "Qishloq", "Xizmat", "Ishlab", "Turizm", "Umumiy"
]

CATEGORY_LABELS = {
    "IT": "💻 IT va Texnologiya",
    "Savdo": "🛒 Savdo va Do'konlar",
    "Qishloq": "🌾 Qishloq xo'jaligi",
    "Xizmat": "🧹 Xizmat ko'rsatish",
    "Ishlab": "🏭 Ishlab chiqarish",
    "Turizm": "✈️ Turizm va Mehmonxona",
    "Umumiy": "📦 Boshqa soha",
}


class PlanAdminStates(StatesGroup):
    # Plan qo'shish
    waiting_file = State()
    waiting_title = State()
    waiting_category = State()
    waiting_price = State()
    waiting_description = State()
    # Plan o'chirish
    waiting_delete_id = State()


async def check_admin(telegram_id: int) -> bool:
    if telegram_id in ADMINS:
        return True
    user = user_db.select_user(telegram_id=telegram_id)
    if not user:
        return False
    return user_db.check_if_admin(user_id=user[0])


# ==================== KIRISH ====================

@dp.message_handler(Text("📋 Biznes rejalar"), state='*')
async def plan_admin_menu(message: types.Message, state: FSMContext):
    await state.finish()
    if not await check_admin(message.from_user.id):
        return

    plans = user_db.execute("SELECT COUNT(*) FROM BusinessPlans WHERE is_active=1", fetchone=True)
    total = plans[0] if plans else 0

    await message.answer(
        f"📋 <b>BIZNES REJALAR BOSHQARUVI</b>\n\n"
        f"Faol planlar soni: <b>{total}</b>\n\n"
        "Quyidagi amalni tanlang:",
        parse_mode='HTML',
        reply_markup=menu_ichki_plan
    )


# ==================== BARCHA PLANLAR RO'YXATI ====================

@dp.message_handler(Text("📋 Barcha planlar"), state='*')
async def list_all_plans(message: types.Message, state: FSMContext):
    await state.finish()
    if not await check_admin(message.from_user.id):
        return

    plans = user_db.execute(
        "SELECT id, title, category, price, sold_count, is_active FROM BusinessPlans ORDER BY id DESC",
        fetchall=True
    )

    if not plans:
        await message.answer("📭 Hozircha hech qanday plan yo'q.", reply_markup=menu_ichki_plan)
        return

    text = "📋 <b>BARCHA BIZNES REJALAR:</b>\n\n"
    for p in plans:
        pid, title, category, price, sold, is_active = p
        status = "✅" if is_active else "❌"
        label = CATEGORY_LABELS.get(category, category)
        text += f"{status} <b>#{pid}</b> — {title}\n"
        text += f"   📁 {label} | 💰 {price:,.0f} so'm | 🛒 {sold} marta\n\n"

    await message.answer(text, parse_mode='HTML', reply_markup=menu_ichki_plan)


# ==================== STATISTIKA ====================

@dp.message_handler(Text("📊 Plan statistikasi"), state='*')
async def plan_statistics(message: types.Message, state: FSMContext):
    await state.finish()
    if not await check_admin(message.from_user.id):
        return

    stats = user_db.execute(
        """SELECT COUNT(*) as total_plans, SUM(sold_count) as total_sold,
           SUM(price * sold_count) as total_revenue FROM BusinessPlans WHERE is_active=1""",
        fetchone=True
    )

    top_plans = user_db.execute(
        """SELECT title, sold_count, price * sold_count as revenue
           FROM BusinessPlans WHERE is_active=1
           ORDER BY sold_count DESC LIMIT 5""",
        fetchall=True
    )

    text = f"""📊 <b>BIZNES REJALAR STATISTIKASI</b>

📋 Faol planlar: <b>{stats[0] or 0}</b>
🛒 Jami sotilgan: <b>{stats[1] or 0}</b>
💰 Jami daromad: <b>{stats[2] or 0:,.0f} so'm</b>

🏆 <b>TOP 5 PLAN:</b>
"""

    if top_plans:
        for i, (title, count, revenue) in enumerate(top_plans, 1):
            text += f"{i}. {title} — {count or 0} ta ({(revenue or 0):,.0f} so'm)\n"
    else:
        text += "Hali sotilmagan.\n"

    await message.answer(text, parse_mode='HTML', reply_markup=menu_ichki_plan)


# ==================== PLAN QO'SHISH ====================

@dp.message_handler(Text("➕ Plan qo'shish"), state='*')
async def add_plan_start(message: types.Message, state: FSMContext):
    if not await check_admin(message.from_user.id):
        return

    await message.answer(
        "📋 <b>YANGI BIZNES PLAN QO'SHISH</b>\n\n"
        "1️⃣ Plan faylini (PDF yoki DOCX) yuboring:\n\n"
        "Bekor qilish uchun /cancel",
        parse_mode='HTML'
    )
    await PlanAdminStates.waiting_file.set()


@dp.message_handler(commands=['cancel'], state=PlanAdminStates)
async def cancel_plan_add(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Bekor qilindi.", reply_markup=menu_ichki_plan)


@dp.message_handler(content_types=['document'], state=PlanAdminStates.waiting_file)
async def plan_file_received(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    await state.update_data(file_id=file_id)

    await message.answer(
        "✅ Fayl qabul qilindi!\n\n"
        "2️⃣ Plan <b>nomini</b> kiriting:\n"
        "<i>Masalan: Restoran biznes rejasi</i>",
        parse_mode='HTML'
    )
    await PlanAdminStates.waiting_title.set()


@dp.message_handler(state=PlanAdminStates.waiting_file)
async def plan_file_wrong(message: types.Message):
    await message.answer("❌ Iltimos, fayl (PDF/DOCX) yuboring.")


@dp.message_handler(state=PlanAdminStates.waiting_title)
async def plan_title_received(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text.strip())

    kb = InlineKeyboardMarkup(row_width=2)
    for key, label in CATEGORY_LABELS.items():
        kb.insert(InlineKeyboardButton(label, callback_data=f"plan_cat:{key}"))

    await message.answer(
        "3️⃣ <b>Kategoriyani tanlang:</b>",
        parse_mode='HTML',
        reply_markup=kb
    )
    await PlanAdminStates.waiting_category.set()


@dp.callback_query_handler(lambda c: c.data.startswith("plan_cat:"), state=PlanAdminStates.waiting_category)
async def plan_category_received(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    category = call.data.split("plan_cat:")[1]
    await state.update_data(category=category)

    label = CATEGORY_LABELS.get(category, category)
    await call.message.edit_text(
        f"✅ Kategoriya: <b>{label}</b>\n\n"
        "4️⃣ <b>Narxini</b> kiriting (so'mda):\n"
        "<i>Masalan: 15000</i>",
        parse_mode='HTML'
    )
    await PlanAdminStates.waiting_price.set()


@dp.message_handler(state=PlanAdminStates.waiting_price)
async def plan_price_received(message: types.Message, state: FSMContext):
    text = message.text.strip().replace(" ", "").replace(",", "")
    if not text.isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting (masalan: 15000).")
        return

    await state.update_data(price=float(text))

    await message.answer(
        "5️⃣ <b>Qisqacha tavsif kiriting:</b>\n"
        "<i>Masalan: Restoranchilik sohasida tayyor biznes reja. 30 sahifa, batafsil moliyaviy hisob-kitoblar bilan.</i>\n\n"
        "O'tkazib yuborish uchun — «-» yuboring.",
        parse_mode='HTML'
    )
    await PlanAdminStates.waiting_description.set()


@dp.message_handler(state=PlanAdminStates.waiting_description)
async def plan_description_received(message: types.Message, state: FSMContext):
    description = message.text.strip()
    if description == "-":
        description = None

    data = await state.get_data()
    await state.finish()

    try:
        user_db.execute(
            """INSERT INTO BusinessPlans (title, description, price, file_id, category, is_active)
               VALUES (?, ?, ?, ?, ?, 1)""",
            (data['title'], description, data['price'], data['file_id'], data['category']),
            commit=True
        )

        label = CATEGORY_LABELS.get(data['category'], data['category'])
        await message.answer(
            f"✅ <b>Plan muvaffaqiyatli qo'shildi!</b>\n\n"
            f"📄 <b>Nomi:</b> {data['title']}\n"
            f"📁 <b>Kategoriya:</b> {label}\n"
            f"💰 <b>Narxi:</b> {data['price']:,.0f} so'm\n"
            f"📝 <b>Tavsif:</b> {description or '—'}",
            parse_mode='HTML',
            reply_markup=menu_ichki_plan
        )
        logger.info(f"Yangi biznes plan qo'shildi: {data['title']}")

    except Exception as e:
        logger.error(f"Plan qo'shishda xato: {e}")
        await message.answer(f"❌ Xato yuz berdi: {e}", reply_markup=menu_ichki_plan)


# ==================== PLAN O'CHIRISH ====================

@dp.message_handler(Text("❌ Plan o'chirish"), state='*')
async def delete_plan_start(message: types.Message, state: FSMContext):
    if not await check_admin(message.from_user.id):
        return

    plans = user_db.execute(
        "SELECT id, title, price FROM BusinessPlans WHERE is_active=1 ORDER BY id DESC",
        fetchall=True
    )

    if not plans:
        await message.answer("📭 O'chirish uchun faol plan yo'q.", reply_markup=menu_ichki_plan)
        return

    kb = InlineKeyboardMarkup(row_width=1)
    for pid, title, price in plans:
        kb.add(InlineKeyboardButton(
            f"❌ #{pid} — {title} ({price:,.0f} so'm)",
            callback_data=f"plan_del:{pid}"
        ))
    kb.add(InlineKeyboardButton("🔙 Bekor qilish", callback_data="plan_del:cancel"))

    await message.answer(
        "🗑 <b>O'chirmoqchi bo'lgan planni tanlang:</b>",
        parse_mode='HTML',
        reply_markup=kb
    )
    await PlanAdminStates.waiting_delete_id.set()


@dp.callback_query_handler(lambda c: c.data.startswith("plan_del:"), state=PlanAdminStates.waiting_delete_id)
async def delete_plan_confirm(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    if call.data == "plan_del:cancel":
        await state.finish()
        await call.message.edit_text("❌ Bekor qilindi.")
        await call.message.answer("Menyu:", reply_markup=menu_ichki_plan)
        return

    plan_id = int(call.data.split("plan_del:")[1])
    plan = user_db.execute(
        "SELECT title FROM BusinessPlans WHERE id=?", (plan_id,), fetchone=True
    )

    if not plan:
        await state.finish()
        await call.message.edit_text("Plan topilmadi.")
        return

    # Soft delete
    user_db.execute(
        "UPDATE BusinessPlans SET is_active=0 WHERE id=?", (plan_id,), commit=True
    )
    await state.finish()
    await call.message.edit_text(
        f"✅ Plan o'chirildi: <b>{plan[0]}</b>",
        parse_mode='HTML'
    )
    await call.message.answer("Menyu:", reply_markup=menu_ichki_plan)
    logger.info(f"Biznes plan o'chirildi: #{plan_id} — {plan[0]}")
