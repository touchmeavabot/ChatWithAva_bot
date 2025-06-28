from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

credit_gift_router = Router(name="credit_gift")  # Router name

# 🎁 Define credit-based gifts
GIFTS = [
    {"emoji": "💍", "name": "Diamond Ring", "credits": 2500},
    {"emoji": "🐱", "name": "Cute Cat", "credits": 1500},
    {"emoji": "💎", "name": "Necklace", "credits": 1000},
    {"emoji": "🌸", "name": "Flower Crown", "credits": 1000},
    {"emoji": "🎧", "name": "Headphones", "credits": 1000},
    {"emoji": "👠", "name": "Heels", "credits": 750},
    {"emoji": "🐰", "name": "Bunny", "credits": 750},
    {"emoji": "🕺", "name": "Dancer", "credits": 750},
    {"emoji": "👜", "name": "Handbag", "credits": 750},
    {"emoji": "🕯️", "name": "Candle", "credits": 350},
    {"emoji": "💋", "name": "Kiss", "credits": 350},
    {"emoji": "🍓", "name": "Strawberry", "credits": 350},
    {"emoji": "☕", "name": "Coffee", "credits": 350},
    {"emoji": "🔑", "name": "Key to Heart", "credits": 350},
    {"emoji": "🌺", "name": "Hibiscus", "credits": 350},
    {"emoji": "🌹", "name": "Rose", "credits": 250},
    {"emoji": "🍬", "name": "Candy", "credits": 250},
]

# ✅ Build gift keyboard
def get_credit_gift_keyboard():
    buttons = [
        InlineKeyboardButton(
            text=f"{gift['emoji']} for ⭐{gift['credits']}",
            callback_data=f"gift_credit_{gift['name'].lower().replace(' ', '_')}_{gift['credits']}"
        )
        for gift in GIFTS
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)])

# ✅ Button to show the gift list
def get_open_gift_list_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💝 Choose a gift here!", callback_data="open_gift_menu")]
        ]
    )

# 🔘 /gift command
@credit_gift_router.message(Command("gift"))
async def send_credit_gift_menu(message: types.Message):
    await message.answer(
        "💖 How do you want to surprise me?",
        reply_markup=get_open_gift_list_button()
    )

# 🧷 When user taps the button, show full gift list
@credit_gift_router.callback_query(lambda c: c.data == "open_gift_menu")
async def show_full_gift_list(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🤖 Pick a gift to make my day! 💌",
        reply_markup=get_credit_gift_keyboard()
    )
    await callback.answer()
