# handlers/users/business_plan_handler.py
# Biznes reja handler - tayyor planlar katalogi + AI generatsiya

import os
import uuid
import logging
import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)

from loader import dp, bot, user_db
from data.config import ADMINS, OPENAI_API_KEY
from keyboards.default.default_keyboard import main_menu_keyboard

logger = logging.getLogger(__name__)

DOWNLOADS_DIR = "downloads"


# ==================== FSM STATES ====================

class BiznesPlanAdminStates(StatesGroup):
    waiting_file = State()
    waiting_title = State()
    waiting_category = State()
    waiting_price = State()
    waiting_description = State()


class BiznesPlanUserStates(StatesGroup):
    waiting_initiator_type = State()   # 1. Jismoniy / Tadbirkorlik
    waiting_company_info = State()     # 2. Korxona nomi (faqat tadbirkorlik uchun)
    waiting_personal_info = State()    # 3. F.I.Sh va telefon
    waiting_location = State()         # 4. Hudud
    waiting_project_info = State()     # 5. Loyiha nomi va maqsadi
    waiting_product_service = State()  # 6. Mahsulot/xizmat
    waiting_expenses = State()         # 7. Xarajatlar
    waiting_financing = State()        # 8. Moliyalashtirish
    waiting_credit_terms = State()     # 9. Kredit shartlari
    waiting_marketing = State()        # 10. Marketing
    waiting_language = State()         # 11. Til tanlash


# ==================== KATEGORIYALAR ====================

CATEGORIES = {
    "💻 IT va Texnologiya": "IT",
    "🛒 Savdo va Do'konlar": "Savdo",
    "🌾 Qishloq xo'jaligi": "Qishloq",
    "🧹 Xizmat ko'rsatish": "Xizmat",
    "🏭 Ishlab chiqarish": "Ishlab",
    "✈️ Turizm va Mehmonxona": "Turizm",
    "📦 Boshqa soha": "Umumiy",
}

CATEGORY_ICONS = {v: k.split()[0] for k, v in CATEGORIES.items()}


def _cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("❌ Bekor qilish")]],
        resize_keyboard=True
    )


def _back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("⬅️ Orqaga")]],
        resize_keyboard=True
    )


# ==============================================================================
# USER: ASOSIY MENYU — "📋 Biznes Reja" TUGMASI
# ==============================================================================

@dp.message_handler(text="📋 Biznes Reja")
async def biznes_reja_menu(message: types.Message, state: FSMContext):
    await state.finish()
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📂 Tayyor biznes planlar", callback_data="bp:catalog"),
        InlineKeyboardButton("🤖 AI bilan biznes reja yaratish", callback_data="bp:ai_generate"),
    )
    await message.answer(
        "📋 <b>Biznes Reja bo'limi</b>\n\n"
        "Ikki imkoniyat mavjud:\n\n"
        "📂 <b>Tayyor planlar</b> — turli sohalardagi tayyor biznes rejalar, darhol yuklab olish mumkin\n\n"
        "🤖 <b>AI generatsiya</b> — sizning biznesingiz uchun maxsus, professional biznes reja",
        parse_mode='HTML',
        reply_markup=kb
    )


# ==============================================================================
# KATALOG — TAYYOR PLANLAR
# ==============================================================================

@dp.callback_query_handler(lambda c: c.data == "bp:catalog")
async def show_catalog(call: types.CallbackQuery):
    await call.answer()
    categories = user_db.get_all_categories()

    if not categories:
        await call.message.edit_text(
            "📂 Hozircha tayyor biznes planlar yo'q.\n\n"
            "Tez orada qo'shiladi! 🤖 AI bilan yaratib ko'ring.",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🤖 AI bilan yaratish", callback_data="bp:ai_generate"),
                InlineKeyboardButton("⬅️ Orqaga", callback_data="bp:back_main"),
            )
        )
        return

    kb = InlineKeyboardMarkup(row_width=2)
    for cat in categories:
        icon = CATEGORY_ICONS.get(cat, "📁")
        plans = user_db.get_business_plans_by_category(cat)
        kb.insert(InlineKeyboardButton(
            f"{icon} {cat} ({len(plans)})",
            callback_data=f"bp:cat:{cat}"
        ))
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="bp:back_main"))

    await call.message.edit_text(
        "📂 <b>Tayyor biznes planlar</b>\n\nKategoriyani tanlang:",
        parse_mode='HTML',
        reply_markup=kb
    )


@dp.callback_query_handler(lambda c: c.data.startswith("bp:cat:"))
async def show_plans_in_category(call: types.CallbackQuery):
    await call.answer()
    category = call.data.split("bp:cat:")[1]
    plans = user_db.get_business_plans_by_category(category)

    if not plans:
        await call.message.edit_text(
            "Bu kategoriyada hozircha plan yo'q.",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("⬅️ Orqaga", callback_data="bp:catalog")
            )
        )
        return

    kb = InlineKeyboardMarkup(row_width=1)
    for plan in plans:
        kb.add(InlineKeyboardButton(
            f"📄 {plan['title']} — {plan['price']:,.0f} so'm",
            callback_data=f"bp:plan:{plan['id']}"
        ))
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="bp:catalog"))

    icon = CATEGORY_ICONS.get(category, "📁")
    await call.message.edit_text(
        f"{icon} <b>{category}</b>\n\nPlanni tanlang:",
        parse_mode='HTML',
        reply_markup=kb
    )


@dp.callback_query_handler(lambda c: c.data.startswith("bp:plan:"))
async def show_plan_detail(call: types.CallbackQuery):
    await call.answer()
    plan_id = int(call.data.split("bp:plan:")[1])
    plan = user_db.get_business_plan_by_id(plan_id)

    if not plan:
        await call.message.edit_text("Plan topilmadi.")
        return

    telegram_id = call.from_user.id
    already_bought = user_db.has_user_purchased_plan(telegram_id, plan_id)
    balance = user_db.get_user_balance(telegram_id)

    desc = plan.get('description') or "Batafsil tavsif mavjud emas."
    icon = CATEGORY_ICONS.get(plan.get('category', ''), "📄")

    text = (
        f"{icon} <b>{plan['title']}</b>\n\n"
        f"📁 Kategoriya: {plan.get('category', '—')}\n"
        f"💰 Narxi: <b>{plan['price']:,.0f} so'm</b>\n"
        f"📊 Sotilgan: {plan.get('sold_count', 0)} marta\n\n"
        f"📝 <b>Tavsif:</b>\n{desc}\n\n"
        f"💳 Sizning balansingiz: <b>{balance:,.0f} so'm</b>"
    )

    kb = InlineKeyboardMarkup(row_width=1)
    if already_bought:
        kb.add(InlineKeyboardButton("📥 Qayta yuklab olish", callback_data=f"bp:download:{plan_id}"))
    else:
        kb.add(InlineKeyboardButton(f"💳 Sotib olish — {plan['price']:,.0f} so'm", callback_data=f"bp:buy:{plan_id}"))
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data=f"bp:cat:{plan.get('category', '')}"))

    await call.message.edit_text(text, parse_mode='HTML', reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("bp:buy:"))
async def buy_plan(call: types.CallbackQuery):
    await call.answer()
    plan_id = int(call.data.split("bp:buy:")[1])
    telegram_id = call.from_user.id
    plan = user_db.get_business_plan_by_id(plan_id)

    if not plan:
        await call.message.edit_text("Plan topilmadi.")
        return

    if user_db.has_user_purchased_plan(telegram_id, plan_id):
        await _send_plan_file(call.message, telegram_id, plan)
        return

    balance = user_db.get_user_balance(telegram_id)
    if balance < plan['price']:
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("⬅️ Orqaga", callback_data=f"bp:plan:{plan_id}")
        )
        await call.message.edit_text(
            f"❌ <b>Balans yetarli emas!</b>\n\n"
            f"Kerakli: <b>{plan['price']:,.0f} so'm</b>\n"
            f"Sizda: <b>{balance:,.0f} so'm</b>\n\n"
            "Balansni to'ldiring va qaytadan urinib ko'ring.",
            parse_mode='HTML',
            reply_markup=kb
        )
        return

    # To'lov
    success = user_db.deduct_from_balance(telegram_id, plan['price'])
    if not success:
        await call.message.edit_text("❌ To'lovda xatolik!")
        return

    user_db.create_transaction(
        telegram_id=telegram_id,
        transaction_type='withdrawal',
        amount=plan['price'],
        description=f"Biznes reja: {plan['title']}",
        status='approved'
    )
    user_db.record_plan_purchase(telegram_id, plan_id, plan['price'])

    await call.message.edit_text(
        f"✅ <b>To'lov qabul qilindi!</b>\nFayl yuborilmoqda...",
        parse_mode='HTML'
    )
    await _send_plan_file(call.message, telegram_id, plan)


@dp.callback_query_handler(lambda c: c.data.startswith("bp:download:"))
async def download_plan(call: types.CallbackQuery):
    await call.answer()
    plan_id = int(call.data.split("bp:download:")[1])
    telegram_id = call.from_user.id
    plan = user_db.get_business_plan_by_id(plan_id)

    if not plan:
        await call.message.edit_text("Plan topilmadi.")
        return

    if not user_db.has_user_purchased_plan(telegram_id, plan_id):
        await call.answer("❌ Bu planni sotib olmadingiz!", show_alert=True)
        return

    await _send_plan_file(call.message, telegram_id, plan)


async def _send_plan_file(message: types.Message, telegram_id: int, plan: dict):
    """Plan faylini yuborish"""
    try:
        balance = user_db.get_user_balance(telegram_id)
        await bot.send_document(
            chat_id=telegram_id,
            document=plan['file_id'],
            caption=(
                f"✅ <b>{plan['title']}</b>\n\n"
                f"📁 {plan.get('category', '')}\n"
                f"💳 Qolgan balans: <b>{balance:,.0f} so'm</b>"
            ),
            parse_mode='HTML',
            reply_markup=main_menu_keyboard(telegram_id=telegram_id, user_db=user_db)
        )
    except Exception as e:
        logger.error(f"Plan fayl yuborishda xato: {e}")
        await bot.send_message(
            telegram_id,
            "❌ Fayl yuborishda xatolik. Admin bilan bog'laning.",
            reply_markup=main_menu_keyboard(telegram_id=telegram_id, user_db=user_db)
        )


@dp.callback_query_handler(lambda c: c.data == "bp:back_main")
async def back_to_bp_main(call: types.CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📂 Tayyor biznes planlar", callback_data="bp:catalog"),
        InlineKeyboardButton("🤖 AI bilan biznes reja yaratish", callback_data="bp:ai_generate"),
    )
    await call.message.edit_text(
        "📋 <b>Biznes Reja bo'limi</b>\n\n"
        "Ikki imkoniyat mavjud:\n\n"
        "📂 <b>Tayyor planlar</b> — turli sohalardagi tayyor biznes rejalar\n\n"
        "🤖 <b>AI generatsiya</b> — sizning biznesingiz uchun maxsus reja",
        parse_mode='HTML',
        reply_markup=kb
    )


# ==============================================================================
# AI GENERATSIYA — USER FLOW
# ==============================================================================

def _initiator_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("👤 Jismoniy shaxs"), KeyboardButton("🏢 Tadbirkorlik subyekti")],
            [KeyboardButton("❌ Bekor qilish")],
        ],
        resize_keyboard=True
    )


@dp.callback_query_handler(lambda c: c.data == "bp:ai_generate")
async def start_ai_generate(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.delete()

    price = user_db.get_price('biznes_plan_ai') or 25000
    balance = user_db.get_user_balance(call.from_user.id)

    await bot.send_message(
        call.from_user.id,
        f"🤖 <b>AI Biznes Reja Generatsiya</b>\n\n"
        f"💡 Sun'iy intellekt sizning biznesingiz uchun <b>professional biznes reja</b> yozadi:\n\n"
        f"✅ Ijroiya xulosa\n"
        f"✅ Bozor tahlili (SWOT, raqobat)\n"
        f"✅ Marketing strategiyasi\n"
        f"✅ Moliyaviy prognoz (jadvallar)\n"
        f"✅ Risk tahlili\n"
        f"✅ va boshqa 6 bo'lim\n\n"
        f"💰 Narxi: <b>{price:,.0f} so'm</b>\n"
        f"💳 Balansingiz: <b>{balance:,.0f} so'm</b>\n\n"
        f"🔹 <b>1/10 — Tashabbuskor turi</b>\n"
        f"Siz kim sifatida ro'yxatdan o'tasiz?",
        parse_mode='HTML',
        reply_markup=_initiator_keyboard()
    )
    await BiznesPlanUserStates.waiting_initiator_type.set()


@dp.message_handler(text="❌ Bekor qilish", state=BiznesPlanUserStates)
async def cancel_ai_generation(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "❌ Bekor qilindi.",
        reply_markup=main_menu_keyboard(telegram_id=message.from_user.id, user_db=user_db)
    )


@dp.message_handler(
    lambda m: m.text in ("👤 Jismoniy shaxs", "🏢 Tadbirkorlik subyekti"),
    state=BiznesPlanUserStates.waiting_initiator_type
)
async def get_initiator_type(message: types.Message, state: FSMContext):
    initiator = message.text.strip()
    await state.update_data(initiator_type=initiator)

    if initiator == "🏢 Tadbirkorlik subyekti":
        await message.answer(
            "🔹 <b>2/10 — Korxona ma'lumoti</b>\n\n"
            "Korxona nomi va faoliyat turini kiriting\n"
            "<i>Masalan: «Nur Savdo» MChJ — oziq-ovqat savdosi</i>",
            parse_mode='HTML',
            reply_markup=_cancel_keyboard()
        )
        await BiznesPlanUserStates.waiting_company_info.set()
    else:
        await state.update_data(company_info="")
        await message.answer(
            "🔹 <b>2/10 — Shaxsiy ma'lumot</b>\n\n"
            "F.I.Sh va telefon raqamingizni kiriting\n"
            "<i>Masalan: Aliyev Jasur Bahodir o'g'li, +998901234567</i>",
            parse_mode='HTML',
            reply_markup=_cancel_keyboard()
        )
        await BiznesPlanUserStates.waiting_personal_info.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_company_info)
async def get_company_info(message: types.Message, state: FSMContext):
    await state.update_data(company_info=message.text.strip())
    await message.answer(
        "🔹 <b>3/10 — Shaxsiy ma'lumot</b>\n\n"
        "F.I.Sh va telefon raqamingizni kiriting\n"
        "<i>Masalan: Aliyev Jasur Bahodir o'g'li, +998901234567</i>",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_personal_info.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_personal_info)
async def get_personal_info(message: types.Message, state: FSMContext):
    await state.update_data(personal_info=message.text.strip())
    await message.answer(
        "🔹 <b>4/10 — Hudud</b>\n\n"
        "Loyihangiz qaysi hududda amalga oshiriladi?\n"
        "<i>Masalan: Toshkent shahri, Samarqand viloyati Urgut tumani</i>",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_location.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_location)
async def get_location(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text.strip())
    await message.answer(
        "🔹 <b>5/10 — Loyiha haqida</b>\n\n"
        "Loyiha nomi va maqsadini qisqacha yozing\n"
        "<i>Masalan: «FreshMart» — mahallada arzon va sifatli oziq-ovqat do'koni ochish</i>",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_project_info.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_project_info)
async def get_project_info(message: types.Message, state: FSMContext):
    await state.update_data(project_info=message.text.strip())
    await message.answer(
        "🔹 <b>6/10 — Mahsulot / xizmat</b>\n\n"
        "Qanday mahsulot yoki xizmat taklif qilasiz?\n"
        "<i>Masalan: kundalik oziq-ovqat mahsulotlari: non, sut, sabzavot, meva</i>",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_product_service.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_product_service)
async def get_product_service(message: types.Message, state: FSMContext):
    await state.update_data(product_service=message.text.strip())
    await message.answer(
        "🔹 <b>7/10 — Xarajatlar</b>\n\n"
        "Qanday uskunalar/tovarlar olinadi va jami qiymati qancha?\n"
        "<i>Masalan: sovutgich 8 mln, javonlar 3 mln, kassa apparati 2 mln — jami 13 mln so'm</i>",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_expenses.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_expenses)
async def get_expenses(message: types.Message, state: FSMContext):
    await state.update_data(expenses=message.text.strip())
    await message.answer(
        "🔹 <b>8/10 — Moliyalashtirish</b>\n\n"
        "O'z mablag'ingiz va kerakli kredit summasini yozing\n"
        "<i>Masalan: o'z mablag'im 5 mln so'm, kredit 10 mln so'm kerak</i>",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_financing.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_financing)
async def get_financing(message: types.Message, state: FSMContext):
    await state.update_data(financing=message.text.strip())
    await message.answer(
        "🔹 <b>9/10 — Kredit shartlari</b>\n\n"
        "Kredit foizi (%) va muddati (necha yil)?\n"
        "<i>Masalan: 18% yillik, 3 yil muddatga</i>",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_credit_terms.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_credit_terms)
async def get_credit_terms(message: types.Message, state: FSMContext):
    await state.update_data(credit_terms=message.text.strip())
    await message.answer(
        "🔹 <b>10/10 — Marketing</b>\n\n"
        "Mijozlarni qanday topasiz? (reklama/sotuv usuli)\n"
        "<i>Masalan: ijtimoiy tarmoqlar, mahalla e'lonlari, og'zaki tavsiya</i>",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_marketing.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_marketing)
async def get_marketing(message: types.Message, state: FSMContext):
    await state.update_data(marketing=message.text.strip())

    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("🇺🇿 O'zbek", callback_data="bp_lang:uz"),
        InlineKeyboardButton("🇷🇺 Rus", callback_data="bp_lang:ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="bp_lang:en"),
    )
    await message.answer(
        "✅ <b>Ma'lumotlar qabul qilindi!</b>\n\n"
        "🌐 Biznes reja tilini tanlang:",
        parse_mode='HTML',
        reply_markup=kb
    )
    await BiznesPlanUserStates.waiting_language.set()


@dp.callback_query_handler(lambda c: c.data.startswith("bp_lang:"), state=BiznesPlanUserStates.waiting_language)
async def start_generation(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    language = call.data.split("bp_lang:")[1]
    await state.update_data(language=language)

    data = await state.get_data()
    telegram_id = call.from_user.id
    await state.finish()

    price = user_db.get_price('biznes_plan_ai') or 25000
    balance = user_db.get_user_balance(telegram_id)

    if balance < price:
        await call.message.edit_text(
            f"❌ <b>Balans yetarli emas!</b>\n\n"
            f"Kerakli: <b>{price:,.0f} so'm</b>\n"
            f"Sizda: <b>{balance:,.0f} so'm</b>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("⬅️ Orqaga", callback_data="bp:ai_generate")
            )
        )
        return

    success = user_db.deduct_from_balance(telegram_id, price)
    if not success:
        await call.message.edit_text("❌ To'lovda xatolik!")
        return

    user_db.create_transaction(
        telegram_id=telegram_id,
        transaction_type='withdrawal',
        amount=price,
        description=f"AI Biznes Reja: {data.get('project_info', '')}",
        status='approved'
    )

    lang_names = {"uz": "O'zbek", "ru": "Rus", "en": "Ingliz"}
    status_msg = await call.message.edit_text(
        f"✅ <b>To'lov qabul qilindi! Generatsiya boshlandi...</b>\n\n"
        f"📋 Loyiha: {data.get('project_info', '')[:60]}\n"
        f"📍 Hudud: {data.get('location', '')}\n"
        f"🌐 Til: {lang_names.get(language, 'Uzbek')}\n\n"
        f"⏳ <b>Taxminiy vaqt: 10-15 daqiqa</b>\n"
        f"<i>AI jami 10 bo'limni alohida yozadi — sifat uchun.\n"
        f"Quyida har bir bosqich haqida xabar beriladi.</i>",
        parse_mode='HTML'
    )

    asyncio.create_task(
        _run_ai_generation(
            telegram_id=telegram_id,
            data=data,
            language=language,
            price=price,
            status_msg=status_msg,
        )
    )


async def _run_ai_generation(
        telegram_id: int,
        data: dict,
        language: str,
        price: float,
        status_msg: types.Message,
):
    """AI generatsiyani background'da ishga tushirish"""
    from utils.business_plan_generator import BusinessPlanGenerator
    from utils.business_plan_docx import BusinessPlanDocx

    try:
        generator = BusinessPlanGenerator(api_key=OPENAI_API_KEY)

        lang_names = {"uz": "O'zbek", "ru": "Rus", "en": "Ingliz"}
        header = (
            f"🤖 <b>Biznes reja tayyorlanmoqda...</b>\n\n"
            f"📋 Loyiha: {data.get('project_info', '')[:60]}\n"
            f"📍 Hudud: {data.get('location', '')}\n"
            f"🌐 Til: {lang_names.get(language, 'Uzbek')}\n"
        )

        # O'rtacha har bir bo'lim ~75 sekundda tayyor bo'ladi
        SECONDS_PER_STEP = 75

        async def progress_cb(step: int, total: int, title: str):
            done = step - 1
            percent = int(done / total * 100)
            filled = done * 2  # 20 ta katak (total * 2)
            bar = "▓" * filled + "░" * (total * 2 - filled)
            remaining_steps = total - done
            remaining_min = max(1, (remaining_steps * SECONDS_PER_STEP) // 60)

            # Oldingi tayyor bo'limlar ro'yxati (belgilangan)
            sections_list = [
                "Ijroiya xulosasi",
                "Tashabbuskor va kompaniya tavsifi",
                "Bozor tahlili",
                "Mahsulot va xizmatlar",
                "Marketing va savdo strategiyasi",
                "Operatsion reja",
                "Moliyaviy prognoz",
                "Boshqaruv jamoasi",
                "Risk tahlili",
                "Xulosa",
            ]
            lines = []
            for i, name in enumerate(sections_list, start=1):
                if i < step:
                    lines.append(f"✅ {i}/10 — {name}")
                elif i == step:
                    lines.append(f"⏳ <b>{i}/10 — {name}</b> (yozilmoqda...)")
                else:
                    lines.append(f"⚪️ {i}/10 — {name}")
            progress_list = "\n".join(lines)

            text = (
                f"{header}\n"
                f"📊 <b>Jarayon: {percent}%</b>  [{bar}]\n"
                f"⏱ <i>Taxminan {remaining_min} daqiqa qoldi</i>\n\n"
                f"{progress_list}"
            )
            try:
                await status_msg.edit_text(text, parse_mode='HTML')
            except Exception as e:
                logger.debug(f"Progress edit xato: {e}")

        content = await generator.generate(
            language=language,
            initiator_type=data.get('initiator_type', ''),
            company_info=data.get('company_info', ''),
            personal_info=data.get('personal_info', ''),
            location=data.get('location', ''),
            project_info=data.get('project_info', ''),
            product_service=data.get('product_service', ''),
            expenses=data.get('expenses', ''),
            financing=data.get('financing', ''),
            credit_terms=data.get('credit_terms', ''),
            marketing=data.get('marketing', ''),
            progress_callback=progress_cb,
        )

        if not content:
            raise ValueError("Generator None qaytardi")

        # Yakuniy bosqich — DOCX yig'ilmoqda
        try:
            await status_msg.edit_text(
                f"{header}\n"
                f"📊 <b>Jarayon: 100%</b>  [{'▓' * 20}]\n"
                f"⏱ <i>Deyarli tayyor — bir necha soniya...</i>\n\n"
                f"✅ Barcha 10 bo'lim yozildi\n"
                f"📄 <b>DOCX hujjat yig'ilmoqda va sizga yuborilmoqda...</b>",
                parse_mode='HTML'
            )
        except Exception:
            pass

        # DOCX yaratish
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        safe_name_src = data.get('project_info') or data.get('business_name') or 'biznes'
        safe_name = "".join(c for c in safe_name_src if c.isalnum() or c in ' _-')[:20].strip() or 'biznes'
        filename = f"BiznesPlan_{safe_name}_{telegram_id}.docx"
        file_path = os.path.join(DOWNLOADS_DIR, filename)

        docx_gen = BusinessPlanDocx()
        success = docx_gen.create(content=content, output_path=file_path)

        if not success:
            raise ValueError("DOCX yaratishda xato")

        balance = user_db.get_user_balance(telegram_id)
        await bot.send_document(
            chat_id=telegram_id,
            document=types.InputFile(file_path),
            caption=(
                f"✅ <b>Biznes reja tayyor!</b>\n\n"
                f"📋 <b>{data.get('project_info', '')[:80]}</b>\n"
                f"📍 Hudud: {data.get('location', '')}\n"
                f"🛒 Mahsulot: {data.get('product_service', '')[:60]}\n\n"
                f"📄 Professional format, 10 bo'lim\n"
                f"💳 Qolgan balans: <b>{balance:,.0f} so'm</b>"
            ),
            parse_mode='HTML',
            reply_markup=main_menu_keyboard(telegram_id=telegram_id, user_db=user_db)
        )

        try:
            os.remove(file_path)
        except Exception:
            pass

        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"AI biznes plan generatsiya xato: {e}")
        # Pulni qaytarish
        try:
            user_db.add_to_balance(telegram_id, price)
            user_db.create_transaction(
                telegram_id=telegram_id,
                transaction_type='refund',
                amount=price,
                description="Qaytarildi: AI biznes plan xatosi",
                status='approved'
            )
        except Exception:
            pass

        try:
            await status_msg.edit_text(
                "❌ <b>Xatolik yuz berdi. Pul qaytarildi.</b>",
                parse_mode='HTML',
                reply_markup=main_menu_keyboard(telegram_id=telegram_id, user_db=user_db)
            )
        except Exception:
            await bot.send_message(
                telegram_id,
                "❌ Xatolik yuz berdi. Pul qaytarildi.",
                reply_markup=main_menu_keyboard(telegram_id=telegram_id, user_db=user_db)
            )


# ==============================================================================
# ADMIN — PLAN QO'SHISH
# ==============================================================================

@dp.message_handler(commands=["add_plan"])
async def admin_add_plan_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    await message.answer(
        "📎 <b>Yangi biznes plan qo'shish</b>\n\n"
        "Biznes reja faylini (PDF yoki DOCX) yuboring:",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanAdminStates.waiting_file.set()


@dp.message_handler(text="❌ Bekor qilish", state=BiznesPlanAdminStates)
async def admin_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=BiznesPlanAdminStates.waiting_file)
async def admin_get_file(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    await state.update_data(file_id=file_id)
    await message.answer(
        "✅ Fayl qabul qilindi.\n\n📝 Plan sarlavhasini kiriting:",
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanAdminStates.waiting_title.set()


@dp.message_handler(state=BiznesPlanAdminStates.waiting_title)
async def admin_get_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text.strip())

    kb = InlineKeyboardMarkup(row_width=2)
    for label, code in CATEGORIES.items():
        kb.insert(InlineKeyboardButton(label, callback_data=f"bp_adm_cat:{code}"))

    await message.answer(
        "📁 Kategoriyani tanlang:",
        reply_markup=kb
    )
    await BiznesPlanAdminStates.waiting_category.set()


@dp.callback_query_handler(lambda c: c.data.startswith("bp_adm_cat:"), state=BiznesPlanAdminStates.waiting_category)
async def admin_get_category(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    category = call.data.split("bp_adm_cat:")[1]
    await state.update_data(category=category)
    await call.message.edit_text(
        f"✅ Kategoriya: <b>{category}</b>\n\n💰 Narxini kiriting (so'mda, faqat raqam):",
        parse_mode='HTML'
    )
    await BiznesPlanAdminStates.waiting_price.set()


@dp.message_handler(state=BiznesPlanAdminStates.waiting_price)
async def admin_get_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.strip().replace(',', '').replace(' ', ''))
    except ValueError:
        await message.answer("❌ Narx noto'g'ri. Faqat raqam kiriting:")
        return

    await state.update_data(price=price)
    await message.answer(
        "📋 Plan tavsifini kiriting (qisqacha, 1-3 jumla):",
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanAdminStates.waiting_description.set()


@dp.message_handler(state=BiznesPlanAdminStates.waiting_description)
async def admin_get_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()

    description = message.text.strip()
    plan_id = user_db.add_business_plan(
        title=data['title'],
        description=description,
        price=data['price'],
        file_id=data['file_id'],
        category=data['category'],
    )

    if plan_id:
        await message.answer(
            f"✅ <b>Plan qo'shildi!</b>\n\n"
            f"📄 Sarlavha: {data['title']}\n"
            f"📁 Kategoriya: {data['category']}\n"
            f"💰 Narxi: {data['price']:,.0f} so'm\n"
            f"🆔 ID: {plan_id}",
            parse_mode='HTML',
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer("❌ Xatolik! Plan qo'shilmadi.", reply_markup=types.ReplyKeyboardRemove())


# ==============================================================================
# ADMIN — PLANLARNI BOSHQARISH
# ==============================================================================

@dp.message_handler(commands=["plans"])
async def admin_list_plans(message: types.Message):
    if message.from_user.id not in ADMINS:
        return

    plans = user_db.get_all_business_plans(active_only=False)
    if not plans:
        await message.answer("📂 Hech qanday plan yo'q. /add_plan bilan qo'shing.")
        return

    kb = InlineKeyboardMarkup(row_width=1)
    for plan in plans[:20]:
        status = "✅" if plan['is_active'] else "❌"
        kb.add(InlineKeyboardButton(
            f"{status} {plan['title']} — {plan['price']:,.0f} so'm",
            callback_data=f"bpadm:manage:{plan['id']}"
        ))

    await message.answer(
        f"📂 <b>Barcha biznes planlar</b> ({len(plans)} ta):",
        parse_mode='HTML',
        reply_markup=kb
    )


@dp.callback_query_handler(lambda c: c.data.startswith("bpadm:manage:"))
async def admin_manage_plan(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    await call.answer()
    plan_id = int(call.data.split("bpadm:manage:")[1])
    plan = user_db.get_business_plan_by_id(plan_id)
    if not plan:
        await call.message.edit_text("Plan topilmadi.")
        return

    status = "✅ Aktiv" if plan['is_active'] else "❌ Nofaol"
    toggle_text = "❌ O'chirish" if plan['is_active'] else "✅ Yoqish"

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(toggle_text, callback_data=f"bpadm:toggle:{plan_id}"),
        InlineKeyboardButton("💰 Narx o'zgartirish", callback_data=f"bpadm:price:{plan_id}"),
    )
    kb.add(InlineKeyboardButton("🗑 O'chirish", callback_data=f"bpadm:delete:{plan_id}"))
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="bpadm:list"))

    await call.message.edit_text(
        f"⚙️ <b>{plan['title']}</b>\n\n"
        f"📁 Kategoriya: {plan.get('category', '—')}\n"
        f"💰 Narxi: {plan['price']:,.0f} so'm\n"
        f"📊 Sotilgan: {plan.get('sold_count', 0)} marta\n"
        f"🔘 Status: {status}",
        parse_mode='HTML',
        reply_markup=kb
    )


@dp.callback_query_handler(lambda c: c.data.startswith("bpadm:toggle:"))
async def admin_toggle_plan(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    await call.answer()
    plan_id = int(call.data.split("bpadm:toggle:")[1])
    user_db.toggle_business_plan(plan_id)
    plan = user_db.get_business_plan_by_id(plan_id)
    status = "✅ Yoqildi" if plan['is_active'] else "❌ O'chirildi"
    await call.answer(f"{status}: {plan['title']}", show_alert=True)
    await admin_manage_plan(call)


@dp.callback_query_handler(lambda c: c.data.startswith("bpadm:delete:"))
async def admin_delete_plan(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    await call.answer()
    plan_id = int(call.data.split("bpadm:delete:")[1])
    plan = user_db.get_business_plan_by_id(plan_id)
    if not plan:
        return

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"bpadm:confirm_delete:{plan_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data=f"bpadm:manage:{plan_id}"),
    )
    await call.message.edit_text(
        f"⚠️ <b>Rostdan ham o'chirilsinmi?</b>\n\n{plan['title']}",
        parse_mode='HTML',
        reply_markup=kb
    )


@dp.callback_query_handler(lambda c: c.data.startswith("bpadm:confirm_delete:"))
async def admin_confirm_delete(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    await call.answer()
    plan_id = int(call.data.split("bpadm:confirm_delete:")[1])
    user_db.delete_business_plan(plan_id)
    await call.message.edit_text("✅ Plan o'chirildi.")


@dp.callback_query_handler(lambda c: c.data == "bpadm:list")
async def admin_back_to_list(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    await call.answer()
    plans = user_db.get_all_business_plans(active_only=False)

    kb = InlineKeyboardMarkup(row_width=1)
    for plan in plans[:20]:
        status = "✅" if plan['is_active'] else "❌"
        kb.add(InlineKeyboardButton(
            f"{status} {plan['title']} — {plan['price']:,.0f} so'm",
            callback_data=f"bpadm:manage:{plan['id']}"
        ))

    await call.message.edit_text(
        f"📂 <b>Barcha biznes planlar</b> ({len(plans)} ta):",
        parse_mode='HTML',
        reply_markup=kb
    )


# ==============================================================================
# NARX O'ZGARTIRISH (FSM - inline + message mix)
# ==============================================================================

class BiznesPlanPriceState(StatesGroup):
    waiting_new_price = State()


@dp.callback_query_handler(lambda c: c.data.startswith("bpadm:price:"))
async def admin_change_price_start(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMINS:
        return
    await call.answer()
    plan_id = int(call.data.split("bpadm:price:")[1])
    await state.update_data(plan_id=plan_id)
    await call.message.edit_text(
        "💰 Yangi narxni kiriting (so'mda, faqat raqam):"
    )
    await BiznesPlanPriceState.waiting_new_price.set()


@dp.message_handler(state=BiznesPlanPriceState.waiting_new_price)
async def admin_change_price_done(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await state.finish()
        return
    try:
        new_price = float(message.text.strip().replace(',', '').replace(' ', ''))
    except ValueError:
        await message.answer("❌ Noto'g'ri narx. Faqat raqam kiriting:")
        return

    data = await state.get_data()
    plan_id = data.get('plan_id')
    await state.finish()

    user_db.update_business_plan_price(plan_id, new_price)
    plan = user_db.get_business_plan_by_id(plan_id)
    await message.answer(
        f"✅ Narx yangilandi!\n\n"
        f"📄 {plan['title']}\n"
        f"💰 Yangi narx: <b>{new_price:,.0f} so'm</b>",
        parse_mode='HTML'
    )
