from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Tuple

from utils import parse_flexible_datetime


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
        # From row
        return cls(
            sale_id=int(row[0]),
            stock_id=int(row[1]),
            added=parse_flexible_datetime(row[2]),
            sold_at=parse_flexible_datetime(row[3]),
            product_name=str(row[4] or ''),
            price=float(row[5] or 0.0),
            kg=float(row[6] or 0.0),
            sold_by_user_id=int(row[7]) if len(row) > 7 and row[7] is not None else None,
            sold_by_username=str(row[8] or '') if len(row) > 8 else '',
            shift_name=str(row[9] or '') if len(row) > 9 else '',
        )
