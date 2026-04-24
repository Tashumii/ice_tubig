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
