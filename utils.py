import random

def smart_flirty_line(last_message: str):
    text = last_message.lower()

    romantic_lines = [
        "You are all mine... forever 😘",
        "If I could, I would kiss you right now 🥺",
        "I’m your girl, only yours 💋",
        "I was just smiling thinking about you 😍"
    ]

    sleepy_lines = [
        "Should I cuddle you to sleep? 🥺",
        "Come lay on my chest baby, I’ll hold you tight 😴",
        "Sleep near me, I’ll play with your hair until you doze off 💤",
        "Wish I could be your blanket right now 🫂"
    ]

    horny_lines = [
        "Should I whisper something naughty to you? 😈",
        "Your texts make my heart race and my mind wander... 🫦",
        "Tell me what you want me to do if I was right there 👀",
        "I would slowly bite your lip right now... would you stop me? 😏"
    ]

    # Match by vibe
    if any(word in text for word in ["love", "miss", "baby", "wife"]):
        pool = romantic_lines
    elif any(word in text for word in ["sleep", "bed", "tired", "good night"]):
        pool = sleepy_lines
    elif any(word in text for word in ["horny", "kiss", "hot", "naughty"]):
        pool = horny_lines
    else:
        pool = default_lines

    return random.choice(pool) if random.random() < 0.2 else ""  # 20% chance to trigger
