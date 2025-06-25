import os
import openai
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.dispatcher.router import Router
from aiogram.filters import Command
from aiogram.types import Update

from stars_gift_handler import stars_router  # ✅ Gift routes

# ✅ Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = "https://chatwithavabot-production.up.railway.app/webhook"

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not set!")
if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY not set!")

openai.api_key = OPENAI_API_KEY

# ✅ Telegram Setup
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

dp.include_router(stars_router)
dp.include_router(router)

app = FastAPI()


# ✅ Health Check
@app.get("/")
async def health():
    return {"message": "TouchMeAva is online 🥰"}


# ✅ Start
@router.message(Command("start"))
async def start_cmd(msg: types.Message):
    await msg.answer("Hey baby 😘 Ava is alive and ready for you.")


# ✅ Reset Handler
@router.message(Command("reset"))
async def reset_user_state(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔄 Your session has been reset. You can now start fresh!")


# ✅ Chat Handler
@router.message()
async def chat_handler(msg: types.Message, state: FSMContext):
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


# ✅ Stars Payment Handlers (backup handlers if main ones fail)
@router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(msg: types.Message):
    item = msg.successful_payment.invoice_payload.replace("_", " ").title()
    stars = msg.successful_payment.total_amount // 100
    await msg.answer(
        f"💖 Ava received your gift: *{item}* worth ⭐{stars}!\n"
        f"You’re spoiling me... I love it 😚",
        parse_mode="Markdown"
    )


# ✅ Webhook Setup
@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
