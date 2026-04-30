from typing import List, Tuple, Optional

from database import DatabaseManager
from models.sale import Sale
from models.dashboard import SalesComparisonSummary

class SalesService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def get_sales_history(self) -> List[Sale]:
        try:
            records = self._db.fetch_sales_history() or []
            return [Sale.from_row(row) for row in records]
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch sales history: {exc}")

    def get_sales_history_by_user(self, username: Optional[str] = None) -> List[Sale]:
        try:
            sales = self.get_sales_history()
            if not username or username.lower() == "all":
                return sales
            return [sale for sale in sales if sale.sold_by_username == username]
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch sales history by user: {exc}")

    def get_employee_shift_summary(self) -> List[dict]:
        try:
            rows = self._db.fetch_employee_sales_summary() or []
            return [
                {
                    "username": row[0],
                    "shift": row[1],
                    "sales_count": int(row[2] or 0),
                    "total_revenue": float(row[3] or 0.0),
                }
                for row in rows
            ]
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch employee shift summary: {exc}")

    def get_shift_schedule(self) -> dict:
        try:
            start, end = self._db.fetch_shift_schedule()
            return {
                "shift_start_time": str(start)[:5],
                "shift_end_time": str(end)[:5],
            }
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch shift schedule: {exc}")

    def clock_in(self, user_id: int) -> None:
        if not isinstance(user_id, int) or user_id < 1:
            raise ValueError("Invalid user ID")
        try:
            self._db.clock_in_user(user_id)
        except Exception as exc:
            raise RuntimeError(f"Failed to clock in: {exc}")

    def clock_out(self, user_id: int) -> None:
        if not isinstance(user_id, int) or user_id < 1:
            raise ValueError("Invalid user ID")
        try:
            self._db.clock_out_user(user_id)
        except Exception as exc:
            raise RuntimeError(f"Failed to clock out: {exc}")

    def get_shift_logs(self, user_id: Optional[int] = None) -> List[dict]:
        try:
            rows = self._db.fetch_shift_logs(user_id)
            return [
                {
                    "log_id": int(row[0]),
                    "username": str(row[1]),
                    "shift_date": str(row[2]),
                    "expected_in": str(row[3] or ""),
                    "expected_out": str(row[4] or ""),
                    "actual_in": str(row[5] or ""),
                    "actual_out": str(row[6] or ""),
                    "status": str(row[7] or ""),
                }
                for row in rows
            ]
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch shift logs: {exc}")

    def get_revenue_by_month(self, months: int = 12) -> List[Tuple[str, float]]:
        try:
            return self._db.fetch_revenue_by_month(months) or []
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch revenue by month: {exc}")

    def get_revenue_by_year(self, years: int = 5) -> List[Tuple[int, float]]:
        try:
            return self._db.fetch_revenue_by_year(years) or []
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch revenue by year: {exc}")

    def get_sales_comparison(self) -> SalesComparisonSummary:
        try:
            raw = self._db.fetch_sales_comparison_summary() or (0.0, 0.0, 0.0, 0.0)
            return SalesComparisonSummary.from_tuple(raw)
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch sales comparison: {exc}")
