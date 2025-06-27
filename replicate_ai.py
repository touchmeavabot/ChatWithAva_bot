import replicate
import os

replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

async def generate_nsfw_image(prompt: str) -> str:
    output = replicate_client.run(
        "lucataco/realistic-vision-nsfw:ced99ce40313907b7f99200fc9085adf6bc65280e1c5512ae1586d2742f9fe6b",
        input={
            "prompt": prompt,
            "width": 512,
            "height": 768,
            "num_outputs": 1,
            "guidance_scale": 7.5,
            "num_inference_steps": 30
        }
    )
    return output[0]
