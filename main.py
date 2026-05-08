import os
import sys
import logging

from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap

from database import DatabaseManager, DatabaseError
from models.services.inventory_service import InventoryService
from models.services.sales_service import SalesService
from models.services.settings_service import SettingsService
from models.services.auth_service import AuthService
from models.services.report_service import ReportService
from models.services.announcement_service import AnnouncementService
from models.views.main_window import IceTubigSystem
from models.views.login_page import LoginPage
from models.views.components.native_polish import FadeStackedWidget
from styles import apply_app_style
from responsive import ResponsiveHelper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_BG_PATH = os.path.join(_BASE_DIR, 'images', 'background_login.png')


class BackgroundWidget(QWidget):
    """Widget that paints the icy background image behind all content."""

    def __init__(self, bg_path: str, parent=None):
        super().__init__(parent)
        self._bg_pixmap = QPixmap(bg_path)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event):
        if not self._bg_pixmap.isNull():
            painter = QPainter(self)
            scaled = self._bg_pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.end()


class IceTubigApp(QMainWindow):
    """Main application window with login flow and consistent icy background."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mr. Ice Buddha — Inventory Management System")

        # Responsive window sizing
        device_type = ResponsiveHelper.get_device_type()
        width, height = ResponsiveHelper.get_window_size(device_type)
        self.resize(width, height)

        if device_type == "mobile":
            self.setMinimumSize(360, 640)
        elif device_type == "tablet":
            self.setMinimumSize(768, 600)
        else:
            self.setMinimumSize(900, 600)

        try:
            self.database_manager = DatabaseManager()
            logging.info("Database connection established successfully")
        except DatabaseError as exc:
            error_msg = f"Database Connection Failed\n\n{exc}\nMySQL is not running or the ice_tubig database is not available."
            logging.error(f"Database connection failed: {exc}")
            QMessageBox.critical(self, 'Database Error', error_msg)
            sys.exit(1)
        except Exception as exc:
            error_msg = f"Unexpected Error\n\n{exc}"
            logging.exception("Unexpected error during startup")
            QMessageBox.critical(self, 'Startup Error', error_msg)
            sys.exit(1)

        # Initialize services
        self.inventory_service = InventoryService(self.database_manager)
        self.sales_service = SalesService(self.database_manager)
        self.settings_service = SettingsService(self.database_manager)
        self.auth_service = AuthService(self.database_manager)
        self.report_service = ReportService(self.database_manager)
        self.announcement_service = AnnouncementService(self.database_manager)

        # Create UI tokens
        self.tokens = apply_app_style(QApplication.instance(), self.settings_service.get_theme())

        # ── Background + container stack ──────────────────────────────────
        # BackgroundWidget paints the icy image behind everything,
        # so both login page and main window share the same background.
        self._bg_widget = BackgroundWidget(_BG_PATH, self)
        self.setCentralWidget(self._bg_widget)

        from PyQt6.QtWidgets import QVBoxLayout
        bg_layout = QVBoxLayout(self._bg_widget)
        bg_layout.setContentsMargins(0, 0, 0, 0)

        self.container = FadeStackedWidget(self._bg_widget)
        self.container.setStyleSheet("background: transparent;")
        bg_layout.addWidget(self.container)

        self.frames = {}
        self.current_user = None
        self.last_login_error = ''
        self.show_login()

    def show_login(self):
        """Show login page."""
        self.current_user = None
        while self.container.count():
            widget = self.container.widget(0)
            self.container.removeWidget(widget)
            widget.deleteLater()

        login_frame = LoginPage(
            self.container,
            self.auth_service,
            self.tokens,
            on_login_success=self.on_login_success,
            initial_error=self.last_login_error,
        )
        self.container.addWidget(login_frame)
        self.container.switch_to(login_frame)
        self.last_login_error = ''

    def on_login_success(self, user):
        """Handle successful login."""
        self.current_user = user
        self.show_main_window()

    def show_main_window(self):
        """Show main application window."""
        try:
            main_window = IceTubigSystem(
                self.inventory_service,
                self.sales_service,
                self.settings_service,
                self.auth_service,
                self.report_service,
                self.announcement_service,
                on_logout_callback=self.show_login,
                tokens=self.tokens,
                parent=self.container,
                current_user=self.current_user,
            )
            logging.info(f"User {self.current_user.username} logged in successfully")
        except Exception as exc:
            self.last_login_error = f'Unable to open dashboard: {exc}'
            logging.error(f"Failed to open dashboard: {exc}")
            self.show_login()
            return

        while self.container.count():
            widget = self.container.widget(0)
            self.container.removeWidget(widget)
            widget.deleteLater()
        self.container.addWidget(main_window)
        self.container.switch_to(main_window)
        self.frames['main'] = main_window

    def _on_close(self):
        """Close app and release DB resources safely."""
        try:
            if getattr(self, 'database_manager', None):
                self.database_manager.close()
                logging.info("Database connection closed successfully")
        except Exception as exc:
            logging.error(f"Error closing database connection: {exc}")

    def closeEvent(self, event):
        """Qt close hook: release resources then accept close."""
        try:
            self._on_close()
        finally:
            event.accept()


if __name__ == '__main__':
    app_qt = QApplication(sys.argv)
    app_qt.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = IceTubigApp()
    app.show()
    sys.exit(app_qt.exec())
