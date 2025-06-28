# reply_mode_manager.py

# You can store user reply modes in memory (temporary) or DB (permanent)
user_reply_modes = {}

async def get_reply_mode(user_id: int) -> str:
    return user_reply_modes.get(user_id, "Text")  # default to Text

async def set_reply_mode(user_id: int, mode: str):
    user_reply_modes[user_id] = mode
