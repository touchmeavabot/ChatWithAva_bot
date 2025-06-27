import os
import replicate

replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

async def generate_nsfw_image(prompt: str) -> str:
    output = replicate_client.run(
        "cjwbw/stable-diffusion:<correct-version-id>",
        input={
            "prompt": prompt,
            "width": 512,
            "height": 768,
            "num_outputs": 1,
            "scheduler": "DPMSolverMultistep",
            "guidance_scale": 7.5,
            "num_inference_steps": 30,
        },
        use_file_output=False  # <<< restores URL behavior
    )
    return output[0]
