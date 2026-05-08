from typing import List, Optional

from database import DatabaseManager
from models.dashboard import DashboardSummary, SalesComparisonSummary
from models.stock import Stock


class InventoryService:
    def __init__(self, database_manager: DatabaseManager):
        # Initializes object
        self._db = database_manager

    def refresh_stock_availability(self) -> None:
        # Refreshes availability
        self._db.refresh_stock_availability()

    def get_active_stocks(self) -> List[Stock]:
        # Gets stocks
        records = self._db.fetch_active_stocks() or []
        return [Stock.from_row(row) for row in records]

    def get_dashboard_summary(self) -> DashboardSummary:
        # Gets summary
        raw = self._db.fetch_dashboard_summary() or (0, 0, 0, 0)
        return DashboardSummary.from_tuple(raw)

    def add_stock(self, quantity: int, product_name: str, kg: float,
                  freeze_duration_hours: int, price: float, instant: bool) -> None:
        # Adds stock
        if not isinstance(quantity, int):
            raise ValueError("Quantity must be a whole number.")
        if quantity < 1 or quantity > 10000:
            raise ValueError("Quantity must be between 1 and 10,000.")

        clean_product = (product_name or "").strip()
        clean_product = clean_product.title() if clean_product else "Ice"
        if len(clean_product) > 80:
            raise ValueError("Product name must be 80 characters or fewer.")
        if kg <= 0 or kg > 999.99:
            raise ValueError("Weight must be between 0.01 and 999.99 kg.")
        if price < 0 or price > 99999999.99:
            raise ValueError("Price must be between 0 and 99,999,999.99.")
        if freeze_duration_hours < 0 or freeze_duration_hours > 8760:
            raise ValueError("Freeze duration must be between 0 and 8,760 hours.")

        # Prevent redundant rapid submission of the same stock
        recent_stocks = self.get_active_stocks()
        if recent_stocks:
            recent_stocks.sort(key=lambda s: s.time_added, reverse=True)
            for s in recent_stocks[:10]:
                if (s.product_name.lower() == clean_product.lower() and 
                    abs(s.kg - kg) < 0.001 and abs(s.price - price) < 0.001 and 
                    s.freeze_duration_hours == freeze_duration_hours):
                    from datetime import datetime
                    now = datetime.now()
                    diff = (now - s.time_added.replace(tzinfo=None)).total_seconds()
                    if diff < 10:
                        raise ValueError(f"Identical stock '{clean_product}' was just added. Please wait a moment to avoid duplicate entries.")

        self._db.add_ice_stock_via_procedure(quantity, clean_product, kg, freeze_duration_hours, price, instant)

    def record_stock_sale(self, stock_id: int, sold_by_user_id: Optional[int] = None) -> None:
        # Record sale
        if not isinstance(stock_id, int) or stock_id < 1:
            raise ValueError("Invalid stock identifier.")
        if sold_by_user_id is not None and (not isinstance(sold_by_user_id, int) or sold_by_user_id < 1):
            raise ValueError("Invalid user identifier.")
        self._db.sell_stock_via_procedure(stock_id, sold_by_user_id)

    # Backward-compatible alias
    sell_stock = record_stock_sale

    def get_sales_comparison(self) -> SalesComparisonSummary:
        # Gets comparison
        raw = self._db.fetch_sales_comparison_summary() or (0.0, 0.0, 0.0, 0.0)
        return SalesComparisonSummary.from_tuple(raw)
