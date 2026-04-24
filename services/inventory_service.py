from typing import List

from database import DatabaseManager, DatabaseError
from models.dashboard import DashboardSummary, SalesComparisonSummary
from models.stock import Stock

class InventoryService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def refresh_stock_availability(self) -> None:
        self._db.refresh_stock_availability()

    def get_active_stocks(self) -> List[Stock]:
        records = self._db.fetch_active_stocks() or []
        return [Stock.from_row(row) for row in records]

    def get_dashboard_summary(self) -> DashboardSummary:
        raw = self._db.fetch_dashboard_summary() or (0, 0, 0, 0)
        return DashboardSummary.from_tuple(raw)

    def add_stock(self, quantity: int, product_name: str, kg: float, freeze_duration_hours: int, price: float, instant: bool) -> None:
        self._db.add_ice_stock_via_procedure(quantity, product_name, kg, freeze_duration_hours, price, instant)

    def sell_stock(self, stock_id: int) -> None:
        self._db.sell_stock_via_procedure(stock_id)

    def get_sales_comparison(self) -> SalesComparisonSummary:
        raw = self._db.fetch_sales_comparison_summary() or (0.0, 0.0, 0.0, 0.0)
        return SalesComparisonSummary.from_tuple(raw)
