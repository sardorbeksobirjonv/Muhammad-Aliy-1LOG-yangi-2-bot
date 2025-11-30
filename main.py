import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

# ⚙️ BOT MA'LUMOTLARI
BOT_TOKEN = "8520283531:AAGLNDSOYm3RY_S2DuUEhk6f61xNyL4dQLw"
ADMIN_ID = 1741270732

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# 🧠 HOLATLAR
class ReplyState(StatesGroup):
    waiting_for_reply = State()

class LanguageState(StatesGroup):
    waiting_for_lang = State()

class AdminLangState(StatesGroup):
    waiting_for_admin_lang = State()


# 🌐 Til tanlash tugmasi
lang_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 Ўзбек тили", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="lang_ru")
        ]
    ]
)

# 📌 Matnlar
messages = {
    "start_uz":
        "👋 Ассалому алайкум, <b>{name}</b>!\n\n"
        "📡 Ушбу бот орқали @iam_mkhmmd билан бевосита боғланишингиз мумкин.\n\n"
        "💬 Хабар, расм, видео ёки овозли хабар юборинг — ва Muhammad-Aliy жавоб беради.",

    "start_ru":
        "👋 Здравствуйте, <b>{name}</b>!\n\n"
        "📡 Через этого бота вы можете напрямую связаться с @iam_mkhmmd.\n\n"
        "💬 Отправьте сообщение, фото, видео или голосовое сообщение — и Muhammad-Aliy ответит вам.",

    "forwarded_uz": "✅ Хабарингиз юборилди!",
    "forwarded_ru": "✅ Ваше сообщение отправлено!",

    "unsupported_uz": "❗ Бу турдаги файл қабул қилинмайди.",
    "unsupported_ru": "❗ Этот тип файла не поддерживается.",

    "new_msg_uz": "📩 Янги хабар:",
    "new_msg_ru": "📩 Новое сообщение:",

    "reply_btn_uz": "✍️ Жавоб бериш",
    "reply_btn_ru": "✍️ Ответить",

    "reply_write_uz": "✍️ Фойдаланувчига жавоб ёзинг:",
    "reply_write_ru": "✍️ Напишите ответ пользователю:",

    "reply_sent_uz": "✅ Жавоб юборилди!",
    "reply_sent_ru": "✅ Ответ отправлен!",

    "user_blocked_uz": "🚫 Фойдаланувчи ботни блоклаган.",
    "user_blocked_ru": "🚫 Пользователь заблокировал бота.",

    "send_error_uz": "⚠️ Юборишда хатолик.",
    "send_error_ru": "⚠️ Ошибка при отправке."
}

# 🧩 Til va ism doimiy saqlanadigan joy
user_settings = {}  # {user_id: {"lang": "uz", "name": "Sardor"}}
admin_language = {"lang": "uz"}


# 🔹 /start
@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):

    user_id = message.from_user.id

    # ADMIN
    if user_id == ADMIN_ID:
        await message.answer("❗ Админ, тилни танланг:", reply_markup=lang_keyboard)
        await state.set_state(AdminLangState.waiting_for_admin_lang)
        return

    # FOYDALANUVCHI – ismini saqlab qo'yamiz
    user_settings[user_id] = {"name": message.from_user.full_name}

    await state.set_state(LanguageState.waiting_for_lang)
    await message.answer("Tilni tanlang / Выберите язык:", reply_markup=lang_keyboard)


# 🔹 Foydalanuvchi til tanlaydi
@dp.callback_query(F.data.startswith("lang_") & (F.from_user.id != ADMIN_ID))
async def set_language(callback: types.CallbackQuery, state: FSMContext):

    user_id = callback.from_user.id
    lang = callback.data.split("_")[1]

    # User sozlamasiga tilni yozamiz
    if user_id not in user_settings:
        user_settings[user_id] = {}

    user_settings[user_id]["lang"] = lang

    name = user_settings[user_id].get("name", "Foydalanuvchi")

    await callback.message.answer(messages[f"start_{lang}"].format(name=name), parse_mode="HTML")

    await callback.answer()
    await state.clear()


# 🔹 Admin til tanlaydi
@dp.callback_query(F.data.startswith("lang_") & (F.from_user.id == ADMIN_ID))
async def set_admin_language(callback: types.CallbackQuery, state: FSMContext):

    lang = callback.data.split("_")[1]
    admin_language["lang"] = lang

    await callback.message.answer(
        f"✅ Админ тили: {'Ўзбек' if lang == 'uz' else 'Русский'}"
    )
    await callback.answer()
    await state.clear()


# 🔹 Foydalanuvchi xabar yuboradi → Admin ga boradi
@dp.message(F.from_user.id != ADMIN_ID)
async def forward_all_to_admin(message: types.Message):

    user = message.from_user
    user_id = user.id

    # Til aniqlaymiz
    lang = user_settings.get(user_id, {}).get("lang", "uz")
    admin_lang = admin_language.get("lang", "uz")

    user_info = f"👤 {user.full_name}\n🆔 <code>{user_id}</code>"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=messages[f"reply_btn_{admin_lang}"],
                    callback_data=f"reply_{user_id}"
                )
            ]
        ]
    )

    try:
        if message.text:
            await bot.send_message(
                ADMIN_ID,
                f"{messages[f'new_msg_{admin_lang}']}\n\n{user_info}\n\n💬 {message.text}",
                parse_mode="HTML",
                reply_markup=keyboard
            )

        elif message.photo:
            await bot.send_photo(
                ADMIN_ID,
                message.photo[-1].file_id,
                caption=f"{messages[f'new_msg_{admin_lang}']}\n\n{user_info}",
                reply_markup=keyboard
            )

        elif message.video:
            await bot.send_video(
                ADMIN_ID,
                message.video.file_id,
                caption=f"{messages[f'new_msg_{admin_lang}']}\n\n{user_info}",
                reply_markup=keyboard
            )

        elif message.voice:
            await bot.send_voice(
                ADMIN_ID,
                message.voice.file_id,
                caption=f"{messages[f'new_msg_{admin_lang}']}\n\n{user_info}",
                reply_markup=keyboard
            )

        else:
            await message.answer(messages[f"unsupported_{lang}"])
            return

        await message.answer(messages[f"forwarded_{lang}"])

    except Exception as e:
        print(f"Xato: {e}")


# 🔹 Admin “Ответить / Javob berish”
@dp.callback_query(F.data.startswith("reply_"))
async def reply_button(callback: types.CallbackQuery, state: FSMContext):

    admin_lang = admin_language.get("lang", "uz")
    user_id = int(callback.data.split("_")[1])

    await state.update_data(target_id=user_id)
    await state.set_state(ReplyState.waiting_for_reply)

    await callback.message.answer(
        f"{messages[f'reply_write_{admin_lang}']}\n🆔 <code>{user_id}</code>",
        parse_mode="HTML"
    )

    await callback.answer()


# 🔹 Admin javobi foydalanuvchiga boradi
@dp.message(ReplyState.waiting_for_reply)
async def send_reply(message: types.Message, state: FSMContext):

    admin_lang = admin_language.get("lang", "uz")
    data = await state.get_data()

    user_id = data.get("target_id")

    try:
        if message.text:
            await bot.send_message(user_id, message.text)

        elif message.photo:
            await bot.send_photo(user_id, message.photo[-1].file_id)

        elif message.video:
            await bot.send_video(user_id, message.video.file_id)

        elif message.voice:
            await bot.send_voice(user_id, message.voice.file_id)

        else:
            await message.answer(messages[f"send_error_{admin_lang}"])
            return

        await message.answer(messages[f"reply_sent_{admin_lang}"])

    except TelegramForbiddenError:
        await message.answer(messages[f"user_blocked_{admin_lang}"])

    except Exception as e:
        await message.answer(f"Xato: {e}")

    await state.clear()


# 🔄 RUN BOT
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
