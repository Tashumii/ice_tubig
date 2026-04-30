import sys
import logging

from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import Qt

from database import DatabaseManager, DatabaseError
from models.services.inventory_service import InventoryService
from models.services.sales_service import SalesService
from models.services.settings_service import SettingsService
from models.services.auth_service import AuthService
from models.services.report_service import ReportService
from models.services.announcement_service import AnnouncementService
from views.main_window import IceTubigSystem
from views.login_page import LoginPage
from views.components.native_polish import FadeStackedWidget
from styles import apply_app_style
from responsive import ResponsiveHelper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class IceTubigApp(QMainWindow):
    """Main application window with login flow."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("IceTubig - Ice Inventory Management System")
        
        # Responsive window sizing
        device_type = ResponsiveHelper.get_device_type()
        width, height = ResponsiveHelper.get_window_size(device_type)
        self.resize(width, height)
        
        # Set minimum size based on device
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
            error_msg = f"Database Connection Failed\n\n{str(exc)}\nMySQL is not running or the ice_tubig database is not available."
            logging.error(f"Database connection failed: {exc}")
            QMessageBox.critical(self, 'Database Error', error_msg)
            sys.exit(1)
        except Exception as exc:
            error_msg = f"Unexpected Error\n\n{str(exc)}"
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
        
        # Create main container
        self.container = FadeStackedWidget(self)
        self.setCentralWidget(self.container)
        
        self.frames = {}
        self.current_user = None
        self.last_login_error = ''
        # Show login page
        
        self.show_login()
    
    def show_login(self):
        """Show login page."""
        self.current_user = None
        # Clear existing frames
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

        # Clear container only after successful creation
        while self.container.count():
            widget = self.container.widget(0)
            self.container.removeWidget(widget)
            widget.deleteLater()
        self.container.addWidget(main_window)
        self.container.switch_to(main_window)

        # Store reference
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
