import os
import aiohttp

PROMPTCHAN_API_KEY = os.getenv("PROMPTCHAN_API_KEY")
BASE_URL = "https://prod.aicloudnetservices.com"
ENDPOINT = "/api/external/create"

async def generate_nsfw_image(prompt: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "x-api-key": PROMPTCHAN_API_KEY
    }

    payload = {
        "prompt": prompt,
        "negativePrompt": "ugly, blurry, distorted, watermark",
        "model": "realistic",  # You can try: 'realistic', 'hentai', 'anime', etc.
        "width": 768,
        "height": 1024,
        "scheduler": "DPM++ 2M Karras",
        "steps": 30,
        "scale": 7.5,
        "samples": 1,
        "nsfw": True
    }

    url = f"{BASE_URL}{ENDPOINT}"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"Promptchan API failed. Status: {resp.status}")
            data = await resp.json()

            # ✅ Corrected here — use 'image' key directly
            try:
                image_url = data["image"]
                return image_url
            except KeyError:
                raise Exception(f"⚠️ Unexpected response format from Promptchan:\n{data}")
