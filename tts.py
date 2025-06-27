import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_voice(text: str, filename: str = "ava_voice.mp3"):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="shimmer",  # Ava's voice
            input=text
        )
        output_path = f"voices/{filename}"
        os.makedirs("voices", exist_ok=True)
        response.stream_to_file(output_path)
        return output_path
    except Exception as e:
        print(f"[TTS ERROR] {e}")
        return None
