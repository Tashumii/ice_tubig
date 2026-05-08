from database import DatabaseManager, DatabaseError
from utils import normalize_shift_time
from typing import Optional, List


class SettingsService:
    def __init__(self, database_manager: DatabaseManager):
        self._db = database_manager

    def get_theme(self) -> str:
        theme = self._db.fetch_theme_setting()
        return theme if theme in {'light', 'dark'} else 'light'

    def set_theme(self, theme: str) -> None:
        theme_value = theme.lower().strip()
        if theme_value not in {'light', 'dark'}:
            raise DatabaseError('Invalid theme selection')
        self._db.update_theme_setting(theme_value)

    def get_shift_schedule(self) -> dict:
        result = self._db.fetch_shift_schedule()
        start = result[0] if len(result) > 0 else "08:00:00"
        end = result[1] if len(result) > 1 else "17:00:00"
        night_start = result[2] if len(result) > 2 else None
        night_end = result[3] if len(result) > 3 else None
        return {
            "shift_start_time": str(start),
            "shift_end_time": str(end),
            "night_shift_start_time": str(night_start) if night_start else None,
            "night_shift_end_time": str(night_end) if night_end else None,
        }

    def set_shift_schedule(self, shift_start_time: str, shift_end_time: str, night_shift_start_time: str = None, night_shift_end_time: str = None) -> None:
        start = normalize_shift_time(shift_start_time, "Shift start")
        end = normalize_shift_time(shift_end_time, "Shift end")
        if start == end:
            raise DatabaseError("Shift start and end cannot be the same.")
        if start > end:
            raise DatabaseError("Shift end must be later than shift start.")
        
        # Validate night shift if provided
        night_start = None
        night_end = None
        if night_shift_start_time and night_shift_end_time:
            night_start = normalize_shift_time(night_shift_start_time, "Night shift start")
            night_end = normalize_shift_time(night_shift_end_time, "Night shift end")
            if night_start == night_end:
                raise DatabaseError("Night shift start and end cannot be the same.")
            if night_start > night_end:
                raise DatabaseError("Night shift end must be later than night shift start.")
        
        self._db.update_shift_schedule(start, end, night_start, night_end)

    def get_staff_shift_schedule(self, user_id: int) -> dict:
        """Get shift schedule for a specific staff member. Returns global schedule if not customized."""
        result = self._db.fetch_user_shift_schedule(user_id)
        start = result[0] if len(result) > 0 else None
        end = result[1] if len(result) > 1 else None
        night_start = result[2] if len(result) > 2 else None
        night_end = result[3] if len(result) > 3 else None
        return {
            "shift_start_time": str(start) if start else None,
            "shift_end_time": str(end) if end else None,
            "night_shift_start_time": str(night_start) if night_start else None,
            "night_shift_end_time": str(night_end) if night_end else None,
            "is_custom": any([start, end, night_start, night_end]),
        }

    def set_staff_shift_schedule(self, user_id: int, shift_start_time: Optional[str] = None, shift_end_time: Optional[str] = None, 
                                 night_shift_start_time: Optional[str] = None, night_shift_end_time: Optional[str] = None) -> None:
        """Set custom shift schedule for a specific staff member. Pass empty strings to clear and use global shifts."""
        # Validate if times are provided
        if shift_start_time or shift_end_time or night_shift_start_time or night_shift_end_time:
            if shift_start_time and shift_end_time:
                start = normalize_shift_time(shift_start_time, "Shift start")
                end = normalize_shift_time(shift_end_time, "Shift end")
                if start == end:
                    raise DatabaseError("Shift start and end cannot be the same.")
            else:
                raise DatabaseError("Both shift start and end times are required.")
            
            # Validate night shift if provided
            night_start = None
            night_end = None
            if night_shift_start_time or night_shift_end_time:
                if not (night_shift_start_time and night_shift_end_time):
                    raise DatabaseError("Both night shift start and end times are required.")
                night_start = normalize_shift_time(night_shift_start_time, "Night shift start")
                night_end = normalize_shift_time(night_shift_end_time, "Night shift end")
                if night_start == night_end:
                    raise DatabaseError("Night shift start and end cannot be the same.")
            
            self._db.update_user_shift_schedule(user_id, start, end, night_start, night_end)
        else:
            # Clear custom shifts (use global)
            self._db.update_user_shift_schedule(user_id, None, None, None, None)

    def get_all_staff_with_shifts(self) -> List[dict]:
        """Get all staff members with their shift schedules."""
        rows = self._db.fetch_all_staff_with_shifts() or []
        result = []
        for row in rows:
            user_id = row[0]
            username = row[1]
            shift_start = row[2] if len(row) > 2 else None
            shift_end = row[3] if len(row) > 3 else None
            night_start = row[4] if len(row) > 4 else None
            night_end = row[5] if len(row) > 5 else None
            
            result.append({
                "user_id": user_id,
                "username": username,
                "shift_start_time": str(shift_start) if shift_start else None,
                "shift_end_time": str(shift_end) if shift_end else None,
                "night_shift_start_time": str(night_start) if night_start else None,
                "night_shift_end_time": str(night_end) if night_end else None,
                "is_custom": any([shift_start, shift_end, night_start, night_end]),
            })
        return result
