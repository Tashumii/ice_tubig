from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Tuple

from utils import parse_flexible_datetime


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
        return cls(
            announcement_id=int(row[0]),
            title=str(row[1] or ''),
            message=str(row[2] or ''),
            created_at=parse_flexible_datetime(row[3]),
            created_by=str(row[4] or ''),
            is_read=bool(row[5]) if len(row) > 5 else False,
            read_at=parse_flexible_datetime(row[6]) if len(row) > 6 and row[6] else None,
        )


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
        return cls(
            announcement_id=int(row[0]),
            title=str(row[1] or ''),
            message=str(row[2] or ''),
            created_at=parse_flexible_datetime(row[3]),
            created_by=str(row[4] or ''),
            is_active=bool(row[5]),
            recipient_count=int(row[6] or 0),
            read_count=int(row[7] or 0),
        )
