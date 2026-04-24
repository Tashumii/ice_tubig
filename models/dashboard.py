from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class DashboardSummary:
    available_count: int
    freezing_count: int
    sold_count: int
    activity_count: int

    @classmethod
    def from_tuple(cls, row: Tuple[int, int, int, int]) -> 'DashboardSummary':
        return cls(
            available_count=int(row[0] or 0),
            freezing_count=int(row[1] or 0),
            sold_count=int(row[2] or 0),
            activity_count=int(row[3] or 0),
        )

@dataclass(frozen=True)
class SalesComparisonSummary:
    current_month: float
    previous_month: float
    current_year: float
    previous_year: float

    @classmethod
    def from_tuple(cls, row: Tuple[float, float, float, float]) -> 'SalesComparisonSummary':
        return cls(
            current_month=float(row[0] or 0.0),
            previous_month=float(row[1] or 0.0),
            current_year=float(row[2] or 0.0),
            previous_year=float(row[3] or 0.0),
        )
