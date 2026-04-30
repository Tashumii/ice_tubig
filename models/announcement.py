from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Tuple

@dataclass(frozen=True)
class Announcement:
    announcement_id: int
    title: str
    message: str
    created_at: datetime
    created_by: str
    is_read: bool = False
    read_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: Tuple[Any, ...]) -> 'Announcement':
        created_at = cls._parse_datetime(row[3])
        read_at = cls._parse_datetime(row[6]) if len(row) > 6 and row[6] else None

        return cls(
            announcement_id=int(row[0]),
            title=str(row[1] or ''),
            message=str(row[2] or ''),
            created_at=created_at,
            created_by=str(row[4] or ''),
            is_read=bool(row[5]) if len(row) > 5 else False,
            read_at=read_at,
        )

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if not value:
            return datetime.now()
        
        text = str(value)
        formats = (
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
        )
        for fmt in formats:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return datetime.now()

@dataclass(frozen=True)
class AnnouncementSummary:
    announcement_id: int
    title: str
    message: str
    created_at: datetime
    created_by: str
    is_active: bool
    recipient_count: int
    read_count: int

    @classmethod
    def from_row(cls, row: Tuple[Any, ...]) -> 'AnnouncementSummary':
        created_at = row[3] if isinstance(row[3], datetime) else datetime.strptime(str(row[3]), '%Y-%m-%d %H:%M:%S')

        return cls(
            announcement_id=int(row[0]),
            title=str(row[1] or ''),
            message=str(row[2] or ''),
            created_at=created_at,
            created_by=str(row[4] or ''),
            is_active=bool(row[5]),
            recipient_count=int(row[6] or 0),
            read_count=int(row[7] or 0),
        )
