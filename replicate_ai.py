import os
import replicate

replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

async def generate_nsfw_image(prompt: str) -> str:
    # Use the correct version ID (64-char hash from the Replicate UI)
    model = "cjwbw/stable-diffusion:<correct-version-hash>"

    output = replicate_client.run(
        model,
        input={
            "prompt": prompt,
            "width": 512,
            "height": 768,
            "num_outputs": 1,
            "scheduler": "DPMSolverMultistep",
            "guidance_scale": 7.5,
            "num_inference_steps": 30
        }
    )
    # `output[0]` is a FileOutput object; get its URL from .url
    return output[0].url
