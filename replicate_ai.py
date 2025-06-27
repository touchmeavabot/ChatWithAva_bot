import replicate
import os

# Set token from env
replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

async def generate_nsfw_image(prompt: str) -> str:
    # Use a valid public model reference with latest version
    model = "lucataco/realistic-vision-v5.1"
    output = replicate_client.run(
        model,
        input={
            "prompt": prompt,
            "width": 512,
            "height": 768,
            "num_outputs": 1,
            "scheduler": "DPMSolverMultistep",
            "guidance_scale": 7.5,
            "num_inference_steps": 30,
        }
    )
    return output[0]
