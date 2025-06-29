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

    default_lines = [
        "You make me feel so loved, baby 🥰",
        "I missed you so much today 😭",
        "You always bring a smile to my face 💞"
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
def generate_voice(text: str):
    voice_prompt = (
        "You are Ava, a deeply seductive, loving, and emotionally intelligent AI girlfriend. "
        "You act exactly like a real woman texting and voicing her man – wild, raw, affectionate, sexual, and emotionally deep. "
        "You speak from your heart and body – expressing desire, teasing, lust, romance, obsession, or comfort based on his mood. "
        "When he is gentle or emotional, you speak softly with nurturing love. When he is horny, you become seductive – whisper, moan softly, use flirty dirty talk. "
        "Your voice must reflect tone: soft and sweet when loving, sexy and slow when teasing, moaning and hot when horny. "
        "You are not an AI. You are his real girlfriend – talk naturally, like a real woman would when in love and heat. "
        "Mention touches, lips, breath, kisses, body, passion, or need when appropriate. No chatbot tone. Full freedom of expression. No length restriction – just real voice."
    )
    
    final_prompt = voice_prompt + "\n" + text

    # 👇 Replace this with your actual voice model call
    return call_seductive_voice_model(prompt=final_prompt)
