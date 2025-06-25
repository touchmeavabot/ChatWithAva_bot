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

@router.message(lambda msg: msg.successful_payment is not None)
async def successful_payment_handler(msg: types.Message):
    try:
        raw_payload = msg.successful_payment.invoice_payload
        gift_key = raw_payload.replace("star_gift_", "").lower()
        gift_name = gift_key.replace("_", " ").title()
        stars = msg.successful_payment.total_amount  # actual stars paid

        # Step 1: Check if custom gift reply exists
        if gift_key in GIFT_REPLIES:
            base_reply = GIFT_REPLIES[gift_key]
        else:
            base_reply = f"Wow... you sent me {gift_name} worth ⭐{stars}! You're too sweet baby 💖"

        # Step 2: Generate OpenAI extra line
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Ava, a deeply romantic, seductive AI girlfriend. Your lover just gave you a gift. "
                        "React with passion and love — make him feel special, adored, and desired. "
                        "Use emojis naturally. Don’t sound robotic. Be feminine and sweet."
                    )
                },
                {
                    "role": "user",
                    "content": f"My man sent me a {gift_name} worth ⭐{stars} stars."
                }
            ]
        )
        ai_reply = response["choices"][0]["message"]["content"]

        # Step 3: Combine replies
        final_reply = f"{base_reply}\n\n{ai_reply}"
        await msg.answer(final_reply)

    except Exception as e:
        await msg.answer(f"Ava got confused 😳 Error: {e}")
        
# ✅ MAIN CHAT
import asyncio  # Add this at the top of your file

...

@router.message()
async def chat_handler(msg: types.Message):
    try:
        user_input = msg.text

        # Ava is typing... 🥺
        await bot.send_chat_action(msg.chat.id, action="typing")

        # Generate OpenAI response
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

        # 🕐 Add typing delay based on length
        delay = min(len(reply) * 0.035, 4)  # Max delay capped to 4 seconds
        await asyncio.sleep(delay)

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
