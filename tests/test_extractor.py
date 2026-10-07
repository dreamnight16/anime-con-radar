from unittest.mock import patch

from pipeline.extractor import _extract_one, _extract_title, _extract_venue, extract_events


def test_extract_events_empty():
    assert extract_events("test", []) == []


def test_extract_events_skips_empty_text():
    assert extract_events("test", [{"text": ""}]) == []


def test_extract_events_skips_ordinary_post_with_single_character_hui():
    item = {"text": "今天开会讨论项目，天气也不错", "url": "https://example.com/post"}
    assert extract_events("weibo", [item]) == []


def test_extract_events_accepts_activity_with_context():
    item = {
        "text": "上海音乐会将于2026年6月1日在大剧院举办",
        "url": "https://example.com/post",
    }
    with patch("pipeline.extractor.extract_city", return_value="上海"), \
         patch("pipeline.extractor.extract_date", return_value="2026-06-01"):
        events = extract_events("weibo", [item])

    assert len(events) == 1
    assert events[0].city == "上海"
    assert events[0].start_date == "2026-06-01"


def test_extract_title_with_event_pattern():
    title = _extract_title("【重磅】第十届上海CP漫展即将开幕！")
    assert "漫展" in title


def test_extract_title_fallback_first_sentence():
    # Regex matches "今天有演唱会" before fallback reaches "。"
    title = _extract_title("大家好。今天有演唱会。")
    assert "演唱会" in title


def test_extract_title_true_fallback():
    # No event keyword, hits sentence fallback
    title = _extract_title("大家好。这是预告。")
    assert title == "大家好"


def test_extract_title_fallback_short_text():
    title = _extract_title("简短预告")
    assert len(title) <= 50


def test_extract_venue_finds_keyword():
    venue = _extract_venue("活动地点在浦东新区国际博览中心举办")
    assert "国际博览中心" in venue


def test_extract_venue_returns_empty_when_no_keyword():
    venue = _extract_venue("没有场馆信息")
    assert venue == ""


def test_extract_one_with_complete_info():
    item = {
        "text": "第十届CP漫展将于6月1日在上海国际博览中心举办",
        "url": "https://example.com/post/1",
    }
    with patch("pipeline.extractor.extract_city", return_value="上海"), \
         patch("pipeline.extractor.extract_date", return_value="2026-06-01"):
        event = _extract_one("weibo", item)
        assert event is not None
        assert event.source_name == "weibo"
        assert event.city == "上海"
        assert event.start_date == "2026-06-01"
        assert event.confidence == 0.9  # 3 fields matched


def test_extract_one_partial_info():
    item = {
        "text": "某活动在上海举办",
        "url": "https://example.com/post/2",
    }
    with patch("pipeline.extractor.extract_city", return_value="上海"), \
         patch("pipeline.extractor.extract_date", return_value=""):
        event = _extract_one("weibo", item)
        assert event is not None
        assert event.city == "上海"
        # score: date=False, city=True, venue=False -> 1 -> confidence=0.5
        assert event.confidence == 0.5
