
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

from loader import dp, bot, user_db
from data.config import ADMINS

logger = logging.getLogger(__name__)


# ==================== FSM STATES ====================
class AdminFreeStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_count = State()
    waiting_for_bulk_count = State()


# ==================== ADMIN TEKSHIRISH ====================
def is_admin(telegram_id: int) -> bool:
    """Admin ekanligini tekshirish"""
    return telegram_id in ADMINS


# ==================== BEPUL PREZENTATSIYA MENU ====================
def free_presentations_menu_keyboard() -> InlineKeyboardMarkup:
    """Bepul prezentatsiya boshqaruv menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("👤 User'ga berish", callback_data="admin_free_give_user"),
        InlineKeyboardButton("👥 Barchaga berish", callback_data="admin_free_give_all"),
        InlineKeyboardButton("🔍 User tekshirish", callback_data="admin_free_check_user"),
        InlineKeyboardButton("📊 Statistika", callback_data="admin_free_stats"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin_main_menu")
    )
    return keyboard


@dp.message_handler(Text(equals="🎁 Bepul prezentatsiya"), state='*')
async def admin_free_menu(message: types.Message, state: FSMContext):
    """Bepul prezentatsiya boshqaruv menyusi"""
    if not is_admin(message.from_user.id):
        return

    await state.finish()

    text = """
🎁 <b>BEPUL PREZENTATSIYA BOSHQARUVI</b>

Quyidagi amallarni bajarishingiz mumkin:

👤 <b>User'ga berish</b> - Bitta user'ga bepul prezentatsiya berish
👥 <b>Barchaga berish</b> - Barcha user'larga bepul prezentatsiya berish
🔍 <b>User tekshirish</b> - User'ning bepul qoldig'ini ko'rish
📊 <b>Statistika</b> - Umumiy statistika

Tanlang:
"""

    await message.answer(text, reply_markup=free_presentations_menu_keyboard(), parse_mode='HTML')


# ==================== USER'GA BERISH ====================
@dp.callback_query_handler(lambda c: c.data == "admin_free_give_user", state='*')
async def admin_free_give_user_start(callback: types.CallbackQuery, state: FSMContext):
    """User'ga bepul prezentatsiya berish - boshlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda ruxsat yo'q!", show_alert=True)
        return

    await callback.message.edit_text(
        "👤 <b>USER'GA BEPUL PREZENTATSIYA BERISH</b>\n\n"
        "User'ning Telegram ID sini kiriting:\n\n"
        "<i>Masalan: 1879114908</i>\n\n"
        "❌ Bekor qilish uchun /cancel",
        parse_mode='HTML'
    )

    await AdminFreeStates.waiting_for_user_id.set()
    await callback.answer()


@dp.message_handler(state=AdminFreeStates.waiting_for_user_id)
async def admin_free_user_id_received(message: types.Message, state: FSMContext):
    """User ID qabul qilish"""
    if not is_admin(message.from_user.id):
        return

    try:
        telegram_id = int(message.text.strip())

        # User mavjudligini tekshirish
        if not user_db.user_exists(telegram_id):
            await message.answer(
                f"❌ User topilmadi: <code>{telegram_id}</code>\n\n"
                "Qaytadan kiriting yoki /cancel",
                parse_mode='HTML'
            )
            return

        # User ma'lumotlarini olish
        current_free = user_db.get_free_presentations(telegram_id)
        balance = user_db.get_user_balance(telegram_id)

        await state.update_data(target_user_id=telegram_id, current_free=current_free)

        # Tez tugmalar
        keyboard = InlineKeyboardMarkup(row_width=3)
        keyboard.add(
            InlineKeyboardButton("1️⃣", callback_data="admin_free_set:1"),
            InlineKeyboardButton("2️⃣", callback_data="admin_free_set:2"),
            InlineKeyboardButton("3️⃣", callback_data="admin_free_set:3"),
        )
        keyboard.add(
            InlineKeyboardButton("5️⃣", callback_data="admin_free_set:5"),
            InlineKeyboardButton("🔟", callback_data="admin_free_set:10"),
            InlineKeyboardButton("➕ Boshqa", callback_data="admin_free_custom"),
        )
        keyboard.add(
            InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_free_cancel")
        )

        await message.answer(
            f"👤 <b>USER TOPILDI</b>\n\n"
            f"🆔 Telegram ID: <code>{telegram_id}</code>\n"
            f"🎁 Hozirgi bepul: <b>{current_free}</b> ta\n"
            f"💰 Balans: <b>{balance:,.0f}</b> so'm\n\n"
            f"Nechta bepul prezentatsiya <b>QO'SHMOQCHISIZ</b>?\n\n"
            f"<i>Bu hozirgi songa qo'shiladi</i>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    except ValueError:
        await message.answer(
            "❌ Noto'g'ri format! Faqat raqam kiriting.\n\n"
            "Qaytadan kiriting yoki /cancel",
            parse_mode='HTML'
        )


@dp.callback_query_handler(lambda c: c.data.startswith("admin_free_set:"), state=AdminFreeStates.waiting_for_user_id)
async def admin_free_set_quick(callback: types.CallbackQuery, state: FSMContext):
    """Tez tugma bilan son tanlash"""
    if not is_admin(callback.from_user.id):
        return

    count = int(callback.data.split(":")[1])
    user_data = await state.get_data()
    telegram_id = user_data.get('target_user_id')
    current_free = user_data.get('current_free', 0)

    # Bepul qo'shish
    success = user_db.add_free_presentations(telegram_id, count)

    if success:
        new_free = user_db.get_free_presentations(telegram_id)

        await callback.message.edit_text(
            f"✅ <b>MUVAFFAQIYATLI!</b>\n\n"
            f"🆔 User: <code>{telegram_id}</code>\n"
            f"➕ Qo'shildi: <b>{count}</b> ta\n"
            f"📊 Eski: {current_free} ta → Yangi: <b>{new_free}</b> ta\n\n"
            f"🎁 User'ga xabar yuborilsinmi?",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("✅ Ha, yuborish", callback_data=f"admin_free_notify:{telegram_id}:{count}"),
                InlineKeyboardButton("❌ Yo'q", callback_data="admin_free_menu")
            ),
            parse_mode='HTML'
        )

        logger.info(f"✅ Admin {callback.from_user.id} -> User {telegram_id} ga {count} ta bepul prezentatsiya berdi")
    else:
        await callback.message.edit_text(
            "❌ Xatolik yuz berdi! Qaytadan urinib ko'ring.",
            reply_markup=free_presentations_menu_keyboard()
        )

    await state.finish()
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_free_custom", state=AdminFreeStates.waiting_for_user_id)
async def admin_free_custom_count(callback: types.CallbackQuery, state: FSMContext):
    """Maxsus son kiritish"""
    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "🔢 <b>MAXSUS SON</b>\n\n"
        "Nechta bepul prezentatsiya qo'shmoqchisiz?\n\n"
        "<i>Faqat raqam kiriting (1-100)</i>",
        parse_mode='HTML'
    )

    await AdminFreeStates.waiting_for_count.set()
    await callback.answer()


@dp.message_handler(state=AdminFreeStates.waiting_for_count)
async def admin_free_count_received(message: types.Message, state: FSMContext):
    """Maxsus son qabul qilish"""
    if not is_admin(message.from_user.id):
        return

    try:
        count = int(message.text.strip())

        if count < 1 or count > 100:
            await message.answer("❌ Son 1 dan 100 gacha bo'lishi kerak!")
            return

        user_data = await state.get_data()
        telegram_id = user_data.get('target_user_id')
        current_free = user_data.get('current_free', 0)

        # Bepul qo'shish
        success = user_db.add_free_presentations(telegram_id, count)

        if success:
            new_free = user_db.get_free_presentations(telegram_id)

            await message.answer(
                f"✅ <b>MUVAFFAQIYATLI!</b>\n\n"
                f"🆔 User: <code>{telegram_id}</code>\n"
                f"➕ Qo'shildi: <b>{count}</b> ta\n"
                f"📊 Eski: {current_free} ta → Yangi: <b>{new_free}</b> ta",
                reply_markup=free_presentations_menu_keyboard(),
                parse_mode='HTML'
            )

            logger.info(f"✅ Admin {message.from_user.id} -> User {telegram_id} ga {count} ta bepul prezentatsiya berdi")
        else:
            await message.answer("❌ Xatolik yuz berdi!", reply_markup=free_presentations_menu_keyboard())

        await state.finish()

    except ValueError:
        await message.answer("❌ Faqat raqam kiriting!")


# ==================== BARCHAGA BERISH ====================
@dp.callback_query_handler(lambda c: c.data == "admin_free_give_all", state='*')
async def admin_free_give_all_start(callback: types.CallbackQuery, state: FSMContext):
    """Barcha user'larga bepul prezentatsiya berish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda ruxsat yo'q!", show_alert=True)
        return

    # User'lar sonini olish
    total_users = user_db.count_users()

    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("1️⃣", callback_data="admin_free_all:1"),
        InlineKeyboardButton("2️⃣", callback_data="admin_free_all:2"),
        InlineKeyboardButton("3️⃣", callback_data="admin_free_all:3"),
    )
    keyboard.add(
        InlineKeyboardButton("5️⃣", callback_data="admin_free_all:5"),
        InlineKeyboardButton("🔢 Boshqa", callback_data="admin_free_all_custom"),
    )
    keyboard.add(
        InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_free_menu")
    )

    await callback.message.edit_text(
        f"👥 <b>BARCHAGA BEPUL PREZENTATSIYA</b>\n\n"
        f"📊 Jami user'lar: <b>{total_users}</b> ta\n\n"
        f"Har bir user'ga nechta bepul prezentatsiya <b>QO'SHMOQCHISIZ</b>?\n\n"
        f"⚠️ <i>Bu amal barcha user'larga ta'sir qiladi!</i>",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("admin_free_all:"), state='*')
async def admin_free_all_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Barchaga berish - tasdiqlash"""
    if not is_admin(callback.from_user.id):
        return

    count = int(callback.data.split(":")[1])
    total_users = user_db.count_users()

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha, barchaga berish", callback_data=f"admin_free_all_exec:{count}"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_free_menu")
    )

    await callback.message.edit_text(
        f"⚠️ <b>TASDIQLASH</b>\n\n"
        f"📊 Jami: <b>{total_users}</b> ta user\n"
        f"🎁 Har biriga: <b>{count}</b> ta bepul prezentatsiya\n\n"
        f"Davom etasizmi?",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("admin_free_all_exec:"), state='*')
async def admin_free_all_execute(callback: types.CallbackQuery, state: FSMContext):
    """Barchaga berish - bajarish"""
    if not is_admin(callback.from_user.id):
        return

    count = int(callback.data.split(":")[1])

    await callback.message.edit_text("⏳ <b>Bajarilmoqda...</b>", parse_mode='HTML')

    try:
        # Barcha user'larga qo'shish
        result = user_db.execute(
            "UPDATE Users SET free_presentations = COALESCE(free_presentations, 0) + ?",
            parameters=(count,),
            commit=True
        )

        total_users = user_db.count_users()

        await callback.message.edit_text(
            f"✅ <b>MUVAFFAQIYATLI!</b>\n\n"
            f"📊 Yangilangan: <b>{total_users}</b> ta user\n"
            f"🎁 Har biriga qo'shildi: <b>{count}</b> ta\n\n"
            f"Jami berildi: <b>{total_users * count}</b> ta bepul prezentatsiya",
            reply_markup=free_presentations_menu_keyboard(),
            parse_mode='HTML'
        )

        logger.info(f"✅ Admin {callback.from_user.id} barcha user'larga {count} ta bepul prezentatsiya berdi")

    except Exception as e:
        logger.error(f"❌ Bulk free presentations xato: {e}")
        await callback.message.edit_text(
            f"❌ <b>Xatolik!</b>\n\n{str(e)}",
            reply_markup=free_presentations_menu_keyboard(),
            parse_mode='HTML'
        )

    await callback.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_free_all_custom", state='*')
async def admin_free_all_custom(callback: types.CallbackQuery, state: FSMContext):
    """Barchaga berish - maxsus son"""
    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "🔢 <b>MAXSUS SON</b>\n\n"
        "Har bir user'ga nechta bepul prezentatsiya qo'shmoqchisiz?\n\n"
        "<i>Faqat raqam kiriting (1-50)</i>\n\n"
        "❌ Bekor qilish uchun /cancel",
        parse_mode='HTML'
    )

    await AdminFreeStates.waiting_for_bulk_count.set()
    await callback.answer()


@dp.message_handler(state=AdminFreeStates.waiting_for_bulk_count)
async def admin_free_bulk_count_received(message: types.Message, state: FSMContext):
    """Bulk son qabul qilish"""
    if not is_admin(message.from_user.id):
        return

    try:
        count = int(message.text.strip())

        if count < 1 or count > 50:
            await message.answer("❌ Son 1 dan 50 gacha bo'lishi kerak!")
            return

        total_users = user_db.count_users()

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✅ Ha, barchaga berish", callback_data=f"admin_free_all_exec:{count}"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_free_menu")
        )

        await message.answer(
            f"⚠️ <b>TASDIQLASH</b>\n\n"
            f"📊 Jami: <b>{total_users}</b> ta user\n"
            f"🎁 Har biriga: <b>{count}</b> ta bepul prezentatsiya\n\n"
            f"Davom etasizmi?",
            reply_markup=keyboard,
            parse_mode='HTML'
        )

        await state.finish()

    except ValueError:
        await message.answer("❌ Faqat raqam kiriting!")


# ==================== USER TEKSHIRISH ====================
@dp.callback_query_handler(lambda c: c.data == "admin_free_check_user", state='*')
async def admin_free_check_user_start(callback: types.CallbackQuery, state: FSMContext):
    """User'ning bepul qoldig'ini tekshirish"""
    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "🔍 <b>USER TEKSHIRISH</b>\n\n"
        "User'ning Telegram ID sini kiriting:\n\n"
        "<i>Masalan: 1879114908</i>\n\n"
        "❌ Bekor qilish uchun /cancel",
        parse_mode='HTML'
    )

    await state.set_state("admin_check_user_free")
    await callback.answer()


@dp.message_handler(state="admin_check_user_free")
async def admin_free_check_user_result(message: types.Message, state: FSMContext):
    """User ma'lumotlarini ko'rsatish"""
    if not is_admin(message.from_user.id):
        return

    try:
        telegram_id = int(message.text.strip())

        if not user_db.user_exists(telegram_id):
            await message.answer(
                f"❌ User topilmadi: <code>{telegram_id}</code>",
                reply_markup=free_presentations_menu_keyboard(),
                parse_mode='HTML'
            )
            await state.finish()
            return

        # Ma'lumotlarni olish
        free_left = user_db.get_free_presentations(telegram_id)
        balance = user_db.get_user_balance(telegram_id)
        stats = user_db.get_user_stats(telegram_id)
        tasks = user_db.get_user_tasks(telegram_id, limit=3)

        # Task statistika
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t['status'] == 'completed'])

        text = f"""
🔍 <b>USER MA'LUMOTLARI</b>

🆔 Telegram ID: <code>{telegram_id}</code>
🎁 Bepul prezentatsiya: <b>{free_left}</b> ta
💰 Balans: <b>{balance:,.0f}</b> so'm

📊 <b>Statistika:</b>
📈 Jami to'ldirgan: {stats['total_deposited']:,.0f} so'm
📉 Jami sarflagan: {stats['total_spent']:,.0f} so'm
📅 A'zo bo'lgan: {stats['member_since'][:10]}

📋 <b>Oxirgi task'lar:</b> {completed_tasks}/{total_tasks} ta bajarilgan
"""

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("➕ Bepul berish", callback_data=f"admin_free_quick:{telegram_id}"),
            InlineKeyboardButton("🔄 Yangilash", callback_data=f"admin_free_refresh:{telegram_id}")
        )
        keyboard.add(
            InlineKeyboardButton("🔙 Orqaga", callback_data="admin_free_menu")
        )

        await message.answer(text, reply_markup=keyboard, parse_mode='HTML')
        await state.finish()

    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting.")


@dp.callback_query_handler(lambda c: c.data.startswith("admin_free_quick:"), state='*')
async def admin_free_quick_give(callback: types.CallbackQuery, state: FSMContext):
    """Tez bepul berish"""
    if not is_admin(callback.from_user.id):
        return

    telegram_id = int(callback.data.split(":")[1])
    current_free = user_db.get_free_presentations(telegram_id)

    await state.update_data(target_user_id=telegram_id, current_free=current_free)

    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("1️⃣", callback_data="admin_free_set:1"),
        InlineKeyboardButton("2️⃣", callback_data="admin_free_set:2"),
        InlineKeyboardButton("3️⃣", callback_data="admin_free_set:3"),
    )
    keyboard.add(
        InlineKeyboardButton("5️⃣", callback_data="admin_free_set:5"),
        InlineKeyboardButton("🔟", callback_data="admin_free_set:10"),
    )
    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin_free_menu")
    )

    await callback.message.edit_text(
        f"➕ <b>BEPUL PREZENTATSIYA QO'SHISH</b>\n\n"
        f"🆔 User: <code>{telegram_id}</code>\n"
        f"🎁 Hozirgi: <b>{current_free}</b> ta\n\n"
        f"Nechta qo'shmoqchisiz?",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

    await AdminFreeStates.waiting_for_user_id.set()
    await callback.answer()


# ==================== STATISTIKA ====================
@dp.callback_query_handler(lambda c: c.data == "admin_free_stats", state='*')
async def admin_free_stats(callback: types.CallbackQuery, state: FSMContext):
    """Bepul prezentatsiya statistikasi"""
    if not is_admin(callback.from_user.id):
        return

    try:
        # Statistikalarni olish
        total_users = user_db.count_users()

        # Bepul prezentatsiyasi bor userlar
        result = user_db.execute(
            "SELECT COUNT(*) FROM Users WHERE free_presentations > 0",
            fetchone=True
        )
        users_with_free = result[0] if result else 0

        # Jami bepul prezentatsiyalar
        result = user_db.execute(
            "SELECT COALESCE(SUM(free_presentations), 0) FROM Users",
            fetchone=True
        )
        total_free = result[0] if result else 0

        # O'rtacha
        result = user_db.execute(
            "SELECT COALESCE(AVG(free_presentations), 0) FROM Users WHERE free_presentations > 0",
            fetchone=True
        )
        avg_free = result[0] if result else 0

        # Top 5 user
        result = user_db.execute(
            """SELECT telegram_id, free_presentations 
               FROM Users 
               WHERE free_presentations > 0 
               ORDER BY free_presentations DESC 
               LIMIT 5""",
            fetchall=True
        )

        top_users = ""
        if result:
            for i, (tid, free) in enumerate(result, 1):
                top_users += f"{i}. <code>{tid}</code> - {free} ta\n"
        else:
            top_users = "Hech kim yo'q"

        text = f"""
📊 <b>BEPUL PREZENTATSIYA STATISTIKASI</b>

👥 <b>User'lar:</b>
├ Jami: <b>{total_users}</b> ta
├ Bepuli bor: <b>{users_with_free}</b> ta
└ Bepuli yo'q: <b>{total_users - users_with_free}</b> ta

🎁 <b>Bepul prezentatsiyalar:</b>
├ Jami: <b>{total_free}</b> ta
└ O'rtacha: <b>{avg_free:.1f}</b> ta/user

🏆 <b>Top 5 (eng ko'p bepul):</b>
{top_users}
"""

        await callback.message.edit_text(
            text,
            reply_markup=free_presentations_menu_keyboard(),
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"❌ Free stats xato: {e}")
        await callback.message.edit_text(
            f"❌ Xatolik: {str(e)}",
            reply_markup=free_presentations_menu_keyboard()
        )

    await callback.answer()


# ==================== USER'GA XABAR YUBORISH ====================
@dp.callback_query_handler(lambda c: c.data.startswith("admin_free_notify:"), state='*')
async def admin_free_notify_user(callback: types.CallbackQuery, state: FSMContext):
    """User'ga xabar yuborish"""
    if not is_admin(callback.from_user.id):
        return

    parts = callback.data.split(":")
    telegram_id = int(parts[1])
    count = int(parts[2])

    try:
        new_free = user_db.get_free_presentations(telegram_id)

        await bot.send_message(
            telegram_id,
            f"🎁 <b>TABRIKLAYMIZ!</b>\n\n"
            f"Sizga <b>{count}</b> ta bepul prezentatsiya berildi!\n\n"
            f"🎁 Hozirgi bepul: <b>{new_free}</b> ta\n\n"
            f"Prezentatsiya yaratish uchun /start bosing! 🚀",
            parse_mode='HTML'
        )

        await callback.message.edit_text(
            f"✅ User'ga xabar yuborildi!\n\n"
            f"🆔 User: <code>{telegram_id}</code>",
            reply_markup=free_presentations_menu_keyboard(),
            parse_mode='HTML'
        )

    except Exception as e:
        await callback.message.edit_text(
            f"❌ Xabar yuborishda xato: {str(e)}",
            reply_markup=free_presentations_menu_keyboard(),
            parse_mode='HTML'
        )

    await callback.answer()


# ==================== MENU GA QAYTISH ====================
@dp.callback_query_handler(lambda c: c.data == "admin_free_menu", state='*')
async def admin_free_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    """Bepul prezentatsiya menyusiga qaytish"""
    if not is_admin(callback.from_user.id):
        return

    await state.finish()

    await callback.message.edit_text(
        "🎁 <b>BEPUL PREZENTATSIYA BOSHQARUVI</b>\n\n"
        "Tanlang:",
        reply_markup=free_presentations_menu_keyboard(),
        parse_mode='HTML'
    )

    await callback.answer()


@dp.callback_query_handler(lambda c: c.data == "admin_free_cancel", state='*')
async def admin_free_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Bekor qilish"""
    await state.finish()
    await callback.message.edit_text(
        "❌ Bekor qilindi",
        reply_markup=free_presentations_menu_keyboard()
    )
    await callback.answer()


# ==================== CANCEL HANDLER ====================
@dp.message_handler(commands=['cancel'], state=[AdminFreeStates.waiting_for_user_id, AdminFreeStates.waiting_for_count,
                                                AdminFreeStates.waiting_for_bulk_count, "admin_check_user_free"])
async def admin_free_cancel_command(message: types.Message, state: FSMContext):
    """Cancel buyrug'i"""
    if not is_admin(message.from_user.id):
        return

    await state.finish()
    await message.answer(
        "❌ Bekor qilindi",
        reply_markup=free_presentations_menu_keyboard()
    )