from typing import List, Tuple

from database import DatabaseManager
from models.sale import Sale
from models.dashboard import SalesComparisonSummary

class SalesService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def get_sales_history(self) -> List[Sale]:
        records = self._db.fetch_sales_history() or []
        return [Sale.from_row(row) for row in records]

    def get_revenue_by_month(self, months: int = 12) -> List[Tuple[str, float]]:
        return self._db.fetch_revenue_by_month(months) or []

    def get_revenue_by_year(self, years: int = 5) -> List[Tuple[int, float]]:
        return self._db.fetch_revenue_by_year(years) or []

    def get_sales_comparison(self) -> SalesComparisonSummary:
        raw = self._db.fetch_sales_comparison_summary() or (0.0, 0.0, 0.0, 0.0)
        return SalesComparisonSummary.from_tuple(raw)
