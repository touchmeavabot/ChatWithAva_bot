from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

credit_gift_router = Router(name="credit_gift")  # 🔥 Better naming for router

# 🎁 Define credit-based gifts
GIFTS = [
    {"emoji": "💍", "name": "Heart Ring", "credits": 50},
    {"emoji": "💄", "name": "Lipstick", "credits": 30},
    {"emoji": "💐", "name": "Bouquet", "credits": 20},
    {"emoji": "🌹", "name": "Rose", "credits": 10},
    {"emoji": "🍫", "name": "Chocolate", "credits": 5},
]

# ✅ Build gift keyboard
def get_credit_gift_keyboard():
    buttons = [
        InlineKeyboardButton(
            text=f"{gift['emoji']} {gift['name']} – {gift['credits']} credits",
            callback_data=f"gift_credit_{gift['name'].lower().replace(' ', '_')}_{gift['credits']}"
        )
        for gift in GIFTS
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)])

# 🔘 /gift command
@credit_gift_router.message(Command("gift"))
async def send_credit_gift_menu(message: types.Message):
    await message.answer(
        "🎁 Send me a gift using your credits:\n\nChoose one below 💕",
        reply_markup=get_credit_gift_keyboard()
    )
