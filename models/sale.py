from dataclasses import dataclass
from datetime import datetime
from typing import Any, Tuple

@dataclass(frozen=True)
class Sale:
    sale_id: int
    stock_id: int
    added: datetime
    sold_at: datetime
    product_name: str
    price: float
    kg: float

    @classmethod
    def from_row(cls, row: Tuple[Any, ...]) -> 'Sale':
        added = row[2]
        sold_at = row[3]
        if not isinstance(added, datetime):
            added = datetime.strptime(str(added), '%b %d, %Y %I:%M %p')
        if not isinstance(sold_at, datetime):
            sold_at = datetime.strptime(str(sold_at), '%b %d, %Y %I:%M %p')

        return cls(
            sale_id=int(row[0]),
            stock_id=int(row[1]),
            added=added,
            sold_at=sold_at,
            product_name=str(row[4] or ''),
            price=float(row[5] or 0.0),
            kg=float(row[6] or 0.0),
        )
