from unittest.mock import AsyncMock, MagicMock, patch

from db.schema import EventModel


def make_event(id="ev1", title="Test", city="上海", start_date="2026-06-01", source_name="bilibili", confidence=1.0, fingerprint=None):
    return EventModel(
        id=id, source_type="ticketing", source_name=source_name,
        title=title, city=city, start_date=start_date, confidence=confidence,
        fingerprint=fingerprint,
    )


def test_orchestrator_dedup_all():
    from pipeline.orchestrator import Orchestrator
    mock_sess = MagicMock()
    mock_sess.get.return_value = None  # upsert treats None as "new record"
    with patch("pipeline.orchestrator.get_session", return_value=mock_sess), \
         patch("pipeline.orchestrator.get_all_events", return_value=[
             make_event(id="a", title="CP2026", fingerprint="fp1"),
             make_event(id="b", title="CP2026", fingerprint="fp2"),
         ]):
        orch = Orchestrator()
        orch._dedup_all()
        assert mock_sess.commit.called


def test_orchestrator_check_and_notify_no_events():
    from pipeline.orchestrator import Orchestrator
    mock_sess = MagicMock()
    with patch("pipeline.orchestrator.get_session", return_value=mock_sess), \
         patch("pipeline.orchestrator.get_all_events", return_value=[]):
        orch = Orchestrator()
        orch._notify_all = AsyncMock()
        import asyncio
        asyncio.run(orch.check_and_notify())
        orch._notify_all.assert_not_called()


def test_orchestrator_check_and_notify_with_events():
    from datetime import date, timedelta

    from pipeline.orchestrator import Orchestrator
    future = (date.today() + timedelta(days=30)).isoformat()
    events = [
        make_event(id="a", title="Upcoming Event", city="上海", start_date=future, confidence=1.0),
    ]
    events[0].status = "售票中"
    mock_sess = MagicMock()
    with patch("pipeline.orchestrator.get_session", return_value=mock_sess), \
         patch("pipeline.orchestrator.get_all_events", return_value=events):
        orch = Orchestrator()
        orch._notify_all = AsyncMock()
        import asyncio
        asyncio.run(orch.check_and_notify())
        orch._notify_all.assert_called_once()


def test_get_stats():
    from pipeline.orchestrator import get_stats
    with patch("pipeline.orchestrator.health_stats", return_value={"disabled": {}, "failures": {}}):
        assert get_stats() == {"disabled": {}, "failures": {}}


def test_orchestrator_run_batch_success():
    from pipeline.orchestrator import Orchestrator
    mock_sess = MagicMock()
    orch = Orchestrator()
    orch.session = mock_sess  # Not used in _run_batch since each task gets its own session

    class MockScraper:
        platform = "mock_platform"

        async def scrape(self):
            return [{"title": "Test Event", "city": "上海", "startDate": "2026-06-01"}]

    task_session = MagicMock()
    task_session.get.return_value = None  # upsert expects None for new records
    with patch("pipeline.orchestrator.get_session", return_value=task_session), \
         patch("pipeline.normalizer.normalize", return_value=[make_event()]), \
         patch("pipeline.orchestrator.issubclass", return_value=False):
        import asyncio
        asyncio.run(orch._run_batch([MockScraper], "test"))
        assert task_session.commit.called


def test_orchestrator_stores_structured_weibo_events():
    import asyncio

    from pipeline.orchestrator import Orchestrator

    class WeiboScraper:
        platform = "weibo"

        async def scrape(self):
            return [{
                "title": "上海漫展", "city": "上海", "date": "2026-10-01",
                "url": "https://example.com/event", "confidence": 0.85,
            }]

    session = MagicMock()
    with patch("pipeline.orchestrator.get_session", return_value=session), \
         patch("pipeline.orchestrator.upsert_event") as upsert:
        orchestrator = Orchestrator()
        asyncio.run(orchestrator._run_batch([WeiboScraper], "social"))

    upsert.assert_called_once()
    event = upsert.call_args.args[1]
    assert event.title == "上海漫展"
    assert event.ticket_url == "https://example.com/event"
    session.commit.assert_called_once()


def test_orchestrator_run_batch_failure():
    from pipeline.orchestrator import Orchestrator
    orch = Orchestrator()
    orch.session = MagicMock()

    class FailingScraper:
        platform = "failing_platform"

        async def scrape(self):
            raise RuntimeError("simulated failure")

    task_session = MagicMock()
    with patch("pipeline.orchestrator.get_session", return_value=task_session), \
         patch("pipeline.orchestrator.issubclass", return_value=False):
        import asyncio
        # Should not raise — failures are isolated
        asyncio.run(orch._run_batch([FailingScraper], "test"))


def test_orchestrator_gather_scraper_classes():
    from pipeline.orchestrator import Orchestrator
    with patch("pipeline.orchestrator.is_enabled", return_value=True):
        orch = Orchestrator()
        classes = orch._gather_scraper_classes()
        assert isinstance(classes, list)
