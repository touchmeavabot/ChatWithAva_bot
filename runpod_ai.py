import os
import aiohttp
import asyncio

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")

async def generate_nsfw_image(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }

    payload = {
        "input": {
            "prompt": prompt,
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
            "scheduler": "DPMSolverMultistepScheduler",  # Required for this model
            "width": 1024,
            "height": 1024,
            "prompt_strength": 0.8
        }
    }

    async with aiohttp.ClientSession() as session:
        # Start job
        async with session.post(
            f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run",
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                raise Exception("RunPod start failed")
            data = await response.json()
            job_id = data["id"]

        # Poll job
        while True:
            async with session.get(
                f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}",
                headers=headers
            ) as poll_response:
                poll_data = await poll_response.json()
                if poll_data["status"] == "COMPLETED":
                    return poll_data["output"]["image_url"]
                elif poll_data["status"] == "FAILED":
                    raise Exception("RunPod generation failed")
            await asyncio.sleep(3)
