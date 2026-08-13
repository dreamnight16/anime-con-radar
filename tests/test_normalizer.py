import pytest
from chinese_scraper_utils import guess_category as _guess_category
from chinese_scraper_utils import normalize_city as _normalize_city
from chinese_scraper_utils import parse_date as _parse_date

from pipeline.normalizer import _parse_tlabel


def test_normalize_city_strips_shi():
    assert _normalize_city("上海市") == "上海"
    assert _normalize_city("北京市") == "北京"
    assert _normalize_city("广州") == "广州"


def test_normalize_city_china_aliases():
    assert _normalize_city("中国") == ""
    assert _normalize_city("全国") == ""


def test_normalize_city_strips_spaces():
    assert _normalize_city("  成都  ") == "成都"


def test_parse_date_iso():
    assert _parse_date("2026-05-20") == "2026-05-20"


def test_parse_date_slashed_falls_through():
    ret = _parse_date("2026/05/20")
    # Falls through to s[:10] when format doesn't match
    assert len(ret) == 10


def test_parse_date_dotted_falls_through():
    ret = _parse_date("2026.05.20")
    assert len(ret) == 10


def test_parse_date_with_time():
    assert _parse_date("2026-05-20 14:30:00") == "2026-05-20"


def test_parse_date_empty():
    assert _parse_date("") == ""


@pytest.mark.parametrize("title,expected", [
    ("上海COMICUP漫展", "漫展"),
    ("某同人展2026", "同人展"),
    ("初音未来演唱会", "演唱会"),
    ("xxx cosplay party", "漫展"),
    ("动漫嘉年华", "漫展"),
    ("主题咖啡馆快闪", "展览"),
    ("某音乐节2026", "演唱会"),
    ("某画展回顾", "展览"),
    ("ONLY同人祭", "同人展"),
    ("科幻展览活动", "展览"),
    ("地下偶像live", "演唱会"),
    ("不明主题", "其他"),
])
def test_guess_category(title, expected):
    assert _guess_category(title) == expected


def test_parse_tlabel_single():
    start, end = _parse_tlabel("2026.05.04")
    assert start == "2026-05-04"
    assert end is None


def test_parse_tlabel_range():
    start, end = _parse_tlabel("2026.05.03 - 05.05")
    assert start == "2026-05-03"
    assert end is not None
    assert "05-05" in end


def test_parse_tlabel_empty():
    start, end = _parse_tlabel("")
    assert start == ""
    assert end is None


def test_normalize_bilibili():
    from pipeline.normalizer import normalize
    raw = [{"id": 123, "name": "CP2026", "city": "上海市", "tlabel": "2026.06.01 - 06.02", "project_type": 1}]
    result = normalize("bilibili", raw)
    assert len(result) == 1
    assert result[0].source_name == "bilibili"
    assert result[0].city == "上海"
    assert result[0].start_date == "2026-06-01"
    assert result[0].end_date is not None


def test_normalize_damai():
    from pipeline.normalizer import normalize
    raw = [{"itemId": 456, "name": "CP2026漫展", "cityName": "上海", "showTime": "2026-06-01", "venueName": "会展中心"}]
    result = normalize("damai", raw)
    assert len(result) == 1
    assert result[0].city == "上海"
    assert result[0].start_date == "2026-06-01"


def test_normalize_showstart():
    from pipeline.normalizer import normalize
    raw = [{"id": 789, "title": "Live Show", "city": "北京", "startTime": "2026-07-01", "price": "¥199"}]
    result = normalize("showstart", raw)
    assert len(result) == 1
    assert result[0].city == "北京"


def test_normalize_unknown_platform():
    from pipeline.normalizer import normalize
    result = normalize("unknown", [{"title": "test"}])
    assert result == []


def test_bili_status_hot_sale():
    from pipeline.normalizer import _bili_status
    assert _bili_status("热卖中", "") == "售票中"


def test_bili_status_ended():
    from pipeline.normalizer import _bili_status
    assert _bili_status("已结束", "") == "已结束"
