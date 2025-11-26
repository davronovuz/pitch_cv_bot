from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging

from data.config import ADMINS
from loader import dp, user_db
from keyboards.default.default_keyboard import menu_ichki_admin, menu_admin

logger = logging.getLogger(__name__)


# ==================== FSM STATES ====================
class AdminStates(StatesGroup):
    # Admin boshqaruvi
    AddAdmin = State()
    RemoveAdmin = State()

    # Narx boshqaruvi
    ChangePriceSelectService = State()
    ChangePriceEnterAmount = State()

    # Tranzaksiya boshqaruvi
    ViewUserTransactions = State()

    # Balans boshqaruvi
    ViewUserBalance = State()
    AddBalanceToUser = State()
    AddBalanceAmount = State()


# ==================== PERMISSION CHECK ====================
async def check_super_admin_permission(telegram_id: int) -> bool:
    """Super admin tekshirish"""
    logger.info(f"Super admin tekshiruv: {telegram_id}")
    return telegram_id in ADMINS


async def check_admin_permission(telegram_id: int) -> bool:
    """Oddiy admin tekshirish"""
    logger.info(f"Admin tekshiruv: {telegram_id}")
    user = user_db.select_user(telegram_id=telegram_id)
    if not user:
        logger.info(f"User topilmadi: {telegram_id}")
        return False

    user_id = user[0]  # Database'dagi user_id
    is_admin = user_db.check_if_admin(user_id=user_id)
    logger.info(f"User {user_id} admin: {is_admin}")
    return is_admin


# ==================== NAVIGATION ====================
@dp.message_handler(Text("🔙 Ortga qaytish"))
async def back_handler(message: types.Message):
    """Ortga qaytish"""
    telegram_id = message.from_user.id
    if await check_super_admin_permission(telegram_id) or await check_admin_permission(telegram_id):
        await message.answer("Bosh sahifa", reply_markup=menu_admin)


@dp.message_handler(commands="panel")
async def control_panel(message: types.Message):
    """Admin panelga kirish"""
    telegram_id = message.from_user.id
    logger.info(f"Panel ochish: {telegram_id}")

    if await check_super_admin_permission(telegram_id) or await check_admin_permission(telegram_id):
        # Statistika olish
        stats = get_admin_statistics()

        stats_text = f"""
🎛 <b>ADMIN PANEL</b>

📊 <b>Statistika:</b>
👥 Jami foydalanuvchilar: {stats['total_users']}
✅ Faol: {stats['active_users']}
🚫 Bloklangan: {stats['blocked_users']}

💰 <b>Moliyaviy:</b>
💳 Jami balans: {stats['total_balance']:,.0f} so'm
📈 Jami to'ldirilgan: {stats['total_deposited']:,.0f} so'm
📉 Jami sarflangan: {stats['total_spent']:,.0f} so'm
⏳ Kutilayotgan to'lovlar: {stats['pending_deposits']:,.0f} so'm

📋 <b>Task'lar:</b>
⏳ Kutilmoqda: {stats['pending_tasks']}
⚙️ Jarayonda: {stats['processing_tasks']}
✅ Tugallangan: {stats['completed_tasks']}
"""

        await message.answer(stats_text, reply_markup=menu_admin)
    else:
        await message.reply("❌ Siz admin emassiz!")


def get_admin_statistics() -> dict:
    """Admin statistikasini olish"""
    try:
        # Foydalanuvchilar statistikasi
        total_users = user_db.count_users()
        active_users = user_db.count_active_users()
        blocked_users = user_db.count_blocked_users()

        # Moliyaviy statistika
        financial_stats = user_db.get_financial_stats()

        # Task statistika
        pending_tasks = len(user_db.get_pending_tasks())

        # Processing va completed task'lar sonini olish
        all_tasks_query = """
            SELECT status, COUNT(*) as count
            FROM PresentationTasks
            WHERE status IN ('processing', 'completed')
            GROUP BY status
        """
        task_stats = user_db.execute(all_tasks_query, fetchall=True)

        processing_tasks = 0
        completed_tasks = 0

        for row in task_stats:
            if row[0] == 'processing':
                processing_tasks = row[1]
            elif row[0] == 'completed':
                completed_tasks = row[1]

        return {
            'total_users': total_users,
            'active_users': active_users,
            'blocked_users': blocked_users,
            'total_balance': financial_stats['total_balance'],
            'total_deposited': financial_stats['total_deposited'],
            'total_spent': financial_stats['total_spent'],
            'pending_deposits': financial_stats['pending_deposits'],
            'pending_tasks': pending_tasks,
            'processing_tasks': processing_tasks,
            'completed_tasks': completed_tasks
        }
    except Exception as e:
        logger.error(f"Statistika olishda xato: {e}")
        return {
            'total_users': 0, 'active_users': 0, 'blocked_users': 0,
            'total_balance': 0, 'total_deposited': 0, 'total_spent': 0,
            'pending_deposits': 0, 'pending_tasks': 0,
            'processing_tasks': 0, 'completed_tasks': 0
        }


# ==================== ADMIN MANAGEMENT ====================
@dp.message_handler(Text(equals="👥 Adminlar boshqaruvi"))
async def admin_control_menu(message: types.Message):
    """Admin boshqaruvi menyusi"""
    telegram_id = message.from_user.id
    logger.info(f"Adminlar boshqaruvi: {telegram_id}")

    if not await check_super_admin_permission(telegram_id):
        await message.reply("❌ Faqat super adminlar uchun!")
        return

    await message.answer("👥 Admin boshqaruvi menyusi", reply_markup=menu_ichki_admin)


@dp.message_handler(Text(equals="➕ Admin qo'shish"))
async def add_admin(message: types.Message):
    """Admin qo'shish - boshlash"""
    telegram_id = message.from_user.id
    logger.info(f"Admin qo'shish boshlandi: {telegram_id}")

    if not await check_super_admin_permission(telegram_id):
        await message.reply("❌ Faqat super adminlar admin qo'sha oladi!")
        return

    await message.answer("✍️ Yangi adminning Telegram ID raqamini kiriting:")
    await AdminStates.AddAdmin.set()


@dp.message_handler(state=AdminStates.AddAdmin)
async def process_admin_add(message: types.Message, state: FSMContext):
    """Admin qo'shish - jarayon"""
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return

    admin_telegram_id = int(message.text)
    logger.info(f"Admin qo'shilmoqda: {admin_telegram_id}")

    # Foydalanuvchi mavjudligini tekshirish
    user = user_db.select_user(telegram_id=admin_telegram_id)

    if not user:
        await message.answer("❌ Bunday foydalanuvchi topilmadi.\nAvval bot bilan /start qilishi kerak.")
        await state.finish()
        return

    user_id = user[0]
    username = user[2] if user[2] else "Username yo'q"

    # Allaqachon admin ekanligini tekshirish
    if user_db.check_if_admin(user_id=user_id):
        await message.answer("❌ Bu foydalanuvchi allaqachon admin!")
        await state.finish()
        return

    # Super admin ekanligini tekshirish
    if admin_telegram_id in ADMINS:
        await message.answer("❌ Bu foydalanuvchi allaqachon Super Admin!")
        await state.finish()
        return

    # Admin qo'shish
    user_db.add_admin(user_id=user_id, name=username, is_super_admin=False)
    logger.info(f"✅ Admin qo'shildi: {admin_telegram_id} (@{username})")

    await message.answer(f"✅ <b>Admin qo'shildi!</b>\n\n👤 @{username}\n🆔 ID: {admin_telegram_id}")
    await state.finish()


@dp.message_handler(Text(equals="❌ Adminni o'chirish"))
async def remove_admin(message: types.Message):
    """Admin o'chirish - boshlash"""
    telegram_id = message.from_user.id
    logger.info(f"Admin o'chirish boshlandi: {telegram_id}")

    if not await check_super_admin_permission(telegram_id):
        await message.reply("❌ Faqat super adminlar admin o'chira oladi!")
        return

    await message.answer("✍️ O'chiriladigan adminning Telegram ID raqamini kiriting:")
    await AdminStates.RemoveAdmin.set()


@dp.message_handler(state=AdminStates.RemoveAdmin)
async def process_admin_remove(message: types.Message, state: FSMContext):
    """Admin o'chirish - jarayon"""
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return

    admin_telegram_id = int(message.text)
    logger.info(f"Admin o'chirilmoqda: {admin_telegram_id}")

    # Super adminni o'chirishga ruxsat bermaslik
    if admin_telegram_id in ADMINS:
        await message.answer("❌ Super adminni o'chirish mumkin emas!")
        await state.finish()
        return

    # Foydalanuvchi mavjudligini tekshirish
    user = user_db.select_user(telegram_id=admin_telegram_id)

    if not user:
        await message.answer("❌ Bunday foydalanuvchi topilmadi.")
        await state.finish()
        return

    user_id = user[0]
    username = user[2] if user[2] else "Username yo'q"

    # Admin ekanligini tekshirish
    if not user_db.check_if_admin(user_id=user_id):
        await message.answer("❌ Bu foydalanuvchi admin emas!")
        await state.finish()
        return

    # Adminni o'chirish
    user_db.remove_admin(user_id=user_id)
    logger.info(f"✅ Admin o'chirildi: {admin_telegram_id} (@{username})")

    await message.answer(f"✅ <b>Admin o'chirildi!</b>\n\n👤 @{username}\n🆔 ID: {admin_telegram_id}")
    await state.finish()


@dp.message_handler(Text(equals="👥 Barcha adminlar"))
async def list_all_admins(message: types.Message):
    """Barcha adminlar ro'yxati"""
    telegram_id = message.from_user.id
    logger.info(f"Adminlar ro'yxati: {telegram_id}")

    if not await check_super_admin_permission(telegram_id) and not await check_admin_permission(telegram_id):
        await message.reply("❌ Siz admin emassiz!")
        return

    # Barcha adminlarni olish
    admins = user_db.get_all_admins()
    logger.info(f"Adminlar soni: {len(admins)}")

    admin_list = ["👥 <b>ADMINLAR RO'YXATI</b>\n"]

    # Super adminlar
    admin_list.append("🔴 <b>SUPER ADMINLAR:</b>")
    for admin_id in ADMINS:
        user = user_db.select_user(telegram_id=admin_id)
        username = user[2] if user and user[2] else "Username yo'q"
        admin_list.append(f"  • @{username} (ID: {admin_id})")

    # Oddiy adminlar
    if admins:
        admin_list.append("\n🟢 <b>ODDIY ADMINLAR:</b>")
        for admin in admins:
            if admin['telegram_id'] not in ADMINS:
                username = admin['name'] if admin['name'] else "Username yo'q"
                admin_list.append(f"  • @{username} (ID: {admin['telegram_id']})")

    if len(admin_list) <= 2:
        admin_list.append("  Oddiy adminlar yo'q")

    await message.answer("\n".join(admin_list))


# ==================== NARXLAR BOSHQARUVI ====================
@dp.message_handler(Text(equals="💰 Narxlarni boshqarish"))
async def manage_prices(message: types.Message):
    """Narxlarni boshqarish menyusi"""
    telegram_id = message.from_user.id

    if not await check_super_admin_permission(telegram_id):
        await message.reply("❌ Faqat super adminlar narxlarni o'zgartira oladi!")
        return

    # Hozirgi narxlarni ko'rsatish
    prices = user_db.get_all_prices()

    price_text = ["💰 <b>HOZIRGI NARXLAR</b>\n"]

    for i, price in enumerate(prices, 1):
        status = "✅" if price['is_active'] else "❌"
        price_text.append(
            f"{i}. <b>{price['description']}</b>\n"
            f"   💵 {price['price']:,.0f} {price['currency']}\n"
            f"   🔑 <code>{price['service_type']}</code>\n"
            f"   {status} {'Faol' if price['is_active'] else 'Nofaol'}\n"
        )

    price_text.append("\n✍️ Narxni o'zgartirish uchun service_type ni kiriting:")
    price_text.append("Masalan: <code>slide_basic</code>")

    await message.answer("\n".join(price_text))
    await AdminStates.ChangePriceSelectService.set()


@dp.message_handler(state=AdminStates.ChangePriceSelectService)
async def select_service_for_price_change(message: types.Message, state: FSMContext):
    """Service type tanlash"""
    service_type = message.text.strip()

    # Service mavjudligini tekshirish
    current_price = user_db.get_price(service_type)

    if current_price is None:
        await message.answer("❌ Bunday service topilmadi!\n\n/panel - ortga qaytish")
        await state.finish()
        return

    await state.update_data(service_type=service_type)

    await message.answer(
        f"📝 Service: <code>{service_type}</code>\n"
        f"💰 Hozirgi narx: <b>{current_price:,.0f} so'm</b>\n\n"
        f"✍️ Yangi narxni kiriting (faqat raqam):"
    )
    await AdminStates.ChangePriceEnterAmount.set()


@dp.message_handler(state=AdminStates.ChangePriceEnterAmount)
async def enter_new_price(message: types.Message, state: FSMContext):
    """Yangi narx kiritish"""
    if not message.text.replace('.', '').replace(',', '').isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return

    new_price = float(message.text.replace(',', ''))
    data = await state.get_data()
    service_type = data.get('service_type')

    # Narxni yangilash
    success = user_db.update_price(service_type, new_price, message.from_user.id)

    if success:
        await message.answer(
            f"✅ <b>Narx yangilandi!</b>\n\n"
            f"📝 Service: <code>{service_type}</code>\n"
            f"💰 Yangi narx: <b>{new_price:,.0f} so'm</b>"
        )
    else:
        await message.answer("❌ Narxni yangilashda xatolik!")

    await state.finish()


# ==================== TRANZAKSIYALAR ====================
@dp.message_handler(Text(equals="💳 Tranzaksiyalar"))
async def view_transactions(message: types.Message):
    """Kutilayotgan tranzaksiyalarni ko'rish"""
    telegram_id = message.from_user.id

    if not await check_super_admin_permission(telegram_id) and not await check_admin_permission(telegram_id):
        await message.reply("❌ Siz admin emassiz!")
        return

    # Kutilayotgan tranzaksiyalarni olish
    pending = user_db.get_pending_transactions()

    if not pending:
        await message.answer("✅ Kutilayotgan tranzaksiyalar yo'q!")
        return

    for trans in pending:
        trans_text = f"""
💳 <b>YANGI TRANZAKSIYA</b>

🆔 ID: {trans['id']}
👤 User: @{trans['username']} (ID: {trans['telegram_id']})
💰 Summa: {trans['amount']:,.0f} so'm
📝 Turi: {trans['type']}
📄 Tavsif: {trans['description'] or 'Yoq'}
📅 Sana: {trans['created_at']}

Tasdiqlaysizmi?
"""

        # Inline keyboard
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_trans:{trans['id']}"),
            types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_trans:{trans['id']}")
        )

        # Chek bor bo'lsa
        if trans['receipt_file_id']:
            try:
                await message.answer_photo(
                    photo=trans['receipt_file_id'],
                    caption=trans_text,
                    reply_markup=keyboard
                )
            except:
                await message.answer(trans_text, reply_markup=keyboard)
        else:
            await message.answer(trans_text, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('approve_trans:'))
async def approve_transaction_callback(callback: types.CallbackQuery):
    """Tranzaksiyani tasdiqlash"""
    transaction_id = int(callback.data.split(':')[1])
    admin_telegram_id = callback.from_user.id

    success = user_db.approve_transaction(transaction_id, admin_telegram_id)

    if success:
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n✅ <b>TASDIQLANDI</b>",
            reply_markup=None
        )
        await callback.answer("✅ Tranzaksiya tasdiqlandi!")
    else:
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith('reject_trans:'))
async def reject_transaction_callback(callback: types.CallbackQuery):
    """Tranzaksiyani rad etish"""
    transaction_id = int(callback.data.split(':')[1])
    admin_telegram_id = callback.from_user.id

    success = user_db.reject_transaction(transaction_id, admin_telegram_id)

    if success:
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n❌ <b>RAD ETILDI</b>",
            reply_markup=None
        )
        await callback.answer("✅ Tranzaksiya rad etildi!")
    else:
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)


# ==================== FOYDALANUVCHI MA'LUMOTLARI ====================
@dp.message_handler(Text(equals="👤 Foydalanuvchi ma'lumotlari"))
async def view_user_info_menu(message: types.Message):
    """Foydalanuvchi ma'lumotlarini ko'rish"""
    telegram_id = message.from_user.id

    if not await check_super_admin_permission(telegram_id) and not await check_admin_permission(telegram_id):
        await message.reply("❌ Siz admin emassiz!")
        return

    await message.answer(
        "👤 Foydalanuvchi ma'lumotlarini ko'rish uchun\n"
        "Telegram ID raqamini kiriting:"
    )
    await AdminStates.ViewUserBalance.set()


@dp.message_handler(state=AdminStates.ViewUserBalance)
async def show_user_info(message: types.Message, state: FSMContext):
    """Foydalanuvchi ma'lumotlarini ko'rsatish"""
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return

    target_user_id = int(message.text)

    # User mavjudligini tekshirish
    user = user_db.select_user(telegram_id=target_user_id)

    if not user:
        await message.answer("❌ Bunday foydalanuvchi topilmadi!")
        await state.finish()
        return

    # User statistikasini olish
    stats = user_db.get_user_stats(target_user_id)
    tasks = user_db.get_user_tasks(target_user_id, limit=5)
    transactions = user_db.get_user_transactions(target_user_id, limit=5)

    username = user[2] if user[2] else "Username yo'q"

    info_text = f"""
👤 <b>FOYDALANUVCHI MA'LUMOTLARI</b>

🆔 ID: {target_user_id}
👤 Username: @{username}
📅 Ro'yxatdan o'tgan: {stats['member_since'][:10]}

💰 <b>BALANS:</b>
💳 Hozirgi: {stats['balance']:,.0f} so'm
📈 Jami to'ldirilgan: {stats['total_deposited']:,.0f} so'm
📉 Jami sarflangan: {stats['total_spent']:,.0f} so'm

📊 <b>TASK'LAR:</b>
"""

    if tasks:
        for task in tasks[:3]:
            status_emoji = {
                'pending': '⏳',
                'processing': '⚙️',
                'completed': '✅',
                'failed': '❌'
            }.get(task['status'], '❓')

            info_text += f"{status_emoji} {task['type']} - {task['status']} ({task['created_at'][:10]})\n"
    else:
        info_text += "Task'lar yo'q\n"

    info_text += f"\n💳 <b>OXIRGI TRANZAKSIYALAR:</b>\n"

    if transactions:
        for trans in transactions[:3]:
            type_emoji = {
                'deposit': '➕',
                'withdrawal': '➖',
                'refund': '↩️'
            }.get(trans['type'], '❓')

            info_text += f"{type_emoji} {trans['amount']:,.0f} so'm - {trans['status']} ({trans['created_at'][:10]})\n"
    else:
        info_text += "Tranzaksiyalar yo'q"

    await message.answer(info_text)
    await state.finish()


# ==================== BALANS QO'SHISH ====================
@dp.message_handler(Text(equals="💵 Balans qo'shish"))
async def add_balance_to_user_menu(message: types.Message):
    """Foydalanuvchiga balans qo'shish"""
    telegram_id = message.from_user.id

    if not await check_super_admin_permission(telegram_id):
        await message.reply("❌ Faqat super adminlar balans qo'sha oladi!")
        return

    await message.answer(
        "💵 Foydalanuvchiga balans qo'shish uchun\n"
        "Telegram ID raqamini kiriting:"
    )
    await AdminStates.AddBalanceToUser.set()


@dp.message_handler(state=AdminStates.AddBalanceToUser)
async def select_user_for_balance(message: types.Message, state: FSMContext):
    """Foydalanuvchini tanlash"""
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return

    target_user_id = int(message.text)

    # User mavjudligini tekshirish
    if not user_db.user_exists(target_user_id):
        await message.answer("❌ Bunday foydalanuvchi topilmadi!")
        await state.finish()
        return

    current_balance = user_db.get_user_balance(target_user_id)

    await state.update_data(target_user_id=target_user_id)

    await message.answer(
        f"👤 User ID: {target_user_id}\n"
        f"💰 Hozirgi balans: {current_balance:,.0f} so'm\n\n"
        f"✍️ Qo'shiladigan summani kiriting:"
    )
    await AdminStates.AddBalanceAmount.set()


@dp.message_handler(state=AdminStates.AddBalanceAmount)
async def add_balance_amount(message: types.Message, state: FSMContext):
    """Balans qo'shish"""
    if not message.text.replace('.', '').replace(',', '').isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return

    amount = float(message.text.replace(',', ''))
    data = await state.get_data()
    target_user_id = data.get('target_user_id')

    # Balans qo'shish
    success = user_db.add_to_balance(target_user_id, amount)

    if success:
        new_balance = user_db.get_user_balance(target_user_id)

        # Tranzaksiya yaratish
        user_db.create_transaction(
            telegram_id=target_user_id,
            transaction_type='deposit',
            amount=amount,
            description='Admin tomonidan qo\'shildi',
            status='approved'
        )

        await message.answer(
            f"✅ <b>Balans qo'shildi!</b>\n\n"
            f"👤 User ID: {target_user_id}\n"
            f"💰 Yangi balans: {new_balance:,.0f} so'm\n"
            f"➕ Qo'shildi: {amount:,.0f} so'm"
        )
    else:
        await message.answer("❌ Balans qo'shishda xatolik!")

    await state.finish()