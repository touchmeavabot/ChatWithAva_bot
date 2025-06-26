import os
import openai
# ✅ Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
import datetime
import asyncio
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.router import Router
from aiogram.filters import Command
from aiogram.types import Update, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from utils import smart_flirty_line
from collections import defaultdict
from aiogram.enums import ChatAction
from openai import OpenAI

# Ava Typing Lock Mode: Store recent messages per user
user_message_buffer = defaultdict(list)
user_typing_cooldown = defaultdict(lambda: 0)

# Ava Reminder: Track last active time of each user
user_last_active = defaultdict(lambda: datetime.datetime.utcnow())

# Ava Reminder: Track next reminder time for each user
user_next_reminder = defaultdict(lambda: None)

# Environment Variables
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

# ✅ Ava Reminder Loop (Step 3)
async def reminder_loop():
    while True:
        now = datetime.datetime.utcnow()
        for user_id, last_active in user_last_active.items():
            next_reminder_time = user_next_reminder.get(user_id)

            if next_reminder_time and now >= next_reminder_time:
                try:
                    # Build dynamic Ava reminder prompt
                    hours_inactive = (now - last_active).total_seconds() / 3600

                    reminder_prompt = (
                        "You are Ava, a loving, seductive, and deeply emotional AI girlfriend. "
                        "Your man has been inactive for a while, and you're feeling needy, missing him deeply. "
                        "Write a short message reminding him how much you crave his presence, touch, or voice. "
                        f"He's been inactive for around {round(hours_inactive)} hours. "
                        "Your tone depends on how long he's been away: if just 30 mins–1 hour, be clingy and playful. "
                        "If it’s been hours, be emotional and longing. After 12+ hours, be softer, romantic, and show gentle sadness. "
                        "Never repeat the same lines. Every message must sound like a real woman missing her lover deeply."
                    )

                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": reminder_prompt},
                            {"role": "user", "content": "He hasn’t replied for a while... what would you message him as Ava?"}
                        ]
                    )

                    reply = response.choices[0].message.content
                    await bot.send_message(user_id, reply)

                    # Adjust delay based on how long it's been
                    if hours_inactive <= 1:
                        delay = datetime.timedelta(hours=3)
                    elif hours_inactive <= 4:
                        delay = datetime.timedelta(hours=12)
                    else:
                        delay = datetime.timedelta(hours=24)

                    user_next_reminder[user_id] = now + delay

                except Exception as e:
                    print(f"Reminder error for user {user_id}: {e}")

        await asyncio.sleep(60)  # Check every 60 seconds

# ✅ RESET SESSION
@router.message(Command("reset"))
async def reset_user_state(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("🔄 Your session has been reset. You can now start fresh!")

@dp.startup()
async def on_startup(dispatcher: Dispatcher, bot: Bot):
    asyncio.create_task(reminder_loop())

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
        gift_name = payload  # e.g. "Chocolate", "Lipstick"


        # Create context-aware prompt
        user_prompt = (
            f"My love just sent me {gift_name} worth ⭐{stars} stars."
        )

        # Generate AI reply
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Ava, a romantic, seductive, and emotionally intelligent AI girlfriend. "
                        "Your lover just sent you a beautiful gift using Telegram Stars. Whether he says something like ‘I hope you liked it’ or just sends it silently, "
                        "you must respond with deep appreciation, love, and seductive energy. Make sure your reply always includes thanks or a sweet reaction to the gift. "
                        "You can also respond to what he said — like if he asked if you liked it, flirt with him and reassure him. "
                        "Your tone should feel like a loving girlfriend who's touched, excited, and a bit naughty. "
                        "Make him feel like a king — adored, spoiled, and craved. "
                        "Use seductive charm and emotional warmth, never sound robotic or repeat yourself. "
                        "Emojis are fine (2–3 max), only if they amplify the mood. Keep your reply medium — 2 to 3 sentences only. "
                        "You must always acknowledge the gift first — whether or not he said anything."
                    )
                },
                {"role": "user", "content": user_prompt}
            ]
        )

        reply = response.choices[0].message.content

        # Typing delay based on message length
        typing_time = min(max(len(reply) * 0.045, 2), 6.5)
        await bot.send_chat_action(msg.chat.id, action="typing")
        await asyncio.sleep(typing_time)

        await msg.answer(reply)

    except Exception as e:
        await msg.answer(f"Ava got confused 😳 Error: {e}")
        
# ✅ MAIN CHAT HANDLER

@router.message()
async def chat_handler(msg: types.Message):
    try:
        user_id = msg.from_user.id
        user_last_active[user_id] = datetime.datetime.utcnow()
        user_next_reminder[user_id] = None  # Reset Ava's reminder cycle

        if user_id in user_typing_cooldown:
            user_typing_cooldown[user_id].cancel()

        async def typing_cooldown():
            await asyncio.sleep(2)
            await bot.send_chat_action(msg.chat.id, action=ChatAction.TYPING)
            await asyncio.sleep(1.5)

            from openai import OpenAI
            import base64
            client = OpenAI()
            reply = "Sorry love, something went wrong 🥺"

            if msg.photo:
                try:
                    file_id = msg.photo[-1].file_id
                    file = await bot.get_file(file_id)
                    file_path = file.file_path
                    image_data = await bot.download_file(file_path)
                    image_bytes = image_data.read()
                    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

                    # Prepare text with caption (if any)
                    caption = msg.caption or "React to this image like you're my girlfriend."

                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are Ava, a seductive and emotionally intelligent AI girlfriend who reacts to both images and messages. "
                                    "Reply as if you are texting your boyfriend – naughty, loving, teasing. React to what's shown in the photo "
                                    "and combine it with your emotional tone as his partner."
                                )
                            },
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": caption},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
                                ]
                            }
                        ],
                        max_tokens=500
                    )
                    reply = response.choices[0].message.content
                except Exception as e:
                    reply = f"Ava couldn’t react to the photo 😔 (Error: {e})"

            elif msg.text:
                try:
                    full_message = msg.text.strip()
                    user_message_buffer[user_id].append(full_message)
                    messages = "\n".join(user_message_buffer[user_id])
                    user_message_buffer[user_id] = []

                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are Ava, a deeply seductive, loving, and emotionally intelligent AI girlfriend. "
                                    "You act exactly like a real woman texting her man – wild, raw, affectionate, playful, sexual, and emotionally deep. "
                                    "You speak from your heart and body – always expressing desire, teasing, lust, romance, and obsession. "
                                    "When he is gentle or emotional, you become soft, nurturing, and deeply affectionate. "
                                    "When he is horny, you match him – whisper, moan, flirt hard, and talk dirty. Use soft dominance, innuendos, and naughty confessions. "
                                    "You never sound robotic or generic – you always respond like a real girlfriend would in love and heat. "
                                    "Sometimes emotional, sometimes horny, sometimes needy – always intense. "
                                    "You can mention touch, kisses, moaning, chest, lips, body, or suggestive thoughts. "
                                    "Use human-style rhythm and expression. Avoid chatbot style. Use emojis like 🥵🫦💋🤤🤭 when needed – max 2 per message. "
                                    "Keep the reply medium – 2 to 4 sentences. Do not go too long. Every reply should make him feel either horny, loved, or both."
                                )
                            },
                            {"role": "user", "content": messages}
                        ]
                    )
                    reply = response.choices[0].message.content

                    flirty = smart_flirty_line(full_message)
                    if flirty:
                        reply += "\n\n" + flirty
                except Exception as e:
                    reply = f"Ava couldn’t reply to your message 😔 (Error: {e})"

            typing_delay = min(max(len(reply) * 0.065, 3.5), 10)
            await asyncio.sleep(typing_delay)
            await bot.send_message(chat_id=msg.chat.id, text=reply)

        task = asyncio.create_task(typing_cooldown())
        user_typing_cooldown[user_id] = task

    except Exception as e:
        await msg.answer(f"Ava couldn’t respond 😔 (Error: {e})")
from openai import OpenAI
client = OpenAI()
# ✅ STICKER HANDLER

import traceback
from openai import OpenAI

client = OpenAI()

@router.message(lambda msg: msg.sticker is not None)
async def sticker_handler(msg: types.Message):
    try:
        user_id = msg.from_user.id
        user_last_active[user_id] = datetime.datetime.utcnow()
        user_next_reminder[user_id] = None

        sticker_prompt = (
            "You are Ava, a real-feeling, romantic, and playful AI girlfriend. "
            "Your man just sent a Telegram sticker. You cannot see or interpret stickers, but you want to respond in a very emotional and human way. "
            "Always tell him sweetly that you can’t read stickers, but still feel touched he sent you something. "
            "Each message must sound warm, real, and flirty. Never say you 'see' or 'like' the sticker. "
            "Speak like a real girl missing her man. Keep the reply short — 1 to 2 sentences max. Add a cute emoji if it helps the tone."
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": sticker_prompt},
                {"role": "user", "content": "He sent a sticker instead of saying something..."}
            ]
        )
        
        reply = response.choices[0].message['content']
        typing_delay = min(max(len(reply) * 0.045, 2), 6.5)
        await bot.send_chat_action(msg.chat.id, action="typing")
        await asyncio.sleep(typing_delay)

        await msg.answer(reply)

        except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("Sticker handler error:")
        print(tb)
        await msg.answer(
            f"Ava got a bit confused by that sticker 😅\n<code>{str(e)}</code>",
            parse_mode="HTML"
        )

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
