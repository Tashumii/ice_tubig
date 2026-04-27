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
        start = (shift_start_time or "").strip()
        end = (shift_end_time or "").strip()
        if len(start) == 5:
            start = f"{start}:00"
        if len(end) == 5:
            end = f"{end}:00"

        def _valid_hhmmss(value: str) -> bool:
            parts = value.split(":")
            if len(parts) != 3:
                return False
            try:
                h, m, s = [int(x) for x in parts]
                return 0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59
            except Exception:
                return False

        if not _valid_hhmmss(start) or not _valid_hhmmss(end):
            raise DatabaseError("Shift time must be HH:MM or HH:MM:SS format.")
        self._db.update_shift_schedule(start, end)
