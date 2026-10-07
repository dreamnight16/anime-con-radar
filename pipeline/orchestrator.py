import asyncio
from datetime import datetime

from db.store import get_all_events, get_session, upsert_event
from logger import get_logger
from pipeline.dedup import deduplicate, make_fingerprint
from scrapers.base import AbstractScraper, SocialScraper
from scrapers.health import is_enabled, record_failure, record_success
from scrapers.health import stats as health_stats

_log = get_logger(__name__)


class Orchestrator:
    def __init__(self):
        self.session = get_session()

    async def scrape_all(self):
        await self.scrape_ticketing()
        await self.scrape_social()
        self._dedup_all()
        self.session.commit()

    def _gather_scraper_classes(self) -> list[type]:
        """Collect all registered scraper classes, including optional imports."""
        scrapers = list(AbstractScraper._registry.values())
        for mod_path in [
            "scrapers.ticketing.bilibili", "scrapers.ticketing.damai",
            "scrapers.ticketing.maoyan", "scrapers.ticketing.showstart",
            "scrapers.ticketing.piaoxingqiu", "scrapers.ticketing.yongle",
            "scrapers.social.weibo",
            "scrapers.nyato", "scrapers.chinajoy", "scrapers.ciefc",
        ]:
            try:
                cls_name = mod_path.rsplit(".", 1)[-1].capitalize() + "Scraper"
                mod = __import__(mod_path, fromlist=[cls_name])
                cls = getattr(mod, cls_name)
                if cls not in scrapers:
                    scrapers.append(cls)
            except (ImportError, AttributeError):
                pass
        # Scrapers whose class name doesn't match the naive capitalize() derivation
        # (e.g. PiaoXingQiuScraper for module "piaoxingqiu") still register via
        # __init_subclass__; merge any newly-registered subclasses so they aren't missed.
        for cls in AbstractScraper._registry.values():
            if cls not in scrapers:
                scrapers.append(cls)
        return [s for s in scrapers if is_enabled(getattr(s, "platform", "unknown"))]

    async def scrape_ticketing(self):
        scrapers = [
            scraper for scraper in self._gather_scraper_classes()
            if not (
                issubclass(scraper, SocialScraper)
                or getattr(scraper, "platform", "") == "weibo"
            )
        ]
        await self._run_batch(scrapers, "ticketing")

    async def scrape_social(self):
        scrapers = self._gather_scraper_classes()
        social_scrapers = [
            s for s in scrapers
            if issubclass(s, SocialScraper) or getattr(s, "platform", "") == "weibo"
        ]
        if social_scrapers:
            await self._run_batch(social_scrapers, "social")

    async def _run_batch(self, scraper_classes: list[type], batch_name: str):
        """Run scrapers in parallel with per-scraper failure isolation."""
        from pipeline.extractor import extract_events
        from pipeline.normalizer import normalize

        async def _run_one(cls) -> tuple[str, int, str | None]:
            """Returns (platform, event_count, error_message_or_None)."""
            session = get_session()
            try:
                scraper = cls()
                raw = await scraper.scrape()
                if issubclass(cls, SocialScraper) and cls.platform != "weibo":
                    events = extract_events(cls.platform, raw)
                else:
                    events = normalize(cls.platform, raw)
                for e in events:
                    e.fingerprint = make_fingerprint(e)
                    upsert_event(session, e)
                session.commit()
                record_success(cls.platform)
                _log.info(f"[{cls.platform}] {len(events)} events")
                return (cls.platform, len(events), None)
            except Exception as exc:
                disabled = record_failure(cls.platform)
                tag = " DISABLED" if disabled else ""
                err_msg = f"{exc}{tag}"
                _log.error(f"[{cls.platform}] failed: {err_msg}")
                return (cls.platform, 0, err_msg)
            finally:
                session.close()

        results = await asyncio.gather(*[_run_one(cls) for cls in scraper_classes], return_exceptions=True)

        succeeded = sum(1 for r in results if isinstance(r, tuple) and r[2] is None)
        failed = [r[0] for r in results if isinstance(r, tuple) and r[2] is not None]
        total = len(scraper_classes)
        _log.info(f"[{batch_name}] {succeeded}/{total} scrapers succeeded")
        if failed:
            _log.warning(f"[{batch_name}] failed platforms: {', '.join(failed)}")

    def _dedup_all(self):
        events = get_all_events(self.session)
        merged = deduplicate(events)
        for e in merged:
            upsert_event(self.session, e)
        self.session.commit()
        _log.info(f"Dedup: {len(events)} -> {len(merged)}")

    async def check_and_notify(self):
        events = get_all_events(self.session)
        upcoming = [e for e in events if e.start_date >= datetime.now().strftime("%Y-%m-%d")]
        new_events = [e for e in upcoming if e.status in ("售票中", "即将开票")]
        if not new_events:
            _log.info("No upcoming on-sale events to notify")
            return
        msg = "\n".join(
            f"• {e.title} | {e.city} | {e.start_date} | {e.price_range or '待定'}"
            for e in new_events[:5]
        )
        await self._notify_all(msg)

    async def _notify_all(self, message: str):
        from notifiers.bark import send as bk_send
        from notifiers.serverchan import send as sc_send
        results = await asyncio.gather(sc_send(message), bk_send(message), return_exceptions=True)
        for i, name in enumerate(["serverchan", "bark"]):
            if isinstance(results[i], Exception):
                _log.warning(f"[{name}] notify failed: {results[i]}")
            elif results[i]:
                _log.info(f"[{name}] sent")


def get_stats() -> dict:
    return health_stats()
