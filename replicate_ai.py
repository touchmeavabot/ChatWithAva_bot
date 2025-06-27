import replicate
import os

# Initialize client
replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

# Generate NSFW image using Stable Diffusion public model
async def generate_nsfw_image(prompt: str) -> str:
    output = replicate_client.run(
        "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
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
    return output[0]  # returns the URL
