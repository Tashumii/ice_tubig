from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from styles import apply_app_style
from services.inventory_service import InventoryService
from services.sales_service import SalesService
from services.settings_service import SettingsService
from services.auth_service import AuthService
from services.report_service import ReportService
from views.dashboard_page import DashboardPage
from views.sales_page import SalesPage
from views.settings_page import SettingsPage
from views.stock_page import StockPage
from views.reports_page import ReportsPage
from views.components.native_polish import FadeStackedWidget, apply_card_polish


# Nav item definitions: (label, page_index)
_NAV_ITEMS = [
    ('Dashboard', 0),
    ('Stocks',    1),
    ('Sales',     2),
    ('Reports',   3),
    ('Settings',  4),
]


class IceTubigSystem(QWidget):
    def __init__(
        self,
        inventory_service: InventoryService,
        sales_service: SalesService,
        settings_service: SettingsService,
        auth_service: AuthService,
        report_service: ReportService = None,
        on_logout_callback=None,
        tokens=None,
        current_user=None,
        parent=None,
    ):
        super().__init__(parent)
        self.inventory_service  = inventory_service
        self.sales_service      = sales_service
        self.settings_service   = settings_service
        self.auth_service       = auth_service
        self.report_service     = report_service
        self.on_logout_callback = on_logout_callback
        self.current_user = current_user

        self.tokens = tokens if tokens is not None else apply_app_style(self.window().windowHandle(), self.settings_service.get_theme())
        self._build_ui()

        self.page_names = [label for label, _ in _NAV_ITEMS]
        self.page_factories = [
            lambda: DashboardPage(self.inventory_service, self.sales_service, self.tokens, self.current_user, self.page_host),
            lambda: StockPage(self.inventory_service, self.tokens, self.current_user, self.page_host),
            lambda: SalesPage(self.sales_service, self.tokens, self.current_user, self.page_host),
            lambda: ReportsPage(self.report_service, self.tokens, self.page_host),
            lambda: SettingsPage(self.settings_service, self.auth_service, self.current_user, self._apply_theme, self.tokens, self.page_host),
        ]
        self.pages = [None] * len(self.page_names)
        self.current_page_index = 1

        QTimer.singleShot(10, lambda: self.switch_page(1))
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self._tick)
        self.tick_timer.start(1000)

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)
        self._build_sidebar(root)
        self._build_content(root)
        apply_card_polish(self)

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self, root_layout):
        self.sidebar = QFrame(self)
        self.sidebar.setProperty("shell", True)
        self.sidebar.setStyleSheet(f"background:{self.tokens['bg_sidebar']};")
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(12, 14, 12, 12)
        side_layout.setSpacing(8)

        # ── Logo block ────────────────────────────────────────────────────────
        brand_title = QLabel('ICETUBIG', self.sidebar)
        brand_title.setProperty("brandTitle", True)
        brand_sub = QLabel('COLD CHAIN DASHBOARD', self.sidebar)
        brand_sub.setProperty("brandSub", True)
        side_layout.addWidget(brand_title)
        side_layout.addWidget(brand_sub)

        # ── Divider ───────────────────────────────────────────────────────────
        side_layout.addSpacing(8)

        # ── Nav items ─────────────────────────────────────────────────────────
        self.navigation_buttons = []
        for (label, idx) in _NAV_ITEMS:
            item = self._nav_item(label, idx)
            side_layout.addWidget(item['button'])
            self.navigation_buttons.append(item)

        # ── Spacer (row 90 has weight=1) ──────────────────────────────────────

        # ── Divider above footer ──────────────────────────────────────────────
        side_layout.addStretch()
        logout_btn = QPushButton('Logout', self.sidebar)
        logout_btn.setProperty("danger", True)
        logout_btn.clicked.connect(self.on_logout)
        side_layout.addWidget(logout_btn)
        version = QLabel('v2.0.0 · 2026', self.sidebar)
        version.setProperty("muted", True)
        side_layout.addWidget(version)
        root_layout.addWidget(self.sidebar, 0)

    def _nav_item(self, label: str, idx: int) -> dict:
        button = QPushButton(label, self.sidebar)
        button.setProperty("nav", True)
        button.clicked.connect(lambda: self.switch_page(idx))
        return {'button': button}

    # ── Content area ──────────────────────────────────────────────────────────

    def _build_content(self, root_layout):
        self.content_frame = QFrame(self)
        self.content_frame.setProperty("shell", True)
        content = QVBoxLayout(self.content_frame)
        content.setContentsMargins(10, 10, 10, 10)
        content.setSpacing(10)

        topbar_frame = QFrame(self.content_frame)
        topbar_frame.setProperty("topbar", True)
        topbar = QHBoxLayout(topbar_frame)
        topbar.setContentsMargins(10, 8, 10, 8)
        topbar.setSpacing(8)

        search = QLineEdit(self.content_frame)
        search.setPlaceholderText('Search reports, products, sales…')
        self.page_status_label = QLabel('', self.content_frame)
        self.page_status_label.setProperty("pill", True)
        profile_name = getattr(self.current_user, "username", "Admin") if self.current_user else "Admin"
        profile = QPushButton(profile_name.title(), self.content_frame)
        profile.setProperty("nav", True)
        profile.setProperty("navActive", True)
        topbar.addWidget(search, 1)
        topbar.addWidget(self.page_status_label)
        topbar.addWidget(profile)
        content.addWidget(topbar_frame)
        self.page_host = FadeStackedWidget(self.content_frame)
        content.addWidget(self.page_host, 1)
        root_layout.addWidget(self.content_frame, 1)

    # ── Navigation ────────────────────────────────────────────────────────────

    def switch_page(self, index: int):
        if index < 0 or index >= len(self.page_names):
            return

        self.current_page_index = index

        for nav_idx, item in enumerate(self.navigation_buttons):
            active = nav_idx == index
            btn = item['button']
            btn.setProperty("navActive", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        page = self._get_or_create_page(index)
        self.page_host.switch_to(page)

        page_name = self.page_names[index]
        self.page_status_label.setText(page_name)

        if hasattr(page, 'refresh'):
            QTimer.singleShot(50, lambda i=index, n=page_name: self._refresh_page(i, n))

    def _refresh_page(self, index: int, page_name: str):
        try:
            page = self.pages[index]
            if page is not None and hasattr(page, 'refresh'):
                page.refresh()
        except Exception as exc:
            self.page_status_label.setText(f'{page_name}: error')

    def _get_or_create_page(self, index: int):
        if self.pages[index] is None:
            page = self._create_page_safely(self.page_names[index], self.page_factories[index])
            self.page_host.addWidget(page)
            apply_card_polish(page)
            self.pages[index] = page
        return self.pages[index]

    def _create_page_safely(self, page_name: str, factory):
        try:
            return factory()
        except Exception as exc:
            fallback = QFrame(self.page_host)
            layout = QVBoxLayout(fallback)
            err = QLabel(f'{page_name} failed to load.\n\n{exc}', fallback)
            err.setStyleSheet(f"color:{self.tokens['danger']};")
            layout.addWidget(err)
            return fallback

    # ── Tick (live countdowns) ────────────────────────────────────────────────

    def _tick(self):
        try:
            stock_page = self.pages[1]
            if stock_page is not None and hasattr(stock_page, 'update_countdowns'):
                stock_page.update_countdowns()
        except Exception:
            pass
        pass

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, theme: str):
        self.tokens = apply_app_style(self.window().windowHandle(), theme)
        self.switch_page(self.current_page_index)

    # ── Logout ────────────────────────────────────────────────────────────────

    def on_logout(self):
        try:
            if callable(self.on_logout_callback):
                self.on_logout_callback()
                return
            parent = self.parentWidget()
            if parent is not None and hasattr(parent, 'show_login'):
                parent.show_login()
                return
            QMessageBox.critical(self, 'Logout Error', 'Unable to return to login screen.')
        except Exception as exc:
            QMessageBox.critical(self, 'Logout Error', str(exc))