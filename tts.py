import os
from openai import OpenAI
from aiogram import types

# ✅ Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ TTS function to generate Ava's voice
def generate_voice(text: str, filename: str = "ava_voice.mp3"):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )
        os.makedirs("voices", exist_ok=True)
        output_path = f"voices/{filename}"
        response.stream_to_file(output_path)
        return types.FSInputFile(output_path)  # Return a Telegram file object
    except Exception as e:
        print(f"[TTS ERROR] {e}")
        return None
