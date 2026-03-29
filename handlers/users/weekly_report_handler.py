"""
📋 HAFTALIK HISOBOT HANDLER
Web App dan ma'lumot qabul qiladi va DOCX yaratadi

Faylni handlers/users/ papkasiga joylashtiring
"""

import json
import os
import logging
from aiogram import types
from aiogram.types import ContentType

from loader import dp, bot, user_db
from data.config import OPENAI_API_KEY, ADMINS
from keyboards.default.default_keyboard import main_menu_keyboard

# Generator importlari
from utils.weekly_report_generator import WeeklyReportGenerator
from utils.weekly_report_docx import WeeklyReportDocx

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# SOZLAMALAR
# ═══════════════════════════════════════════════════════════════
WEB_APP_URL = "https://mahalla-hisobot-yoshlar.vercel.app/"  # <-- O'zgartiring
REPORT_PRICE = 5000  # Narxi (so'm)


# ═══════════════════════════════════════════════════════════════
# 1. TUGMA - HAFTALIK HISOBOT
# ═══════════════════════════════════════════════════════════════
@dp.message_handler(text="📋Xaftalik ish reja")
async def weekly_report_start(message: types.Message):
    """Haftalik hisobot tugmasi bosilganda"""
    telegram_id = message.from_user.id

    # Balansni tekshirish
    balance = user_db.get_user_balance(telegram_id)

    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(
        text="📱 Formani ochish",
        web_app=WebAppInfo(url=WEB_APP_URL)
    ))
    markup.add(KeyboardButton(text="⬅️ Bosh menyu"))

    text = f"""
📋 <b>HAFTALIK ISH REJASI</b>

Mahalla yoshlar yetakchilari uchun professional haftalik ish rejasi yaratish.

💰 <b>Narxi:</b> {REPORT_PRICE:,} so'm
💳 <b>Balansingiz:</b> {balance:,.0f} so'm

📝 <b>Jarayon:</b>
1. Formani to'ldiring (FIO, mahalla, vazifalar)
2. AI professional hujjat yaratadi
3. Tayyor DOCX fayl yuboriladi

👇 Boshlash uchun tugmani bosing:
"""

    await message.answer(text, reply_markup=markup, parse_mode='HTML')


# ═══════════════════════════════════════════════════════════════
# 2. WEB APP DATA HANDLER
# ═══════════════════════════════════════════════════════════════
@dp.message_handler(content_types=ContentType.WEB_APP_DATA)
async def web_app_data_handler(message: types.Message):
    """Web App dan kelgan ma'lumotni qayta ishlash"""
    telegram_id = message.from_user.id

    # 1. JSON ni o'qish
    try:
        raw_data = message.web_app_data.data
        data = json.loads(raw_data)

        # Faqat weekly_report turini qayta ishlash
        if data.get('type') != 'weekly_report':
            return

    except Exception as e:
        logger.error(f"Web App data xato: {e}")
        await message.answer(
            "❌ Ma'lumotni o'qishda xatolik yuz berdi.",
            reply_markup=main_menu_keyboard(telegram_id=message.from_user.id, user_db=user_db)
        )
        return

    # 2. Balansni tekshirish
    balance = user_db.get_user_balance(telegram_id)

    if balance < REPORT_PRICE:
        await message.answer(
            f"❌ <b>Balans yetarli emas!</b>\n\n"
            f"💰 Kerakli: {REPORT_PRICE:,} so'm\n"
            f"💳 Sizda: {balance:,.0f} so'm\n"
            f"❗ Yetishmayotgan: {(REPORT_PRICE - balance):,.0f} so'm\n\n"
            f"Balansni to'ldiring: 💳 To'ldirish",
            parse_mode='HTML',
            reply_markup=main_menu_keyboard(telegram_id=message.from_user.id, user_db=user_db)
        )
        return

    # 3. Ma'lumotlarni olish
    full_name = data.get('fullName', '')
    mahalla = data.get('mahalla', '')
    tuman = data.get('tuman', '')
    week_date = data.get('weekDate', '')
    tasks = data.get('tasks', {})

    # 4. Status xabar
    status_msg = await message.answer(
        f"✅ <b>Qabul qilindi!</b>\n\n"
        f"👤 {full_name}\n"
        f"🏘️ {mahalla}\n"
        f"📅 {week_date}\n\n"
        f"⏳ <b>AI hujjat yaratmoqda...</b>\n"
        f"<i>Iltimos kuting, 1-3 daqiqa vaqt ketadi.</i>",
        parse_mode='HTML'
    )

    try:
        # 5. Balansdan yechish
        success = user_db.deduct_from_balance(telegram_id, REPORT_PRICE)

        if not success:
            await status_msg.edit_text("❌ Balansdan yechishda xatolik!")
            return

        # Tranzaksiya yozish
        user_db.create_transaction(
            telegram_id=telegram_id,
            transaction_type='withdrawal',
            amount=REPORT_PRICE,
            description='Haftalik hisobot yaratish',
            status='approved'
        )

        # 6. AI GENERATOR - Content yaratish
        ai_generator = WeeklyReportGenerator(api_key=OPENAI_API_KEY)

        content = await ai_generator.generate_weekly_report(
            full_name=full_name,
            mahalla=mahalla,
            tuman=tuman,
            week_date=week_date,
            tasks=tasks
        )

        if not content:
            # Xatolik - pulni qaytarish
            user_db.add_to_balance(telegram_id, REPORT_PRICE)
            await status_msg.edit_text(
                "❌ AI generatsiya qila olmadi. Pul qaytarildi. Qaytadan urinib ko'ring."
            )
            await message.answer("🏠 Bosh menyu:", reply_markup=main_menu_keyboard(telegram_id=message.from_user.id, user_db=user_db))
            return

        # 7. Status yangilash
        try:
            await status_msg.edit_text("📄 <b>DOCX fayl shakllantirilmoqda...</b>", parse_mode='HTML')
        except:
            pass

        # 8. DOCX yaratish
        docx_generator = WeeklyReportDocx()

        # Fayl nomi
        safe_name = "".join([c for c in full_name if c.isalnum() or c in (' ', '-', '_')]).strip()[:15]
        filename = f"Haftalik_reja_{safe_name}_{telegram_id}.docx"

        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        file_path = f"downloads/{filename}"

        success = docx_generator.create_weekly_report(
            content=content,
            output_path=file_path,
            full_name=full_name,
            mahalla=mahalla,
            tuman=tuman,
            week_date=week_date
        )

        if not success:
            user_db.add_to_balance(telegram_id, REPORT_PRICE)
            await message.answer(
                "❌ Fayl yaratishda xatolik bo'ldi. Pul qaytarildi.",
                reply_markup=main_menu_keyboard(telegram_id=message.from_user.id, user_db=user_db)
            )
            return

        # 9. Faylni yuborish
        new_balance = user_db.get_user_balance(telegram_id)

        await message.answer_document(
            document=types.InputFile(file_path),
            caption=f"✅ <b>Haftalik ish rejasi tayyor!</b>\n\n"
                    f"👤 <b>Yetakchi:</b> {full_name}\n"
                    f"🏘️ <b>Mahalla:</b> {mahalla}\n"
                    f"📅 <b>Hafta:</b> {week_date}\n\n"
                    f"💰 Yechildi: {REPORT_PRICE:,} so'm\n"
                    f"💳 Qoldi: {new_balance:,.0f} so'm",
            parse_mode='HTML',
            reply_markup=main_menu_keyboard(telegram_id=message.from_user.id, user_db=user_db)
        )

        # 10. Tozalash
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Faylni o'chirishda xato: {e}")

        try:
            await status_msg.delete()
        except:
            pass

        logger.info(f"✅ Haftalik hisobot yaratildi: User {telegram_id}, {full_name}")

    except Exception as e:
        logger.error(f"Haftalik hisobot xato: {e}")

        # Pulni qaytarish
        try:
            user_db.add_to_balance(telegram_id, REPORT_PRICE)
        except:
            pass

        try:
            await status_msg.edit_text(
                "❌ Tizimda kutilmagan xatolik yuz berdi. Pul qaytarildi."
            )
        except:
            await message.answer(
                "❌ Tizimda kutilmagan xatolik yuz berdi. Pul qaytarildi."
            )

        await message.answer("🏠 Bosh menyu:", reply_markup=main_menu_keyboard(telegram_id=message.from_user.id, user_db=user_db))