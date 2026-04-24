import sys
import tkinter.messagebox as messagebox

import customtkinter as ctk

from database import DatabaseManager, DatabaseError
from services.inventory_service import InventoryService
from services.sales_service import SalesService
from services.settings_service import SettingsService
from services.auth_service import AuthService
from services.report_service import ReportService
from views.main_window import IceTubigSystem
from views.login_page import LoginPage
from styles import apply_app_style


class IceTubigApp(ctk.CTk):
    """Main application window with login flow."""
    
    def __init__(self):
        super().__init__()
        
        self.title("IceTubig - Ice Inventory Management System")
        self.geometry("900x600")
        
        try:
            self.database_manager = DatabaseManager()
        except DatabaseError as exc:
            error_msg = f"Database Connection Failed\n\n{str(exc)}\n\nPlease ensure MySQL is running and the ice_tubig database exists."
            messagebox.showerror('Database Error', error_msg)
            sys.exit(1)
        except Exception as exc:
            error_msg = f"Unexpected Error\n\n{str(exc)}"
            messagebox.showerror('Startup Error', error_msg)
            sys.exit(1)
        
        # Initialize services
        self.inventory_service = InventoryService(self.database_manager)
        self.sales_service = SalesService(self.database_manager)
        self.settings_service = SettingsService(self.database_manager)
        self.auth_service = AuthService(self.database_manager)
        self.report_service = ReportService(self.database_manager)
        
        # Create UI tokens
        self.tokens = apply_app_style(self, self.settings_service.get_theme())
        
        # Create main container
        self.container = ctk.CTkFrame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        self.current_user = None
        
        # Show login page
        
        self.show_login()
    
    def show_login(self):
        """Show login page."""
        # Clear existing frames
        for widget in self.container.winfo_children():
            widget.destroy()
        
        login_frame = LoginPage(
            self.auth_service,
            self.tokens,
            on_login_success=self.on_login_success,
            master=self.container
        )
        login_frame.grid(row=0, column=0, sticky="nsew")
    
    def on_login_success(self, user):
        """Handle successful login."""
        self.current_user = user
        self.show_main_window()
    
    def show_main_window(self):
        """Show main application window."""
        # Clear container
        for widget in self.container.winfo_children():
            widget.destroy()
        
        # Create main window
        main_window = IceTubigSystem(
            self.inventory_service,
            self.sales_service,
            self.settings_service,
            self.report_service,
            master=self.container
        )
        main_window.grid(row=0, column=0, sticky="nsew")
        
        # Store reference
        self.frames['main'] = main_window


if __name__ == '__main__':
    ctk.set_appearance_mode('Dark')
    ctk.set_default_color_theme('dark-blue')
    
    app = IceTubigApp()
    app.mainloop()
