import os
import requests
import time

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")  # You can hardcode if you want

def generate_nsfw_image(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }

    payload = {
        "input": {
            "prompt": prompt,
            "negative_prompt": "ugly, blurry, watermark",
            "width": 512,
            "height": 768,
            "guidance_scale": 7.5,
            "num_inference_steps": 30
        }
    }

    response = requests.post(
        f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    job_id = response.json()["id"]

    # Polling
    while True:
        poll = requests.get(
            f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}",
            headers=headers
        ).json()

        if poll["status"] == "COMPLETED":
            return poll["output"]["image_url"]
        elif poll["status"] == "FAILED":
            raise Exception("RunPod generation failed.")

        time.sleep(3)
