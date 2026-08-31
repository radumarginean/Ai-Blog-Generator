"""Minimal WordPress REST API client for publishing posts with media."""

import logging
from dataclasses import dataclass

import requests
from requests.auth import HTTPBasicAuth

import config

logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    post_id: int
    link: str
    status: str


class WordPressClient:
    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        app_password: str | None = None,
        timeout: int = 60,
    ):
        self.base_url = (base_url or config.WP_BASE_URL).rstrip("/")
        self.api = f"{self.base_url}/wp-json/wp/v2"
        self.auth = HTTPBasicAuth(
            username or config.WP_USERNAME,
            app_password or config.WP_APP_PASSWORD,
        )
        self.timeout = timeout

    def upload_media(self, image_bytes: bytes, filename: str, alt_text: str = "") -> int:
        """Upload an image to the media library and return its attachment ID."""
        logger.info("Uploading media: %s", filename)
        resp = requests.post(
            f"{self.api}/media",
            auth=self.auth,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "image/png",
            },
            data=image_bytes,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        media_id = resp.json()["id"]

        if alt_text:
            requests.post(
                f"{self.api}/media/{media_id}",
                auth=self.auth,
                json={"alt_text": alt_text},
                timeout=self.timeout,
            )
        logger.info("Uploaded media id=%s", media_id)
        return media_id

    def _resolve_tags(self, tag_names: list[str]) -> list[int]:
        """Look up (or create) tag IDs for the given tag names."""
        tag_ids: list[int] = []
        for name in tag_names:
            try:
                search = requests.get(
                    f"{self.api}/tags",
                    auth=self.auth,
                    params={"search": name},
                    timeout=self.timeout,
                )
                search.raise_for_status()
                matches = [t for t in search.json() if t["name"].lower() == name.lower()]
                if matches:
                    tag_ids.append(matches[0]["id"])
                    continue
                create = requests.post(
                    f"{self.api}/tags",
                    auth=self.auth,
                    json={"name": name},
                    timeout=self.timeout,
                )
                create.raise_for_status()
                tag_ids.append(create.json()["id"])
            except requests.RequestException as exc:
                logger.warning("Could not resolve tag '%s': %s", name, exc)
        return tag_ids

    def create_post(
        self,
        *,
        title: str,
        content_html: str,
        excerpt: str = "",
        slug: str = "",
        status: str | None = None,
        featured_media_id: int | None = None,
        category_ids: list[int] | None = None,
        tag_names: list[str] | None = None,
    ) -> PublishResult:
        payload: dict = {
            "title": title,
            "content": content_html,
            "status": status or config.WP_POST_STATUS,
        }
        if excerpt:
            payload["excerpt"] = excerpt
        if slug:
            payload["slug"] = slug
        if featured_media_id:
            payload["featured_media"] = featured_media_id
        categories = category_ids if category_ids is not None else config.WP_CATEGORY_IDS
        if categories:
            payload["categories"] = categories
        if tag_names:
            payload["tags"] = self._resolve_tags(tag_names)

        logger.info("Creating WordPress post: %s", title)
        resp = requests.post(
            f"{self.api}/posts",
            auth=self.auth,
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        result = PublishResult(
            post_id=data["id"],
            link=data.get("link", ""),
            status=data.get("status", ""),
        )
        logger.info("Post created id=%s status=%s link=%s",
                    result.post_id, result.status, result.link)
        return result
