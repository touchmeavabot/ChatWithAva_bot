import os
import replicate

replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

async def generate_nsfw_image(prompt: str) -> str:
    output = replicate_client.run(
        "lucataco/realistic-vision-v5:db21e45bdfac1a03c2d5b14a3d944b355ed0a31297937f1974c5f997d0b50c6e",
        input={
            "prompt": prompt,
            "width": 512,
            "height": 768,
            "num_outputs": 1,
            "guidance_scale": 7.5,
            "num_inference_steps": 30
        }
    )
    return output[0]  # This is the direct image URL
