import os
import requests
from aiogram import types

# ✅ Set your ElevenLabs API key (make sure it's in environment or hardcoded if testing)
ELEVENLABS_API_KEY = os.getenv("ELEVEN_API_KEY")

# ✅ ElevenLabs TTS voice ID – you can change this to any better sounding female voice
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Default: Rachel (realistic female). Change if needed.

def generate_voice(text: str, filename: str = "ava_voice.mp3"):
    try:
        os.makedirs("voices", exist_ok=True)
        output_path = f"voices/{filename}"

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",  # or "eleven_multilingual_v2"
            "voice_settings": {
                "stability": 0.4,
                "similarity_boost": 0.7
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return types.FSInputFile(output_path)
        else:
            print(f"[TTS ERROR] Status Code: {response.status_code}, Body: {response.text}")
            return None

    except Exception as e:
        print(f"[TTS ERROR] {e}")
        return None
