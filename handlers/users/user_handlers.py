from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import json
import uuid

from loader import dp, bot, user_db
from keyboards.default.user_keyboards import (
    main_menu_keyboard,
    cancel_keyboard,
    confirm_keyboard
)
from data.config import ADMINS

logger = logging.getLogger(__name__)


# ==================== FSM STATES ====================
class PitchDeckStates(StatesGroup):
    waiting_for_answer = State()
    confirming_creation = State()


class PresentationStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_details = State()
    waiting_for_slide_count = State()
    confirming_creation = State()


class BalanceStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_receipt = State()


# ==================== SAVOLLAR ====================
PITCH_QUESTIONS = [
    "1️⃣ Ismingiz va lavozimingiz?",
    "2️⃣ Loyiha/Startup nomi?",
    "3️⃣ Loyiha tavsifi (qisqacha, 2-3 jumla)?",
    "4️⃣ Qanday muammoni hal qilasiz?",
    "5️⃣ Sizning yechimingiz?",
    "6️⃣ Maqsadli auditoriya kimlar?",
    "7️⃣ Biznes model (qanday daromad olasiz)?",
    "8️⃣ Asosiy raqobatchilaringiz?",
    "9️⃣ Sizning ustunligingiz (raqobatchilardan farqi)?",
    "🔟 Moliyaviy prognoz (keyingi 1 yil)?",
]


# ==================== ADMIN NOTIFICATION ====================
async def send_admin_notification(trans_id: int, user_id: int, amount: float, file_id: str, user_name: str):
    """Admin'larga tranzaksiya haqida xabar yuborish"""
    try:
        # ✅ TO'G'IRLANGAN: admin_panel.py bilan bir xil format (IKKI NUQTA)
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_trans:{trans_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_trans:{trans_id}")
        )

        user_info = f"""
🔔 <b>YANGI TRANZAKSIYA</b>

👤 <b>User:</b> {user_name}
🆔 <b>User ID:</b> <code>{user_id}</code>
💰 <b>Summa:</b> {amount:,.0f} so'm
🆔 <b>Tranzaksiya ID:</b> {trans_id}

📸 Chek quyida 👇
"""

        for admin_id in ADMINS:
            try:
                await bot.send_message(admin_id, user_info, reply_markup=keyboard, parse_mode='HTML')

                try:
                    await bot.send_photo(admin_id, file_id)
                except:
                    await bot.send_document(admin_id, file_id)

                logger.info(f"✅ Admin notification yuborildi: Admin {admin_id}, Trans {trans_id}")

            except Exception as e:
                logger.error(f"❌ Admin {admin_id} ga xabar yuborishda xato: {e}")

    except Exception as e:
        logger.error(f"💥 Admin notification xatosi: {e}")


# ==================== START ====================
@dp.message_handler(commands=['start'], state='*')
async def start_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.finish()

    user = message.from_user
    telegram_id = user.id
    username = user.username or "username_yoq"

    try:
        if not user_db.user_exists(telegram_id):
            user_db.add_user(telegram_id, username)
            logger.info(f"✅ Yangi user qo'shildi: {telegram_id}")

        balance = user_db.get_user_balance(telegram_id)

        welcome_text = f"""
👋 <b>Assalomu alaykum, {user.first_name}!</b>

🎨 <b>Men professional prezentatsiyalar yaratadigam bot!</b>

💰 <b>Sizning balansingiz:</b> {balance:,.0f} so'm

<b>📋 Xizmatlarimiz:</b>

🎯 <b>Pitch Deck</b> - Startup uchun to'liq pitch prezentatsiya
   • 10 ta savol
   • Professional AI content
   • Bozor tahlili
   • Moliyaviy prognozlar

📊 <b>Oddiy Prezentatsiya</b> - Istalgan mavzu bo'yicha
   • Tez va oddiy
   • Mavzu kiriting
   • Professional dizayn

Pastdagi tugmalardan birini tanlang! 👇
"""

        await message.answer(welcome_text, reply_markup=main_menu_keyboard(), parse_mode='HTML')

    except Exception as e:
        logger.error(f"❌ Start handler xato: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")


# ==================== PITCH DECK ====================
@dp.message_handler(Text(equals="🎯 Pitch Deck yaratish"), state='*')
async def pitch_deck_start(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id

    try:
        price = user_db.get_price('pitch_deck')
        if not price:
            price = 1500

        balance = user_db.get_user_balance(telegram_id)

        info_text = f"""
🎯 <b>PITCH DECK YARATISH</b>

📝 <b>Jarayon:</b>
1. 10 ta savolga javob bering
2. Professional AI content yaratadi
3. Zamonaviy dizayn qilinadi
4. Tayyor PPTX sizga yuboriladi

💰 <b>Narx:</b> {price:,.0f} so'm har bir varoq
💳 <b>Sizning balansingiz:</b> {balance:,.0f} so'm
"""

        if balance < price:
            info_text += f"""
❌ <b>Balans yetarli emas!</b>

Kerakli: {price:,.0f} so'm
Sizda: {balance:,.0f} so'm
Yetishmayotgan: {(price - balance):,.0f} so'm

Avval balansni to'ldiring: 💳 Balans to'ldirish
"""
            await message.answer(info_text, parse_mode='HTML')
            return

        info_text += "\n✅ Balans yetarli!\n\nBoshlaysizmi?"

        await message.answer(info_text, reply_markup=confirm_keyboard(), parse_mode='HTML')
        await state.update_data(service_type='pitch_deck', price=price)
        await PitchDeckStates.confirming_creation.set()

    except Exception as e:
        logger.error(f"❌ Pitch deck start xato: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")


@dp.message_handler(Text(equals="✅ Ha, boshlash"), state=PitchDeckStates.confirming_creation)
async def pitch_deck_confirm(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    try:
        if 'answers' not in user_data or not user_data.get('answers'):
            await state.update_data(current_question=0, answers=[])

            text = f"""
📝 <b>Ajoyib! Boshlaylik!</b>

Har bir savolga <b>BATAFSIL</b> javob bering.
Qancha ko'p ma'lumot bersangiz, shuncha yaxshi natija!

{PITCH_QUESTIONS[0]}
"""

            await message.answer(text, reply_markup=cancel_keyboard(), parse_mode='HTML')
            await PitchDeckStates.waiting_for_answer.set()

        else:
            telegram_id = message.from_user.id
            answers = user_data.get('answers', [])
            price = user_data.get('price', 50000)

            current_balance = user_db.get_user_balance(telegram_id)
            logger.info(f"📊 Pitch Deck: User {telegram_id}, Balans: {current_balance}, Narx: {price}")

            if current_balance < price:
                await message.answer(
                    f"❌ <b>Balans yetarli emas!</b>\n\n"
                    f"Kerakli: {price:,.0f} so'm\n"
                    f"Sizda: {current_balance:,.0f} so'm\n\n"
                    f"Balansni to'ldiring: 💳 Balans to'ldirish",
                    parse_mode='HTML',
                    reply_markup=main_menu_keyboard()
                )
                await state.finish()
                return

            success = user_db.deduct_from_balance(telegram_id, price)
            logger.info(f"💰 Balansdan yechish natijasi: {success}")

            if not success:
                await message.answer(
                    "❌ <b>Balansdan yechishda xatolik!</b>\n\nBalansni tekshiring: 💰 Balansim",
                    parse_mode='HTML',
                    reply_markup=main_menu_keyboard()
                )
                await state.finish()
                return

            new_balance = user_db.get_user_balance(telegram_id)
            logger.info(f"✅ Yangi balans: {new_balance}")

            user_db.create_transaction(
                telegram_id=telegram_id,
                transaction_type='withdrawal',
                amount=price,
                description='Pitch Deck yaratish',
                status='approved'
            )

            task_uuid = str(uuid.uuid4())
            content_data = {'answers': answers, 'questions': PITCH_QUESTIONS}

            task_id = user_db.create_presentation_task(
                telegram_id=telegram_id,
                task_uuid=task_uuid,
                presentation_type='pitch_deck',
                slide_count=12,
                answers=json.dumps(content_data, ensure_ascii=False),
                amount_charged=price
            )

            if not task_id:
                user_db.add_to_balance(telegram_id, price)
                await message.answer("❌ Task yaratishda xatolik!", parse_mode='HTML')
                await state.finish()
                return

            success_text = f"""
✅ <b>Pitch Deck yaratish boshlandi!</b>

💰 Balansdan yechildi: {price:,.0f} so'm
💳 Yangi balans: {new_balance:,.0f} so'm

⏳ <b>Jarayon:</b>
1. ⚙️ Content yaratilmoqda...
2. 🎨 Dizayn qilinmoqda...
3. 📊 Formatlash...
4. ✅ Tayyor!

⏱️ Taxminan <b>3-7 daqiqa</b> vaqt ketadi.

Tayyor bo'lgach sizga <b>professional PPTX fayl</b> yuboriladi! 🎉
"""

            await message.answer(success_text, reply_markup=main_menu_keyboard(), parse_mode='HTML')
            await state.finish()

            logger.info(f"✅ Pitch Deck task yaratildi: {task_uuid} | User: {telegram_id}")

    except Exception as e:
        logger.error(f"❌ Pitch deck confirm xato: {e}")
        await message.answer("❌ <b>Xatolik yuz berdi!</b>", parse_mode='HTML')
        await state.finish()


@dp.message_handler(state=PitchDeckStates.waiting_for_answer)
async def pitch_deck_answer(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    current_q = user_data.get('current_question', 0)
    answers = user_data.get('answers', [])

    answers.append(message.text.strip())
    next_q = current_q + 1

    if next_q < len(PITCH_QUESTIONS):
        await state.update_data(current_question=next_q, answers=answers)
        progress = f"✅ {next_q}/{len(PITCH_QUESTIONS)} savol javoblandi\n\n"
        await message.answer(progress + PITCH_QUESTIONS[next_q], reply_markup=cancel_keyboard(), parse_mode='HTML')
    else:
        await state.update_data(answers=answers)
        price = user_data.get('price', 50000)
        balance = user_db.get_user_balance(message.from_user.id)

        summary = f"""
🎉 <b>Barcha savollar tugadi!</b>

📊 Jami {len(answers)} ta javob qabul qilindi

💰 <b>To'lov ma'lumotlari:</b>
Narx: {price:,.0f} so'm
Balansingiz: {balance:,.0f} so'm
Qoladi: {(balance - price):,.0f} so'm

✅ Pitch Deck yaratishni boshlaymizmi?
"""

        await message.answer(summary, reply_markup=confirm_keyboard(), parse_mode='HTML')
        await PitchDeckStates.confirming_creation.set()


# ==================== ODDIY PREZENTATSIYA ====================
@dp.message_handler(Text(equals="📊 Prezentatsiya yaratish"), state='*')
async def presentation_start(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id

    try:
        price_per_slide = user_db.get_price('slide_basic')
        if not price_per_slide:
            price_per_slide = 2000.0

        balance = user_db.get_user_balance(telegram_id)

        info_text = f"""
📊 <b>PREZENTATSIYA YARATISH</b>

📝 <b>Jarayon:</b>
1. Mavzu kiriting
2. Qo'shimcha ma'lumotlar (ixtiyoriy)
3. Slaydlar sonini tanlang
4. Professional AI prezentatsiya yaratadi

💰 <b>Narx:</b> {price_per_slide:,.0f} so'm / slayd
💳 <b>Balansingiz:</b> {balance:,.0f} so'm

<b>Masalan:</b>
- 5 slayd = {(price_per_slide * 5):,.0f} so'm
- 10 slayd = {(price_per_slide * 10):,.0f} so'm
- 15 slayd = {(price_per_slide * 15):,.0f} so'm

✍️ Prezentatsiya mavzusini kiriting:
"""

        await message.answer(info_text, reply_markup=cancel_keyboard(), parse_mode='HTML')
        await state.update_data(price_per_slide=price_per_slide)
        await PresentationStates.waiting_for_topic.set()

    except Exception as e:
        logger.error(f"❌ Presentation start xato: {e}")
        await message.answer("❌ Xatolik yuz berdi.")


@dp.message_handler(state=PresentationStates.waiting_for_topic)
async def presentation_topic(message: types.Message, state: FSMContext):
    topic = message.text.strip()
    await state.update_data(topic=topic)

    text = f"""
✅ Mavzu qabul qilindi: <b>{topic}</b>

📝 Endi qo'shimcha ma'lumotlar kiriting:

- Asosiy nuqtalar
- Qamrab olish kerak bo'lgan mavzular
- Maqsadli auditoriya
- Maxsus talablar

Yoki "o'tkazib yuborish" yozing.
"""

    await message.answer(text, reply_markup=cancel_keyboard(), parse_mode='HTML')
    await PresentationStates.waiting_for_details.set()


@dp.message_handler(state=PresentationStates.waiting_for_details)
async def presentation_details(message: types.Message, state: FSMContext):
    details = message.text.strip()

    if details.lower() in ['o\'tkazib yuborish', 'otkazib yuborish', 'skip', 'yo\'q', 'yoq']:
        details = "Qo'shimcha ma'lumot yo'q"

    await state.update_data(details=details)

    text = """
🔢 <b>Slaydlar sonini kiriting:</b>

Minimal: 5 slayd
Maksimal: 20 slayd

Masalan: 10
"""

    await message.answer(text, reply_markup=cancel_keyboard(), parse_mode='HTML')
    await PresentationStates.waiting_for_slide_count.set()


@dp.message_handler(state=PresentationStates.waiting_for_slide_count)
async def presentation_slide_count(message: types.Message, state: FSMContext):
    try:
        slide_count = int(message.text.strip())

        if slide_count < 5 or slide_count > 20:
            await message.answer("❌ Slaydlar soni 5 dan 20 gacha bo'lishi kerak!")
            return

        user_data = await state.get_data()
        price_per_slide = user_data.get('price_per_slide', 2000)
        total_price = price_per_slide * slide_count

        balance = user_db.get_user_balance(message.from_user.id)
        topic = user_data.get('topic', '')
        details = user_data.get('details', '')

        await state.update_data(slide_count=slide_count, total_price=total_price)

        summary = f"""
📊 <b>PREZENTATSIYA YARATISH</b>

<b>Mavzu:</b> {topic}
<b>Qo'shimcha:</b> {details[:50]}...
<b>Slaydlar:</b> {slide_count} ta

💰 <b>To'lov:</b>
Narx: {total_price:,.0f} so'm
Balansingiz: {balance:,.0f} so'm
"""

        if balance < total_price:
            summary += f"""
❌ <b>Balans yetarli emas!</b>

Kerakli: {total_price:,.0f} so'm
Yetishmayotgan: {(total_price - balance):,.0f} so'm

Balansni to'ldiring: 💳 Balans to'ldirish
"""
            await message.answer(summary, parse_mode='HTML')
            await state.finish()
            return

        summary += f"""
Qoladi: {(balance - total_price):,.0f} so'm

✅ Prezentatsiya yaratishni boshlaymizmi?
"""

        await message.answer(summary, reply_markup=confirm_keyboard(), parse_mode='HTML')
        await PresentationStates.confirming_creation.set()

    except ValueError:
        await message.answer("❌ Iltimos, faqat raqam kiriting!")


@dp.message_handler(Text(equals="✅ Ha, boshlash"), state=PresentationStates.confirming_creation)
async def presentation_confirm(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    user_data = await state.get_data()

    topic = user_data.get('topic')
    details = user_data.get('details')
    slide_count = user_data.get('slide_count')
    total_price = user_data.get('total_price')

    try:
        current_balance = user_db.get_user_balance(telegram_id)

        if current_balance < total_price:
            await message.answer(
                f"❌ <b>Balans yetarli emas!</b>\n\n"
                f"Kerakli: {total_price:,.0f} so'm\n"
                f"Sizda: {current_balance:,.0f} so'm",
                parse_mode='HTML',
                reply_markup=main_menu_keyboard()
            )
            await state.finish()
            return

        success = user_db.deduct_from_balance(telegram_id, total_price)

        if not success:
            await message.answer("❌ <b>Balansdan yechishda xatolik!</b>", parse_mode='HTML', reply_markup=main_menu_keyboard())
            await state.finish()
            return

        new_balance = user_db.get_user_balance(telegram_id)

        user_db.create_transaction(
            telegram_id=telegram_id,
            transaction_type='withdrawal',
            amount=total_price,
            description=f'Prezentatsiya yaratish ({slide_count} slayd)',
            status='approved'
        )

        task_uuid = str(uuid.uuid4())
        content_data = {'topic': topic, 'details': details, 'slide_count': slide_count}

        task_id = user_db.create_presentation_task(
            telegram_id=telegram_id,
            task_uuid=task_uuid,
            presentation_type='basic',
            slide_count=slide_count,
            answers=json.dumps(content_data, ensure_ascii=False),
            amount_charged=total_price
        )

        if not task_id:
            user_db.add_to_balance(telegram_id, total_price)
            await message.answer("❌ Task yaratishda xatolik!", parse_mode='HTML')
            await state.finish()
            return

        success_text = f"""
✅ <b>Prezentatsiya yaratish boshlandi!</b>

💰 Balansdan yechildi: {total_price:,.0f} so'm
💳 Yangi balans: {new_balance:,.0f} so'm

⏳ <b>Jarayon:</b>
1. ⚙️ Content tayyorlanmoqda...
2. 🎨 Professional dizayn qilinmoqda...
3. 📊 Slaydlar yaratilyapti...
4. ✅ Tayyor!

⏱️ Taxminan <b>3-7 daqiqa</b> vaqt ketadi.

Tayyor bo'lgach sizga <b>PPTX fayl</b> yuboriladi! 🎉
"""

        await message.answer(success_text, reply_markup=main_menu_keyboard(), parse_mode='HTML')
        await state.finish()

    except Exception as e:
        logger.error(f"❌ Prezentatsiya yaratishda xato: {e}")
        await message.answer("❌ <b>Xatolik yuz berdi!</b>", parse_mode='HTML')
        await state.finish()


# ==================== BALANS ====================
@dp.message_handler(Text(equals="💰 Balansim"), state='*')
async def balance_info(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id

    try:
        stats = user_db.get_user_stats(telegram_id)

        if not stats:
            await message.answer("❌ Ma'lumot topilmadi!")
            return

        transactions = user_db.get_user_transactions(telegram_id, limit=5)

        info_text = f"""
💰 <b>BALANSINGIZ</b>

💳 Hozirgi balans: <b>{stats['balance']:,.0f} so'm</b>

📊 <b>Statistika:</b>
📈 Jami to'ldirilgan: {stats['total_deposited']:,.0f} so'm
📉 Jami sarflangan: {stats['total_spent']:,.0f} so'm
📅 A'zo bo'lganingizga: {stats['member_since'][:10]}

💳 <b>Oxirgi tranzaksiyalar:</b>
"""

        if transactions:
            for trans in transactions:
                type_emoji = {'deposit': '➕', 'withdrawal': '➖', 'refund': '↩️'}.get(trans['type'], '❓')
                status_emoji = {'pending': '⏳', 'approved': '✅', 'rejected': '❌'}.get(trans['status'], '❓')
                info_text += f"\n{type_emoji} {trans['amount']:,.0f} so'm - {status_emoji} {trans['status']}"
        else:
            info_text += "\nTranzaksiyalar yo'q"

        await message.answer(info_text, parse_mode='HTML')

    except Exception as e:
        logger.error(f"❌ Balans info xato: {e}")
        await message.answer("❌ Ma'lumotlarni olishda xatolik yuz berdi.")


@dp.message_handler(Text(equals="💳 Balans to'ldirish"), state='*')
async def balance_topup_start(message: types.Message, state: FSMContext):
    text = """
💳 <b>BALANS TO'LDIRISH</b>

✍️ Qancha summa to'ldirmoqchisiz?

Minimal: 10,000 so'm
Maksimal: 10,000,000 so'm

Masalan: 50000
"""

    await message.answer(text, reply_markup=cancel_keyboard(), parse_mode='HTML')
    await BalanceStates.waiting_for_amount.set()


@dp.message_handler(state=BalanceStates.waiting_for_amount)
async def balance_topup_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(',', '').replace(' ', ''))

        if amount < 10000:
            await message.answer("❌ Minimal summa: 10,000 so'm")
            return

        if amount > 10000000:
            await message.answer("❌ Maksimal summa: 10,000,000 so'm")
            return

        await state.update_data(amount=amount)

        CARD_NUMBER = "4916990312518431"
        CARD_HOLDER = "Boburjon Astanov"

        payment_text = f"""
💳 <b>TO'LOV MA'LUMOTLARI</b>

💰 Summa: <b>{amount:,.0f} so'm</b>

📇 <b>Karta raqami:</b>
<code>{CARD_NUMBER}</code>

👤 <b>Karta egasi:</b>
{CARD_HOLDER}

📸 <b>To'lov qilgandan keyin:</b>
Chek (skrinshot yoki PDF) ni bu chatga yuboring

⏳ Admin 5-30 daqiqada tasdiqlaydi
"""

        await message.answer(payment_text, reply_markup=cancel_keyboard(), parse_mode='HTML')
        await BalanceStates.waiting_for_receipt.set()

    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri summa kiriting!")


@dp.message_handler(content_types=['photo', 'document'], state=BalanceStates.waiting_for_receipt)
async def balance_topup_receipt(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    user_data = await state.get_data()
    amount = user_data.get('amount')

    try:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        else:
            file_id = message.document.file_id

        logger.info(f"📥 Chek qabul qilindi: User {telegram_id}, Amount {amount}")

        # ✅ TO'G'IRLANGAN: Tranzaksiya yaratish
        trans_id = user_db.create_transaction(
            telegram_id=telegram_id,
            transaction_type='deposit',
            amount=amount,
            description='Balans to\'ldirish',
            receipt_file_id=file_id,
            status='pending'
        )

        logger.info(f"📝 Tranzaksiya yaratildi: ID={trans_id}")

        # ✅ Agar trans_id None bo'lsa, xatolik
        if not trans_id:
            await message.answer("❌ Tranzaksiya yaratishda xatolik! Qaytadan urinib ko'ring.", parse_mode='HTML')
            await state.finish()
            return

        success_text = f"""
✅ <b>Chek qabul qilindi!</b>

💰 Summa: {amount:,.0f} so'm
🆔 Tranzaksiya ID: {trans_id}

⏳ Admin 5-30 daqiqada tasdiqlaydi

Tasdiqlangach balansingizga avtomatik qo'shiladi! 💳
"""

        await message.answer(success_text, reply_markup=main_menu_keyboard(), parse_mode='HTML')

        # Admin'larga notification yuborish
        user_name = message.from_user.full_name
        await send_admin_notification(trans_id, telegram_id, amount, file_id, user_name)

        logger.info(f"✅ Balans to'ldirish so'rovi yaratildi: ID {trans_id}, User {telegram_id}, Amount {amount}")

        await state.finish()

    except Exception as e:
        logger.error(f"❌ Balance receipt xato: {e}")
        await message.answer("❌ <b>Xatolik yuz berdi!</b>", parse_mode='HTML')
        await state.finish()


# ==================== CANCEL ====================
@dp.message_handler(Text(equals="❌ Bekor qilish"), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state:
        await state.finish()
        await message.answer("❌ Jarayon bekor qilindi", reply_markup=main_menu_keyboard())
    else:
        await message.answer("Hozir hech narsa bajarilmayapti", reply_markup=main_menu_keyboard())


@dp.message_handler(Text(equals="❌ Yo'q"), state='*')
async def no_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Bekor qilindi", reply_markup=main_menu_keyboard())


# ==================== NARXLAR ====================
@dp.message_handler(Text(equals="💵 Narxlar"), state='*')
async def prices_handler(message: types.Message):
    try:
        prices = user_db.get_all_prices()

        price_text = "💵 <b>XIZMATLAR NARXLARI</b>\n\n"

        for price in prices:
            if price['is_active']:
                price_text += f"<b>{price['description']}</b>\n💰 {price['price']:,.0f} {price['currency']}\n━━━━━━━━━━━━━━━\n"

        await message.answer(price_text, parse_mode='HTML')

    except Exception as e:
        logger.error(f"❌ Prices handler xato: {e}")
        await message.answer("❌ Narxlarni olishda xatolik yuz berdi.")


# ==================== YORDAM ====================
@dp.message_handler(Text(equals="ℹ️ Yordam"), state='*')
async def help_handler(message: types.Message):
    help_text = """
ℹ️ <b>YORDAM</b>

<b>📋 Buyruqlar:</b>
/start - Boshlash
/help - Yordam

<b>🎯 Pitch Deck:</b>
1. "Pitch Deck yaratish" tugmasini bosing
2. 10 ta savolga javob bering
3. Tasdiqlang
4. 3-7 daqiqada tayyor!

<b>📊 Prezentatsiya:</b>
1. "Prezentatsiya yaratish" tugmasini bosing
2. Mavzu kiriting
3. Slaydlar sonini tanlang
4. Tasdiqlang
5. 3-7 daqiqada tayyor!

<b>💳 Balans to'ldirish:</b>
1. Summani kiriting
2. Kartaga o'tkazing
3. Chek yuboring
4. Admin tasdiqlaydi (5-30 daqiqa)

<b>🤖 Professional AI:</b>
- AI content yaratadi
- Professional dizayn
- PPTX format

❓ Savol: @sam_ecobench
"""

    await message.answer(help_text, parse_mode='HTML')