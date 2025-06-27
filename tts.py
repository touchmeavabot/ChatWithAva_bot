# 🔄 FIXED version of generate_voice
def generate_voice(text: str, filename: str = "ava_voice.mp3"):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="shimmer",
            input=text
        )
        os.makedirs("voices", exist_ok=True)
        output_path = f"voices/{filename}"
        response.stream_to_file(output_path)
        return types.FSInputFile(output_path)  # ✅ Return as file object
    except Exception as e:
        print(f"[TTS ERROR] {e}")
        return None
