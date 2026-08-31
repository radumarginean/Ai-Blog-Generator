"""Entry point for the Protection Tax AI blog generator.

Usage:
    python main.py run              Generate & publish one post now (advances rotation)
    python main.py run --topic "…"  Generate & publish a post for a specific topic
    python main.py schedule         Run continuously on the configured cron schedule
    python main.py topics           List the topic rotation and current position
"""

import argparse
import logging
import sys

import config
from topics import TopicRotator


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def cmd_run(args: argparse.Namespace) -> int:
    config.validate()
    from blog_generator import BlogGenerator

    generator = BlogGenerator()
    result = generator.run_once(topic=args.topic)
    print(f"Published post #{result.post_id} [{result.status}] {result.link}")
    return 0


def cmd_schedule(_: argparse.Namespace) -> int:
    config.validate()
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    from blog_generator import BlogGenerator

    generator = BlogGenerator()
    scheduler = BlockingScheduler(timezone=config.SCHEDULE_TIMEZONE)
    trigger = CronTrigger.from_crontab(config.POST_CRON, timezone=config.SCHEDULE_TIMEZONE)

    def job() -> None:
        try:
            generator.run_once()
        except Exception:  # noqa: BLE001 - keep the scheduler alive on failures
            logging.getLogger(__name__).exception("Scheduled blog generation failed")

    scheduler.add_job(job, trigger, name="generate_blog_post", misfire_grace_time=3600)
    logging.getLogger(__name__).info(
        "Scheduler started. Cron='%s' TZ=%s. Next topic: %s",
        config.POST_CRON, config.SCHEDULE_TIMEZONE, generator.rotator.peek(),
    )
    print("Scheduler running. Press Ctrl+C to stop.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nScheduler stopped.")
    return 0


def cmd_topics(_: argparse.Namespace) -> int:
    rotator = TopicRotator()
    upcoming = rotator.peek()
    print(f"{len(rotator.topics)} topics in rotation. Next up: \"{upcoming}\"\n")
    for i, topic in enumerate(rotator.topics):
        marker = " <- next" if i == rotator.state.index else ""
        print(f"  {i + 1:>2}. {topic}{marker}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Protection Tax AI blog generator")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Generate & publish one post now")
    run_p.add_argument("--topic", help="Override the rotating topic with a specific one")
    run_p.set_defaults(func=cmd_run)

    sched_p = sub.add_parser("schedule", help="Run continuously on the cron schedule")
    sched_p.set_defaults(func=cmd_schedule)

    topics_p = sub.add_parser("topics", help="List the topic rotation")
    topics_p.set_defaults(func=cmd_topics)

    return parser


def main() -> int:
    _setup_logging()
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
