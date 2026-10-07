import re
from datetime import datetime

from chinese_scraper_utils import extract_city, extract_date, guess_category, stable_id

from db.schema import EventModel

VENUE_KEYWORDS = [
    "会展中心", "展览中心", "国际博览中心", "展览馆", "体育馆", "大剧院",
    "剧院", "艺术中心", "文化中心", "大会堂", "展厅", "博览馆", "会议中心",
    "美术馆", "博物馆", "科技馆", "livehouse", "live house", "LiveHouse",
]

EVENT_TERMS = (
    "活动", "演出", "演唱会", "音乐会", "舞台剧", "音乐节", "嘉年华", "见面会",
    "ONLY", "CP展", "ComiCup", "ChinaJoy",
)
EXPLICIT_EVENT_TERMS = (
    "漫展", "同人展", "展会", "会展", "动漫展", "展览", "博览会", "票务", "购票", "售票", "开票", "门票", "预售票",
)


def is_likely_event_post(
    text: str,
    *,
    city: str | None = None,
    date: str | None = None,
    venue: str | None = None,
) -> bool:
    """Require an event term plus context, unless the text is explicitly event-related."""
    if not text:
        return False
    normalized_text = text.casefold()
    if not any(term.casefold() in normalized_text for term in EVENT_TERMS + EXPLICIT_EVENT_TERMS):
        return False
    if any(term.casefold() in normalized_text for term in EXPLICIT_EVENT_TERMS):
        return True
    if city is None:
        city = extract_city(text)
    if date is None:
        date = extract_date(text)
    if venue is None:
        venue = _extract_venue(text)
    return bool(city or date or venue)


def extract_events(platform: str, raw_items: list[dict]) -> list[EventModel]:
    events = []
    for item in raw_items:
        text = item.get("text", "")
        if not text:
            continue
        event = _extract_one(platform, item)
        if event:
            events.append(event)
    return events


def _extract_one(platform: str, item: dict) -> EventModel | None:
    text = item.get("text", "")
    city = extract_city(text)
    date = extract_date(text)
    venue = _extract_venue(text)
    if not is_likely_event_post(text, city=city, date=date, venue=venue):
        return None
    title = _extract_title(text) or item.get("user", "") + " 发布的演出"
    event_id = stable_id(title, city, date)
    score = sum([bool(date), bool(city), bool(venue)])
    confidence = {3: 0.9, 2: 0.7, 1: 0.5}.get(score, 0.5)
    return EventModel(
        id=f"{platform}_{event_id}",
        source_type="social",
        source_name=platform,
        source_id=item.get("url", ""),
        title=title,
        category=guess_category(text),
        city=city,
        venue=venue,
        start_date=date or datetime.now().strftime("%Y-%m-%d"),
        ticket_url=None,
        image_url=(item.get("images") or [None])[0],
        status="预告",
        confidence=confidence,
    )


def _extract_title(text: str) -> str:
    # Look for event name patterns like "XXX展", "第X届XXX"
    m = re.search(r"(第[一二三四五六七八九十\d]+届)?[^\s，。,\.]{2,20}(展|同人展|嘉年华|见面会|演唱会)", text)
    if m:
        return m.group(0)
    # Fallback: first line or first sentence
    for sep in ("。", "！", "！", "\n"):
        if sep in text:
            return text[:text.index(sep)]
    return text[:50]


def _extract_venue(text: str) -> str:
    for kw in VENUE_KEYWORDS:
        # Find the keyword and get surrounding context as venue name
        idx = text.find(kw)
        if idx >= 0:
            start = max(0, idx - 8)
            end = min(len(text), idx + len(kw) + 4)
            return text[start:end].strip()
    return ""


