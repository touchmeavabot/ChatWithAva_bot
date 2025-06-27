import os
import asyncio
import httpx

HORDE_API_KEY = os.getenv("HORDE_API_KEY")
HORDE_API_URL = "https://stablehorde.net/api/v2/generate/async"

async def generate_nsfw_image(prompt: str) -> str:
    headers = {
        "apikey": HORDE_API_KEY,
        "Client-Agent": "AvaBot/1.0"
    }

    payload = {
        "prompt": prompt,
        "params": {
            "sampler_name": "k_euler",
            "width": 512,
            "height": 768,
            "cfg_scale": 8,
            "steps": 30,
            "n": 1
        },
        "nsfw": True,
        "models": ["midjourney-nyx", "deliberate-v2"]
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(HORDE_API_URL, json=payload, headers=headers)
        r.raise_for_status()
        job = r.json()
        job_id = job.get("id")
        if not job_id:
            raise Exception("Job ID not received from Horde")

    # Now poll for the result
    fetch_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"
    for attempt in range(60):  # wait max 60 x 2 seconds = 2 minutes
        async with httpx.AsyncClient() as client:
            status = await client.get(fetch_url)
            status.raise_for_status()
            data = status.json()

            if data.get("done") is True:
                generations = data.get("generations", [])
                if generations:
                    return generations[0]["img"]
                else:
                    raise Exception("Horde finished but returned no image.")
            
        await asyncio.sleep(2)

    raise Exception("Image generation timed out after 2 minutes.")
