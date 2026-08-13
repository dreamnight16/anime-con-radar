from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from chinese_scraper_utils import (
    extract_city,
    extract_date,
    guess_category,
    normalize_city,
    parse_date,
    stable_id,
)

from db.schema import EventModel
from pipeline.extractor import _extract_title, _extract_venue

NORMALIZERS: dict[str, Callable[[dict], EventModel]] = {}


def register(platform: str):
    return lambda fn: NORMALIZERS.update({platform: fn}) or fn


def normalize(platform: str, raw_events: list[dict]) -> list[EventModel]:
    fn = NORMALIZERS.get(platform)
    if not fn:
        return []
    return [e for raw in raw_events if (e := _try_normalize(fn, raw)) is not None]


def _try_normalize(fn: Callable[[dict], EventModel], raw: dict) -> EventModel | None:
    try:
        return fn(raw)
    except Exception as e:
        from logger import get_logger
        get_logger(__name__).warning(f"[normalizer:{fn.__name__}] {type(e).__name__}: {e}")
        return None


@register("bilibili")
def _(raw: dict) -> EventModel:
    detail = raw.get("_detail") or {}
    pid = str(raw.get("id") or detail.get("id", "") or uuid4().hex[:12])
    title = detail.get("name") or raw.get("project_name") or raw.get("name", "")
    tlabel = raw.get("tlabel", "")
    start, end = _parse_tlabel(tlabel)
    price = _extract_bili_price(detail)
    ptype = detail.get("project_type") or raw.get("project_type", 1)
    category = {1: "漫展", 2: "演唱会", 3: "展览", 4: "其他"}.get(int(ptype) if ptype else 1, "其他")
    if category == "其他":
        category = guess_category(title)
    status = _bili_status(raw.get("label", ""), raw.get("countdown", ""))
    cover = raw.get("cover", "")
    if cover and not cover.startswith("http"):
        cover = "https:" + cover
    return EventModel(
        id=f"bilibili_{pid}",
        source_type="ticketing",
        source_name="bilibili",
        source_id=pid,
        title=title or f"演出 #{pid}",
        category=category,
        city=normalize_city(raw.get("city", "")),
        venue=_clean_venue(str(raw.get("venueId", ""))),
        start_date=start or datetime.now().strftime("%Y-%m-%d"),
        end_date=end,
        price_range=price,
        ticket_url=f"https://show.bilibili.com/platform/detail.html?id={pid}",
        image_url=cover,
        status=status,
        confidence=1.0,
    )


@register("damai")
def _(raw: dict) -> EventModel:
    rid = str(raw.get("itemId") or raw.get("id") or raw.get("projectId", ""))
    title = raw.get("name") or raw.get("title") or raw.get("itemName", "")
    return EventModel(
        id=f"damai_{rid}",
        source_type="ticketing",
        source_name="damai",
        source_id=rid,
        title=title,
        category=guess_category(title),
        city=normalize_city(raw.get("cityName") or raw.get("city", "")),
        venue=raw.get("venueName") or raw.get("venue", ""),
        start_date=parse_date(raw.get("showTime") or raw.get("startTime") or raw.get("startDate", "")),
        price_range=raw.get("priceStr") or raw.get("priceRange", ""),
        ticket_url=raw.get("detailUrl") or raw.get("url", ""),
        image_url=raw.get("poster") or raw.get("image", ""),
        status=_guess_status(raw),
        confidence=1.0,
    )


@register("showstart")
def _(raw: dict) -> EventModel:
    sid = str(raw.get("id") or raw.get("showId", ""))
    return EventModel(
        id=f"showstart_{sid}",
        source_type="ticketing",
        source_name="showstart",
        source_id=sid,
        title=raw.get("title") or raw.get("showName", ""),
        category=guess_category(raw.get("title", "")),
        city=normalize_city(raw.get("city") or raw.get("cityName", "")),
        venue=raw.get("venue") or raw.get("venueName", ""),
        start_date=parse_date(raw.get("startTime") or raw.get("showTime", "")),
        price_range=raw.get("price") or raw.get("priceRange", ""),
        ticket_url=raw.get("url") or f"https://www.showstart.com/event/{sid}",
        image_url=raw.get("poster") or raw.get("image", ""),
        status=_guess_status(raw),
        confidence=1.0,
    )


@register("maoyan")
def _(raw: dict) -> EventModel:
    mid = str(raw.get("id") or stable_id(raw.get("title", "")))
    return EventModel(
        id=f"maoyan_{mid}",
        source_type="ticketing",
        source_name="maoyan",
        source_id=mid,
        title=raw.get("title", ""),
        category=guess_category(raw.get("title", "")),
        start_date=parse_date(raw.get("showDate") or raw.get("date", "")),
        ticket_url=raw.get("url", ""),
        image_url=raw.get("image", ""),
        status="售票中",
        confidence=1.0,
    )


@register("piaoxingqiu")
def _(raw: dict) -> EventModel:
    sid = stable_id(raw.get("title", ""))
    return EventModel(
        id=f"piaoxingqiu_{sid}",
        source_type="ticketing",
        source_name="piaoxingqiu",
        source_id=sid,
        title=raw.get("title", ""),
        category=guess_category(raw.get("title", "")),
        start_date="",
        ticket_url=raw.get("url", ""),
        status="售票中",
        confidence=1.0,
    )


@register("yongle")
def _(raw: dict) -> EventModel:
    sid = stable_id(raw.get("title", ""))
    return EventModel(
        id=f"yongle_{sid}",
        source_type="ticketing",
        source_name="yongle",
        source_id=sid,
        title=raw.get("title", ""),
        category=guess_category(raw.get("title", "")),
        start_date="",
        ticket_url=raw.get("url", ""),
        status="售票中",
        confidence=1.0,
    )


@register("weibo")
def _(raw: dict) -> EventModel:
    # AI output format: {title, date, endDate, city, venue, category, confidence}
    ai_title = raw.get("title", "")
    if ai_title:
        sid = stable_id(ai_title, raw.get("city", ""), raw.get("date", ""))
        return EventModel(
            id=f"weibo_ai_{sid}",
            source_type="social",
            source_name="weibo",
            source_id=raw.get("_source", "weibo_ai"),
            title=ai_title,
            category=raw.get("category", "其他"),
            city=normalize_city(raw.get("city", "")),
            venue=raw.get("venue", ""),
            start_date=raw.get("date") or "",
            end_date=raw.get("endDate"),
            status="预告",
            confidence=float(raw.get("confidence", 0.3)),
        )
    # Raw text format (fallback)
    text = raw.get("text", "")
    sid = stable_id(text)
    city = extract_city(text)
    date = extract_date(text)
    venue = _extract_venue(text)
    title = _extract_title(text)
    if not date and not city:
        date = datetime.now().strftime("%Y-%m-%d")
    return EventModel(
        id=f"weibo_{sid}",
        source_type="social",
        source_name="weibo",
        source_id=sid,
        title=title or "微博演出信息",
        category=guess_category(text),
        city=city,
        venue=venue,
        start_date=date or datetime.now().strftime("%Y-%m-%d"),
        status="预告",
        confidence=0.3,
    )


def _parse_tlabel(tlabel: str) -> tuple[str, str | None]:
    """Parse B站 tlabel like '2026.05.04' or '2026.05.03 - 05.05'"""
    if not tlabel:
        return "", None
    tlabel = tlabel.replace(".", "-").strip()
    if " - " in tlabel:
        start, end = tlabel.split(" - ", 1)
        if len(end) < 8:
            end = start[:5] + "-" + end
        return start.strip(), end.strip()
    return tlabel, None


def _extract_bili_price(detail: dict) -> str:
    """Extract price from B站 detail API response."""
    performances = detail.get("performance", []) or []
    for perf in performances:
        screens = perf.get("screenList", []) or []
        for screen in screens:
            skus = screen.get("skuList", []) or screen.get("skus", []) or []
            prices = [s.get("price", 0) for s in skus if s.get("price")]
            if prices:
                lo, hi = min(prices), max(prices)
                if lo and hi:
                    return f"¥{int(lo/100)}-{int(hi/100)}"
    return "待定"


def _bili_status(label: str, countdown: str) -> str:
    s = (label + countdown).lower()
    if any(w in s for w in ["热卖", "售票", "销售"]):
        return "售票中"
    if any(w in s for w in ["即将", "预告", "预售"]):
        return "即将开票"
    if any(w in s for w in ["截止", "结束", "停售"]):
        return "已结束"
    return "售票中"


@register("chinajoy")
def _(raw: dict) -> EventModel:
    return EventModel(id=f"cj_{raw.get('startDate','')}", source_type="ticketing",
        source_name="chinajoy", source_id="cj2026", title=raw.get("title","ChinaJoy"),
        category="漫展", city="上海", venue=raw.get("venue","上海新国际博览中心"),
        start_date=raw.get("startDate","2026-07-31"), end_date=raw.get("endDate","2026-08-03"),
        status="预告", confidence=0.95)


@register("ciefc")
def _(raw: dict) -> EventModel:
    pid = stable_id(raw.get("title",""), raw.get("date",""))
    return EventModel(id=f"ciefc_{pid}",source_type="ticketing",source_name="ciefc",
        source_id=pid,title=raw.get("title",""),category="漫展",
        city="广州",venue=raw.get("venue","广交会展馆"),
        start_date=raw.get("date",""),status="预告",confidence=0.8)


@register("nyato")
def _(raw: dict) -> EventModel:
    pid = stable_id(raw.get("title", ""), raw.get("city", ""), raw.get("startDate", ""))
    return EventModel(
        id=f"nyato_{pid}",
        source_type="ticketing",
        source_name="nyato",
        source_id=pid,
        title=raw.get("title", ""),
        category=guess_category(raw.get("title", "")),
        city=normalize_city(raw.get("city", "")),
        venue=raw.get("venue", ""),
        start_date=raw.get("startDate", ""),
        end_date=raw.get("endDate", ""),
        status="售票中",
        confidence=0.9,
    )


def _clean_venue(v: str) -> str:
    """Hide numeric-only venue IDs (B站)."""
    if not v or v.isdigit():
        return ""
    return v


def _guess_status(raw: dict) -> str:
    s = str(raw.get("status", "")).lower()
    if s in ("1", "onsale", "selling", "售票中"):
        return "售票中"
    if s in ("0", "upcoming", "coming", "预告"):
        return "预告"
    if s in ("2", "end", "over", "已结束"):
        return "已结束"
    return "售票中"
