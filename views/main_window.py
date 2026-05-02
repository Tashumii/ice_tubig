from PyQt6.QtCore import QTimer, Qt
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
from utils import clean_display_text, humanize_name, humanize_status
from views.dashboard_page import DashboardPage
from views.sales_page import SalesPage
from views.settings_page import SettingsPage
from views.stock_page import StockPage
from views.reports_page import ReportsPage
from views.announcements_page import AnnouncementsPage
from views.components.native_polish import FadeStackedWidget, apply_card_polish


# Nav item definitions: (label, page_index, icon)
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
        self,
        inventory_service: InventoryService,
        sales_service: SalesService,
        settings_service: SettingsService,
        auth_service: AuthService,
        report_service: ReportService = None,
        announcement_service: AnnouncementService = None,
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
        self.announcement_service = announcement_service
        self.on_logout_callback = on_logout_callback
        self.current_user = current_user
        self._notification_cache = []
        self.search_menu = None

        self.tokens = tokens if tokens is not None else apply_app_style(self.window().windowHandle(), self.settings_service.get_theme())
        self.device_type = ResponsiveHelper.get_device_type()
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._run_global_search)
        self._build_ui()

        self.page_names = [label for label, _, _ in _NAV_ITEMS]
        self.page_factories = [
            lambda: DashboardPage(self.inventory_service, self.sales_service, self.tokens, self.current_user, self.page_host),
            lambda: StockPage(self.inventory_service, self.tokens, self.current_user, self.page_host),
            lambda: SalesPage(self.sales_service, self.tokens, self.current_user, self.page_host),
            lambda: ReportsPage(self.report_service, self.tokens, self.page_host),
            lambda: AnnouncementsPage(self.announcement_service, self.current_user, self.tokens, self.page_host),
            lambda: SettingsPage(self.settings_service, self.auth_service, self.current_user, self._apply_theme, self.tokens, self.page_host),
        ]
        self.pages = [None] * len(self.page_names)
        self.current_page_index = 1

        QTimer.singleShot(10, lambda: self.switch_page(1))
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self._tick)
        self.tick_timer.start(1000)

        if self._is_admin():
            self.notification_timer = QTimer(self)
            self.notification_timer.timeout.connect(self._refresh_notification_bell)
            self.notification_timer.start(10000)
            QTimer.singleShot(250, self._refresh_notification_bell)

    def _build_ui(self):
        root = QHBoxLayout(self)
        spacing = ResponsiveHelper.get_spacing(self.device_type)
        margins = ResponsiveHelper.get_margins(self.device_type)
        root.setContentsMargins(*margins)
        root.setSpacing(spacing)
        
        # Show sidebar only on larger screens
        if ResponsiveHelper.should_show_sidebar(self.device_type):
            self._build_sidebar(root)
        
        self._build_content(root)
        apply_card_polish(self)

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self, root_layout):
        self.sidebar = QFrame(self)
        self.sidebar.setProperty("shell", True)
        self.sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background: {self.tokens['bg_sidebar']};
            }}
            QLabel {{
                color: {self.tokens['sidebar_text_primary']};
            }}
        """)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        # Responsive sidebar width
        if self.device_type == "tablet":
            self.sidebar.setMinimumWidth(140)
            self.sidebar.setMaximumWidth(180)
        else:
            self.sidebar.setMinimumWidth(180)
            self.sidebar.setMaximumWidth(260)
        
        side_layout = QVBoxLayout(self.sidebar)
        spacing = ResponsiveHelper.get_spacing(self.device_type)
        side_layout.setContentsMargins(spacing, spacing + 2, spacing, spacing)
        side_layout.setSpacing(spacing - 2)

        # ── Logo block ────────────────────────────────────────────────────────
        brand_title = QLabel('ICETUBIG', self.sidebar)
        brand_title.setProperty("brandTitle", True)
        brand_title.setStyleSheet(f"color: {self.tokens['accent_1']}; font-size: 30px; font-weight: 800; letter-spacing: 0.5px;")
        brand_sub = QLabel('COLD CHAIN DASHBOARD', self.sidebar)
        brand_sub.setProperty("brandSub", True)
        brand_sub.setStyleSheet(f"color: {self.tokens['sidebar_text_secondary']}; font-size: 11px; font-weight: 600; letter-spacing: 1.5px;")
        side_layout.addWidget(brand_title)
        side_layout.addWidget(brand_sub)

        # ── Divider ───────────────────────────────────────────────────────────
        side_layout.addSpacing(8)

        # ── Nav items ─────────────────────────────────────────────────────────
        self.navigation_buttons = []
        for (label, idx, icon) in _NAV_ITEMS:
            item = self._nav_item(label, idx, icon)
            side_layout.addWidget(item['button'])
            self.navigation_buttons.append(item)

        # ── Spacer (row 90 has weight=1) ──────────────────────────────────────

        # ── Divider above footer ──────────────────────────────────────────────
        side_layout.addStretch()
        logout_btn = QPushButton('Logout', self.sidebar)
        logout_btn.setProperty("danger", True)
        logout_btn.setIcon(qta.icon('fa5s.sign-out-alt', color=self.tokens['danger']))
        logout_btn.clicked.connect(self.on_logout)
        side_layout.addWidget(logout_btn)
        version = QLabel('v2.0.0 · 2026', self.sidebar)
        version.setProperty("muted", True)
        version.setStyleSheet(f"color: {self.tokens['sidebar_text_muted']}; font-size: 13px;")
        side_layout.addWidget(version)
        root_layout.addWidget(self.sidebar, 0)

    def _nav_item(self, label: str, idx: int, icon: str) -> dict:
        button = QPushButton(label, self.sidebar)
        button.setProperty("nav", True)
        button.setIcon(qta.icon(icon, color=self.tokens['sidebar_text_primary']))
        button.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 12px 14px;
                border-radius: 6px;
                background: transparent;
                color: {self.tokens['sidebar_text_primary']};
                border: 1px solid transparent;
                font-size: 13px;
                font-weight: 500;
                transition: all 0.2s ease;
                icon-size: 16px;
            }}
            QPushButton:hover {{
                background: {self.tokens['nav_hover']};
                border: 1px solid {self.tokens['border']};
                color: {self.tokens['accent_2']};
            }}
        """)
        button.clicked.connect(lambda: self.switch_page(idx))
        return {'button': button}

    # ── Content area ──────────────────────────────────────────────────────────

    def _build_content(self, root_layout):
        self.content_frame = QFrame(self)
        self.content_frame.setProperty("shell", True)
        self.content_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content = QVBoxLayout(self.content_frame)
        content.setContentsMargins(10, 10, 10, 10)
        content.setSpacing(10)

        topbar_frame = QFrame(self.content_frame)
        topbar_frame.setProperty("topbar", True)
        topbar = QHBoxLayout(topbar_frame)
        topbar.setContentsMargins(10, 8, 10, 8)
        topbar.setSpacing(8)

        self.search_input = QLineEdit(self.content_frame)
        self.search_input.setPlaceholderText('Search stocks, sales, staff, reports…')
        self.search_input.setMaxLength(100)
        self.search_input.addAction(
            qta.icon('fa5s.search', color=self.tokens['text_secondary']),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.page_status_label = QLabel('', self.content_frame)
        self.page_status_label.setProperty("pill", True)
        profile_name = getattr(self.current_user, "username", "Admin") if self.current_user else "Admin"
        profile = QPushButton(profile_name.title(), self.content_frame)
        profile.setProperty("nav", True)
        profile.setProperty("navActive", True)
        topbar.addWidget(self.search_input, 1)
        topbar.addWidget(self.page_status_label)
        if self._is_admin():
            self.notification_button = QPushButton(self.content_frame)
            self.notification_button.setObjectName("notificationBell")
            self.notification_button.setIcon(qta.icon('fa5s.bell', color=self.tokens['text_secondary']))
            self.notification_button.setToolTip("Staff activity notifications")
            self.notification_button.clicked.connect(self._show_notifications)
            self.notification_button.setStyleSheet(f"""
                QPushButton#notificationBell {{
                    min-width: 42px;
                    padding: 8px 10px;
                    border-radius: 6px;
                    border: 1px solid {self.tokens['border']};
                    background: {self.tokens['bg_surface']};
                    color: {self.tokens['text_primary']};
                    font-weight: 700;
                    text-align: center;
                }}
                QPushButton#notificationBell:hover {{
                    border-color: {self.tokens['accent_1']};
                    background: {self.tokens['bg_elevated']};
                }}
            """)
            topbar.addWidget(self.notification_button)
        topbar.addWidget(profile)
        content.addWidget(topbar_frame)
        self.page_host = FadeStackedWidget(self.content_frame)
        self.page_host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content.addWidget(self.page_host, 1)

        self.content_scroll = QScrollArea(self)
        self.content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_scroll.setStyleSheet("QScrollArea { border: none; }")
        self.content_scroll.setWidget(self.content_frame)
        root_layout.addWidget(self.content_scroll, 1)

    # ── Navigation ────────────────────────────────────────────────────────────

    def switch_page(self, index: int):
        if index < 0 or index >= len(self.page_names):
            return

        self.current_page_index = index

        for nav_idx, item in enumerate(self.navigation_buttons):
            active = nav_idx == index
            btn = item['button']
            if active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        text-align: left;
                        padding: 12px 14px;
                        border-radius: 6px;
                        background: {self.tokens['nav_active_bg']};
                        color: white;
                        border: 1px solid {self.tokens['nav_active_bg']};
                        font-size: 13px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background: #2563EB;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        text-align: left;
                        padding: 12px 14px;
                        border-radius: 6px;
                        background: transparent;
                        color: {self.tokens['sidebar_text_primary']};
                        border: 1px solid transparent;
                        font-size: 13px;
                        font-weight: 500;
                    }}
                    QPushButton:hover {{
                        background: {self.tokens['nav_hover']};
                        border: 1px solid {self.tokens['border']};
                        color: {self.tokens['accent_2']};
                    }}
                """)

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
            self._apply_current_search_to_page()
        except Exception as exc:
            self.page_status_label.setText(f'{page_name}: error')

    def _on_search_text_changed(self, query: str):
        """Handle search input changes and delegate to current page."""
        current_page = self.pages[self.current_page_index]
        if current_page is not None and hasattr(current_page, 'search'):
            try:
                current_page.search(query)
            except Exception as exc:
                print(f"Search error: {exc}")

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

    def _collect_global_search_results(self, query: str):
        query_lower = query.lower()
        results = []

        def matches(*values):
            return query_lower in " ".join(str(value or "") for value in values).lower()

        def add(page_index: int, title: str, detail: str, icon: str):
            if len(results) < 12:
                results.append({
                    "page_index": page_index,
                    "title": title,
                    "detail": detail,
                    "icon": icon,
                })

        try:
            for stock in self.inventory_service.get_active_stocks():
                status = humanize_status(stock.status)
                if matches(stock.stock_id, stock.product_name, stock.kg, stock.price, status):
                    add(
                        1,
                        f"Stock #{stock.stock_id} · {stock.product_name}",
                        f"{status} · {stock.kg:g} kg · ₱ {stock.price:,.2f}",
                        'fa5s.box',
                    )
        except Exception:
            pass

        try:
            sales = self.sales_service.get_sales_history()
            if not self._is_admin():
                username = getattr(self.current_user, "username", "")
                sales = [sale for sale in sales if sale.sold_by_username == username]
            for sale in sales:
                seller = humanize_name(sale.sold_by_username)
                shift = humanize_name(sale.shift_name, "No shift")
                if matches(sale.sale_id, sale.stock_id, sale.product_name, seller, shift, sale.price, sale.sold_at):
                    add(
                        2,
                        f"Sale #{sale.sale_id} · {sale.product_name}",
                        f"{seller} · ₱ {sale.price:,.2f} · {sale.sold_at.strftime('%b %d %I:%M %p')}",
                        'fa5s.credit-card',
                    )
        except Exception:
            pass

        try:
            user_id = None if self._is_admin() else getattr(self.current_user, "user_id", None)
            for log in self.sales_service.get_shift_logs(user_id):
                if matches(log.get("username"), log.get("shift_date"), log.get("actual_in"), log.get("actual_out"), log.get("status")):
                    add(
                        2,
                        f"Attendance · {log.get('username')}",
                        f"{log.get('shift_date')} · {log.get('status')}",
                        'fa5s.user-clock',
                    )
        except Exception:
            pass

        try:
            if self.report_service is not None:
                for product in self.report_service.get_top_products(10):
                    if matches(product.get("product_name"), product.get("sale_count"), product.get("total_revenue")):
                        add(
                            3,
                            f"Report · {product.get('product_name')}",
                            f"{product.get('sale_count', 0)} sales · ₱ {product.get('total_revenue', 0):,.2f}",
                            'fa5s.chart-bar',
                        )
        except Exception:
            pass

        try:
            if self.announcement_service is not None:
                announcements = (
                    self.announcement_service.get_all_announcements(self.current_user)
                    if self._is_admin()
                    else self.announcement_service.get_announcements_for_user(self.current_user)
                )
                for ann in announcements:
                    if matches(getattr(ann, "title", ""), getattr(ann, "message", ""), getattr(ann, "created_by", "")):
                        add(
                            4,
                            f"Announcement · {getattr(ann, 'title', 'Untitled')}",
                            f"By {humanize_name(getattr(ann, 'created_by', ''))}",
                            'fa5s.bell',
                        )
        except Exception:
            pass

        try:
            if self._is_admin():
                for account in self.auth_service.list_accounts(self.current_user):
                    status = "Active" if account.get("is_active") else "Disabled"
                    if matches(account.get("username"), account.get("roles"), status):
                        add(
                            5,
                            f"User · {account.get('username')}",
                            f"{account.get('roles') or 'staff'} · {status}",
                            'fa5s.user',
                        )
        except Exception:
            pass

        try:
            if self._is_admin():
                for item in self.sales_service.get_admin_notifications(12):
                    if matches(item.get("title"), item.get("message"), item.get("username"), item.get("event_type")):
                        add(
                            0,
                            clean_display_text(item.get("title")),
                            f"{humanize_name(item.get('username'), 'System')} · {clean_display_text(item.get('message'))}",
                            'fa5s.info-circle',
                        )
        except Exception:
            pass

        return results

    def _show_search_results(self, query: str, results):
        self._close_search_menu()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {self.tokens['bg_surface']};
                color: {self.tokens['text_primary']};
                border: 1px solid {self.tokens['border']};
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                min-width: 430px;
            }}
            QMenu::item:selected {{
                background: {self.tokens['table_row_hover']};
            }}
        """)

        header = menu.addAction(f"Search results for \"{query}\"")
        header.setEnabled(False)
        menu.addSeparator()

        if not results:
            empty_action = menu.addAction("No matching records found.")
            empty_action.setEnabled(False)
        else:
            for result in results:
                action = menu.addAction(
                    qta.icon(result["icon"], color=self.tokens['accent_1']),
                    f"{result['title']}\n{result['detail']}",
                )
                action.triggered.connect(
                    lambda checked=False, page_index=result["page_index"]: self._open_search_result(page_index)
                )

        self.search_menu = menu
        pos = self.search_input.mapToGlobal(self.search_input.rect().bottomLeft())
        menu.popup(pos)

    def _open_search_result(self, page_index: int):
        self._close_search_menu()
        self.switch_page(page_index)
        QTimer.singleShot(150, self._apply_current_search_to_page)

    def _close_search_menu(self):
        menu = getattr(self, "search_menu", None)
        if menu is not None:
            menu.close()
            menu.deleteLater()
            self.search_menu = None

    def _is_admin(self) -> bool:
        roles = getattr(self.current_user, "roles", []) or []
        return "admin" in roles

    def _refresh_notification_bell(self):
        if not self._is_admin() or not hasattr(self, "notification_button"):
            return
        try:
            unread_count = self.sales_service.get_unread_admin_notification_count()
            self._notification_cache = self.sales_service.get_admin_notifications(8)
            if unread_count:
                self.notification_button.setText(str(min(unread_count, 99)))
                self.notification_button.setIcon(qta.icon('fa5s.bell', color=self.tokens['warning']))
                self.notification_button.setToolTip(f"{unread_count} unread staff activity notification{'s' if unread_count != 1 else ''}")
            else:
                self.notification_button.setText("")
                self.notification_button.setIcon(qta.icon('fa5s.bell', color=self.tokens['text_secondary']))
                self.notification_button.setToolTip("No unread staff activity notifications")
        except Exception as exc:
            self.notification_button.setToolTip(f"Unable to load notifications: {exc}")

    def _show_notifications(self):
        if not self._is_admin():
            return

        try:
            notifications = self.sales_service.get_admin_notifications(8)
        except Exception as exc:
            QMessageBox.warning(self, "Notifications", f"Unable to load notifications: {exc}")
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {self.tokens['bg_surface']};
                color: {self.tokens['text_primary']};
                border: 1px solid {self.tokens['border']};
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                min-width: 380px;
            }}
            QMenu::item:selected {{
                background: {self.tokens['table_row_hover']};
            }}
        """)

        title_action = menu.addAction("Staff Activity")
        title_action.setEnabled(False)
        menu.addSeparator()

        if not notifications:
            empty_action = menu.addAction("No staff activity yet.")
            empty_action.setEnabled(False)
        else:
            for item in notifications:
                icon = self._notification_icon(item.get("severity", "info"))
                message = self._format_notification_message(item)
                action = menu.addAction(icon, message)
                action.setEnabled(False)
            menu.addSeparator()

        dashboard_action = menu.addAction(qta.icon('fa5s.chart-line', color=self.tokens['accent_1']), "Open Dashboard Notifications")
        dashboard_action.triggered.connect(lambda: self.switch_page(0))

        pos = self.notification_button.mapToGlobal(self.notification_button.rect().bottomRight())
        menu.exec(pos)

        try:
            self.sales_service.mark_admin_notifications_read()
        except Exception:
            pass
        self._refresh_notification_bell()

    def _notification_icon(self, severity: str):
        normalized = (severity or "info").lower()
        if normalized == "success":
            return qta.icon('fa5s.check-circle', color=self.tokens['success'])
        if normalized == "warning":
            return qta.icon('fa5s.exclamation-triangle', color=self.tokens['warning'])
        if normalized == "danger":
            return qta.icon('fa5s.times-circle', color=self.tokens['danger'])
        return qta.icon('fa5s.info-circle', color=self.tokens['accent_2'])

    def _format_notification_message(self, item: dict) -> str:
        created_at = item.get("created_at", "")
        title = clean_display_text(item.get("title", "Activity"))
        username = humanize_name(item.get("username", "Staff"), "Staff")
        message = clean_display_text(item.get("message", ""))
        return f"{created_at} · {title}\n{username}: {message}"

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
