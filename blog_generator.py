"""Orchestrates a single end-to-end blog post: topic -> content -> image -> publish."""

import logging
import os
from datetime import datetime, timezone

import config
from content_generator import ContentGenerator
from image_generator import ImageGenerator
from topics import TopicRotator
from wordpress_client import PublishResult, WordPressClient

logger = logging.getLogger(__name__)


class BlogGenerator:
    def __init__(
        self,
        rotator: TopicRotator | None = None,
        content_gen: ContentGenerator | None = None,
        image_gen: ImageGenerator | None = None,
        wp_client: WordPressClient | None = None,
    ):
        self.rotator = rotator or TopicRotator()
        self.content_gen = content_gen or ContentGenerator()
        self.image_gen = image_gen or ImageGenerator()
        self.wp_client = wp_client or WordPressClient()

    def run_once(self, topic: str | None = None, save_local: bool = True) -> PublishResult:
        """Generate and publish one blog post. Returns the publish result."""
        topic = topic or self.rotator.next()
        logger.info("=== Generating blog post for: %s ===", topic)

        content = self.content_gen.generate(topic)

        featured_media_id: int | None = None
        try:
            image_bytes = self.image_gen.generate(content.image_prompt)
            if save_local:
                self._save_local(content.slug, image_bytes)
            featured_media_id = self.wp_client.upload_media(
                image_bytes,
                filename=f"{content.slug}.png",
                alt_text=content.title,
            )
        except Exception:  # noqa: BLE001 - image is non-critical, keep publishing
            logger.exception("Image generation/upload failed; publishing without a featured image")

        result = self.wp_client.create_post(
            title=content.title,
            content_html=content.body_html,
            excerpt=content.excerpt,
            slug=content.slug,
            featured_media_id=featured_media_id,
            tag_names=content.tags,
        )
        logger.info("=== Done: %s (%s) ===", result.link or "no link", result.status)
        return result

    @staticmethod
    def _save_local(slug: str, image_bytes: bytes) -> None:
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        path = os.path.join(config.OUTPUT_DIR, f"{stamp}-{slug}.png")
        with open(path, "wb") as fh:
            fh.write(image_bytes)
        logger.debug("Saved image locally to %s", path)
