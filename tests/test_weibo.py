import asyncio
import json
from types import SimpleNamespace
from unittest.mock import patch


def _scrape_posts(posts):
    completed = SimpleNamespace(
        returncode=0,
        stdout=json.dumps(posts, ensure_ascii=False),
        stderr="",
    )
    with patch("scrapers.social.weibo.subprocess.run", return_value=completed):
        from scrapers.social.weibo import WeiboScraper

        return asyncio.run(WeiboScraper().scrape())


def test_weibo_without_api_key_returns_deterministic_matches(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    posts = [
        {"text": "上海同人展将于本周末举办", "url": "https://example.com/event"},
        {"text": "今天开会讨论项目，天气也不错", "url": "https://example.com/meeting"},
    ]

    result = _scrape_posts(posts)

    assert result == [posts[0]]


def test_weibo_with_api_key_and_missing_sdk_uses_deterministic_fallback(monkeypatch, caplog):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret")
    posts = [
        {"text": "上海同人展将于本周末举办", "url": "https://example.com/event"},
        {"text": "今天开会讨论项目，天气也不错", "url": "https://example.com/meeting"},
    ]

    with patch(
        "scrapers.social.weibo._load_ai_components",
        side_effect=ModuleNotFoundError("openai"),
    ):
        result = _scrape_posts(posts)

    assert result == [posts[0]]
    assert "ai_sdk_unavailable" in caplog.text
    assert "sk-test-secret" not in caplog.text


def test_weibo_ai_exception_uses_deterministic_fallback(monkeypatch, caplog):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret")
    posts = [
        {"text": "上海漫展将于2026年10月1日在展览馆举办", "url": "https://example.com/event"},
        {"text": "今天开会讨论项目，天气也不错", "url": "https://example.com/meeting"},
    ]

    class FailingExtractor:
        def extract(self, texts):
            raise RuntimeError("request included sk-test-secret")

    with patch(
        "scrapers.social.weibo._create_ai_extractor",
        return_value=(FailingExtractor(), None, None),
    ):
        result = _scrape_posts(posts)

    assert result == [posts[0]]
    assert "ai_extract_failed:RuntimeError" in caplog.text
    assert "sk-test-secret" not in caplog.text


def test_weibo_ai_success_keeps_structured_event_fields(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-secret")
    posts = [{"text": "上海漫展", "url": "https://example.com/event"}]
    extracted = SimpleNamespace(
        title="上海CP30漫展",
        date="2026-10-01",
        end_date="2026-10-03",
        city="上海",
        venue="上海新国际博览中心",
        category="漫展",
        confidence=0.85,
        source_index=0,
    )

    class SuccessfulExtractor:
        def extract(self, texts):
            return [extracted]

    with patch(
        "scrapers.social.weibo._create_ai_extractor",
        return_value=(SuccessfulExtractor(), None, None),
    ):
        result = _scrape_posts(posts)

    assert result == [{
        "title": "上海CP30漫展",
        "date": "2026-10-01",
        "endDate": "2026-10-03",
        "city": "上海",
        "venue": "上海新国际博览中心",
        "category": "漫展",
        "confidence": 0.85,
        "url": "https://example.com/event",
        "_source": "weibo_ai",
    }]
