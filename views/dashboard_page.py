from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from models.sale import Sale
from services.inventory_service import InventoryService
from services.sales_service import SalesService
from views.components.modern_table import ModernTable


class _MiniChart(QWidget):
    def __init__(self, tokens: dict, parent=None):
        super().__init__(parent)
        self.tokens = tokens
        self.points = []
        self.setMinimumHeight(220)

    def set_points(self, points):
        self.points = points
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().window())
        if not self.points:
            painter.drawText(20, self.height() // 2, "No recent sales data")
            return
        values = [v for _, v in self.points]
        max_value = max(max(values), 10.0) * 1.15
        w = max(self.width() - 72, 1)
        h = max(self.height() - 56, 1)
        step = w / max(len(self.points) - 1, 1)
        pen = QPen()
        pen.setColor(Qt.GlobalColor.gray)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        for i in range(5):
            y = 20 + (h * i / 4)
            painter.drawLine(48, int(y), 48 + w, int(y))
        pen.setStyle(Qt.PenStyle.SolidLine)
        pen.setWidth(2)
        pen.setColor(Qt.GlobalColor.red)
        painter.setPen(pen)
        coords = []
        for i, (_, value) in enumerate(self.points):
            x = 48 + i * step
            y = 20 + h - (value / max_value) * h
            coords.append((int(x), int(y)))
        for i in range(1, len(coords)):
            painter.drawLine(coords[i - 1][0], coords[i - 1][1], coords[i][0], coords[i][1])


class DashboardPage(QWidget):
    def __init__(
        self,
        inventory_service: InventoryService,
        sales_service: SalesService,
        tokens: dict,
        current_user=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.inventory_service = inventory_service
        self.sales_service = sales_service
        self.tokens = tokens
        self.current_user = current_user
        self.setStyleSheet(f"background:{self.tokens['bg_base']};")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # ── Header ───────────────────────────────────────────────────────────
        header_frame = QFrame(self)
        header_layout = QHBoxLayout(header_frame)

        left = QVBoxLayout()
        title = QLabel('Dashboard', header_frame)
        title.setStyleSheet("font-size:24px; font-weight:700;")

        subtitle = QLabel('Real-time stock availability, sales performance, and activity trends.', header_frame)
        subtitle.setStyleSheet(f"color:{self.tokens['text_secondary']};")

        self.refresh_button = QPushButton('REFRESH', header_frame)
        self.refresh_button.clicked.connect(self.refresh)
        left.addWidget(title)
        left.addWidget(subtitle)
        header_layout.addLayout(left)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_button)
        root.addWidget(header_frame)

        # ── Inventory status cards ────────────────────────────────────────────
        inv_card = QFrame(self)
        inv_card.setProperty("card", True)
        inv_layout = QGridLayout(inv_card)

        inv_label = QLabel('INVENTORY STATUS', inv_card)
        inv_label.setStyleSheet(f"color:{self.tokens['text_secondary']}; font-size:10px; font-weight:700;")
        inv_layout.addWidget(inv_label, 0, 0, 1, 4)

        self.available_label = self._metric_item(inv_layout, 'Available', 1, 0, accent=self.tokens['success'])
        self.freezing_label = self._metric_item(inv_layout, 'Freezing', 1, 1, accent=self.tokens['accent_1'])
        self.sold_label = self._metric_item(inv_layout, 'Sold', 1, 2)
        self.activity_label = self._metric_item(inv_layout, 'Events', 1, 3)
        root.addWidget(inv_card)

        # ── Sales comparison cards ────────────────────────────────────────────
        cmp_card = QFrame(self)
        cmp_card.setProperty("card", True)
        cmp_layout = QGridLayout(cmp_card)

        cmp_label = QLabel('REVENUE COMPARISON', cmp_card)
        cmp_label.setStyleSheet(f"color:{self.tokens['text_secondary']}; font-size:10px; font-weight:700;")
        cmp_layout.addWidget(cmp_label, 0, 0, 1, 4)

        self.this_month_label = self._metric_item(cmp_layout, 'This Month', 1, 0, accent=self.tokens['accent_1'])
        self.last_month_label = self._metric_item(cmp_layout, 'Last Month', 1, 1)
        self.this_year_label = self._metric_item(cmp_layout, 'This Year', 1, 2, accent=self.tokens['accent_1'])
        self.last_year_label = self._metric_item(cmp_layout, 'Last Year', 1, 3)
        root.addWidget(cmp_card)

        # ── Sales breakdown ───────────────────────────────────────────────────
        breakdown_card = QFrame(self)
        breakdown_card.setProperty("card", True)
        breakdown_layout = QVBoxLayout(breakdown_card)

        breakdown_title = QLabel('Sales Breakdown', breakdown_card)
        breakdown_title.setStyleSheet("font-size:15px; font-weight:700;")

        self.breakdown_text = QLabel('Loading…', breakdown_card)
        self.breakdown_text.setStyleSheet(f"color:{self.tokens['text_secondary']};")
        self.breakdown_text.setWordWrap(True)
        breakdown_layout.addWidget(breakdown_title)
        breakdown_layout.addWidget(self.breakdown_text)
        root.addWidget(breakdown_card)

        # ── Weekly revenue chart ──────────────────────────────────────────────
        chart_card = QFrame(self)
        chart_card.setProperty("card", True)
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.addWidget(QLabel("7-Day Revenue", chart_card))
        self.chart_canvas = _MiniChart(self.tokens, chart_card)
        chart_layout.addWidget(self.chart_canvas)
        root.addWidget(chart_card)

        # ── Data tables (web-like dashboard blocks) ──────────────────────────
        tables_wrap = QHBoxLayout()

        recent_card = QFrame(self)
        recent_card.setProperty("card", True)
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.addWidget(QLabel("Recent Sales", recent_card))
        self.recent_sales_table = ModernTable(
            recent_card,
            columns=("sale_id", "seller", "product", "shift", "price", "sold_at"),
            tokens=self.tokens,
        )
        recent_layout.addWidget(self.recent_sales_table)
        tables_wrap.addWidget(recent_card, 2)

        stock_card = QFrame(self)
        stock_card.setProperty("card", True)
        stock_layout = QVBoxLayout(stock_card)
        stock_layout.addWidget(QLabel("Live Stock Snapshot", stock_card))
        self.stock_snapshot_table = ModernTable(
            stock_card,
            columns=("stock_id", "product", "status", "weight", "price"),
            tokens=self.tokens,
        )
        stock_layout.addWidget(self.stock_snapshot_table)
        tables_wrap.addWidget(stock_card, 1)

        root.addLayout(tables_wrap, 1)

    # ── Metric card helper ────────────────────────────────────────────────────

    def _metric_item(self, parent_layout, title: str, row: int, col: int, accent: str = None):
        frame = QFrame(self)
        frame.setProperty("card", True)
        layout = QVBoxLayout(frame)
        frame.setProperty("panel", True)
        value = QLabel("N/A", frame)
        value.setStyleSheet(f"font-size:22px; font-weight:700; color:{accent or self.tokens['text_primary']};")
        label = QLabel(title, frame)
        label.setStyleSheet(f"font-size:10px; color:{self.tokens['text_secondary']};")
        layout.addWidget(value)
        layout.addWidget(label)
        frame.value_label = value
        parent_layout.addWidget(frame, row, col)
        return frame

    # ── Data ─────────────────────────────────────────────────────────────────

    def refresh(self):
        self.inventory_service.refresh_stock_availability()

        summary = self.inventory_service.get_dashboard_summary()
        self.available_label.value_label.setText(str(summary.available_count))
        self.freezing_label.value_label.setText(str(summary.freezing_count))
        self.sold_label.value_label.setText(str(summary.sold_count))
        self.activity_label.value_label.setText(str(summary.activity_count))

        comparison = self.inventory_service.get_sales_comparison()
        self.this_month_label.value_label.setText(self._fmt(comparison.current_month))
        self.last_month_label.value_label.setText(self._fmt(comparison.previous_month))
        self.this_year_label.value_label.setText(self._fmt(comparison.current_year))
        self.last_year_label.value_label.setText(self._fmt(comparison.previous_year))

        monthly = self.sales_service.get_revenue_by_month(12)
        yearly  = self.sales_service.get_revenue_by_year(5)
        self.breakdown_text.setText(self._format_breakdown(monthly, yearly))
        sales_history = self.sales_service.get_sales_history()
        if not self._is_admin():
            username = getattr(self.current_user, "username", "")
            sales_history = [sale for sale in sales_history if sale.sold_by_username == username]
        self._draw_chart(sales_history)
        self._refresh_data_tables(sales_history)

    def _fmt(self, amount: float) -> str:
        try:
            return f'₱ {float(amount):,.2f}'
        except Exception:
            return '₱ 0.00'

    def _format_breakdown(self, monthly, yearly) -> str:
        monthly_lines = '\n'.join(
            f'  {period}   {self._fmt(total)}' for period, total in monthly
        ) or '  No monthly data'
        yearly_lines = '\n'.join(
            f'  {year}   {self._fmt(total)}' for year, total in yearly
        ) or '  No yearly data'
        return f'Monthly\n{monthly_lines}\n\nYearly\n{yearly_lines}'

    # ── Chart ─────────────────────────────────────────────────────────────────

    def _draw_chart(self, sales: List[Sale]):
        points = self._aggregate_weekly_sales(sales)
        self.chart_canvas.set_points(points)

    def _refresh_data_tables(self, sales: List[Sale]):
        recent_rows = []
        for sale in sales[:8]:
            recent_rows.append({
                "sale_id": f"#{sale.sale_id}",
                "seller": sale.sold_by_username or "Unassigned",
                "product": sale.product_name,
                "shift": sale.shift_name or "N/A",
                "price": self._fmt(sale.price),
                "sold_at": sale.sold_at.strftime("%b %d %I:%M %p"),
            })
        self.recent_sales_table.insert_rows(recent_rows)

        stock_rows = []
        for stock in self.inventory_service.get_active_stocks()[:10]:
            stock_rows.append({
                "stock_id": f"#{stock.stock_id}",
                "product": stock.product_name,
                "status": stock.status.value,
                "weight": f"{stock.kg:g} kg",
                "price": self._fmt(stock.price),
            })
        self.stock_snapshot_table.insert_rows(stock_rows)

    def _aggregate_weekly_sales(self, sales: List[Sale]):
        from datetime import datetime, timedelta
        now    = datetime.now()
        totals = {}
        for offset in range(6, -1, -1):
            totals[(now - timedelta(days=offset)).date()] = 0.0
        for sale in sales:
            if sale.sold_at.date() in totals:
                totals[sale.sold_at.date()] += sale.price
        return list(totals.items())

    def _is_admin(self) -> bool:
        roles = getattr(self.current_user, "roles", []) or []
        return "admin" in roles