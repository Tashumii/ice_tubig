from typing import List, Tuple, Optional

from database import DatabaseManager
from models.sale import Sale
from models.dashboard import SalesComparisonSummary
from utils import clean_display_text, humanize_name, humanize_status


class SalesService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def get_sales_history(self) -> List[Sale]:
        records = self._db.fetch_sales_history() or []
        return [Sale.from_row(row) for row in records]

    def get_sales_history_by_user(self, username: Optional[str] = None) -> List[Sale]:
        sales = self.get_sales_history()
        if not username or username.lower() == "all":
            return sales
        return [sale for sale in sales if sale.sold_by_username == username]

    def get_employee_shift_summary(self) -> List[dict]:
        rows = self._db.fetch_employee_sales_summary() or []
        return [
            {
                "username": humanize_name(row[0]),
                "shift": humanize_name(row[1], "No shift"),
                "sales_count": int(row[2] or 0),
                "total_revenue": float(row[3] or 0.0),
            }
            for row in rows
        ]

    def get_shift_schedule(self) -> dict:
        start, end = self._db.fetch_shift_schedule()
        return {
            "shift_start_time": str(start)[:5],
            "shift_end_time": str(end)[:5],
        }

    def record_clock_in(self, user_id: int) -> None:
        if not isinstance(user_id, int) or user_id < 1:
            raise ValueError("Invalid user ID")
        self._db.clock_in_user(user_id)

    # Backward-compatible alias
    clock_in = record_clock_in

    def record_clock_out(self, user_id: int) -> None:
        if not isinstance(user_id, int) or user_id < 1:
            raise ValueError("Invalid user ID")
        self._db.clock_out_user(user_id)

    # Backward-compatible alias
    clock_out = record_clock_out

    def get_shift_logs(self, user_id: Optional[int] = None) -> List[dict]:
        rows = self._db.fetch_shift_logs(user_id)
        return [
            {
                "log_id": int(row[0]),
                "username": humanize_name(row[1]),
                "shift_date": str(row[2]),
                "expected_in": str(row[3] or ""),
                "expected_out": str(row[4] or ""),
                "actual_in": str(row[5] or ""),
                "actual_out": str(row[6] or ""),
                "status": humanize_status(row[7]),
            }
            for row in rows
        ]

    def get_admin_notifications(self, limit: int = 20, unread_only: bool = False) -> List[dict]:
        rows = self._db.fetch_admin_notifications(limit, unread_only)
        return [
            {
                "notification_id": int(row[0]),
                "event_type": humanize_status(row[1]),
                "username": humanize_name(row[2], "System"),
                "title": clean_display_text(row[3]),
                "message": clean_display_text(row[4]),
                "severity": humanize_status(row[5]),
                "is_read": bool(row[6]),
                "created_at": str(row[7] or ""),
            }
            for row in rows
        ]

    def get_unread_admin_notification_count(self) -> int:
        return self._db.count_unread_admin_notifications()

    def mark_admin_notifications_read(self) -> None:
        self._db.mark_admin_notifications_read()

    def get_revenue_by_month(self, months: int = 12) -> List[Tuple[str, float]]:
        return self._db.fetch_revenue_by_month(months) or []

    def get_revenue_by_year(self, years: int = 5) -> List[Tuple[int, float]]:
        return self._db.fetch_revenue_by_year(years) or []

    def get_sales_comparison(self) -> SalesComparisonSummary:
        raw = self._db.fetch_sales_comparison_summary() or (0.0, 0.0, 0.0, 0.0)
        return SalesComparisonSummary.from_tuple(raw)
