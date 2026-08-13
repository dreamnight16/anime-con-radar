from datetime import UTC, datetime

from pydantic import BaseModel as PydanticBase
from sqlalchemy import DateTime, Float, String, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import DB_PATH


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class EventRecord(Base):
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, default="", nullable=False)
    city: Mapped[str] = mapped_column(String, default="", nullable=False)
    venue: Mapped[str] = mapped_column(String, default="", nullable=False)
    start_date: Mapped[str] = mapped_column(String, nullable=False, index=True)
    end_date: Mapped[str | None] = mapped_column(String, nullable=True)
    price_range: Mapped[str | None] = mapped_column(String, nullable=True)
    ticket_url: Mapped[str | None] = mapped_column(String, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="预告", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    fingerprint: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    canonical_id: Mapped[str | None] = mapped_column(String, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, index=True, nullable=False
    )


engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


Base.metadata.create_all(engine)


class EventModel(PydanticBase):
    id: str
    source_type: str
    source_name: str
    source_id: str = ""
    title: str
    category: str = ""
    city: str = ""
    venue: str = ""
    start_date: str
    end_date: str | None = None
    price_range: str | None = None
    ticket_url: str | None = None
    image_url: str | None = None
    status: str = "预告"
    confidence: float = 1.0
    fingerprint: str | None = None
    canonical_id: str | None = None
    scraped_at: str | None = None
