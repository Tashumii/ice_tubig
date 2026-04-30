from typing import List

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from models.sale import Sale
from models.services.inventory_service import InventoryService
from models.services.sales_service import SalesService
from views.components.modern_table import ModernTable
from views.components.animated_charts import AnimatedPieChart
from views.components.loading_widgets import LoadingSpinner


class _MiniChart(QWidget):
    def __init__(self, tokens: dict, parent=None):
        super().__init__(parent)
        self.tokens = tokens
        self.points = []
        self.setMinimumHeight(220)

    def set_points(self, points):
        self.points = points or []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg_color = QColor(self.tokens.get('bg_surface', '#151311'))
        painter.fillRect(self.rect(), bg_color)

        if not self.points:
            painter.setPen(QColor(self.tokens.get('text_muted', '#8A8177')))
            painter.drawText(20, self.height() // 2, "No recent sales data")
            return

        values = [float(v or 0) for _, v in self.points]
        max_value = max(values) if values else 0
        if max_value <= 0:
            painter.setPen(QColor(self.tokens.get('text_muted', '#8A8177')))
            painter.drawText(20, self.height() // 2, "No revenue recorded in the last 30 days")
            return

        left = 48
        right = 14
        top = 18
        bottom = 28
        w = max(self.width() - left - right, 1)
        h = max(self.height() - top - bottom, 1)

        grid_pen = QPen(QColor(self.tokens.get('border', '#2B2621')))
        grid_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)
        for i in range(5):
            y = top + (h * i / 4)
            painter.drawLine(left, int(y), left + w, int(y))

        count = max(len(self.points), 1)
        gap = max(int(w * 0.01), 2)
        bar_width = max(int((w - gap * (count - 1)) / count), 3)
        bar_color = QColor(self.tokens.get('accent_1', '#F28A4B'))
        painter.setPen(QPen(bar_color))
        painter.setBrush(bar_color)

        for i, (day, value) in enumerate(self.points):
            bar_height = int((value / max_value) * (h - 4))
            x = left + i * (bar_width + gap)
            y = top + h - bar_height
            painter.drawRoundedRect(x, y, bar_width, bar_height, 4, 4)

        painter.setPen(QColor(self.tokens.get('text_secondary', '#C8BFB2')))
        label_step = max(len(self.points) // 6, 1)
        for i, (day, _value) in enumerate(self.points):
            if i % label_step != 0 and i != len(self.points) - 1:
                continue
            label = day.strftime('%b %d') if hasattr(day, 'strftime') else str(day)
            text_width = painter.fontMetrics().horizontalAdvance(label)
            x = left + i * (bar_width + gap) + (bar_width - text_width) / 2
            painter.drawText(int(x), top + h + 18, label)

        max_label = f"₱ {max_value:,.0f}"
        painter.drawText(left, top - 4, max_label)


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
        
        # Auto-refresh dashboard every 30 seconds to update freezing status
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.refresh)
        self.auto_refresh_timer.start(30000)  # 30 seconds
        
        # Initial refresh to populate data
        self.refresh()
    
    def closeEvent(self, event):
        """Stop the timer when the widget is closed."""
        self.auto_refresh_timer.stop()
        super().closeEvent(event)

    def _build_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        scroll = QScrollArea(self)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; } QScrollBar:vertical { width: 0px; } QScrollBar:horizontal { height: 0px; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        root = content_layout

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

        # ── Pie Charts Row ────────────────────────────────────────────────────
        charts_row = QHBoxLayout()
        
        # Stock Status Pie Chart
        stock_chart_card = QFrame(self)
        stock_chart_card.setProperty("card", True)
        stock_chart_layout = QVBoxLayout(stock_chart_card)
        stock_chart_title = QLabel('Stock Distribution', stock_chart_card)
        stock_chart_title.setStyleSheet("font-size:15px; font-weight:700;")
        stock_chart_layout.addWidget(stock_chart_title)
        self.stock_pie_chart = AnimatedPieChart(self.tokens, stock_chart_card)
        stock_chart_layout.addWidget(self.stock_pie_chart)
        charts_row.addWidget(stock_chart_card)
        
        # Revenue by Product Pie Chart
        revenue_chart_card = QFrame(self)
        revenue_chart_card.setProperty("card", True)
        revenue_chart_layout = QVBoxLayout(revenue_chart_card)
        revenue_chart_title = QLabel('Revenue by Product', revenue_chart_card)
        revenue_chart_title.setStyleSheet("font-size:15px; font-weight:700;")
        revenue_chart_layout.addWidget(revenue_chart_title)
        self.revenue_pie_chart = AnimatedPieChart(self.tokens, revenue_chart_card)
        revenue_chart_layout.addWidget(self.revenue_pie_chart)
        charts_row.addWidget(revenue_chart_card)
        
        root.addLayout(charts_row)

        # ── Weekly revenue chart ──────────────────────────────────────────────
        chart_card = QFrame(self)
        chart_card.setProperty("card", True)
        chart_layout = QVBoxLayout(chart_card)
        chart_header = QHBoxLayout()
        chart_title = QLabel("Total Revenue (30 Days)", chart_card)
        self.chart_total_label = QLabel("₱ 0.00", chart_card)
        self.chart_total_label.setStyleSheet(
            f"font-weight:700; color:{self.tokens['accent_1']};"
        )
        chart_header.addWidget(chart_title)
        chart_header.addStretch()
        chart_header.addWidget(self.chart_total_label)
        chart_layout.addLayout(chart_header)
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
        recent_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        stock_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        stock_layout.addWidget(self.stock_snapshot_table)
        tables_wrap.addWidget(stock_card, 1)

        tables_wrap.setStretch(0, 2)
        tables_wrap.setStretch(1, 1)

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
        self._draw_chart(sales_history, 30)
        self._refresh_data_tables(sales_history)
        self._refresh_pie_charts(summary, sales_history)

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

    def _draw_chart(self, sales: List[Sale], days: int = 30):
        points = self._aggregate_daily_sales(sales, days)
        total = sum(value for _, value in points)
        self.chart_total_label.setText(self._fmt(total))
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

    def _aggregate_daily_sales(self, sales: List[Sale], days: int = 30):
        from datetime import datetime, timedelta
        now = datetime.now()
        totals = {}
        days = max(int(days), 1)
        for offset in range(days - 1, -1, -1):
            totals[(now - timedelta(days=offset)).date()] = 0.0
        for sale in sales:
            if sale.sold_at.date() in totals:
                totals[sale.sold_at.date()] += sale.price
        return list(totals.items())

    def _is_admin(self) -> bool:
        roles = getattr(self.current_user, "roles", []) or []
        return "admin" in roles

    def _refresh_pie_charts(self, summary, sales_history: List[Sale]):
        """Update pie charts with current data."""
        # Stock distribution pie chart
        stock_data = [
            ('Available', summary.available_count, self.tokens.get('success', '#7EDC98')),
            ('Freezing', summary.freezing_count, self.tokens.get('accent_1', '#F28A4B')),
            ('Sold', summary.sold_count, self.tokens.get('text_muted', '#8A8177')),
        ]
        self.stock_pie_chart.set_data(stock_data)
        
        # Revenue by product pie chart
        from collections import defaultdict
        product_revenue = defaultdict(float)
        for sale in sales_history:
            product_revenue[sale.product_name] += sale.price
        
        # Get top 5 products
        sorted_products = sorted(product_revenue.items(), key=lambda x: x[1], reverse=True)[:5]
        
        colors = [
            self.tokens.get('accent_1', '#F28A4B'),
            self.tokens.get('accent_3', '#F5C27A'),
            self.tokens.get('success', '#7EDC98'),
            self.tokens.get('warning', '#F3B562'),
            self.tokens.get('text_secondary', '#C8BFB2'),
        ]
        
        revenue_data = [
            (product, revenue, colors[i % len(colors)])
            for i, (product, revenue) in enumerate(sorted_products)
        ]
        
        if revenue_data:
            self.revenue_pie_chart.set_data(revenue_data)
        else:
            self.revenue_pie_chart.set_data([('No Sales', 1, self.tokens.get('text_muted', '#8A8177'))])