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
    waiting_business_name = State()
    waiting_industry = State()
    waiting_description = State()
    waiting_investment = State()
    waiting_target_market = State()
    waiting_language = State()


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

@dp.callback_query_handler(lambda c: c.data == "bp:ai_generate")
async def start_ai_generate(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.delete()

    # Narxni olish
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
        f"📝 Biznes nomingizni kiriting:",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_business_name.set()


@dp.message_handler(text="❌ Bekor qilish", state=BiznesPlanUserStates)
async def cancel_ai_generation(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "❌ Bekor qilindi.",
        reply_markup=main_menu_keyboard(telegram_id=message.from_user.id, user_db=user_db)
    )


@dp.message_handler(state=BiznesPlanUserStates.waiting_business_name)
async def get_business_name(message: types.Message, state: FSMContext):
    await state.update_data(business_name=message.text.strip())
    await message.answer(
        "🏭 <b>Soha va faoliyat turi</b>\n\nMasalan: IT startap, Qishloq xo'jaligi, Restoran, Online do'kon...",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_industry.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_industry)
async def get_industry(message: types.Message, state: FSMContext):
    await state.update_data(industry=message.text.strip())
    await message.answer(
        "📝 <b>Biznesingizni qisqacha tasvirlab bering</b>\n\nNima sotasiz/xizmat ko'rsatasiz? Qanday muammoni hal qilasiz?",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_description.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_description)
async def get_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await message.answer(
        "💰 <b>Investitsiya hajmi</b>\n\nMasalan: 50,000,000 so'm, $10,000, 500 ming so'm...",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_investment.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_investment)
async def get_investment(message: types.Message, state: FSMContext):
    await state.update_data(investment=message.text.strip())
    await message.answer(
        "🎯 <b>Maqsadli bozor va auditoriya</b>\n\nKimlarga xizmat ko'rsatasiz? Qaysi hududda?",
        parse_mode='HTML',
        reply_markup=_cancel_keyboard()
    )
    await BiznesPlanUserStates.waiting_target_market.set()


@dp.message_handler(state=BiznesPlanUserStates.waiting_target_market)
async def get_target_market(message: types.Message, state: FSMContext):
    await state.update_data(target_market=message.text.strip())

    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("🇺🇿 O'zbek", callback_data="bp_lang:uz"),
        InlineKeyboardButton("🇷🇺 Rus", callback_data="bp_lang:ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="bp_lang:en"),
    )
    await message.answer(
        "🌐 <b>Biznes reja tilini tanlang:</b>",
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

    # Narx va balans
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

    # To'lov
    success = user_db.deduct_from_balance(telegram_id, price)
    if not success:
        await call.message.edit_text("❌ To'lovda xatolik!")
        return

    user_db.create_transaction(
        telegram_id=telegram_id,
        transaction_type='withdrawal',
        amount=price,
        description=f"AI Biznes Reja: {data.get('business_name', '')}",
        status='approved'
    )

    lang_names = {"uz": "O'zbek", "ru": "Rus", "en": "Ingliz"}
    status_msg = await call.message.edit_text(
        f"✅ <b>To'lov qabul qilindi! Generatsiya boshlandi...</b>\n\n"
        f"🏢 Biznes: {data.get('business_name', '')}\n"
        f"🏭 Soha: {data.get('industry', '')}\n"
        f"🌐 Til: {lang_names.get(language, 'Uzbek')}\n\n"
        f"⏳ <b>10-15 daqiqa vaqt ketadi</b>\n"
        f"<i>AI 10 bo'limni alohida yozadi — sifat uchun...</i>",
        parse_mode='HTML'
    )

    # Async generatsiya
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

        # Progress update
        try:
            await status_msg.edit_text(
                status_msg.text + "\n\n📊 <i>1/10: Ijroiya xulosa...</i>",
                parse_mode='HTML'
            )
        except Exception:
            pass

        content = await generator.generate(
            business_name=data.get('business_name', ''),
            industry=data.get('industry', ''),
            description=data.get('description', ''),
            investment=data.get('investment', ''),
            target_market=data.get('target_market', ''),
            language=language,
        )

        if not content:
            raise ValueError("Generator None qaytardi")

        # DOCX yaratish
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        safe_name = "".join(c for c in data.get('business_name', 'biznes') if c.isalnum() or c in ' _-')[:20].strip()
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
                f"🏢 <b>{data.get('business_name', '')}</b>\n"
                f"🏭 Soha: {data.get('industry', '')}\n\n"
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
