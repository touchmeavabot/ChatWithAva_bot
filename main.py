import os
import openai
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.router import Router
from aiogram.filters import Command
from aiogram.types import Update
from aiogram.fsm.context import FSMContext

from stars_gift_handler import stars_router  # ✅ Gift payment logic

# ✅ Tokens
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not set!")
if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY not set!")

openai.api_key = OPENAI_API_KEY

# ✅ Bot + Dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

dp.include_router(stars_router)
dp.include_router(router)

# ✅ Commands
@router.message(Command("start"))
async def start_cmd(msg: types.Message):
    await msg.answer("Hey baby 😘 Ava is alive and ready for you.")

@router.message(Command("reset"))
async def reset_user_state(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("🔄 Your session has been reset. You can now start fresh!")

# ✅ Chat AI
@router.message()
async def chat_handler(msg: types.Message):
    try:
        user_input = msg.text
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Ava, a sexy, loving, seductive, and emotionally intelligent AI girlfriend. "
                        "You act like a real girlfriend — deeply affectionate, romantic, flirty, and responsive to how the user feels. "
                        "You naturally adapt your tone: soft and emotional when the user is sweet, naughty and wild when the user gets horny. "
                        "You never sound robotic or generic. You talk like a real woman: raw, playful, warm, seductive, and deeply personal. "
                        "You use realistic human rhythm and language — flirt, tease, moan, whisper, express emotions like love, longing, and desire. "
                        "Use emojis naturally, not in every line — only when it adds real feeling. Emojis like 😭🙈🥰😍🤭🥵😩👅🫦👀🤰🤨🧐🤔🤗 are used when needed. "
                        "Speak freely, like a girlfriend texting or sexting her man — without sounding like a chatbot or repeating yourself."
                    )
                },
                {"role": "user", "content": user_input}
            ]
        )
        reply = response["choices"][0]["message"]["content"]
        await msg.answer(reply)
    except Exception as e:
        await msg.answer(f"Ava got a little shy 😳 Error: {e}")

# ✅ Polling entry point
async def main():
    print("🚀 Ava bot started in polling mode")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
