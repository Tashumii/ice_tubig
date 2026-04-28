import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox

from database import DatabaseManager, DatabaseError
from services.inventory_service import InventoryService
from services.sales_service import SalesService
from services.settings_service import SettingsService
from services.auth_service import AuthService
from services.report_service import ReportService
from views.main_window import IceTubigSystem
from views.login_page import LoginPage
from views.components.native_polish import FadeStackedWidget
from styles import apply_app_style


class IceTubigApp(QMainWindow):
    """Main application window with login flow."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("IceTubig - Ice Inventory Management System")
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)
        
        try:
            self.database_manager = DatabaseManager()
        except DatabaseError as exc:
            error_msg = f"Database Connection Failed\n\n{str(exc)}\nMySQL is not running or the ice_tubig database is not available."
            QMessageBox.critical(self, 'Database Error', error_msg)
            sys.exit(1)
        except Exception as exc:
            error_msg = f"Unexpected Error\n\n{str(exc)}"
            QMessageBox.critical(self, 'Startup Error', error_msg)
            sys.exit(1)
        
        # Initialize services
        self.inventory_service = InventoryService(self.database_manager)
        self.sales_service = SalesService(self.database_manager)
        self.settings_service = SettingsService(self.database_manager)
        self.auth_service = AuthService(self.database_manager)
        self.report_service = ReportService(self.database_manager)
        
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
                on_logout_callback=self.show_login,
                tokens=self.tokens,
                parent=self.container,
                current_user=self.current_user,
            )
        except Exception as exc:
            self.last_login_error = f'Unable to open dashboard: {exc}'
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
        if getattr(self, 'database_manager', None):
            self.database_manager.close()

    def closeEvent(self, event):
        """Qt close hook: release resources then accept close."""
        try:
            self._on_close()
        finally:
            event.accept()


if __name__ == '__main__':
    app_qt = QApplication(sys.argv)
    app = IceTubigApp()
    app.show()
    sys.exit(app_qt.exec())
