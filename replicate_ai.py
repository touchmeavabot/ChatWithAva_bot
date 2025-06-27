import replicate, os

# Set token from env
replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

async def generate_nsfw_image(prompt: str) -> str:
    output = replicate_client.run(
        "stability-ai/stable-diffusion:ac732df8",  # Stable Diffusion 2.1
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
    return output[0]  # This is the image URL
