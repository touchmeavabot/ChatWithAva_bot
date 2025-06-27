import replicate, os

# Set token from env
replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

async def generate_nsfw_image(prompt: str) -> str:
    # Use a known public model and version from Replicate
    output = replicate_client.run(
        "stability-ai/stable-diffusion:ac732df8",  # SD 2.1 version  [oai_citation:0‡replicate.com](https://replicate.com/stability-ai/stable-diffusion/versions?utm_source=chatgpt.com) [oai_citation:1‡replicate.com](https://replicate.com/blog/google-imagen-4?utm_source=chatgpt.com) [oai_citation:2‡medium.com](https://medium.com/%40arjunaraneta/creating-an-image-generator-with-streamlit-and-replicate-api-hint-its-pretty-easy-a995ff3d1d0a?utm_source=chatgpt.com) [oai_citation:3‡replicate.com](https://replicate.com/docs/reference/how-does-replicate-work?utm_source=chatgpt.com)
        input={
            "prompt": prompt,
            "width": 512,
            "height": 768,
            "num_outputs": 1,
            "scheduler": "DPMSolverMultistep",
            "guidance_scale": 7.5,
            "num_inference_steps": 30
        },
        use_file_output=False
    )
    # output[0] is the image URL
    return output[0]
