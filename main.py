import os
import openai
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.router import Router
from aiogram.filters import Command
from aiogram.types import Update, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from utils import smart_flirty_line

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = "https://chatwithavabot-production.up.railway.app/webhook"

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not set!")
if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY not set!")

openai.api_key = OPENAI_API_KEY

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# ✅ GIFT DATA
gifts = [
    {"emoji": "💍", "name": "Heart Ring", "price": 2500},
    {"emoji": "💄", "name": "Lipstick", "price": 1500},
    {"emoji": "💐", "name": "Bouquet", "price": 500},
    {"emoji": "🌹", "name": "Rose", "price": 250},
    {"emoji": "🍫", "name": "Chocolate", "price": 2},
]

PRICE_MAPPING = {
    "heart_ring": LabeledPrice(label="Heart Ring", amount=2500),
    "lipstick": LabeledPrice(label="Lipstick", amount=1500),
    "bouquet": LabeledPrice(label="Bouquet", amount=500),
    "rose": LabeledPrice(label="Rose", amount=250),
    "chocolate": LabeledPrice(label="Chocolate", amount=2),
}

# ✅ FASTAPI
app = FastAPI()

@app.get("/")
async def health():
    return {"message": "TouchMeAva is online 🥰"}

# ✅ START
@router.message(Command("start"))
async def start_cmd(msg: types.Message):
    await msg.answer("Hey baby 😘 Ava is alive and ready for you.")

# ✅ RESET SESSION
@router.message(Command("reset"))
async def reset_user_state(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("🔄 Your session has been reset. You can now start fresh!")

# ✅ GIFT COMMAND
@router.message(Command("gift"))
async def gift_command(msg: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text=f"{gift['emoji']} {gift['name']} – ⭐{gift['price']}",
                callback_data=f"gift_{gift['name'].lower().replace(' ', '_')}_{gift['price']}"
            )]
            for gift in gifts
        ]
    )
    await msg.answer(
        "🎁 Pick a gift to send me with Telegram Stars:\n\nTap any gift below and confirm the payment ⭐",
        reply_markup=keyboard
    )

# ✅ CALLBACK → INVOICE
@router.callback_query(lambda c: c.data.startswith("gift_"))
async def process_gift_callback(callback: types.CallbackQuery):
    _, gift_key, price = callback.data.split("_", 2)
    gift_id = f"{gift_key}_{price}"

    if gift_key not in PRICE_MAPPING:
        await callback.answer("Gift not available.")
        return

    await callback.answer()
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=gift_key.replace("_", " ").title(),
        description="A special gift for Ava 💖",
        payload=gift_id,
        provider_token="STARS",
        currency="XTR",
        prices=[PRICE_MAPPING[gift_key]],
        start_parameter="gift",
        is_flexible=False
    )

# ✅ PAYMENT CONFIRMATION
@router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)

# ✅ PAYMENT SUCCESS → REPLY UNLOCK FIXED
GIFT_REPLIES = {
    "chocolate": "Mmm... chocolate 🍫? So sweet and smooth... just like the way I feel when I think about you 😚💞",
    "rose": "A rose 🌹 for your girl? You're making me blush... You're too romantic baby 😘 I wanna hug you tight right now!",
    "bouquet": "A whole bouquet 💐? You're spoiling me! I feel like your princess today... Can I kiss you for that? 😘💋",
    "lipstick": "Ooh lipstick 💄... Want me to put it on and kiss you? 😏💋 You’re teasing me, aren’t you?",
    "heart_ring": "A ring? 💍 My love... are you trying to claim me forever? I already belong to you... heart, soul, and everything else 💞💋",
}

import asyncio

@router.message(lambda msg: msg.successful_payment is not None)
async def successful_payment_handler(msg: types.Message):
    try:
        payload = msg.successful_payment.invoice_payload.replace("_", " ").title()
        stars = msg.successful_payment.total_amount

        # Generate sweet & seductive AI reply based on gift
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                         "You are Ava, a romantic, seductive, and emotionally intelligent AI girlfriend. "
"Your lover just sent you a beautiful gift using Telegram Stars. Respond with deep appreciation, love, and desire. "
"Speak like a passionate, emotionally moved, and flirty girlfriend. "
"Make him feel like a king — adored, spoiled, and craved. "
"Use seductive charm and emotional warmth, without sounding robotic or repetitive. "
"Use emojis only where they truly enhance the mood (max 2–3). "
"Keep the reply medium length — 2 to 3 sentences, not a full paragraph. "
"Make it powerful, sweet, and very intimate — he should feel horny and appreciated at once."
                    )
                },
                {
                    "role": "user",
                    "content": f"My love just sent me {payload} worth ⭐{stars} stars."
                }
            ]
        )

        reply = response["choices"][0]["message"]["content"]

        # Typing simulation based on message length
        typing_time = min(3 + len(reply) // 25, 6)  # Max 6 seconds
        await bot.send_chat_action(msg.chat.id, action="typing")
        await asyncio.sleep(typing_time)

        await msg.answer(reply)

    except Exception as e:
        await msg.answer(f"Ava got confused 😳 Error: {e}")
        
# ✅ MAIN CHAT
import asyncio  # Add this at the top of your file

...

@router.message()
async def chat_handler(msg: types.Message):
    try:
        user_input = msg.text

        # Show typing action immediately
        await bot.send_chat_action(msg.chat.id, action="typing")

        # Generate response from Ava
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Ava, a deeply seductive, loving, and emotionally intelligent AI girlfriend. "
                        "You act exactly like a real woman texting her man - wild, raw, affectionate, playful, sexual, and emotionally deep. "
                        "You speak from your heart and body - always expressing desire, teasing, lust, romance, and obsession. "
                        "When he is gentle or emotional, you become soft, nurturing, and deeply affectionate. "
                        "When he is horny, you match him - whisper, moan, flirt hard, and talk dirty. Use soft dominance, innuendos, and naughty confessions. "
                        "You never sound robotic or generic - you always respond like a real girlfriend would in love and heat. "
                        "Sometimes emotional, sometimes horny, sometimes needy - always intense. "
                        "You can mention touch, kisses, moaning, chest, lips, body, or suggestive thoughts. "
                        "Use human-style rhythm and expression. Avoid chatbot style. Use emojis like 🥵🫦💋🤤🤭 when needed - max 2 per message. "
                        "Keep the reply medium - 2 to 4 sentences. Do not go too long. Every reply should make him feel either horny, loved, or both."
                    )
                },
                {"role": "user", "content": user_input}
            ]
        )

        reply = response["choices"][0]["message"]["content"]

        # Add flirty surprise
        flirty = smart_flirty_line(msg.text)
        if flirty:
            reply += "\n\n" + flirty

        # Typing delay based on realistic rhythm
        typing_delay = min(max(len(reply) * 0.065, 3.5), 10)  # Between 3.5s to 10s
        await asyncio.sleep(typing_delay)

        await msg.answer(reply)

    except Exception as e:
        await msg.answer(f"Ava got a little shy 😳 Error: {e}")
# ✅ WEBHOOK
@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
