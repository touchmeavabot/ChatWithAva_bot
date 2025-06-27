import replicate
import os

replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

async def generate_nsfw_image(prompt: str) -> str:
    output = replicate_client.run(
        "tstramer/realistic-vision-v5:5c7b6ae5b154cd2f96e5bbcb361d38c5784c20617a3687175b0c49c10ed3e911",
        input={
            "prompt": prompt,
            "width": 512,
            "height": 768,
            "num_inference_steps": 30,
            "guidance_scale": 7.5
        }
    )
    return output[0]
