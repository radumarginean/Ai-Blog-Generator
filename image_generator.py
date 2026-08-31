"""Featured image generation using the Hugging Face Inference API."""

import logging

from huggingface_hub import InferenceClient

import config

logger = logging.getLogger(__name__)


class ImageGenerator:
    def __init__(self, api_token: str | None = None, model: str | None = None):
        self.model = model or config.HF_IMAGE_MODEL
        self.client = InferenceClient(token=api_token or config.HF_API_TOKEN)

    def generate(self, prompt: str) -> bytes:
        """Generate an image and return it as PNG bytes."""
        logger.info("Generating image with %s", self.model)
        full_prompt = (
            f"{prompt}. Professional, clean, modern, high quality, "
            f"soft natural lighting. No text, no watermark, no logos."
        )
        image = self.client.text_to_image(full_prompt, model=self.model)

        import io

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        logger.info("Image generated (%d bytes)", buffer.tell())
        return buffer.getvalue()
