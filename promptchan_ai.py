import aiohttp
import os
import asyncio

API_KEY = os.getenv("PROMPTCHAN_API_KEY")
BASE_URL = "https://prod.aicloudnetservices.com/"

async def generate_nsfw_image(prompt: str) -> str:
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": prompt,
        "negative_prompt": "low quality, blurry, watermark",
        "sampler": "Euler a",
        "width": 512,
        "height": 768,
        "cfg_scale": 7,
        "steps": 30,
        "n": 1
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(BASE_URL + "v1/generate", headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"Promptchan API failed. Status: {resp.status}")
            data = await resp.json()

            # Check and return image URL
            if "data" in data and len(data["data"]) > 0 and "url" in data["data"][0]:
                return data["data"][0]["url"]
            else:
                raise Exception(f"❌ Failed to get image URL: {data}")
