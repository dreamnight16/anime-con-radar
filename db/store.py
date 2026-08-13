from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.schema import EventModel, EventRecord, engine


def get_session() -> Session:
    return Session(engine)


def upsert_event(session: Session, event: EventModel) -> bool:
    """Returns True if new, False if updated."""
    existing = session.get(EventRecord, event.id)
    now = datetime.now(UTC).replace(tzinfo=None)
    if existing:
        # Check if this data is newer
        record_scraped_at = _parse_scraped_at(event.scraped_at) or now
        if existing.scraped_at and record_scraped_at <= existing.scraped_at:
            return False
        record_dict = event.model_dump()
        for key, value in record_dict.items():
            if key == "scraped_at":
                continue
            setattr(existing, key, value)
        existing.scraped_at = max(existing.scraped_at or now, record_scraped_at)
        return False
    record = EventRecord(
        id=event.id,
        source_type=event.source_type,
        source_name=event.source_name,
        source_id=event.source_id,
        title=event.title,
        category=event.category,
        city=event.city,
        venue=event.venue,
        start_date=event.start_date,
        end_date=event.end_date,
        price_range=event.price_range,
        ticket_url=event.ticket_url,
        image_url=event.image_url,
        status=event.status,
        confidence=event.confidence,
        fingerprint=event.fingerprint,
        canonical_id=event.canonical_id,
        scraped_at=now,
    )
    try:
        session.add(record)
        session.flush()
        return True
    except IntegrityError:
        session.rollback()
        # Another process inserted the same event, treat as update
        existing2 = session.get(EventRecord, event.id)
        if existing2:
            record_dict = event.model_dump()
            for key, value in record_dict.items():
                if key in ("scraped_at",):
                    continue
                setattr(existing2, key, value)
            parsed = _parse_scraped_at(event.scraped_at) or now
            existing2.scraped_at = max(existing2.scraped_at or now, parsed)
        return False


def get_all_events(session: Session) -> list[EventModel]:
    stmt = select(EventRecord).order_by(EventRecord.start_date.asc())
    rows = session.execute(stmt).scalars().all()
    return [_row_to_model(r) for r in rows]


def _row_to_model(row: EventRecord) -> EventModel:
    return EventModel(
        id=row.id,
        source_type=row.source_type,
        source_name=row.source_name,
        source_id=row.source_id,
        title=row.title,
        category=row.category,
        city=row.city,
        venue=row.venue,
        start_date=row.start_date,
        end_date=row.end_date,
        price_range=row.price_range,
        ticket_url=row.ticket_url,
        image_url=row.image_url,
        status=row.status,
        confidence=row.confidence,
        fingerprint=row.fingerprint,
        canonical_id=row.canonical_id,
        scraped_at=row.scraped_at.isoformat() if row.scraped_at else None,
    )


def _parse_scraped_at(val: str | None) -> datetime | None:
    """Parse scraped_at from ISO string to datetime, handling type mismatch."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None
