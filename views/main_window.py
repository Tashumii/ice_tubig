import os
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
import qtawesome as qta

from styles import apply_app_style
from responsive import ResponsiveHelper
from models.services.inventory_service import InventoryService
from models.services.sales_service import SalesService
from models.services.settings_service import SettingsService
from models.services.auth_service import AuthService
from models.services.report_service import ReportService
from models.services.announcement_service import AnnouncementService
from utils import clean_display_text, humanize_name, humanize_status, is_admin
from views.dashboard_page import DashboardPage
from views.sales_page import SalesPage
from views.settings_page import SettingsPage
from views.stock_page import StockPage
from views.reports_page import ReportsPage
from views.announcements_page import AnnouncementsPage
from views.components.native_polish import FadeStackedWidget, apply_card_polish

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOGO_PATH = os.path.join(_BASE_DIR, 'images', 'logo.png')

_NAV_ITEMS = [
    ('Dashboard', 0, 'fa5s.chart-line'),
    ('Stocks',    1, 'fa5s.box'),
    ('Sales',     2, 'fa5s.credit-card'),
    ('Reports',   3, 'fa5s.chart-bar'),
    ('Announcements', 4, 'fa5s.bell'),
    ('Settings',  5, 'fa5s.cog'),
]


class IceTubigSystem(QWidget):
    def __init__(
        self, inventory_service, sales_service, settings_service,
        auth_service, report_service=None, announcement_service=None,
        on_logout_callback=None, tokens=None, current_user=None, parent=None,
    ):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.sales_service = sales_service
        self.settings_service = settings_service
        self.auth_service = auth_service
        self.report_service = report_service
        self.announcement_service = announcement_service
        self.on_logout_callback = on_logout_callback
        self.current_user = current_user
        self._notification_cache = []
        self.search_menu = None
        self.tokens = tokens if tokens is not None else apply_app_style(
            self.window().windowHandle(), self.settings_service.get_theme())
        self.device_type = ResponsiveHelper.get_device_type()
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._run_global_search)
        self._build_ui()

        self.page_names = [label for label, _, _ in _NAV_ITEMS]
        self.page_factories = [
            lambda: DashboardPage(self.inventory_service, self.sales_service, self.tokens, self.current_user, self.page_stack),
            lambda: StockPage(self.inventory_service, self.tokens, self.current_user, self.page_stack),
            lambda: SalesPage(self.sales_service, self.tokens, self.current_user, self.page_stack),
            lambda: ReportsPage(self.report_service, self.tokens, self.page_stack),
            lambda: AnnouncementsPage(self.announcement_service, self.current_user, self.tokens, self.page_stack),
            lambda: SettingsPage(self.settings_service, self.auth_service, self.current_user, self._apply_theme, self.tokens, self.page_stack),
        ]
        self.pages = [None] * len(self.page_names)
        self.current_page_index = 1

        QTimer.singleShot(10, lambda: self.switch_page(1))
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self._update_stock_countdowns)
        self.tick_timer.start(1000)

        if is_admin(self.current_user):
            self.notification_timer = QTimer(self)
            self.notification_timer.timeout.connect(self._refresh_notification_bell)
            self.notification_timer.start(10000)
            QTimer.singleShot(250, self._refresh_notification_bell)

    def _build_ui(self):
        # Transparent so parent BackgroundWidget's icy background shows through
        self.setStyleSheet("background: transparent;")
        root_layout = QHBoxLayout(self)
        spacing = ResponsiveHelper.get_spacing(self.device_type)
        margins = ResponsiveHelper.get_margins(self.device_type)
        root_layout.setContentsMargins(*margins)
        root_layout.setSpacing(spacing)
        if ResponsiveHelper.should_show_sidebar(self.device_type):
            self._build_sidebar(root_layout)
        self._build_content_area(root_layout)
        apply_card_polish(self)

    # ── Sidebar ───────────────────────────────────────────────────────────

    def _build_sidebar(self, root_layout):
        self.sidebar = QFrame(self)
        self.sidebar.setProperty("shell", True)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.tokens['bg_sidebar']}, stop:1 #0A1929);
                border: 1px solid {self.tokens['border']};
                border-radius: 16px;
            }}
            QLabel {{ color: {self.tokens['sidebar_text_primary']}; }}
        """)
        min_w, max_w = (140, 180) if self.device_type == "tablet" else (190, 260)
        self.sidebar.setMinimumWidth(min_w)
        self.sidebar.setMaximumWidth(max_w)

        sidebar_layout = QVBoxLayout(self.sidebar)
        spacing = ResponsiveHelper.get_spacing(self.device_type)
        sidebar_layout.setContentsMargins(spacing, spacing + 4, spacing, spacing)
        sidebar_layout.setSpacing(spacing - 2)

        # Logo
        logo_label = QLabel(self.sidebar)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_pm = QPixmap(_LOGO_PATH)
        if not logo_pm.isNull():
            logo_label.setPixmap(logo_pm.scaled(
                180, 70, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        logo_label.setStyleSheet("background: transparent; border: none; margin: 4px 0;")
        sidebar_layout.addWidget(logo_label)

        # Tagline
        tagline = QLabel('PURIFIED ICE TUBE', self.sidebar)
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet(f"color: {self.tokens['sidebar_text_muted']}; font-size: 9px; font-weight: 600; letter-spacing: 2px; margin-bottom: 8px;")
        sidebar_layout.addWidget(tagline)

        # Separator
        sep = QFrame(self.sidebar)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {self.tokens['border']}; max-height: 1px; border: none;")
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(6)

        # Nav items
        self.navigation_buttons = []
        for label, page_idx, icon_name in _NAV_ITEMS:
            nav_button = self._create_nav_button(label, page_idx, icon_name)
            sidebar_layout.addWidget(nav_button)
            self.navigation_buttons.append(nav_button)

        sidebar_layout.addStretch()

        # Footer
        logout_btn = QPushButton('Logout', self.sidebar)
        logout_btn.setProperty("danger", True)
        logout_btn.setIcon(qta.icon('fa5s.sign-out-alt', color=self.tokens['danger']))
        logout_btn.clicked.connect(self.on_logout)
        sidebar_layout.addWidget(logout_btn)
        version_label = QLabel('v2.0.0 · Mr. Ice Buddha', self.sidebar)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(f"color: {self.tokens['sidebar_text_muted']}; font-size: 10px;")
        sidebar_layout.addWidget(version_label)
        root_layout.addWidget(self.sidebar, 0)

    def _create_nav_button(self, label, page_idx, icon_name):
        button = QPushButton(f"  {label}", self.sidebar)
        button.setProperty("nav", True)
        button.setIcon(qta.icon(icon_name, color=self.tokens['sidebar_text_primary']))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(self._nav_inactive_style())
        button.clicked.connect(lambda: self.switch_page(page_idx))
        return button

    def _nav_active_style(self):
        return f"""
            QPushButton {{
                text-align: left; padding: 12px 16px; border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.tokens['accent_1']}, stop:1 {self.tokens['accent_2']});
                color: white; border: none;
                font-size: 13px; font-weight: 600; letter-spacing: 0.3px;
            }}
            QPushButton:hover {{ background: {self.tokens['accent_2']}; }}
        """

    def _nav_inactive_style(self):
        return f"""
            QPushButton {{
                text-align: left; padding: 12px 16px; border-radius: 10px;
                background: transparent; color: {self.tokens['sidebar_text_secondary']};
                border: 1px solid transparent; font-size: 13px; font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(93, 173, 226, 0.12);
                border: 1px solid rgba(93, 173, 226, 0.2);
                color: #FFFFFF;
            }}
        """

    # ── Content area ──────────────────────────────────────────────────────

    def _build_content_area(self, root_layout):
        self.content_frame = QFrame(self)
        self.content_frame.setProperty("shell", True)
        self.content_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        # Top bar
        topbar_frame = QFrame(self.content_frame)
        topbar_frame.setProperty("topbar", True)
        topbar_layout = QHBoxLayout(topbar_frame)
        topbar_layout.setContentsMargins(12, 8, 12, 8)
        topbar_layout.setSpacing(10)

        self.search_input = QLineEdit(self.content_frame)
        self.search_input.setPlaceholderText('Search stocks, sales, staff, reports…')
        self.search_input.setMaxLength(100)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {self.tokens['bg_input']};
                border: 1px solid {self.tokens['border']};
                border-radius: 20px; padding: 10px 16px;
                color: {self.tokens['text_primary']}; font-size: 13px;
            }}
            QLineEdit:focus {{ border: 2px solid {self.tokens['accent_1']}; padding: 9px 15px; }}
        """)
        self.search_input.addAction(
            qta.icon('fa5s.search', color=self.tokens['text_muted']),
            QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.textChanged.connect(self._on_search_text_changed)

        self.page_status_label = QLabel('', self.content_frame)
        self.page_status_label.setProperty("pill", True)

        display_name = getattr(self.current_user, "username", "Admin") if self.current_user else "Admin"
        profile_button = QPushButton(f"  {display_name.title()}", self.content_frame)
        profile_button.setIcon(qta.icon('fa5s.user-circle', color='#FFFFFF'))
        profile_button.setCursor(Qt.CursorShape.PointingHandCursor)

        topbar_layout.addWidget(self.search_input, 1)
        topbar_layout.addWidget(self.page_status_label)

        if is_admin(self.current_user):
            self.notification_button = QPushButton(self.content_frame)
            self.notification_button.setObjectName("notificationBell")
            self.notification_button.setIcon(qta.icon('fa5s.bell', color=self.tokens['text_secondary']))
            self.notification_button.setToolTip("Staff activity notifications")
            self.notification_button.clicked.connect(self._show_notifications)
            self.notification_button.setStyleSheet(f"""
                QPushButton#notificationBell {{
                    min-width: 42px; padding: 8px 10px; border-radius: 20px;
                    border: 1px solid {self.tokens['border']};
                    background: {self.tokens['bg_input']};
                    color: {self.tokens['text_primary']}; font-weight: 700;
                }}
                QPushButton#notificationBell:hover {{
                    border-color: {self.tokens['accent_1']};
                    background: {self.tokens['bg_elevated']};
                }}
            """)
            topbar_layout.addWidget(self.notification_button)

        topbar_layout.addWidget(profile_button)
        content_layout.addWidget(topbar_frame)

        self.page_stack = FadeStackedWidget(self.content_frame)
        self.page_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout.addWidget(self.page_stack, 1)

        content_scroll = QScrollArea(self)
        content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        content_scroll.setWidgetResizable(True)
        content_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content_scroll.setStyleSheet("QScrollArea { border: none; }")
        content_scroll.setWidget(self.content_frame)
        root_layout.addWidget(content_scroll, 1)

    # ── Navigation ────────────────────────────────────────────────────────

    def switch_page(self, index):
        if index < 0 or index >= len(self.page_names):
            return
        self.current_page_index = index
        for nav_idx, button in enumerate(self.navigation_buttons):
            is_active = nav_idx == index
            button.setStyleSheet(self._nav_active_style() if is_active else self._nav_inactive_style())
            icon_name = _NAV_ITEMS[nav_idx][2]
            button.setIcon(qta.icon(icon_name, color='#FFFFFF' if is_active else self.tokens['sidebar_text_secondary']))
        page = self._get_or_create_page(index)
        self.page_stack.switch_to(page)
        self.page_status_label.setText(self.page_names[index])
        if hasattr(page, 'refresh'):
            QTimer.singleShot(50, lambda i=index: self._refresh_page(i))

    def _refresh_page(self, index):
        try:
            page = self.pages[index]
            if page is not None and hasattr(page, 'refresh'):
                page.refresh()
            self._apply_current_search_to_page()
        except Exception:
            self.page_status_label.setText(f'{self.page_names[index]}: error')

    def _on_search_text_changed(self, query):
        current_page = self.pages[self.current_page_index]
        if current_page is not None and hasattr(current_page, 'search'):
            try:
                current_page.search(query)
            except Exception:
                pass
        if len((query or "").strip()) >= 2:
            self.search_timer.start(250)
        else:
            self._close_search_menu()

    def _apply_current_search_to_page(self):
        if not hasattr(self, "search_input"):
            return
        query = self.search_input.text()
        current_page = self.pages[self.current_page_index]
        if current_page is not None and hasattr(current_page, 'search'):
            current_page.search(query)

    def _run_global_search(self):
        query = self.search_input.text().strip()
        if len(query) < 2:
            self._close_search_menu()
            return
        results = self._collect_global_search_results(query)
        self._show_search_results(query, results)

    def _collect_global_search_results(self, query):
        query_lower = query.lower()
        results = []
        def matches(*values):
            return query_lower in " ".join(str(v or "") for v in values).lower()
        def add(page_index, title, detail, icon):
            if len(results) < 12:
                results.append({"page_index": page_index, "title": title, "detail": detail, "icon": icon})

        try:
            for stock in self.inventory_service.get_active_stocks():
                status = humanize_status(stock.status)
                if matches(stock.stock_id, stock.product_name, stock.kg, stock.price, status):
                    add(1, f"Stock #{stock.stock_id} · {stock.product_name}",
                        f"{status} · {stock.kg:g} kg · ₱ {stock.price:,.2f}", 'fa5s.box')
        except Exception: pass

        try:
            sales = self.sales_service.get_sales_history()
            if not is_admin(self.current_user):
                username = getattr(self.current_user, "username", "")
                sales = [s for s in sales if s.sold_by_username == username]
            for sale in sales:
                seller = humanize_name(sale.sold_by_username)
                if matches(sale.sale_id, sale.product_name, seller, sale.price, sale.sold_at):
                    add(2, f"Sale #{sale.sale_id} · {sale.product_name}",
                        f"{seller} · ₱ {sale.price:,.2f}", 'fa5s.credit-card')
        except Exception: pass

        try:
            if self.report_service:
                for product in self.report_service.get_top_products(10):
                    if matches(product.get("product_name"), product.get("sale_count")):
                        add(3, f"Report · {product.get('product_name')}",
                            f"{product.get('sale_count',0)} sales · ₱ {product.get('total_revenue',0):,.2f}", 'fa5s.chart-bar')
        except Exception: pass

        try:
            if self.announcement_service:
                announcements = (self.announcement_service.get_all_announcements(self.current_user)
                    if is_admin(self.current_user) else self.announcement_service.get_announcements_for_user(self.current_user))
                for ann in announcements:
                    if matches(getattr(ann, "title", ""), getattr(ann, "message", "")):
                        add(4, f"Announcement · {getattr(ann, 'title', 'Untitled')}",
                            f"By {humanize_name(getattr(ann, 'created_by', ''))}", 'fa5s.bell')
        except Exception: pass

        try:
            if is_admin(self.current_user):
                for account in self.auth_service.list_accounts(self.current_user):
                    status = "Active" if account.get("is_active") else "Disabled"
                    if matches(account.get("username"), account.get("roles"), status):
                        add(5, f"User · {account.get('username')}",
                            f"{account.get('roles') or 'staff'} · {status}", 'fa5s.user')
        except Exception: pass
        return results

    def _show_search_results(self, query, results):
        self._close_search_menu()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {self.tokens['bg_surface']}; color: {self.tokens['text_primary']};
                border: 1px solid {self.tokens['border']}; border-radius: 12px; padding: 8px;
            }}
            QMenu::item {{ padding: 10px 18px; min-width: 430px; border-radius: 8px; }}
            QMenu::item:selected {{ background: {self.tokens['table_row_hover']}; }}
        """)
        header = menu.addAction(f"Search results for \"{query}\"")
        header.setEnabled(False)
        menu.addSeparator()
        if not results:
            empty = menu.addAction("No matching records found.")
            empty.setEnabled(False)
        else:
            for r in results:
                action = menu.addAction(qta.icon(r["icon"], color=self.tokens['accent_1']),
                    f"{r['title']}\n{r['detail']}")
                action.triggered.connect(lambda c=False, pi=r["page_index"]: self._open_search_result(pi))
        self.search_menu = menu
        menu.popup(self.search_input.mapToGlobal(self.search_input.rect().bottomLeft()))

    def _open_search_result(self, page_index):
        self._close_search_menu()
        self.switch_page(page_index)
        QTimer.singleShot(150, self._apply_current_search_to_page)

    def _close_search_menu(self):
        menu = getattr(self, "search_menu", None)
        if menu:
            menu.close(); menu.deleteLater(); self.search_menu = None

    def _refresh_notification_bell(self):
        if not is_admin(self.current_user) or not hasattr(self, "notification_button"):
            return
        try:
            count = self.sales_service.get_unread_admin_notification_count()
            self._notification_cache = self.sales_service.get_admin_notifications(8)
            if count:
                self.notification_button.setText(str(min(count, 99)))
                self.notification_button.setIcon(qta.icon('fa5s.bell', color=self.tokens['warning']))
            else:
                self.notification_button.setText("")
                self.notification_button.setIcon(qta.icon('fa5s.bell', color=self.tokens['text_secondary']))
        except Exception: pass

    def _show_notifications(self):
        if not is_admin(self.current_user): return
        try:
            notifications = self.sales_service.get_admin_notifications(8)
        except Exception as exc:
            QMessageBox.warning(self, "Notifications", f"Unable to load: {exc}"); return
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {self.tokens['bg_surface']}; color: {self.tokens['text_primary']};
                border: 1px solid {self.tokens['border']}; border-radius: 12px; padding: 8px; }}
            QMenu::item {{ padding: 10px 18px; min-width: 380px; border-radius: 8px; }}
            QMenu::item:selected {{ background: {self.tokens['table_row_hover']}; }}
        """)
        title_action = menu.addAction("Staff Activity"); title_action.setEnabled(False)
        menu.addSeparator()
        if not notifications:
            empty = menu.addAction("No staff activity yet."); empty.setEnabled(False)
        else:
            for item in notifications:
                icon = self._notification_icon(item.get("severity", "info"))
                msg = f"{item.get('created_at','')} · {clean_display_text(item.get('title',''))}\n{humanize_name(item.get('username','Staff'), 'Staff')}: {clean_display_text(item.get('message',''))}"
                action = menu.addAction(icon, msg); action.setEnabled(False)
            menu.addSeparator()
        dash = menu.addAction(qta.icon('fa5s.chart-line', color=self.tokens['accent_1']), "Open Dashboard")
        dash.triggered.connect(lambda: self.switch_page(0))
        menu.exec(self.notification_button.mapToGlobal(self.notification_button.rect().bottomRight()))
        try: self.sales_service.mark_admin_notifications_read()
        except Exception: pass
        self._refresh_notification_bell()

    def _notification_icon(self, severity):
        m = {"success": ('fa5s.check-circle', self.tokens['success']),
             "warning": ('fa5s.exclamation-triangle', self.tokens['warning']),
             "danger": ('fa5s.times-circle', self.tokens['danger'])}
        name, color = m.get((severity or "info").lower(), ('fa5s.info-circle', self.tokens['accent_1']))
        return qta.icon(name, color=color)

    def _get_or_create_page(self, index):
        if self.pages[index] is None:
            page = self._create_page_safely(self.page_names[index], self.page_factories[index])
            self.page_stack.addWidget(page)
            apply_card_polish(page)
            self.pages[index] = page
        return self.pages[index]

    def _create_page_safely(self, page_name, factory):
        try:
            return factory()
        except Exception as exc:
            fallback = QFrame(self.page_stack)
            layout = QVBoxLayout(fallback)
            error_label = QLabel(f'{page_name} failed to load.\n\n{exc}', fallback)
            error_label.setStyleSheet(f"color:{self.tokens['danger']};")
            layout.addWidget(error_label)
            return fallback

    def _update_stock_countdowns(self):
        try:
            stock_page = self.pages[1]
            if stock_page and hasattr(stock_page, 'update_countdowns'):
                stock_page.update_countdowns()
        except Exception: pass

    def _apply_theme(self, theme):
        self.tokens = apply_app_style(self.window().windowHandle(), theme)
        self.switch_page(self.current_page_index)

    def on_logout(self):
        try:
            if callable(self.on_logout_callback):
                self.on_logout_callback(); return
            parent = self.parentWidget()
            if parent and hasattr(parent, 'show_login'):
                parent.show_login(); return
            QMessageBox.critical(self, 'Logout Error', 'Unable to return to login screen.')
        except Exception as exc:
            QMessageBox.critical(self, 'Logout Error', str(exc))
