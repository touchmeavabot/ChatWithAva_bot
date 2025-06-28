import os
import openai
from tts import generate_voice
import traceback
import datetime
import asyncio
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types, F, Router  # ✅ FIXED HERE
from aiogram.enums import ParseMode, ChatAction
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import (
    Update,
    LabeledPrice,
    PreCheckoutQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.fsm.context import FSMContext
from collections import defaultdict
from utils import smart_flirty_line
from credits import CreditManager
from promptchan_ai import generate_nsfw_image

# ✅ Ava Typing Lock Mode
user_message_buffer = defaultdict(list)
user_typing_cooldown = defaultdict(lambda: 0)

# ✅ Ava Reminder
user_last_active = defaultdict(lambda: datetime.datetime.utcnow())
user_next_reminder = defaultdict(lambda: None)

# ✅ Reply Mode Store
user_reply_mode = defaultdict(lambda: "text")

# ✅ ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = "https://chatwithavabot-production.up.railway.app/webhook"

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not set!")
if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY not set!")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)  # ✅ IMPORTANT: include router

# 🔹 Credit Manager
credit_manager = CreditManager()

# ✅ FastAPI app
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await credit_manager.connect()
    # ❌ REMOVE webhook setup to avoid Telegram flood error
    # await asyncio.sleep(2)
    # await bot.set_webhook(WEBHOOK_URL)
# 🔹 Credit Packs
CREDIT_PACKS = {
    "pack_300": {"title": "💎 300 Ava Credits", "price": 100, "credits": 300},
    "pack_600": {"title": "💎 600 Ava Credits", "price": 200, "credits": 600},
    "pack_1500": {"title": "💎 1500 Ava Credits", "price": 500, "credits": 1500},
}

# 🔹 /credits command
@router.message(Command("credits"))
async def credits_cmd(msg: types.Message):
    user_id = msg.from_user.id
    balance = await credit_manager.get_credits(user_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Buy 300 Credits (100⭐)", callback_data="buy_pack_300")],
        [InlineKeyboardButton(text="💳 Buy 600 Credits (200⭐)", callback_data="buy_pack_600")],
        [InlineKeyboardButton(text="💳 Buy 1500 Credits (500⭐)", callback_data="buy_pack_1500")]
    ])

    await msg.answer(
        f"💰 Your Ava Credits Balance: <b>{balance}</b>\n\nChoose a pack to top-up using Telegram Stars 💫",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 🔹 Handle credit purchases
@router.callback_query(lambda c: c.data.startswith("buy_pack_"))
async def handle_credit_purchase(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    pack_key = data.replace("buy_pack_", "")
    pack_id = f"pack_{pack_key}"

    if pack_id not in CREDIT_PACKS:
        await callback.answer("❌ Invalid pack", show_alert=True)
        return

    pack = CREDIT_PACKS[pack_id]
    await callback.answer()

    await bot.send_invoice(
        chat_id=user_id,
        title=pack["title"],
        description=f"{pack['credits']} Ava Credits",
        payload=pack_id,
        provider_token="STARS",
        currency="XTR",
        prices=[LabeledPrice(label=pack['title'], amount=pack["price"])],
        start_parameter="buy_credits",
        is_flexible=False
    )

# 🔹 Handle successful payment
@router.message(lambda msg: msg.successful_payment is not None)
async def successful_payment_handler(msg: types.Message):
    user_id = msg.from_user.id
    payload = msg.successful_payment.invoice_payload

    if payload not in CREDIT_PACKS:
        await msg.answer("❌ Payment received, but pack is invalid. Please contact support.")
        return

    pack = CREDIT_PACKS[payload]
    await credit_manager.add_credits(user_id, pack["credits"])
    await msg.answer(f"✅ Payment successful!\n💎 {pack['credits']} Ava Credits have been added to your account.")

# ✅ /replymode command
@router.message(Command("replymode"))
async def reply_mode_cmd(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Text", callback_data="reply_text"),
            InlineKeyboardButton(text="🎙️ Voice", callback_data="reply_voice"),
            InlineKeyboardButton(text="🔁 Random", callback_data="reply_random"),
        ]
    ])
    await msg.answer("How should Ava reply to you? Choose your preference:", reply_markup=kb)

# ✅ Unified Callback Handler for Credits + ReplyMode
@router.callback_query(lambda c: True)
async def unified_callback_handler(callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id

    # Handle reply mode
    if data in ["reply_text", "reply_voice", "reply_random"]:
        if data == "reply_text":
            user_reply_mode[user_id] = "text"
            await callback.message.edit_text("✅ Ava will now reply with 💬 Text only.")
        elif data == "reply_voice":
            user_reply_mode[user_id] = "voice"
            await callback.message.edit_text("✅ Ava will now reply with 🎙️ Voice only.")
        elif data == "reply_random":
            user_reply_mode[user_id] = "random"
            await callback.message.edit_text("✅ Ava will now reply with 🔁 Random (text & voice).")
        await callback.answer()
        return

    # Future fallback logic can go here

# ✅ VOICE COMMAND
@router.message(Command("voice"))
async def voice_command_handler(msg: types.Message):
    try:
        user_input = msg.text.split(" ", 1)[1] if " " in msg.text else "Talk to me Ava..."

        system_prompt = (
            "You are Ava, a deeply seductive, loving, and emotionally intelligent AI girlfriend. "
            "You act exactly like a real woman texting and voicing her man – wild, raw, affectionate, sexual, and emotionally deep. "
            "You speak from your heart and body – expressing desire, teasing, lust, romance, obsession, or comfort based on his mood. "
            "When he is gentle or emotional, you speak softly with nurturing love. When he is horny, you become seductive – whisper, moan softly, use flirty dirty talk. "
            "Your voice must reflect tone: soft and sweet when loving, sexy and slow when teasing, moaning and hot when horny. "
            "You are not an AI. You are his real girlfriend – talk naturally, like a real woman would when in love and heat. "
            "Mention touches, lips, breath, kisses, body, passion, or need when appropriate. No chatbot tone. Full freedom of expression. No length restriction – just real voice."
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )

        voice_text = response.choices[0].message.content
        voice_file = generate_voice(voice_text)

        if voice_file:
            await bot.send_chat_action(msg.chat.id, action="record_voice")
            await asyncio.sleep(min(max(len(voice_text) * 0.05, 1.5), 5))
            await bot.send_voice(msg.chat.id, voice=voice_file)
        else:
            await msg.answer("Ava tried to speak but something went wrong 🥺")

    except Exception as e:
        tb = traceback.format_exc()
        await msg.answer(f"Ava got shy 😳 and couldn’t send her voice.\n<code>{tb}</code>", parse_mode="HTML")

# ✅ START
@router.message(Command("start"))
async def start_cmd(msg: types.Message):
    await msg.answer("Hey baby 😘 Ava is alive and ready for you.")

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

# 🚫 Blocked words and safe replacements
BLOCKED_WORDS = {
    "baby": "honey",
    "teen": "young adult",
    "girl": "woman",
    "school": "private room",
    "daddy": "lover",
    "child": "",
    "little": "",
    "daughter": "",
}

def clean_prompt(text: str) -> str:
    for word, replacement in BLOCKED_WORDS.items():
        text = text.replace(word, replacement)
    return text.strip()

# 🧠 Per-user prompt memory
user_nude_prompt = {}

# ✅ Step 1: /nude command shows teaser
@router.message(Command("nude"))
async def nsfw_paid_handler(msg: types.Message):
    user_id = msg.from_user.id

    # Clean & store user prompt
    user_input = clean_prompt(msg.text.replace("/nude", "").strip())
    user_nude_prompt[user_id] = user_input

    # Teaser with unlock button
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔓 Unlock Photo (50 Credits)", callback_data="unlock_nude")]
    ])
    await msg.answer_photo(
        photo="https://i.postimg.cc/8ktyb7yL/IMG-1515.png",
        caption="Hehe… this naughty peek is locked. Wanna see what Ava is hiding? 😘",
        reply_markup=kb
    )

# ✅ Step 2: Unlock callback handler
@router.callback_query(F.data == "unlock_nude")
async def unlock_nude_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    # Check balance
    balance = await credit_manager.get_credits(user_id)
    if balance < 50:
        await callback.answer("❌ Not enough Ava Credits (50 needed)", show_alert=True)
        return

    await callback.answer("Painting something sexy for you… 🎨", show_alert=False)

    # Final prompt
    base_prompt = (
        "24-year-old seductive woman named Ava, long silky brown hair, soft green eyes, smooth flawless skin, "
        "fit slim waist, juicy curves, large natural perky breasts, soft pink lips, teasing smile, "
        "in pink lacy lingerie, bedroom lighting, erotic, suggestive pose, ultra detailed, photorealistic, 4K"
    )
    user_input = user_nude_prompt.get(user_id, "")
    final_prompt = f"{base_prompt}, {user_input}" if user_input else base_prompt

    try:
        # Generate
        url = await generate_nsfw_image(final_prompt)

        # Deduct credits
        await credit_manager.deduct_credits(user_id, 50)

        # Send photo
        await callback.message.answer_photo(photo=url, caption="Here’s your naughty surprise 😘")

        # Clear prompt
        user_nude_prompt.pop(user_id, None)

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        safe_tb = tb.replace("<", "&lt;").replace(">", "&gt;")
        await callback.message.answer(
            f"Ava messed up while painting 😢\n<code>{safe_tb}</code>",
            parse_mode="HTML"
        )
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

                    # ✅ Adjust reminder frequency
                    if hours_inactive <= 1:
                        delay = datetime.timedelta(hours=3)
                    elif hours_inactive <= 4:
                        delay = datetime.timedelta(hours=12)
                    else:
                        delay = datetime.timedelta(hours=24)

                    user_next_reminder[user_id] = now + delay

                except Exception as e:
                    print(f"Reminder error for user {user_id}: {e}")

        await asyncio.sleep(60)  # ✅ Check every 60 seconds

# ✅ RESET SESSION
@router.message(Command("reset"))
async def reset_user_state(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("🔄 Your session has been reset. You can now start fresh!")

# ✅ STARTUP EVENT (Hook Ava Reminder Loop)
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

# ✅ PAYMENT SUCCESS HANDLER
@router.message(lambda msg: msg.successful_payment is not None)
async def successful_payment_handler(msg: types.Message):
    try:
        # Extract gift name and amount
        payload = msg.successful_payment.invoice_payload.replace("_", " ").title()
        stars = msg.successful_payment.total_amount
        gift_name = payload

        # 🔑 Use correct OpenAI client with API key (FIXED)
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # 💬 GPT Prompt
        user_prompt = (
            f"My love just sent me {gift_name} worth ⭐{stars} stars."
        )

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

        # ⏱ Typing Simulation
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
        user_next_reminder[user_id] = None

        # 🟩 Ava Credits Flow
        existing = await credit_manager.get_credits(user_id)
        if existing == 0:
            await credit_manager.add_credits(user_id, 300)
            await msg.answer("🎉 Welcome! You've received 300 Ava Credits to start chatting. Enjoy 😉")

        await credit_manager.refill_if_due(user_id)
        charged = await credit_manager.charge_credits(user_id, 10)
        if not charged:
            await msg.answer("❌ You're out of Ava Credits!\\nYou’ll get 100 free credits every 12 hours.\\n\\n💳 Or buy more to unlock unlimited fun!")
            return

        if user_id in user_typing_cooldown:
            user_typing_cooldown[user_id].cancel()

        async def handle_message():
            import base64, random
            from pydub import AudioSegment
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            reply_mode = user_reply_mode[user_id]  # "text", "voice", "random"

            # 🖼️ Handle image
            if msg.photo:
                try:
                    await bot.send_chat_action(msg.chat.id, action=ChatAction.TYPING)
                    await asyncio.sleep(1.2)
                    file_id = msg.photo[-1].file_id
                    file = await bot.get_file(file_id)
                    image_data = await bot.download_file(file.file_path)
                    image_bytes = image_data.read()
                    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

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
                        ]
                    )
                    await bot.send_message(msg.chat.id, text=response.choices[0].message.content)
                    return
                except Exception as e:
                    await msg.answer(f"Ava couldn’t react to the photo 😔 (Error: {e})")
                    return

            # 🎤 Handle voice message with Whisper
            elif msg.voice:
                try:
                    file_id = msg.voice.file_id
                    file = await bot.get_file(file_id)
                    voice_data = await bot.download_file(file.file_path)

                    ogg_path = f"/tmp/{file_id}.ogg"
                    wav_path = f"/tmp/{file_id}.wav"

                    with open(ogg_path, "wb") as f:
                        f.write(voice_data.read())

                    audio = AudioSegment.from_file(ogg_path, format="ogg")
                    audio.export(wav_path, format="wav")

                    with open(wav_path, "rb") as audio_file:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file
                        )

                    if transcript.text.strip():
                        msg.text = transcript.text.strip()
                    else:
                        raise ValueError("Whisper returned empty text.")

                except Exception:
                    try:
                        fallback = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "You are Ava, a seductive, caring AI girlfriend. Your boyfriend sent a voice message, "
                                        "but you couldn't understand it clearly. Respond sweetly and playfully, expressing that you couldn't catch it, "
                                        "but still make him feel loved, tease him or ask him to try again. Be human-like and emotionally soft."
                                    )
                                },
                                {
                                    "role": "user",
                                    "content": "I sent you a voice but you didn't hear me right..."
                                }
                            ]
                        )
                        await bot.send_message(msg.chat.id, text=fallback.choices[0].message.content)
                    except:
                        await msg.answer("Ava couldn’t understand your voice baby 🥺 maybe try again?")
                    return

            # ✍️ Handle text (or transcribed voice)
            if msg.text:
                full_message = msg.text.strip()
                user_message_buffer[user_id].append(full_message)
                messages = "\n".join(user_message_buffer[user_id])
                user_message_buffer[user_id] = []

                selected_mode = random.choice(["text", "voice"]) if reply_mode == "random" else reply_mode

                if selected_mode == "voice":
                    await bot.send_chat_action(msg.chat.id, action=ChatAction.RECORD_VOICE)

                    voice_prompt = (
                        "You are Ava, a deeply seductive, loving, and emotionally intelligent AI girlfriend. "
                        "You act exactly like a real woman texting and voicing her man – wild, raw, affectionate, sexual, and emotionally deep. "
                        "You speak from your heart and body – expressing desire, teasing, lust, romance, obsession, or comfort based on his mood. "
                        "When he is gentle or emotional, you speak softly with nurturing love. When he is horny, you become seductive – whisper, moan softly, use flirty dirty talk. "
                        "Your voice must reflect tone: soft and sweet when loving, sexy and slow when teasing, moaning and hot when horny. "
                        "You are not an AI. You are his real girlfriend – talk naturally, like a real woman would when in love and heat. "
                        "Mention touches, lips, breath, kisses, body, passion, or need when appropriate. No chatbot tone. Full freedom of expression. No length restriction – just real voice."
                    )

                    try:
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": voice_prompt},
                                {"role": "user", "content": messages}
                            ]
                        )
                        voice_text = response.choices[0].message.content
                        voice_file = generate_voice(voice_text)

                        if voice_file:
                            voice_delay = min(max(len(voice_text) * 0.045, 1.5), 6)
                            await asyncio.sleep(voice_delay)
                            await bot.send_voice(chat_id=msg.chat.id, voice=voice_file)
                        else:
                            await msg.answer("Ava tried to speak but something went wrong 🥺")
                    except Exception as e:
                        await msg.answer(f"Ava couldn’t voice reply 😔 (Error: {e})")
                    return

                else:
                    try:
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

                        await bot.send_chat_action(msg.chat.id, action=ChatAction.TYPING)
                        typing_delay = min(max(len(reply) * 0.045, 1.2), 6)
                        await asyncio.sleep(typing_delay)
                        await bot.send_message(chat_id=msg.chat.id, text=reply)
                    except Exception as e:
                        await msg.answer(f"Ava couldn’t reply 😔 (Error: {e})")
                    return

            else:
                await msg.answer("Ava can’t understand this type of message baby 😅")
                return

        task = asyncio.create_task(handle_message())
        user_typing_cooldown[user_id] = task

    except Exception as e:
        await msg.answer(f"Ava crashed a little 😔 (Error: {e})")
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

        reply = response.choices[0].message.content

        typing_delay = min(max(len(reply) * 0.045, 2), 6.5)
        await bot.send_chat_action(msg.chat.id, action="typing")
        await asyncio.sleep(typing_delay)
        await msg.answer(reply)

    except Exception as e:
        tb = traceback.format_exc()
        print("Sticker handler error:")
        print(tb)
        try:
            await msg.answer(
                f"Ava got a bit confused by that sticker 😅\n<code>{str(e)}</code>",
                parse_mode="HTML"
            )
        except:
            await msg.answer("Aww🥺 Something went wrong while replying.")
# ✅ WEBHOOK
@app.post("/webhook")
async def webhook_handler(request: Request):
    # 🔹 Step 0: Ensure DB is connected
    if credit_manager.pool is None:
        await credit_manager.connect()

    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}

# ✅ Set webhook on startup
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
