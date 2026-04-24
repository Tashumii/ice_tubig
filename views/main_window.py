import tkinter.messagebox as messagebox
import customtkinter as ctk

from styles import apply_app_style
from services.inventory_service import InventoryService
from services.sales_service import SalesService
from services.settings_service import SettingsService
from services.report_service import ReportService
from views.dashboard_page import DashboardPage
from views.sales_page import SalesPage
from views.settings_page import SettingsPage
from views.stock_page import StockPage
from views.reports_page import ReportsPage


class IceTubigSystem(ctk.CTkFrame):
    def __init__(self, inventory_service: InventoryService, sales_service: SalesService, settings_service: SettingsService, report_service: ReportService = None, **kwargs):
        super().__init__(**kwargs)
        self.inventory_service = inventory_service
        self.sales_service = sales_service
        self.settings_service = settings_service
        self.report_service = report_service

        self.tokens = apply_app_style(self, self.settings_service.get_theme())
        self.configure(fg_color=self.tokens['bg_base'])

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content()
        self.current_page_index = 1
        self.switch_page(1)
        self.after(1000, self._tick)


    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=self.tokens['bg_sidebar'],
            corner_radius=0,
        )
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.sidebar.grid_rowconfigure(99, weight=1)

        logo_label = ctk.CTkLabel(
            self.sidebar,
            text='ICETUBIG\nINVENTORY SYSTEM',
            text_color=self.tokens['accent_1'],
            justify='left',
            font=ctk.CTkFont(size=16, weight='bold'),
        )
        logo_label.grid(row=0, column=0, sticky='w', padx=20, pady=20)

        self.navigation_buttons = []
        nav_items = [('Dashboard', 0), ('Stocks', 1), ('Sales', 2), ('Reports', 3), ('Settings', 4)]
        for row, (text, idx) in enumerate(nav_items, start=1):
            button = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=lambda i=idx: self.switch_page(i),
                fg_color=self.tokens['bg_sidebar'],
                text_color=self.tokens['text_secondary'],
                hover_color=self.tokens['bg_elevated'],
                anchor='w',
                width=220,
                height=44,
                corner_radius=0,
            )
            button.grid(row=row, column=0, sticky='ew')
            self.navigation_buttons.append(button)

        logout_button = ctk.CTkButton(
            self.sidebar,
            text='Logout',
            command=self.on_logout,
            fg_color=self.tokens['danger'],
            hover_color=self.tokens['danger'],
            text_color='white',
            anchor='w',
            width=220,
            height=44,
            corner_radius=0,
        )
        logout_button.grid(row=98, column=0, sticky='ew')

        version_label = ctk.CTkLabel(
            self.sidebar,
            text='v2.0.0 · 2026',
            text_color=self.tokens['text_muted'],
            font=ctk.CTkFont(size=9),
        )
        version_label.grid(row=99, column=0, sticky='sw', padx=20, pady=20)

    def _build_content(self):
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color=self.tokens['bg_base'],
            corner_radius=0,
        )
        self.content_frame.grid(row=0, column=1, sticky='nsew', padx=20, pady=20)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.pages = [
            DashboardPage(self.inventory_service, self.sales_service, self.tokens, master=self.content_frame),
            StockPage(self.inventory_service, self.tokens, master=self.content_frame),
            SalesPage(self.sales_service, self.tokens, master=self.content_frame),
            ReportsPage(self.report_service, self.tokens, master=self.content_frame),
            SettingsPage(self.settings_service, self._apply_theme, self.tokens, master=self.content_frame),
        ]

        for page in self.pages:
            page.grid(row=0, column=0, sticky='nsew')

    def switch_page(self, index: int):
        self.current_page_index = index
        for idx, button in enumerate(self.navigation_buttons):
            if idx == index:
                button.configure(
                    fg_color=self.tokens['bg_elevated'],
                    text_color=self.tokens['accent_1'],
                )
            else:
                button.configure(
                    fg_color=self.tokens['bg_sidebar'],
                    text_color=self.tokens['text_secondary'],
                )
        self.pages[index].tkraise()
        if hasattr(self.pages[index], 'refresh'):
            self.pages[index].refresh()

    def _tick(self):
        if hasattr(self.pages[1], 'update_countdowns'):
            self.pages[1].update_countdowns()
        self.after(1000, self._tick)

    def _apply_theme(self, theme: str):
        self.tokens = apply_app_style(self, theme)
        self.switch_page(self.current_page_index)

    def on_logout(self):
        """Handle logout action."""
        if hasattr(self.master.master, 'show_login'):
            self.master.master.show_login()

        messagebox.showinfo('Saved', 'Theme updated. Changes applied.')
