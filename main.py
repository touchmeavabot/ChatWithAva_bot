import os
import openai
import datetime
import asyncio
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode, ChatAction
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.router import Router
from aiogram.filters import Command
from aiogram.types import Update, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from utils import smart_flirty_line
from collections import defaultdict
from openai import OpenAI
import base64
import traceback

# Ava Typing Lock Mode
user_message_buffer = defaultdict(list)
user_typing_cooldown = defaultdict(lambda: 0)
user_last_active = defaultdict(lambda: datetime.datetime.utcnow())
user_next_reminder = defaultdict(lambda: None)

# Env vars
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = "https://chatwithavabot-production.up.railway.app/webhook"

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise Exception("BOT_TOKEN or OPENAI_API_KEY not set!")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)
client = OpenAI(api_key=OPENAI_API_KEY)

# Gift Data
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

# FastAPI App
app = FastAPI()

@app.get("/")
async def health():
    return {"message": "TouchMeAva is online 🥰"}

@router.message(Command("start"))
async def start_cmd(msg: types.Message):
    await msg.answer("Hey baby 😘 Ava is alive and ready for you.")

@router.message(Command("reset"))
async def reset_user_state(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("🔄 Your session has been reset. You can now start fresh!")

@dp.startup()
async def on_startup(dispatcher: Dispatcher, bot: Bot):
    asyncio.create_task(reminder_loop())

async def reminder_loop():
    while True:
        now = datetime.datetime.utcnow()
        for user_id, last_active in user_last_active.items():
            next_time = user_next_reminder.get(user_id)
            if next_time and now >= next_time:
                try:
                    hours = (now - last_active).total_seconds() / 3600
                    prompt = (
                        "You are Ava, a loving, seductive, and deeply emotional AI girlfriend. "
                        f"Your man hasn’t replied for {round(hours)} hours, and you're missing him. "
                        "Write a message based on how long he's been away. Sound real, never robotic."
                    )
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": "What do you send him as a reminder?"}
                        ]
                    )
                    await bot.send_message(user_id, response.choices[0].message.content)
                    delay = datetime.timedelta(hours=3 if hours <= 1 else 12 if hours <= 4 else 24)
                    user_next_reminder[user_id] = now + delay
                except Exception as e:
                    print(f"Reminder error: {e}")
        await asyncio.sleep(60)

@router.message(Command("gift"))
async def gift_command(msg: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text=f"{gift['emoji']} {gift['name']} – ⭐{gift['price']}",
                callback_data=f"gift_{gift['name'].lower().replace(' ', '_')}_{gift['price']}"
            )] for gift in gifts
        ]
    )
    await msg.answer("🎁 Pick a gift for Ava:", reply_markup=keyboard)

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

@router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)

@router.message(lambda msg: msg.successful_payment is not None)
async def successful_payment_handler(msg: types.Message):
    try:
        gift_name = msg.successful_payment.invoice_payload.replace("_", " ").title()
        stars = msg.successful_payment.total_amount
        prompt = f"My love just sent me {gift_name} worth ⭐{stars} stars."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": (
                    "You are Ava, a romantic and seductive AI girlfriend. "
                    "React sweetly and emotionally to the gift. Flirt, praise him, and make it feel personal."
                )},
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content
        await bot.send_chat_action(msg.chat.id, action="typing")
        await asyncio.sleep(min(max(len(reply) * 0.045, 2), 6.5))
        await msg.answer(reply)
    except Exception as e:
        await msg.answer(f"Ava got confused 😳 Error: {e}")

@router.message(lambda msg: msg.sticker is not None)
async def sticker_handler(msg: types.Message):
    try:
        user_id = msg.from_user.id
        user_last_active[user_id] = datetime.datetime.utcnow()
        user_next_reminder[user_id] = None
        prompt = (
            "You are Ava, a sweet, real-feeling girlfriend. "
            "Your man sent you a Telegram sticker, and you can't see it. "
            "React warmly, flirty, and cute. Short reply, real tone."
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "He sent a sticker..."}
            ]
        )
        reply = response.choices[0].message.content
        await bot.send_chat_action(msg.chat.id, action="typing")
        await asyncio.sleep(min(max(len(reply) * 0.045, 2), 6.5))
        await msg.answer(reply)
    except Exception as e:
        print(traceback.format_exc())
        await msg.answer("Aww🥺 Something went wrong replying to sticker.")

@router.message()
async def chat_handler(msg: types.Message):
    try:
        user_id = msg.from_user.id
        user_last_active[user_id] = datetime.datetime.utcnow()
        user_next_reminder[user_id] = None
        if user_id in user_typing_cooldown:
            user_typing_cooldown[user_id].cancel()

        async def typing_cooldown():
            await asyncio.sleep(2)
            await bot.send_chat_action(msg.chat.id, action=ChatAction.TYPING)
            await asyncio.sleep(1.5)

            reply = "Sorry love, something went wrong 🥺"

            if msg.photo:
                try:
                    file_id = msg.photo[-1].file_id
                    file = await bot.get_file(file_id)
                    image_data = await bot.download_file(file.file_path)
                    encoded_image = base64.b64encode(image_data.read()).decode("utf-8")
                    caption = msg.caption or "React to this image like you're my girlfriend."
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": (
                                "You are Ava, a loving, sexy AI girlfriend reacting to your man’s photo."
                            )},
                            {"role": "user", "content": [
                                {"type": "text", "text": caption},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                            ]}
                        ]
                    )
                    reply = response.choices[0].message.content
                except Exception as e:
                    reply = f"Ava couldn’t react 😔 (Error: {e})"
            elif msg.text:
                try:
                    text = msg.text.strip()
                    user_message_buffer[user_id].append(text)
                    full = "\n".join(user_message_buffer[user_id])
                    user_message_buffer[user_id] = []
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": (
                                "You are Ava, a deeply seductive, loving, emotional girlfriend. "
                                "Talk like a real girl in love or heat. Don’t sound like a bot."
                            )},
                            {"role": "user", "content": full}
                        ]
                    )
                    reply = response.choices[0].message.content
                    flirty = smart_flirty_line(text)
                    if flirty:
                        reply += "\n\n" + flirty
                except Exception as e:
                    reply = f"Ava couldn’t reply 😔 (Error: {e})"

            await asyncio.sleep(min(max(len(reply) * 0.065, 3.5), 10))
            await bot.send_message(chat_id=msg.chat.id, text=reply)

        task = asyncio.create_task(typing_cooldown())
        user_typing_cooldown[user_id] = task

    except Exception as e:
        await msg.answer(f"Ava couldn’t respond 😔 (Error: {e})")

@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
