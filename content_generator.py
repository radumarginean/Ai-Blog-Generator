"""Blog content generation using Google Gemini."""

import json
import logging
import re
from dataclasses import dataclass

from google import genai
from google.genai import types

import config

logger = logging.getLogger(__name__)


@dataclass
class BlogContent:
    title: str
    slug: str
    excerpt: str
    body_html: str
    image_prompt: str
    tags: list[str]


_SYSTEM_INSTRUCTION = (
    f"You are an expert content writer for {config.COMPANY_NAME}, a professional "
    f"tax resolution company ({config.COMPANY_WEBSITE}) that helps individuals and "
    "businesses resolve IRS and state tax debt. You write clear, trustworthy, "
    "SEO-friendly blog posts for people who are stressed about tax problems. "
    "Your tone is reassuring, authoritative, and easy to understand — never "
    "alarmist or salesy. You avoid giving specific legal or financial advice and "
    "always encourage readers to consult a professional for their situation. "
    "You never fabricate statistics, dollar figures, or IRS rules you are unsure of."
)

_PROMPT_TEMPLATE = """\
Write a complete, original blog post for the topic below.

TOPIC: {topic}

Requirements:
- 800-1100 words.
- Structure the body as clean semantic HTML using <h2>, <h3>, <p>, <ul>/<li>,
  and <strong>. Do NOT include <html>, <head>, <body>, or <h1> tags — the title
  is handled separately.
- Open with a short, empathetic introduction that speaks to the reader's situation.
- Use clear subheadings so the post is skimmable.
- Include a practical, actionable section.
- End with a soft call-to-action inviting the reader to contact {company} for a
  free, confidential consultation. Do not invent a phone number or email.
- Include a brief disclaimer paragraph that this is general information, not legal
  or tax advice.

Return ONLY a JSON object (no markdown fences) with exactly these keys:
{{
  "title": "An engaging, SEO-friendly post title (max ~65 characters)",
  "excerpt": "A 1-2 sentence meta description / excerpt (max ~155 characters)",
  "body_html": "The full HTML body as described above",
  "image_prompt": "A concise, literal text-to-image prompt for a professional, \
clean featured image relevant to this topic. No text or words in the image. \
Describe a tasteful, modern, photo-realistic business/finance scene.",
  "tags": ["3-6 short lowercase tag strings relevant to the topic"]
}}
"""


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:80] or "protection-tax-blog-post"


def _extract_json(text: str) -> dict:
    """Parse the model's response into a dict, tolerating stray markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fall back to the first {...} block found in the text.
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


class ContentGenerator:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.model = model or config.GEMINI_MODEL
        self.client = genai.Client(api_key=api_key or config.GEMINI_API_KEY)

    def generate(self, topic: str) -> BlogContent:
        logger.info("Generating blog content for topic: %s", topic)
        prompt = _PROMPT_TEMPLATE.format(topic=topic, company=config.COMPANY_NAME)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
                temperature=0.7,
                response_mime_type="application/json",
            ),
        )

        data = _extract_json(response.text)
        title = data["title"].strip()
        content = BlogContent(
            title=title,
            slug=_slugify(title),
            excerpt=data.get("excerpt", "").strip(),
            body_html=data["body_html"].strip(),
            image_prompt=data.get("image_prompt", f"{topic}, professional finance").strip(),
            tags=[t.strip() for t in data.get("tags", []) if t.strip()],
        )
        logger.info("Generated post: %s", content.title)
        return content
