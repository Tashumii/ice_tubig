from collections import defaultdict
from PyQt6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget
from models.services.sales_service import SalesService
from views.components.modern_table import ModernTable


class SalesPage(QWidget):
    def __init__(self, sales_service: SalesService, tokens: dict, current_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sales_service = sales_service
        self.tokens = tokens
        self.current_user = current_user
        self._all_sales = []
        self._shift_logs = []
        self.setStyleSheet(f"background:{self.tokens['bg_base']};")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # ── Header ──────────────────────────────────────────────────────────
        header = QHBoxLayout()
        left = QVBoxLayout()

        title = QLabel('Sales History', self)
        title.setStyleSheet("font-size:24px; font-weight:700;")

        subtitle = QLabel('Revenue, transaction logs, and product-size breakdowns.', self)
        subtitle.setStyleSheet(f"color:{self.tokens['text_secondary']};")

        refresh_button = QPushButton('REFRESH', self)
        refresh_button.clicked.connect(self.refresh)
        self.employee_filter = QComboBox(self)
        self.employee_filter.currentTextChanged.connect(self._apply_sales_filter)
        self.employee_filter.setMinimumWidth(180)
        left.addWidget(title)
        left.addWidget(subtitle)
        header.addLayout(left); header.addStretch(); header.addWidget(refresh_button)
        if self._is_admin():
            header.addWidget(self.employee_filter)
        root.addLayout(header)

        # ── Shift controls ────────────────────────────────────────────────────
        shift_control = QFrame(self)
        shift_control.setProperty("card", True)
        shift_layout = QHBoxLayout(shift_control)
        shift_layout.addWidget(QLabel("Shift Attendance", shift_control))
        self.shift_schedule_label = QLabel("", shift_control)
        self.shift_schedule_label.setStyleSheet(f"color:{self.tokens['text_secondary']};")
        self.shift_status_label = QLabel("", shift_control)
        self.shift_status_label.setStyleSheet(f"color:{self.tokens['accent_1']};")
        shift_layout.addWidget(self.shift_schedule_label)
        shift_layout.addWidget(self.shift_status_label, 1)
        self.on_site_btn = QPushButton("On Site", shift_control)
        self.on_site_btn.clicked.connect(self._clock_in)
        # Only staff members should use clock in/out
        self.on_site_btn.setEnabled(self._is_staff())
        self.out_btn = QPushButton("Time Out", shift_control)
        self.out_btn.clicked.connect(self._clock_out)
        # Only staff members should use clock in/out
        self.out_btn.setEnabled(self._is_staff())
        shift_layout.addWidget(self.on_site_btn)
        shift_layout.addWidget(self.out_btn)
        root.addWidget(shift_control)

        # ── KPI metric cards ─────────────────────────────────────────────────
        kpi_frame = QFrame(self); kpi_frame.setProperty("card", True)
        kpi_layout = QGridLayout(kpi_frame)

        self._total_card = self._metric_card(kpi_layout, 'Total Revenue', '₱ 0.00', col=0, accent=True)
        self._count_card = self._metric_card(kpi_layout, 'Transactions', '0', col=1)
        self._avg_card = self._metric_card(kpi_layout, 'Avg. Sale', '₱ 0.00', col=2)
        self._top_kg_card = self._metric_card(kpi_layout, 'Top Weight', 'N/A', col=3)
        root.addWidget(kpi_frame)

        # ── Size breakdown strip ─────────────────────────────────────────────
        breakdown_frame = QFrame(self); breakdown_frame.setProperty("card", True)
        breakdown_layout = QHBoxLayout(breakdown_frame)

        breakdown_layout.addWidget(QLabel('By Weight', breakdown_frame))
        self.kg_revenue_label = QLabel('No sales recorded yet.', breakdown_frame)
        breakdown_layout.addWidget(self.kg_revenue_label, 1)
        root.addWidget(breakdown_frame)

        # ── Transactions table ───────────────────────────────────────────────
        table_frame = QFrame(self); table_frame.setProperty("card", True)
        table_layout = QVBoxLayout(table_frame)

        table_header = QHBoxLayout()
        table_header.addWidget(QLabel('Transactions', table_frame))
        table_header.addStretch()
        self._row_count_label = QLabel('', table_frame)
        table_header.addWidget(self._row_count_label)
        table_layout.addLayout(table_header)

        columns = ('sale_id', 'stock_id', 'added', 'sold_at', 'product', 'price', 'weight', 'seller', 'shift')
        self.sales_table = ModernTable(table_frame, columns=columns, tokens=self.tokens)
        table_layout.addWidget(self.sales_table)
        root.addWidget(table_frame, 1)

        # Admin shift-performance table
        self.shift_frame = QFrame(self)
        self.shift_frame.setProperty("card", True)
        shift_layout = QVBoxLayout(self.shift_frame)
        shift_header = QHBoxLayout()
        shift_header.addWidget(QLabel('Employee Shift Performance', self.shift_frame))
        shift_header.addStretch()
        self.shift_count_label = QLabel('', self.shift_frame)
        shift_header.addWidget(self.shift_count_label)
        shift_layout.addLayout(shift_header)
        self.shift_table = ModernTable(
            self.shift_frame,
            columns=('employee', 'shift', 'sales_count', 'revenue'),
            tokens=self.tokens,
        )
        shift_layout.addWidget(self.shift_table)
        if self._is_admin():
            root.addWidget(self.shift_frame, 1)

        # Attendance logs
        self.attendance_frame = QFrame(self)
        self.attendance_frame.setProperty("card", True)
        attendance_layout = QVBoxLayout(self.attendance_frame)
        attendance_header = QHBoxLayout()
        attendance_header.addWidget(QLabel("Shift Attendance Logs", self.attendance_frame))
        attendance_header.addStretch()
        self.attendance_count = QLabel("", self.attendance_frame)
        attendance_header.addWidget(self.attendance_count)
        attendance_layout.addLayout(attendance_header)
        self.attendance_table = ModernTable(
            self.attendance_frame,
            columns=("employee", "date", "expected_in", "actual_in", "expected_out", "actual_out", "status"),
            tokens=self.tokens,
        )
        attendance_layout.addWidget(self.attendance_table)
        root.addWidget(self.attendance_frame, 1)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _metric_card(self, parent, title: str, value: str, col: int, accent: bool = False):
        """Return a styled metric card; the value label is the returned widget."""
        frame = QFrame(self)
        frame.setProperty("panel", True)
        layout = QVBoxLayout(frame)

        value_color = self.tokens['success'] if accent else self.tokens['text_primary']
        value_label = QLabel(value, frame)
        value_label.setStyleSheet(f"font-size:22px; font-weight:700; color:{value_color};")
        title_label = QLabel(title, frame)
        layout.addWidget(value_label); layout.addWidget(title_label)
        parent.addWidget(frame, 0, col)
        return value_label

    def _is_admin(self) -> bool:
        roles = getattr(self.current_user, "roles", []) or []
        return "admin" in roles
    
    def _is_staff(self) -> bool:
        roles = getattr(self.current_user, "roles", []) or []
        return "staff" in roles

    # ── Data ─────────────────────────────────────────────────────────────────

    def refresh(self):
        schedule = self.sales_service.get_shift_schedule()
        self.shift_schedule_label.setText(
            f"Shift In {schedule['shift_start_time']} · Out {schedule['shift_end_time']}"
        )
        self._all_sales = self.sales_service.get_sales_history()
        self._populate_employee_filter(self._all_sales)
        self._apply_sales_filter()
        self._refresh_shift_table()
        self._refresh_attendance_table()

    def _populate_employee_filter(self, sales):
        if not self._is_admin():
            return
        current = self.employee_filter.currentText() if self.employee_filter.count() else "All"
        self.employee_filter.blockSignals(True)
        self.employee_filter.clear()
        self.employee_filter.addItem("All")
        usernames = sorted({sale.sold_by_username for sale in sales if sale.sold_by_username})
        for name in usernames:
            self.employee_filter.addItem(name)
        idx = max(self.employee_filter.findText(current), 0)
        self.employee_filter.setCurrentIndex(idx)
        self.employee_filter.blockSignals(False)

    def _apply_sales_filter(self):
        if self._is_admin():
            selected = "All"
            if self.employee_filter.count():
                selected = self.employee_filter.currentText()
            filtered_sales = self._all_sales
            if selected and selected != "All":
                filtered_sales = [sale for sale in self._all_sales if sale.sold_by_username == selected]
        else:
            username = getattr(self.current_user, "username", "")
            filtered_sales = [sale for sale in self._all_sales if sale.sold_by_username == username]

        total_revenue = 0.0
        kg_revenue: dict[float, float] = defaultdict(float)

        rows = []
        for sale in filtered_sales:
            rows.append({
                'sale_id': f'#{sale.sale_id}',
                'stock_id': f'#{sale.stock_id}',
                'added': sale.added.strftime('%b %d, %Y %I:%M %p'),
                'sold_at': sale.sold_at.strftime('%b %d, %Y %I:%M %p'),
                'product': sale.product_name,
                'price': f'₱ {sale.price:.2f}',
                'weight': f'{sale.kg} kg',
                'seller': sale.sold_by_username or 'Unassigned',
                'shift': sale.shift_name or 'N/A',
            })
            total_revenue += sale.price
            kg_revenue[sale.kg] += sale.price

        self.sales_table.insert_rows(rows)

        # KPI cards
        count = len(rows)
        avg = total_revenue / count if count else 0.0
        top_kg = max(kg_revenue, key=kg_revenue.__getitem__) if kg_revenue else None

        self._total_card.setText(f'₱ {total_revenue:,.2f}')
        self._count_card.setText(str(count))
        self._avg_card.setText(f'₱ {avg:,.2f}')
        self._top_kg_card.setText(f'{top_kg:g} kg' if top_kg is not None else 'N/A')

        # Row count badge
        self._row_count_label.setText(f'{count} record{"s" if count != 1 else ""}')

        # Weight breakdown strip
        if kg_revenue:
            self.kg_revenue_label.setText('   ·   '.join(f'{kg:g} kg  →  ₱ {amount:,.2f}' for kg, amount in sorted(kg_revenue.items())))
        else:
            self.kg_revenue_label.setText('No sales recorded yet.')

    def _refresh_shift_table(self):
        if not self._is_admin():
            return
        rows = []
        for item in self.sales_service.get_employee_shift_summary():
            rows.append({
                "employee": item["username"],
                "shift": item["shift"],
                "sales_count": str(item["sales_count"]),
                "revenue": f"₱ {item['total_revenue']:,.2f}",
            })
        self.shift_table.insert_rows(rows)
        self.shift_count_label.setText(f"{len(rows)} shift rows")

    def _refresh_attendance_table(self):
        user_id = None if self._is_admin() else getattr(self.current_user, "user_id", None)
        logs = self.sales_service.get_shift_logs(user_id)
        self._shift_logs = logs
        rows = []
        for log in logs:
            rows.append(
                {
                    "_iid": str(log["log_id"]),
                    "employee": log["username"],
                    "date": log["shift_date"],
                    "expected_in": log["expected_in"],
                    "actual_in": log["actual_in"] or "N/A",
                    "expected_out": log["expected_out"],
                    "actual_out": log["actual_out"] or "N/A",
                    "status": log["status"],
                }
            )
        self.attendance_table.insert_rows(rows)
        self.attendance_count.setText(f"{len(rows)} logs")
        if rows:
            self.shift_status_label.setText(f"Today: {rows[0]['status']}")
        else:
            self.shift_status_label.setText("Today: OFFSITE")

    def _clock_in(self):
        user_id = getattr(self.current_user, "user_id", None)
        if user_id is None:
            QMessageBox.warning(self, "Account Error", "Unable to identify your account.")
            return
        try:
            self.sales_service.clock_in(user_id)
            self.refresh()
            QMessageBox.information(self, "Shift Updated", "You are now marked as On Site.")
        except Exception as exc:
            QMessageBox.critical(self, "Shift Error", str(exc))

    def _clock_out(self):
        user_id = getattr(self.current_user, "user_id", None)
        if user_id is None:
            QMessageBox.warning(self, "Account Error", "Unable to identify your account.")
            return
        try:
            self.sales_service.clock_out(user_id)
            self.refresh()
            QMessageBox.information(self, "Shift Updated", "Time Out recorded.")
        except Exception as exc:
            QMessageBox.critical(self, "Shift Error", str(exc))