from typing import List, Optional

from database import DatabaseManager
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
        if not isinstance(quantity, int):
            raise ValueError("Quantity must be a whole number.")
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")
        if quantity > 10000:
            raise ValueError("Quantity is too large (max 10,000).")

        clean_product = (product_name or "").strip() or "Ice"
        if len(clean_product) > 80:
            raise ValueError("Product name must be 80 characters or fewer.")

        if kg <= 0:
            raise ValueError("Weight must be a positive number.")
        if kg > 999.99:
            raise ValueError("Weight must be 999.99 kg or less.")

        if price < 0:
            raise ValueError("Price cannot be negative.")
        if price > 99999999.99:
            raise ValueError("Price is too large.")

        if freeze_duration_hours < 0:
            raise ValueError("Freeze duration must be 0 or greater.")
        if freeze_duration_hours > 8760:
            raise ValueError("Freeze duration is too long (max 8,760 hours).")

        self._db.add_ice_stock_via_procedure(quantity, clean_product, kg, freeze_duration_hours, price, instant)

    def sell_stock(self, stock_id: int, sold_by_user_id: Optional[int] = None) -> None:
        if not isinstance(stock_id, int) or stock_id < 1:
            raise ValueError("Invalid stock identifier.")
        if sold_by_user_id is not None and (not isinstance(sold_by_user_id, int) or sold_by_user_id < 1):
            raise ValueError("Invalid user identifier.")
        self._db.sell_stock_via_procedure(stock_id, sold_by_user_id)

    def get_sales_comparison(self) -> SalesComparisonSummary:
        raw = self._db.fetch_sales_comparison_summary() or (0.0, 0.0, 0.0, 0.0)
        return SalesComparisonSummary.from_tuple(raw)
