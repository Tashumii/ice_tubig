from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Tuple

from utils import parse_flexible_datetime


class StockStatus(str, Enum):
    NOT_AVAILABLE = 'NOT_AVAILABLE'
    AVAILABLE = 'AVAILABLE'
    SOLD = 'SOLD'


@dataclass(frozen=True)
class Stock:
    stock_id: int
    time_added: datetime
    product_name: str
    kg: float
    freeze_duration_hours: int
    status: StockStatus
    price: float

    @classmethod
    def from_row(cls, row: Tuple[Any, ...]) -> 'Stock':
        return cls(
            stock_id=int(row[0]),
            time_added=parse_flexible_datetime(row[1]),
            product_name=str(row[2] or ''),
            kg=float(row[3] or 0),
            freeze_duration_hours=int(row[4] or 0),
            status=StockStatus(str(row[5] or StockStatus.NOT_AVAILABLE.value)),
            price=float(row[6] or 0.0),
        )
