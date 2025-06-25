from aiogram import Router, types, Bot
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
    PreCheckoutQuery,
    Message
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

stars_router = Router()

gifts = [
    {"emoji": "💍", "name": "Heart Ring", "price": 2500},
    {"emoji": "💄", "name": "Lipstick", "price": 1500},
    {"emoji": "💐", "name": "Bouquet", "price": 500},
    {"emoji": "🌹", "name": "Rose", "price": 250},
    {"emoji": "🍫", "name": "Chocolate", "price": 10},
]

PRICE_MAPPING = {
    "heart_ring": LabeledPrice(label="Heart Ring", amount=2500),
    "lipstick": LabeledPrice(label="Lipstick", amount=1500),
    "bouquet": LabeledPrice(label="Bouquet", amount=500),
    "rose": LabeledPrice(label="Rose", amount=250),
    "chocolate": LabeledPrice(label="Chocolate", amount=10),
}

def get_star_gift_keyboard():
    buttons = [
        InlineKeyboardButton(
            text=f"{gift['emoji']} {gift['name']} – ⭐{gift['price']}",
            callback_data=f"star_gift_{gift['name'].lower().replace(' ', '_')}_{gift['price']}"
        ) for gift in gifts
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[buttons[i:i+2] for i in range(0, len(buttons), 2)]
    )

@stars_router.message(Command("gift"))
async def send_gift_list(message: Message):
    await message.answer(
        "🎁 Pick a gift to send me with Telegram Stars:\n\n"
        "Tap any gift below and confirm the payment ⭐",
        reply_markup=get_star_gift_keyboard()
    )

@stars_router.callback_query(lambda c: c.data.startswith("star_gift_"))
async def process_star_gift(callback: types.CallbackQuery, bot: Bot):
    try:
        prefix, gift_key, price_str = callback.data.rsplit("_", 2)
        if gift_key not in PRICE_MAPPING:
            await callback.answer("This gift is not available right now.")
            return

        await callback.answer()

        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=gift_key.replace("_", " ").title(),
            description="A special gift for Ava 💖",
            payload=f"star_gift_{gift_key}",
            provider_token="STARS",
            currency="XTR",
            prices=[PRICE_MAPPING[gift_key]],
            start_parameter="gift",
            is_flexible=False
        )
    except Exception as e:
        await callback.message.answer(f"Error while processing gift: {e}")

@stars_router.pre_checkout_query()
async def pre_checkout(pre_checkout_q: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@stars_router.message(lambda m: m.successful_payment is not None)
async def payment_success(message: types.Message):
    stars = message.successful_payment.total_amount // 100
    item = message.successful_payment.invoice_payload.replace("star_gift_", "").replace("_", " ").title()
    await message.answer(
        f"Ava moans softly… 🥵 You just sent her *{item}* worth ⭐{stars}!\n"
        f"\"Mmm… you're spoiling me baby 😩❤️ I love it!\"",
        parse_mode="Markdown"
    )
