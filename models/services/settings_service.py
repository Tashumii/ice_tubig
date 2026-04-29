import re

from database import DatabaseManager, DatabaseError

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
        start, end = self._db.fetch_shift_schedule()
        return {
            "shift_start_time": str(start),
            "shift_end_time": str(end),
        }

    def set_shift_schedule(self, shift_start_time: str, shift_end_time: str) -> None:
        start = self._normalize_shift_time(shift_start_time, "Shift start")
        end = self._normalize_shift_time(shift_end_time, "Shift end")
        if start == end:
            raise DatabaseError("Shift start and end cannot be the same.")
        if start > end:
            raise DatabaseError("Shift end must be later than shift start.")
        self._db.update_shift_schedule(start, end)

    def _normalize_shift_time(self, value: str, label: str) -> str:
        text = (value or "").strip()
        if not text:
            raise DatabaseError(f"{label} time is required.")
        if re.match(r"^\d{2}:\d{2}$", text):
            text = f"{text}:00"
        elif not re.match(r"^\d{2}:\d{2}:\d{2}$", text):
            raise DatabaseError("Shift time must be HH:MM or HH:MM:SS format.")

        parts = text.split(":")
        if len(parts) != 3:
            raise DatabaseError("Shift time must be HH:MM or HH:MM:SS format.")
        try:
            h, m, s = [int(x) for x in parts]
        except Exception as exc:
            raise DatabaseError("Shift time must be a valid 24-hour time.") from exc
        if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
            raise DatabaseError("Shift time must be a valid 24-hour time.")
        return text
