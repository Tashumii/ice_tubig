from typing import List, Tuple, Optional

from database import DatabaseManager
from models.sale import Sale
from models.dashboard import SalesComparisonSummary
from utils import clean_display_text, humanize_name, humanize_status


class SalesService:
    def __init__(self, database_manager: DatabaseManager):
        # Initializes object
        self._db = database_manager

    def get_sales_history(self) -> List[Sale]:
        # Gets history
        records = self._db.fetch_sales_history() or []
        return [Sale.from_row(row) for row in records]

    def get_sales_history_by_user(self, username: Optional[str] = None) -> List[Sale]:
        # Gets user
        sales = self.get_sales_history()
        if not username or username.lower() == "all":
            return sales
        return [sale for sale in sales if sale.sold_by_username == username]

    def get_employee_shift_summary(self) -> List[dict]:
        # Gets summary
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

    def get_shift_schedule(self, user_id: Optional[int] = None) -> dict:
        # Gets schedule
        if user_id is not None:
            user_schedule = self._db.fetch_user_shift_schedule(user_id)
            if user_schedule and any(user_schedule):
                start = user_schedule[0] if len(user_schedule) > 0 else None
                end = user_schedule[1] if len(user_schedule) > 1 else None
                night_start = user_schedule[2] if len(user_schedule) > 2 else None
                night_end = user_schedule[3] if len(user_schedule) > 3 else None
                if start and end:
                    return {
                        "shift_start_time": str(start)[:5],
                        "shift_end_time": str(end)[:5],
                        "night_shift_start_time": str(night_start)[:5] if night_start else None,
                        "night_shift_end_time": str(night_end)[:5] if night_end else None,
                    }
        result = self._db.fetch_shift_schedule()
        start = result[0] if len(result) > 0 else "08:00:00"
        end = result[1] if len(result) > 1 else "17:00:00"
        night_start = result[2] if len(result) > 2 else None
        night_end = result[3] if len(result) > 3 else None
        return {
            "shift_start_time": str(start)[:5],
            "shift_end_time": str(end)[:5],
            "night_shift_start_time": str(night_start)[:5] if night_start else None,
            "night_shift_end_time": str(night_end)[:5] if night_end else None,
        }

    def record_clock_in(self, user_id: int) -> None:
        # Record in
        if not isinstance(user_id, int) or user_id < 1:
            print("Err: Invalid user")
            raise ValueError("Invalid user ID")
        self._db.clock_in_user(user_id)

    # Backward-compatible alias
    clock_in = record_clock_in

    def record_clock_out(self, user_id: int) -> None:
        # Record out
        if not isinstance(user_id, int) or user_id < 1:
            print("Err: Invalid user")
            raise ValueError("Invalid user ID")
        self._db.clock_out_user(user_id)

    # Backward-compatible alias
    clock_out = record_clock_out

    def get_shift_logs(self, user_id: Optional[int] = None) -> List[dict]:
        # Gets logs
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
        # Gets notifications
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
        # Gets count
        return self._db.count_unread_admin_notifications()

    def mark_admin_notifications_read(self) -> None:
        # Mark read
        self._db.mark_admin_notifications_read()

    def get_revenue_by_month(self, months: int = 12) -> List[Tuple[str, float]]:
        # Gets month
        return self._db.fetch_revenue_by_month(months) or []

    def get_revenue_by_year(self, years: int = 5) -> List[Tuple[int, float]]:
        # Gets year
        return self._db.fetch_revenue_by_year(years) or []

    def get_sales_comparison(self) -> SalesComparisonSummary:
        # Gets comparison
        raw = self._db.fetch_sales_comparison_summary() or (0.0, 0.0, 0.0, 0.0)
        return SalesComparisonSummary.from_tuple(raw)
