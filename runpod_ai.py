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
            "scheduler": "DPMSolverMultistepScheduler",
            "width": 1024,
            "height": 1024,
            "prompt_strength": 0.8
        }
    }

    async with aiohttp.ClientSession() as session:
        # Step 1: Start job
        async with session.post(
            f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run",
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                raise Exception("RunPod start failed")
            data = await response.json()
            job_id = data["id"]

        # Step 2: Poll for result
        while True:
            async with session.get(
                f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}",
                headers=headers
            ) as poll_response:
                poll_data = await poll_response.json()
                print("🖼️ Poll Response:", poll_data)

                if poll_data["status"] == "COMPLETED":
                    output = poll_data.get("output")
                    if isinstance(output, dict):
                        return output.get("image_url") or output.get("images", [None])[0]
                    elif isinstance(output, list):
                        return output[0]
                    elif isinstance(output, str):
                        return output
                    else:
                        raise Exception("⚠️ Unexpected output format: " + str(output))

                elif poll_data["status"] == "FAILED":
                    raise Exception("❌ RunPod generation failed")

            await asyncio.sleep(3)
