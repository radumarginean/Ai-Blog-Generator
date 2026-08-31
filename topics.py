"""Rotating topic queue for Protection Tax blog posts.

Topics are consumed in order and the position is persisted to disk so the
rotation continues across restarts. When every topic has been used once the
queue wraps back to the start.
"""

import json
import os
from dataclasses import dataclass

from config import STATE_DIR

# Tax-resolution topics relevant to Protection Tax's audience. Add or reorder
# freely — new topics appended to the end are picked up automatically.
TOPICS: list[str] = [
    "How to stop an IRS wage garnishment",
    "Understanding the IRS Offer in Compromise program",
    "What to do when you receive an IRS notice of intent to levy",
    "How to remove a federal tax lien from your property",
    "Setting up an IRS installment agreement you can actually afford",
    "Currently Not Collectible status: pausing IRS collections",
    "Innocent spouse relief: when you're not liable for a joint tax debt",
    "How the IRS Fresh Start program can reduce your back taxes",
    "What happens if you don't file your tax returns for years",
    "Dealing with IRS bank levies and how to release them",
    "Penalty abatement: getting IRS penalties reduced or removed",
    "State tax debt vs. IRS debt: what's different and why it matters",
    "How to handle a payroll tax problem as a small business owner",
    "The IRS audit process explained and how to prepare",
    "Statute of limitations on IRS tax debt collection",
    "How to protect your assets when you owe the IRS",
    "Tax debt relief options for the self-employed and gig workers",
    "What a tax resolution firm actually does for you",
]


@dataclass
class TopicState:
    index: int = 0


class TopicRotator:
    """Serves topics in rotation, persisting the position to a JSON file."""

    def __init__(self, topics: list[str] | None = None, state_dir: str = STATE_DIR):
        self.topics = topics or TOPICS
        if not self.topics:
            raise ValueError("TopicRotator requires at least one topic.")
        os.makedirs(state_dir, exist_ok=True)
        self.state_path = os.path.join(state_dir, "topic_state.json")
        self.state = self._load()

    def _load(self) -> TopicState:
        try:
            with open(self.state_path, encoding="utf-8") as fh:
                data = json.load(fh)
            return TopicState(index=int(data.get("index", 0)))
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            return TopicState()

    def _save(self) -> None:
        with open(self.state_path, "w", encoding="utf-8") as fh:
            json.dump({"index": self.state.index}, fh, indent=2)

    def peek(self) -> str:
        """Return the next topic without advancing the rotation."""
        return self.topics[self.state.index % len(self.topics)]

    def next(self) -> str:
        """Return the next topic and advance (and persist) the rotation."""
        topic = self.peek()
        self.state.index = (self.state.index + 1) % len(self.topics)
        self._save()
        return topic
