import argparse
import asyncio
import json
import re
from datetime import date, timedelta

from config import EXPORT_PATH
from logger import get_logger, setup_logging

_SCRIPT_RE = re.compile(r"<script[^>]*>.*?</script>", re.DOTALL | re.IGNORECASE)
_log = get_logger(__name__)
_HTML_RE = re.compile(r"<[^>]+>")


def _sanitize_str(s: str) -> str:
    s = _SCRIPT_RE.sub("", s)
    s = _HTML_RE.sub("", s)
    return s


def _sanitize_event(e: dict) -> dict:
    for key in ("title", "venue", "category", "city"):
        if key in e and isinstance(e[key], str):
            e[key] = _sanitize_str(e[key])
    return e


async def cmd_scrape(args):
    from pipeline.orchestrator import Orchestrator
    orch = Orchestrator()
    if args.target == "all":
        await orch.scrape_all()
    elif args.target == "ticketing":
        await orch.scrape_ticketing()
    elif args.target == "social":
        await orch.scrape_social()


def cmd_export(args):
    from db.store import get_all_events, get_session
    session = get_session()
    try:
        events = get_all_events(session)
        today = date.today().isoformat()
        # Filter: drop events that have definitely ended
        active = []
        for e in events:
            if not e.start_date:
                continue
            if e.end_date:
                cutoff = e.end_date
            else:
                # No end date — assume runs 7 days
                try:
                    cutoff = (date.fromisoformat(e.start_date) + timedelta(days=7)).isoformat()
                except ValueError:
                    # Malformed/LLM-generated start date — keep the event, treat as active today
                    cutoff = today
            if cutoff >= today and e.status != "已结束":
                active.append(e)
        data = [_sanitize_event(_event_to_dict(e)) for e in active]
        with open(EXPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        _log.info(f"Exported {len(data)} events (filtered {len(events)-len(data)} expired)")
    finally:
        session.close()


def cmd_notify(args):
    from pipeline.orchestrator import Orchestrator
    orch = Orchestrator()
    asyncio.run(orch.check_and_notify())


def cmd_run(args):
    asyncio.run(cmd_scrape(argparse.Namespace(target="all")))
    cmd_export(None)
    cmd_notify(None)


def cmd_stats(args):
    from db.store import get_all_events, get_session
    from pipeline.orchestrator import get_stats
    _log.info("=== Platform Health ===")
    for k, v in get_stats().items():
        _log.info(f"  {k}: {v}")
    session = get_session()
    try:
        events = get_all_events(session)
        by_source = {}
        for e in events:
            by_source[e.source_name] = by_source.get(e.source_name, 0) + 1
        _log.info(f"=== Events: {len(events)} total ===")
        for src, cnt in sorted(by_source.items()):
            _log.info(f"  {src}: {cnt}")
    finally:
        session.close()


def _event_to_dict(event) -> dict:
    return {
        "id": event.id,
        "sourceType": event.source_type,
        "sourceName": event.source_name,
        "title": event.title,
        "category": event.category,
        "city": event.city,
        "venue": event.venue,
        "startDate": event.start_date,
        "endDate": event.end_date,
        "priceRange": event.price_range,
        "ticketUrl": event.ticket_url,
        "imageUrl": event.image_url,
        "status": event.status,
        "confidence": event.confidence,
        "canonicalId": event.canonical_id,
        "scrapedAt": event.scraped_at,
    }


def main():
    parser = argparse.ArgumentParser(prog="anime-scraper")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    sub = parser.add_subparsers(dest="command")

    scrape_p = sub.add_parser("scrape")
    scrape_p.add_argument("target", nargs="?", default="all", choices=["all", "ticketing", "social"])

    sub.add_parser("export")
    sub.add_parser("notify")
    sub.add_parser("run")
    sub.add_parser("stats")

    args = parser.parse_args()
    setup_logging(level=args.log_level)

    from config import validate_config
    for warning in validate_config():
        _log.warning(warning)

    if args.command == "scrape":
        asyncio.run(cmd_scrape(args))
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "notify":
        cmd_notify(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
