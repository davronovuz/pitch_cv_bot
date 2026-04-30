import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from loader import dp
from environs import Env

env = Env()
env.read_env()
from utils.content_generator import ContentGenerator

OPENAI_API_KEY = env.str("OPENAI_API_KEY")

logger = logging.getLogger(__name__)


# =========================================================================
# 1. STATES
# =========================================================================
class MahallaStates(StatesGroup):
    confirming_start = State()
    mahalla_nomi = State()
    aholi_soni = State()
    yoshlar_soni = State()
    ayollar_soni = State()
    maktablar = State()
    bogchalar = State()
    tadbirkorlik_turi = State()
    tadbirkorlik_boshqa = State()
    xarid_qobiliyati = State()
    yol_yaqinligi = State()
    hudud_turi = State()
    turizm = State()
    turizm_batafsil = State()
    ehtiyojlar = State()


# =========================================================================
# 2. KEYBOARDS
# =========================================================================

def cancel_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton("❌ Bekor qilish"))
    return markup


def confirm_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("✅ Ha, boshlash"), KeyboardButton("❌ Bekor qilish"))
    return markup


def kb_tadbirkorlik():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🛍 Savdo"), KeyboardButton("🍽 Ovqatlanish"),
        KeyboardButton("🛠 Xizmat ko'rsatish"), KeyboardButton("🧵 Tikuvchilik"),
        KeyboardButton("🚕 Transport"), KeyboardButton("🔘 Boshqa")
    )
    markup.add(KeyboardButton("❌ Bekor qilish"))
    return markup


def kb_daraja():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add("📉 Past", "📊 O'rtacha", "📈 Yaxshi")
    markup.add("❌ Bekor qilish")
    return markup


def kb_masofa():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add("🛣 Yaqin", "🚗 O'rtacha", "🏔 Uzoq")
    markup.add("❌ Bekor qilish")
    return markup


def kb_hudud():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🏢 Shahar", "🏡 Qishloq")
    markup.add("❌ Bekor qilish")
    return markup


def kb_ha_yoq():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("✅ Ha", "🚫 Yo'q")
    markup.add("❌ Bekor qilish")
    return markup


# =========================================================================
# 3. HANDLERS
# =========================================================================

@dp.message_handler(Text(equals="🏘 Mahalla Tahlili"), state='*')
async def mahalla_start(message: types.Message, state: FSMContext):
    await state.finish()

    text = """
🤖 <b>AiDA — Mahalla Biznes Tahlili</b>

Sizning mahallangiz uchun sun'iy intellekt orqali <b>TOP-3 Biznes g'oyalar</b> ishlab chiqamiz!

🎁 <b>XIZMAT BEPUL!</b>

📊 12 ta savolga javob bering va <b>tayyor matnli tahlil</b> oling.
Boshlaymizmi?
"""
    await message.answer(text, reply_markup=confirm_keyboard(), parse_mode='HTML')
    await MahallaStates.confirming_start.set()


@dp.message_handler(Text(equals="✅ Ha, boshlash"), state=MahallaStates.confirming_start)
async def q1_start(message: types.Message, state: FSMContext):
    await message.answer("1️⃣ <b>Mahalla nomini kiriting:</b>", reply_markup=cancel_keyboard(), parse_mode='HTML')
    await MahallaStates.mahalla_nomi.set()


@dp.message_handler(Text(equals="❌ Bekor qilish"), state=MahallaStates)
async def cancel_mahalla(message: types.Message, state: FSMContext):
    from keyboards.default.default_keyboard import main_menu_keyboard
    await state.finish()
    await message.answer("❌ Tahlil bekor qilindi.", reply_markup=main_menu_keyboard())


@dp.message_handler(state=MahallaStates.mahalla_nomi)
async def q2_aholi(message: types.Message, state: FSMContext):
    await state.update_data(mahalla_nomi=message.text)
    await message.answer("2️⃣ <b>Aholi soni nechta?</b> (taxminan)", reply_markup=cancel_keyboard(), parse_mode='HTML')
    await MahallaStates.aholi_soni.set()


@dp.message_handler(state=MahallaStates.aholi_soni)
async def q3_yoshlar(message: types.Message, state: FSMContext):
    await state.update_data(aholi_soni=message.text)
    await message.answer("3️⃣ <b>Yoshlar soni (14–30 yosh):</b>", reply_markup=cancel_keyboard(), parse_mode='HTML')
    await MahallaStates.yoshlar_soni.set()


@dp.message_handler(state=MahallaStates.yoshlar_soni)
async def q4_ayollar(message: types.Message, state: FSMContext):
    await state.update_data(yoshlar_soni=message.text)
    await message.answer("4️⃣ <b>Xotin-qizlar soni:</b>", reply_markup=cancel_keyboard(), parse_mode='HTML')
    await MahallaStates.ayollar_soni.set()


@dp.message_handler(state=MahallaStates.ayollar_soni)
async def q5_maktab(message: types.Message, state: FSMContext):
    await state.update_data(ayollar_soni=message.text)
    await message.answer("5️⃣ <b>Maktablar soni nechta?</b>", reply_markup=cancel_keyboard(), parse_mode='HTML')
    await MahallaStates.maktablar.set()


@dp.message_handler(state=MahallaStates.maktablar)
async def q6_bogcha(message: types.Message, state: FSMContext):
    await state.update_data(maktablar=message.text)
    await message.answer("6️⃣ <b>Bog'chalar (MTT) soni nechta?</b>", reply_markup=cancel_keyboard(), parse_mode='HTML')
    await MahallaStates.bogchalar.set()


@dp.message_handler(state=MahallaStates.bogchalar)
async def q7_tadbirkorlik(message: types.Message, state: FSMContext):
    await state.update_data(bogchalar=message.text)
    await message.answer("7️⃣ <b>Mahallada eng ko'p uchraydigan tadbirkorlik turi?</b>", reply_markup=kb_tadbirkorlik(),
                         parse_mode='HTML')
    await MahallaStates.tadbirkorlik_turi.set()


@dp.message_handler(state=MahallaStates.tadbirkorlik_turi)
async def q7_logic(message: types.Message, state: FSMContext):
    if message.text == "🔘 Boshqa":
        await message.answer("✏️ <b>Qanday tadbirkorlik turi? Yozib yuboring:</b>", reply_markup=cancel_keyboard(),
                             parse_mode='HTML')
        await MahallaStates.tadbirkorlik_boshqa.set()
    else:
        await state.update_data(tadbirkorlik_turi=message.text, tadbirkorlik_boshqa="")
        await message.answer("8️⃣ <b>Aholi xarid qobiliyati qaysi darajada?</b>", reply_markup=kb_daraja(),
                             parse_mode='HTML')
        await MahallaStates.xarid_qobiliyati.set()


@dp.message_handler(state=MahallaStates.tadbirkorlik_boshqa)
async def q7_custom(message: types.Message, state: FSMContext):
    await state.update_data(tadbirkorlik_turi="Boshqa", tadbirkorlik_boshqa=message.text)
    await message.answer("8️⃣ <b>Aholi xarid qobiliyati qaysi darajada?</b>", reply_markup=kb_daraja(),
                         parse_mode='HTML')
    await MahallaStates.xarid_qobiliyati.set()


@dp.message_handler(state=MahallaStates.xarid_qobiliyati)
async def q8_save(message: types.Message, state: FSMContext):
    await state.update_data(xarid_qobiliyati=message.text)
    await message.answer("9️⃣ <b>Magistral yo'lga qanchalik yaqin?</b>", reply_markup=kb_masofa(), parse_mode='HTML')
    await MahallaStates.yol_yaqinligi.set()


@dp.message_handler(state=MahallaStates.yol_yaqinligi)
async def q9_save(message: types.Message, state: FSMContext):
    await state.update_data(yol_yaqinligi=message.text)
    await message.answer("🔟 <b>Hudud turi qanday?</b>", reply_markup=kb_hudud(), parse_mode='HTML')
    await MahallaStates.hudud_turi.set()


@dp.message_handler(state=MahallaStates.hudud_turi)
async def q10_save(message: types.Message, state: FSMContext):
    await state.update_data(hudud_turi=message.text)
    await message.answer("1️⃣1️⃣ <b>Turizm obyektlari bormi?</b>", reply_markup=kb_ha_yoq(), parse_mode='HTML')
    await MahallaStates.turizm.set()


@dp.message_handler(state=MahallaStates.turizm)
async def q11_logic(message: types.Message, state: FSMContext):
    if message.text == "✅ Ha":
        await message.answer("✏️ <b>Qaysi obyektlar bor?</b>", reply_markup=cancel_keyboard(), parse_mode='HTML')
        await MahallaStates.turizm_batafsil.set()
    elif message.text == "🚫 Yo'q":
        await state.update_data(turizm="Yo'q", turizm_batafsil="")
        await message.answer(
            "1️⃣2️⃣ <b>Mahallaning eng muhim ehtiyojlari?</b>\n(Masalan: bozorcha, dorixona, o'quv markazi...)",
            reply_markup=cancel_keyboard(), parse_mode='HTML')
        await MahallaStates.ehtiyojlar.set()
    else:
        await message.answer("1️⃣1️⃣ <b>Turizm obyektlari bormi?</b>", reply_markup=kb_ha_yoq(), parse_mode='HTML')


@dp.message_handler(state=MahallaStates.turizm_batafsil)
async def q11_custom(message: types.Message, state: FSMContext):
    await state.update_data(turizm="Ha", turizm_batafsil=message.text)
    await message.answer(
        "1️⃣2️⃣ <b>Mahallaning eng muhim ehtiyojlari?</b>\n(Masalan: bozorcha, dorixona, o'quv markazi...)",
        reply_markup=cancel_keyboard(), parse_mode='HTML')
    await MahallaStates.ehtiyojlar.set()


# =========================================================================
# 4. AI GENERATSIYA
# =========================================================================

@dp.message_handler(state=MahallaStates.ehtiyojlar)
async def finish_and_generate(message: types.Message, state: FSMContext):
    from keyboards.default.default_keyboard import main_menu_keyboard
    await state.update_data(ehtiyojlar=message.text)
    user_data = await state.get_data()

    wait_msg = await message.answer(
        "🤖 <b>Rahmat! AiDA ma'lumotlarni tahlil qilmoqda...</b>\n\n"
        "⏳ <i>Iltimos, kuting (taxminan 10-15 soniya)...</i>",
        reply_markup=main_menu_keyboard(),
        parse_mode='HTML'
    )

    await types.ChatActions.typing()

    try:
        generator = ContentGenerator(api_key=OPENAI_API_KEY)
        result = await generator.generate_mahalla_analysis(user_data)

        mahalla = user_data.get('mahalla_nomi', 'Nomaʼlum')
        summary = result.get('summary', 'Maʼlumot yo\'q')

        response_text = f"📊 <b>MAHALLA BIZNES TAHLILI (AiDA)</b>\n"
        response_text += f"📍 <b>Mahalla:</b> {mahalla}\n\n"
        response_text += f"💡 <b>XULOSA:</b>\n{summary}\n"
        response_text += "➖➖➖➖➖➖➖➖➖➖\n\n"
        response_text += "🏆 <b>TOP 3 BIZNES G'OYA:</b>\n\n"

        businesses = result.get('top_businesses', [])
        icons = ["1️⃣", "2️⃣", "3️⃣"]
        for i, biz in enumerate(businesses):
            icon = icons[i] if i < 3 else "🔹"
            name = biz.get('name', 'Nomaʼlum biznes')
            reason = biz.get('reason', '-')
            inv = biz.get('investment', '-')
            profit = biz.get('profitability', '-')

            response_text += f"{icon} <b>{name}</b>\n"
            response_text += f"🎯 <i>Sabab:</i> {reason}\n"
            response_text += f"💰 <i>Investitsiya:</i> {inv}\n"
            response_text += f"📈 <i>Foyda:</i> {profit}\n\n"

        response_text += "➖➖➖➖➖➖➖➖➖➖\n"
        response_text += "✅ <i>Tahlil AiDA tomonidan tayyorlandi.</i>"

        await wait_msg.delete()
        await message.answer(response_text, parse_mode='HTML')

    except Exception as e:
        logger.exception(f"AiDA Error: {e}")
        try:
            await wait_msg.delete()
        except Exception:
            pass
        await message.answer(
            "⚠️ <b>Kechirasiz, texnik xatolik yuz berdi.</b>\nIltimos, keyinroq qayta urinib ko'ring.",
            reply_markup=main_menu_keyboard(),
            parse_mode='HTML'
        )

    await state.finish()
