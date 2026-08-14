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


def test_bili_status_upcoming():
    from pipeline.normalizer import _bili_status
    assert _bili_status("即将开票", "") == "即将开票"
    assert _bili_status("", "预售中") == "即将开票"


def test_bili_status_default():
    from pipeline.normalizer import _bili_status
    assert _bili_status("", "") == "售票中"


def test_extract_bili_price():
    from pipeline.normalizer import _extract_bili_price
    detail = {"performance": [{"screenList": [{"skuList": [{"price": 28000}, {"price": 88000}]}]}]}
    assert _extract_bili_price(detail) == "¥280-880"


def test_extract_bili_price_empty():
    from pipeline.normalizer import _extract_bili_price
    assert _extract_bili_price({}) == "待定"
    assert _extract_bili_price({"performance": []}) == "待定"


def test_clean_venue_hides_numeric():
    from pipeline.normalizer import _clean_venue
    assert _clean_venue("123") == ""
    assert _clean_venue("") == ""
    assert _clean_venue("上海新国际博览中心") == "上海新国际博览中心"


def test_guess_status():
    from pipeline.normalizer import _guess_status
    assert _guess_status({"status": "1"}) == "售票中"
    assert _guess_status({"status": "0"}) == "预告"
    assert _guess_status({"status": "2"}) == "已结束"
    assert _guess_status({"status": "onsale"}) == "售票中"
    assert _guess_status({"status": "upcoming"}) == "预告"
    assert _guess_status({"status": "end"}) == "已结束"
    assert _guess_status({}) == "售票中"


def test_parse_tlabel_full_range():
    from pipeline.normalizer import _parse_tlabel
    start, end = _parse_tlabel("2026.07.18 - 2026.07.19")
    assert start == "2026-07-18"
    assert end == "2026-07-19"


def test_normalize_bilibili_detail():
    from pipeline.normalizer import normalize
    raw = [{
        "id": "12345",
        "_detail": {
            "name": "BML2026",
            "project_type": 2,
            "performance": [{"screenList": [{"skuList": [{"price": 28000}, {"price": 88000}]}]}],
        },
        "tlabel": "2026.07.18 - 2026.07.19",
        "city": "上海市",
        "venueId": "123",
        "label": "热卖中",
    }]
    e = normalize("bilibili", raw)[0]
    assert e.id == "bilibili_12345"
    assert e.source_name == "bilibili"
    assert e.title == "BML2026"
    assert e.category == "演唱会"
    assert e.city == "上海"
    assert e.venue == ""  # numeric venueId is hidden
    assert e.start_date == "2026-07-18"
    assert e.end_date == "2026-07-19"
    assert e.price_range == "¥280-880"
    assert e.ticket_url == "https://show.bilibili.com/platform/detail.html?id=12345"
    assert e.status == "售票中"


def test_normalize_bilibili_cover_prefix():
    from pipeline.normalizer import normalize
    raw = [{"id": 1, "name": "CP", "cover": "//i0.hdslb.com/x.jpg", "tlabel": "2026.05.04"}]
    e = normalize("bilibili", raw)[0]
    assert e.image_url == "https://i0.hdslb.com/x.jpg"


def test_normalize_damai_full():
    from pipeline.normalizer import normalize
    raw = [{
        "itemId": 456,
        "name": "CP30漫展",
        "cityName": "上海",
        "showTime": "2026-10-01 10:00:00",
        "venueName": "上海新国际博览中心",
        "priceStr": "¥180-580",
        "detailUrl": "https://damai.cn/x",
        "poster": "https://img/x.jpg",
        "status": "onsale",
    }]
    e = normalize("damai", raw)[0]
    assert e.id == "damai_456"
    assert e.title == "CP30漫展"
    assert e.category == "漫展"
    assert e.city == "上海"
    assert e.venue == "上海新国际博览中心"
    assert e.start_date == "2026-10-01"
    assert e.price_range == "¥180-580"
    assert e.ticket_url == "https://damai.cn/x"
    assert e.image_url == "https://img/x.jpg"
    assert e.status == "售票中"


def test_normalize_showstart_full():
    from pipeline.normalizer import normalize
    raw = [{"id": 789, "title": "某乐队Live", "city": "北京", "startTime": "2026-07-01", "price": "¥199"}]
    e = normalize("showstart", raw)[0]
    assert e.id == "showstart_789"
    assert e.category == "演唱会"
    assert e.city == "北京"
    assert e.start_date == "2026-07-01"
    assert e.price_range == "¥199"
    assert e.ticket_url == "https://www.showstart.com/event/789"


def test_normalize_maoyan():
    from pipeline.normalizer import normalize
    e = normalize("maoyan", [{"id": 999, "title": "CP30漫展", "showDate": "2026-10-01"}])[0]
    assert e.id == "maoyan_999"
    assert e.title == "CP30漫展"
    assert e.category == "漫展"
    assert e.start_date == "2026-10-01"
    assert e.status == "售票中"


def test_normalize_piaoxingqiu():
    from pipeline.normalizer import normalize
    e = normalize("piaoxingqiu", [{"title": "CP30漫展", "url": "https://pxq.com/x"}])[0]
    assert e.id == "piaoxingqiu_741314883367055e"
    assert e.source_name == "piaoxingqiu"
    assert e.category == "漫展"
    assert e.start_date == ""
    assert e.ticket_url == "https://pxq.com/x"
    assert e.status == "售票中"


def test_normalize_yongle():
    from pipeline.normalizer import normalize
    e = normalize("yongle", [{"title": "BML2026", "url": "https://yongle.com/x"}])[0]
    assert e.id == "yongle_68c7c5ec4c40d5e0"
    assert e.title == "BML2026"
    assert e.category == "其他"
    assert e.start_date == ""
    assert e.status == "售票中"


def test_normalize_weibo_ai():
    from pipeline.normalizer import normalize
    raw = [{
        "title": "上海CP30漫展",
        "date": "2026-10-01",
        "endDate": "2026-10-03",
        "city": "上海市",
        "venue": "上海新国际博览中心",
        "category": "漫展",
        "confidence": 0.85,
        "_source": "weibo_ai",
    }]
    e = normalize("weibo", raw)[0]
    assert e.id == "weibo_ai_dc04e49bdaba189f"
    assert e.source_type == "social"
    assert e.source_id == "weibo_ai"
    assert e.title == "上海CP30漫展"
    assert e.category == "漫展"
    assert e.city == "上海"
    assert e.start_date == "2026-10-01"
    assert e.end_date == "2026-10-03"
    assert e.status == "预告"
    assert e.confidence == 0.85


def test_normalize_weibo_raw_text():
    from pipeline.normalizer import normalize
    raw = [{"text": "2026年10月1日，上海CP30漫展在浦东新国际博览中心举办"}]
    e = normalize("weibo", raw)[0]
    assert e.id == "weibo_9e28c739a1170baf"
    assert e.source_type == "social"
    assert e.city == "上海"
    assert e.start_date == "2026-10-01"
    assert e.category == "漫展"
    assert "漫展" in e.title
    assert "国际博览中心" in e.venue
    assert e.status == "预告"
    assert e.confidence == 0.3


def test_normalize_chinajoy():
    from pipeline.normalizer import normalize
    raw = [{"startDate": "2026-07-31", "endDate": "2026-08-03", "title": "ChinaJoy 2026", "venue": "上海新国际博览中心"}]
    e = normalize("chinajoy", raw)[0]
    assert e.id == "cj_2026-07-31"
    assert e.source_name == "chinajoy"
    assert e.title == "ChinaJoy 2026"
    assert e.category == "漫展"
    assert e.city == "上海"
    assert e.start_date == "2026-07-31"
    assert e.end_date == "2026-08-03"
    assert e.status == "预告"
    assert e.confidence == 0.95


def test_normalize_ciefc():
    from pipeline.normalizer import normalize
    e = normalize("ciefc", [{"title": "广州CICF漫展", "date": "2026-10-01"}])[0]
    assert e.id == "ciefc_7b9b0bf5c55718cf"
    assert e.title == "广州CICF漫展"
    assert e.category == "漫展"
    assert e.city == "广州"
    assert e.venue == "广交会展馆"
    assert e.start_date == "2026-10-01"
    assert e.status == "预告"
    assert e.confidence == 0.8


def test_normalize_nyato():
    from pipeline.normalizer import normalize
    raw = [{"title": "成都NYATO漫展", "city": "成都", "startDate": "2026-10-02", "endDate": "2026-10-04", "venue": "成都国际会展中心"}]
    e = normalize("nyato", raw)[0]
    assert e.id == "nyato_6b517abe70623d15"
    assert e.title == "成都NYATO漫展"
    assert e.category == "漫展"
    assert e.city == "成都"
    assert e.start_date == "2026-10-02"
    assert e.end_date == "2026-10-04"
    assert e.status == "售票中"
    assert e.confidence == 0.9


def test_normalize_swallows_bad_record():
    from pipeline.normalizer import normalize
    assert normalize("bilibili", ["not a dict"]) == []


def test_normalize_empty_raw_list():
    from pipeline.normalizer import normalize
    assert normalize("bilibili", []) == []
