import hashlib
import re
from datetime import datetime

from db.schema import EventModel
from logger import get_logger

_log = get_logger(__name__)

TITLE_ALIASES = {
    "cp": "comicup", "cp展": "comicup", "cp2026": "comicup2026",
    "cj": "chinajoy", "bw": "bilibiliworld", "bml": "bilibilimacrolink",
    "ccg": "ccgexpo", "cd": "comiday",
}

TITLE_CLEANUP = re.compile(r"[　\s!！?？。，,、·•「」『』【】()（）\[\]{}:：#＃\-\-~～★☆♥♦♣♠✓✔✗✘]+")


def _normalize_title(title: str) -> str:
    """归一化标题，处理别名和特殊字符。"""
    t = TITLE_CLEANUP.sub("", title.lower().strip())
    for alias, full in TITLE_ALIASES.items():
        t = t.replace(alias, full)
    return t


def make_fingerprint(event: EventModel) -> str:
    """Generate a dedup fingerprint (NOT for cryptographic use).

    SHA256 truncated to 16 hex chars provides 64-bit collision resistance,
    sufficient for event deduplication but not for security purposes.
    """
    city = event.city.strip().rstrip("市")
    parts = [
        _normalize_title(event.title),
        city,
        event.start_date,
    ]
    raw = "|".join(p for p in parts if p)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def deduplicate(events: list[EventModel]) -> list[EventModel]:
    # First pass: fingerprint exact match
    seen: dict[str, EventModel] = {}
    for e in events:
        fp = e.fingerprint or make_fingerprint(e)
        if fp in seen:
            existing = seen[fp]
            if e.confidence > existing.confidence:
                e.fingerprint = fp
                seen[fp] = e
            # Merge missing fields from higher-confidence source
            if e.confidence <= existing.confidence:
                _merge_fields(existing, e)
        else:
            e.fingerprint = fp
            seen[fp] = e

    # Second pass: fuzzy merge by city+date proximity
    result = list(seen.values())
    result.sort(key=lambda x: x.start_date or "")

    merged: list[EventModel] = []
    for e in result:
        found = False
        for i, m in enumerate(merged):
            if _is_same_event(e, m):
                if e.confidence > m.confidence:
                    _merge_fields(e, m)
                    merged[i] = e
                else:
                    _merge_fields(m, e)
                found = True
                break
        if not found:
            merged.append(e)

    _log.info(f"Dedup: {len(events)}->{len(seen)}->{len(merged)}")
    return merged


def _is_same_event(a: EventModel, b: EventModel) -> bool:
    """Same city, titles similar, dates close."""
    if not a.city or not b.city:
        return False
    if a.city != b.city:
        return False
    if not a.title or not b.title:
        return False
    # Title fuzzy match
    ta = _normalize_title(a.title)
    tb = _normalize_title(b.title)
    titles_similar = ta == tb or (
        len(ta) >= 4 and len(tb) >= 4
        and (ta[:4] == tb[:4] or ta in tb or tb in ta)
    )
    if not titles_similar:
        return False
    # Title match requires date proximity: ±3 day window
    if a.start_date and b.start_date:
        try:
            da = datetime.strptime(a.start_date, "%Y-%m-%d")
            db = datetime.strptime(b.start_date, "%Y-%m-%d")
            if abs((da - db).days) <= 3:
                return True
        except ValueError:
            return False
    return False


def _merge_fields(target: EventModel, source: EventModel):
    """用 source 补全 target 的缺失字段，合并来源。"""
    for field in ["venue", "end_date", "price_range", "ticket_url", "image_url"]:
        src_val = getattr(source, field, None)
        tgt_val = getattr(target, field, None)
        if not tgt_val and src_val:
            setattr(target, field, src_val)
    # Merge source names (dedup to avoid "bilibili,bilibili,bilibili")
    src_names = set(target.source_name.split(","))
    for s in source.source_name.split(","):
        if s and s not in src_names:
            src_names.add(s)
    target.source_name = ",".join(sorted(src_names))
