import replicate
import os

# ✅ Set token from environment variable
replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

# ✅ NSFW image generation function
async def generate_nsfw_image(prompt: str) -> str:
    output = replicate_client.run(
        "cjwbw/stable-diffusion",  # ✅ Use base model name instead of broken version hash
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
    return output[0]  # Returns URL of generated image
