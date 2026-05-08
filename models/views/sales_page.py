from collections import defaultdict
from datetime import date
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
import qtawesome as qta
from models.services.sales_service import SalesService
from utils import format_currency, friendly_error, humanize_name, humanize_status, is_admin, is_staff
from .components.modern_table import ModernTable


class SalesPage(QWidget):
    def __init__(self, sales_service, tokens, current_user=None, *args, **kwargs):
        # Initializes object
        super().__init__(*args, **kwargs)
        self.sales_service = sales_service
        self.tokens = tokens
        self.current_user = current_user
        self._cached_sales = []
        self._shift_logs = []
        self._active_search_query = ""
        self.setStyleSheet("background:transparent;")
        self._apply_modern_styling()
        self._build_ui()
        self.refresh()

    def _apply_modern_styling(self):
        # Apply styling
        """Apply modern glassmorphic styling to all cards and components."""
        self.setStyleSheet(f"""
            QWidget {{ background: transparent; }}
            QFrame[card="true"] {{
                background: {self.tokens.get('bg_surface', 'rgba(8, 20, 38, 0.92)')};
                border: 1px solid {self.tokens.get('card_border', 'rgba(100, 184, 224, 0.25)')};
                border-radius: 12px;
                padding: 0px;
            }}
            QLabel[cardTitle="true"] {{
                color: {self.tokens.get('text_primary', '#EDF6FC')};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }}
            QLabel[kpiValue="true"] {{
                color: {self.tokens.get('accent_1', '#64B8E0')};
                font-size: 20px;
                font-weight: 800;
                background: transparent;
            }}
            QLabel[kpiLabel="true"] {{
                color: {self.tokens.get('text_secondary', '#93C5E8')};
                font-size: 12px;
                background: transparent;
            }}
            QLabel[muted="true"] {{
                color: {self.tokens.get('text_muted', '#5F9CC0')};
                font-size: 13px;
                background: transparent;
            }}
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.tokens.get('accent_1', '#64B8E0')}, stop:1 {self.tokens.get('accent_2', '#3FA9D6')});
                color: white;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 1px;
                border: 2px solid transparent;
                border-radius: 8px;
                padding: 8px 16px;
                cursor: pointer;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.tokens.get('accent_2', '#3FA9D6')}, stop:1 #2E7FAD);
                border: 2px solid rgba(255, 255, 255, 0.4);
                box-shadow: 0 0 16px rgba(100, 184, 224, 0.6);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2E7FAD, stop:1 #1E5A7E);
                border: 2px solid rgba(255, 255, 255, 0.2);
            }}
            QPushButton:focus {{
                outline: none;
            }}
        """)

    def _add_card_shadow(self, widget):
        # Adds shadow
        """Add drop shadow effect to a card widget."""
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 40))
        widget.setGraphicsEffect(shadow)

    def _build_ui(self):
        # Build ui
        root = QVBoxLayout(self)
        # Header
        header = QHBoxLayout(); left = QVBoxLayout()
        title = QLabel('Sales History', self); title.setProperty('pageTitle', True)
        subtitle = QLabel('Revenue, sales records, and product-size breakdowns.', self)
        subtitle.setProperty('muted', True)
        refresh_btn = QPushButton('REFRESH', self)
        refresh_btn.setIcon(qta.icon('fa5s.sync-alt', color=self.tokens['accent_1']))
        refresh_btn.clicked.connect(self.refresh)
        self.employee_filter = QComboBox(self)
        self.employee_filter.currentTextChanged.connect(self._apply_sales_filter)
        self.employee_filter.setMinimumWidth(180)
        left.addWidget(title); left.addWidget(subtitle)
        header.addLayout(left); header.addStretch(); header.addWidget(refresh_btn)
        header.addWidget(self.employee_filter)
        root.addLayout(header)

        # Shift controls
        shift_card = QFrame(self); shift_card.setProperty("card", True); self._add_card_shadow(shift_card)
        shift_layout = QHBoxLayout(shift_card); shift_layout.setContentsMargins(20, 16, 20, 16); shift_layout.setSpacing(12)
        sl = QLabel("Shift Attendance", shift_card); sl.setProperty('cardTitle', True)
        shift_layout.addWidget(sl)
        self.shift_schedule_label = QLabel("", shift_card)
        self.shift_schedule_label.setProperty('muted', True)
        self.shift_status_label = QLabel("", shift_card)
        self.shift_status_label.setStyleSheet(f"color:{self.tokens['accent_1']};font-weight:600;")
        shift_layout.addWidget(self.shift_schedule_label)
        shift_layout.addWidget(self.shift_status_label, 1)
        self.clock_in_button = QPushButton("On Site", shift_card)
        self.clock_in_button.clicked.connect(self._clock_in)
        self.clock_in_button.setEnabled(is_staff(self.current_user))
        self.clock_out_button = QPushButton("Time Out", shift_card)
        self.clock_out_button.clicked.connect(self._clock_out)
        self.clock_out_button.setEnabled(is_staff(self.current_user))
        shift_layout.addWidget(self.clock_in_button); shift_layout.addWidget(self.clock_out_button)
        root.addWidget(shift_card)

        # KPI cards
        kpi_frame = QFrame(self); kpi_frame.setProperty("card", True); self._add_card_shadow(kpi_frame)
        kpi_grid = QGridLayout(kpi_frame); kpi_grid.setContentsMargins(20, 16, 20, 16); kpi_grid.setSpacing(12)
        self._total_card = self._metric_card(kpi_grid, 'Total Revenue', '\u20b1 0.00', col=0, accent=True)
        self._count_card = self._metric_card(kpi_grid, 'Transactions', '0', col=1)
        self._avg_card = self._metric_card(kpi_grid, 'Avg. Sale', '\u20b1 0.00', col=2)
        self._top_kg_card = self._metric_card(kpi_grid, 'Top Weight', 'Not recorded', col=3)
        root.addWidget(kpi_frame)

        # Size breakdown
        breakdown_frame = QFrame(self); breakdown_frame.setProperty("card", True); self._add_card_shadow(breakdown_frame)
        bd_layout = QHBoxLayout(breakdown_frame); bd_layout.setContentsMargins(20, 16, 20, 16); bd_layout.setSpacing(12)
        bwl = QLabel('By Weight', breakdown_frame); bwl.setProperty('cardTitle', True)
        bd_layout.addWidget(bwl)
        self.kg_revenue_label = QLabel('No sales recorded yet.', breakdown_frame)
        bd_layout.addWidget(self.kg_revenue_label, 1)
        root.addWidget(breakdown_frame)

        # Transactions table
        table_frame = QFrame(self); table_frame.setProperty("card", True); self._add_card_shadow(table_frame)
        table_layout = QVBoxLayout(table_frame); table_layout.setContentsMargins(20, 16, 20, 16)
        tl = QLabel('Transactions', table_frame); tl.setProperty('cardTitle', True)
        th = QHBoxLayout(); th.addWidget(tl); th.addStretch()
        self._row_count_label = QLabel('', table_frame); th.addWidget(self._row_count_label)
        table_layout.addLayout(th)
        self.sales_table = ModernTable(table_frame,
            columns=('sale_id','stock_id','added','sold_at','product','price','weight','seller','shift'), tokens=self.tokens)
        table_layout.addWidget(self.sales_table)
        root.addWidget(table_frame, 1)

        # Admin shift-performance table
        self.shift_frame = QFrame(self); self.shift_frame.setProperty("card", True); self._add_card_shadow(self.shift_frame)
        sf_layout = QVBoxLayout(self.shift_frame); sf_layout.setContentsMargins(20, 16, 20, 16)
        espl = QLabel('Employee Shift Performance', self.shift_frame); espl.setProperty('cardTitle', True)
        sh = QHBoxLayout(); sh.addWidget(espl); sh.addStretch()
        self.shift_count_label = QLabel('', self.shift_frame); sh.addWidget(self.shift_count_label)
        sf_layout.addLayout(sh)
        self.shift_table = ModernTable(self.shift_frame, columns=('employee','shift','sales_count','revenue'), tokens=self.tokens)
        sf_layout.addWidget(self.shift_table)
        root.addWidget(self.shift_frame, 1)

        # Attendance records
        self.attendance_frame = QFrame(self); self.attendance_frame.setProperty("card", True)
        att_layout = QVBoxLayout(self.attendance_frame)
        sarl = QLabel("Shift Attendance Records", self.attendance_frame); sarl.setProperty('cardTitle', True)
        ah = QHBoxLayout(); ah.addWidget(sarl); ah.addStretch()
        self.attendance_count = QLabel("", self.attendance_frame); ah.addWidget(self.attendance_count)
        att_layout.addLayout(ah)
        self.attendance_table = ModernTable(self.attendance_frame,
            columns=("employee","date","expected_in","actual_in","expected_out","actual_out","status"), tokens=self.tokens)
        att_layout.addWidget(self.attendance_table)
        root.addWidget(self.attendance_frame, 1)

    def _metric_card(self, parent_grid, title, value, col, accent=False):
        # Metric card
        frame = QFrame(self); frame.setProperty("panel", True)
        layout = QVBoxLayout(frame)
        val_label = QLabel(value, frame); val_label.setProperty('kpiValue', True)
        if accent:
            val_label.setStyleSheet(f"font-size:22px;font-weight:800;color:{self.tokens['success']};")
        title_label = QLabel(title, frame); title_label.setProperty('kpiLabel', True)
        layout.addWidget(val_label); layout.addWidget(title_label)
        parent_grid.addWidget(frame, 0, col)
        return val_label

    def refresh(self):
        # Refreshes data
        user_id = getattr(self.current_user, 'user_id', None)
        schedule = self.sales_service.get_shift_schedule(user_id if is_staff(self.current_user) else None)
        self.shift_schedule_label.setText(f"Time In {schedule['shift_start_time']} \u00b7 Time Out {schedule['shift_end_time']}")
        self._cached_sales = self.sales_service.get_sales_history()
        self._populate_employee_filter(self._cached_sales)
        self._apply_sales_filter()
        self._refresh_shift_table()
        self._refresh_attendance_table()

    def _populate_employee_filter(self, sales):
        # Populate employee filter for all roles for UI consistency
        current = self.employee_filter.currentText() if self.employee_filter.count() else "All"
        self.employee_filter.blockSignals(True)
        self.employee_filter.clear(); self.employee_filter.addItem("All")
        for name in sorted({s.sold_by_username for s in sales if s.sold_by_username}):
            self.employee_filter.addItem(name)
        self.employee_filter.setCurrentIndex(max(self.employee_filter.findText(current), 0))
        self.employee_filter.blockSignals(False)

    def _apply_sales_filter(self):
        # Apply filter
        selected = self.employee_filter.currentText() if self.employee_filter.count() else "All"
        filtered = self._cached_sales if selected == "All" else [s for s in self._cached_sales if s.sold_by_username == selected]
        filtered = self._filter_sales_by_query(filtered)
        total_revenue = 0.0; kg_revenue = defaultdict(float); rows = []
        for sale in filtered:
            rows.append({
                'sale_id': f'#{sale.sale_id}', 'stock_id': f'#{sale.stock_id}',
                'added': sale.added.strftime('%b %d, %Y %I:%M %p'),
                'sold_at': sale.sold_at.strftime('%b %d, %Y %I:%M %p'),
                'product': sale.product_name, 'price': format_currency(sale.price),
                'weight': f'{sale.kg:g} kg', 'seller': humanize_name(sale.sold_by_username),
                'shift': humanize_name(sale.shift_name, "No shift"),
            })
            total_revenue += sale.price; kg_revenue[sale.kg] += sale.price
        self.sales_table.insert_rows(rows)
        count = len(rows); avg = total_revenue / count if count else 0.0
        top_kg = max(kg_revenue, key=kg_revenue.__getitem__) if kg_revenue else None
        self._total_card.setText(format_currency(total_revenue))
        self._count_card.setText(str(count))
        self._avg_card.setText(format_currency(avg))
        self._top_kg_card.setText(f'{top_kg:g} kg' if top_kg is not None else 'Not recorded')
        self._row_count_label.setText(f'{count} record{"s" if count != 1 else ""}')
        self.kg_revenue_label.setText(
            '   \u00b7   '.join(f'{kg:g} kg  \u2192  {format_currency(amt)}' for kg, amt in sorted(kg_revenue.items()))
            if kg_revenue else 'No sales recorded yet.')

    def _filter_sales_by_query(self, sales):
        # Filter query
        q = self._active_search_query.strip().lower()
        if not q: return sales
        def matches(s):
            # Matches data
            vals = (str(s.sale_id), f"#{s.sale_id}", str(s.stock_id), f"#{s.stock_id}",
                s.product_name, f"{s.price:.2f}", f"{s.kg:g}", f"{s.kg:g} kg",
                humanize_name(s.sold_by_username), humanize_name(s.shift_name, "No shift"),
                s.added.strftime('%b %d, %Y %I:%M %p'), s.sold_at.strftime('%b %d, %Y %I:%M %p'))
            return any(q in str(v).lower() for v in vals)
        return [s for s in sales if matches(s)]

    def search(self, query):
        # Search data
        self._active_search_query = query or ""
        self._apply_sales_filter()

    def _refresh_shift_table(self):
        # Allow staff to see the shift table layout
        rows = [{"employee": i["username"], "shift": humanize_name(i["shift"], "No shift"),
                 "sales_count": str(i["sales_count"]), "revenue": format_currency(i['total_revenue'])}
                for i in self.sales_service.get_employee_shift_summary()]
        self.shift_table.insert_rows(rows)
        self.shift_count_label.setText(f"{len(rows)} shift record{'s' if len(rows) != 1 else ''}")

    def _refresh_attendance_table(self):
        # Refreshes table
        user_id = None  # Show all attendance records to match admin design
        logs = self.sales_service.get_shift_logs(user_id); self._shift_logs = logs
        rows = [{"_iid": str(l["log_id"]), "employee": l["username"], "date": l["shift_date"],
                 "expected_in": l["expected_in"], "actual_in": l["actual_in"] or "Not recorded",
                 "expected_out": l["expected_out"], "actual_out": l["actual_out"] or "Not recorded",
                 "status": humanize_status(l["status"])} for l in logs]
        self.attendance_table.insert_rows(rows)
        self.attendance_count.setText(f"{len(rows)} attendance record{'s' if len(rows) != 1 else ''}")
        today = date.today().isoformat()
        today_row = next((r for r in rows if r["date"] == today), None)
        self.shift_status_label.setText(f"Today: {today_row['status']}" if today_row else "Today: Not On Site")

    def _clock_in(self):
        # Clock in
        user_id = getattr(self.current_user, "user_id", None)
        if user_id is None:
            QMessageBox.warning(self, "Account Error", "Unable to identify your account."); return
        try:
            self.sales_service.clock_in(user_id); self.refresh()
            QMessageBox.information(self, "Shift Updated", "You are now marked as On Site.")
        except Exception as exc:
            QMessageBox.critical(self, "Shift Error", friendly_error(exc))

    def _clock_out(self):
        # Clock out
        user_id = getattr(self.current_user, "user_id", None)
        if user_id is None:
            QMessageBox.warning(self, "Account Error", "Unable to identify your account."); return
        try:
            self.sales_service.clock_out(user_id); self.refresh()
            QMessageBox.information(self, "Shift Updated", "Time Out recorded.")
        except Exception as exc:
            QMessageBox.critical(self, "Shift Error", friendly_error(exc))
