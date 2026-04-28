from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Tuple

@dataclass(frozen=True)
class Sale:
    sale_id: int
    stock_id: int
    added: datetime
    sold_at: datetime
    product_name: str
    price: float
    kg: float
    sold_by_user_id: Optional[int] = None
    sold_by_username: str = ''
    shift_name: str = ''

    @classmethod
    def from_row(cls, row: Tuple[Any, ...]) -> 'Sale':
        added = cls._parse_datetime(row[2])
        sold_at = cls._parse_datetime(row[3])

        return cls(
            sale_id=int(row[0]),
            stock_id=int(row[1]),
            added=added,
            sold_at=sold_at,
            product_name=str(row[4] or ''),
            price=float(row[5] or 0.0),
            kg=float(row[6] or 0.0),
            sold_by_user_id=int(row[7]) if len(row) > 7 and row[7] is not None else None,
            sold_by_username=str(row[8] or '') if len(row) > 8 else '',
            shift_name=str(row[9] or '') if len(row) > 9 else '',
        )

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value

        text = str(value)
        formats = (
            '%b %d, %Y %I:%M %p',
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
