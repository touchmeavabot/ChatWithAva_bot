import replicate
import os

# Set token from environment
replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

# Generate NSFW image
async def generate_nsfw_image(prompt: str) -> str:
    output = replicate_client.run(
        "lucataco/realistic-vision-v5:acdfed9c44297cd448cc61698a8ed822c64db55c3ff857d4b11871cd6e8bff5e",
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
