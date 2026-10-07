import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from logger import get_logger
from scrapers.base import validate_worker_args

ROOT = Path(__file__).parent.parent.parent
_log = get_logger(__name__)


def _load_ai_components():
    """Load the optional AI dependencies only when a key is configured."""
    import importlib

    importlib.import_module("openai")
    from chinese_scraper_utils import DeepSeekClient, EventExtractor

    return DeepSeekClient, EventExtractor


class _SafeAIError(RuntimeError):
    """Error wrapper that prevents provider exception text from reaching logs."""


class _TrackingClient:
    """Preserve client behavior while exposing swallowed extractor failures."""

    def __init__(self, client: Any):
        self._client = client
        self.model = client.model
        self.failure_type: str | None = None

    def chat_json(self, *args: Any, **kwargs: Any):
        try:
            return self._client.chat_json(*args, **kwargs)
        except Exception as exc:
            self.failure_type = type(exc).__name__
            raise _SafeAIError(self.failure_type) from None

    def chat(self, *args: Any, **kwargs: Any):
        try:
            return self._client.chat(*args, **kwargs)
        except Exception as exc:
            self.failure_type = type(exc).__name__
            raise _SafeAIError(self.failure_type) from None


def _create_ai_extractor(
    api_key: str,
) -> tuple[Any | None, _TrackingClient | None, str | None]:
    if not api_key:
        return None, None, "api_key_missing"

    try:
        deepseek_client, event_extractor = _load_ai_components()
        client = _TrackingClient(
            deepseek_client(api_key=api_key, model="deepseek-v4-flash")
        )
        extractor = event_extractor(
            client=client,
            event_types=["漫展", "同人展", "演唱会", "音乐会", "展览"],
            min_confidence=0.4,
        )
    except ImportError:
        return None, None, "ai_sdk_unavailable"
    except Exception as exc:
        return None, None, f"ai_init_failed:{type(exc).__name__}"

    return extractor, client, None


class WeiboScraper:
    platform = "weibo"

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self._extractor, self._ai_client, self._fallback_reason = _create_ai_extractor(api_key)

    async def scrape(self) -> list[dict]:
        # Step 1: Playwright 抓取微博帖文
        worker_args = ["weibo"]
        validate_worker_args(worker_args)
        pw_result = subprocess.run(
            [sys.executable, str(ROOT / "_playwright_worker.py"), *worker_args],
            capture_output=True, text=True, timeout=300, cwd=ROOT,
        )
        if pw_result.stderr:
            for line in pw_result.stderr.strip().split("\n"):
                _log.info(line)
        if pw_result.returncode != 0:
            _log.warning("[weibo] Playwright worker failed")
            return []

        try:
            posts = json.loads(pw_result.stdout.strip())
        except (json.JSONDecodeError, IndexError):
            return []

        if not posts:
            return []

        # Step 2: use the optional structured extractor when configured.
        if self._extractor:
            texts = [p.get("text", "") for p in posts]
            if self._ai_client:
                self._ai_client.failure_type = None
            try:
                extracted = self._extractor.extract(texts)
                if self._ai_client and self._ai_client.failure_type:
                    return self._deterministic_fallback(
                        posts, f"ai_call_failed:{self._ai_client.failure_type}"
                    )
                if extracted:
                    events = []
                    for e in extracted:
                        source_index = getattr(e, "source_index", -1)
                        source_url = posts[source_index].get("url", "") if 0 <= source_index < len(posts) else ""
                        events.append({
                            "title": e.title,
                            "date": e.date,
                            "endDate": e.end_date,
                            "city": e.city,
                            "venue": e.venue,
                            "category": e.category,
                            "confidence": e.confidence,
                            "url": source_url,
                            "_source": "weibo_ai",
                        })
                    _log.info("[weibo] EventExtractor found %d events", len(events))
                    return events
            except Exception as exc:
                return self._deterministic_fallback(
                    posts, f"ai_extract_failed:{type(exc).__name__}"
                )

            return self._deterministic_fallback(posts, "ai_no_events")

        # Fallback: keep matching posts for the deterministic extractor in the
        # orchestrator. Social discovery must not disappear when the optional
        # model provider is unavailable.
        return self._deterministic_fallback(posts, self._fallback_reason or "ai_unavailable")

    def _deterministic_fallback(self, posts: list[dict], reason: str) -> list[dict]:
        from pipeline.extractor import is_likely_event_post

        _log.warning("[weibo] deterministic fallback: %s", reason)
        posts = [p for p in posts if is_likely_event_post(p.get("text", ""))]
        _log.info("[weibo] deterministic fallback found %d posts", len(posts))
        return posts
