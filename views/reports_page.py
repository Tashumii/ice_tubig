from views.components.modern_table import ModernTable
from typing import Dict
from models.services.report_service import ReportService
from datetime import datetime, timedelta
import qtawesome as qta

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget


class ReportsPage(QWidget):
    def __init__(
        self,
        report_service: ReportService,
        tokens: Dict[str, str],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.report_service = report_service
        self.tokens = tokens
        self.last_refresh_time = datetime.now() - timedelta(seconds=2)
        self.refresh_cooldown_seconds = 1
        self.setStyleSheet(f"background:transparent;")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # ── Header ───────────────────────────────────────────────────────────
        header = QHBoxLayout()
        left = QVBoxLayout()
        title = QLabel('Reports', self)
        title.setStyleSheet("font-size:24px; font-weight:700;")
        subtitle = QLabel('Revenue, sales trends, inventory status, and performance analytics.', self)
        subtitle.setStyleSheet(f"color:{self.tokens['text_secondary']};")
        self.status_label = QLabel('', self)
        self.status_label.setStyleSheet(f"color:{self.tokens['danger']};")
        left.addWidget(title); left.addWidget(subtitle); left.addWidget(self.status_label)
        refresh_button = QPushButton('REFRESH', self)
        refresh_button.setIcon(qta.icon('fa5s.sync-alt', color=self.tokens['accent_1']))
        refresh_button.clicked.connect(self.refresh)
        header.addLayout(left); header.addStretch(); header.addWidget(refresh_button)
        root.addLayout(header)

        # ── Scrollable content ────────────────────────────────────────────────
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        body = QWidget(scroll)
        self.body_layout = QVBoxLayout(body)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        self._build_revenue_card(body)
        self._build_stock_status_card(body)
        self._build_sales_trend_table(body)
        self._build_top_products_table(body)

    # ── Section builders ──────────────────────────────────────────────────────

    def _build_revenue_card(self, parent):
        card = self._section_card(parent, row=0, title='Revenue Summary', section_label='ALL TIME')
        card.layout().setSpacing(8)

        self.total_label      = self._metric_card(card, 'Total Revenue', '₱ 0.00', row=1, col=0, accent=True)
        self.this_month_label = self._metric_card(card, 'This Month',    '₱ 0.00', row=1, col=1)
        self.this_year_label  = self._metric_card(card, 'This Year',     '₱ 0.00', row=1, col=2)

    def _build_stock_status_card(self, parent):
        card = self._section_card(parent, row=1, title='Stock Status', section_label='CURRENT')
        card.layout().setSpacing(8)

        self.available_stock_label = self._metric_card(card, 'Ready to Sell', '0', row=1, col=0, accent_color=self.tokens['success'])
        self.freezing_stock_label  = self._metric_card(card, 'Freezing',  '0', row=1, col=1, accent_color=self.tokens['accent_1'])
        self.sold_stock_label      = self._metric_card(card, 'Sold',      '0', row=1, col=2)
        self.total_stock_label     = self._metric_card(card, 'Total',     '0', row=1, col=3)

    def _build_sales_trend_table(self, parent):
        card = self._section_card(parent, row=2, title='Sales Trend', section_label='LAST 30 DAYS')
        self._trend_row_label = QLabel('', card)
        card.layout().addWidget(self._trend_row_label)

        columns = ('date', 'quantity', 'amount')
        self.sales_table = ModernTable(card, columns=columns, tokens=self.tokens)
        card.layout().addWidget(self.sales_table)
        self._set_table_height(self.sales_table, 6)

    def _build_top_products_table(self, parent):
        card = self._section_card(parent, row=3, title='Top Products', section_label='BY REVENUE')
        self._products_row_label = QLabel('', card)
        card.layout().addWidget(self._products_row_label)

        columns = ('product', 'sales', 'revenue')
        self.products_table = ModernTable(card, columns=columns, tokens=self.tokens)
        card.layout().addWidget(self.products_table)
        self._set_table_height(self.products_table, 6)

    # ── Widget helpers ────────────────────────────────────────────────────────

    def _section_card(self, parent, row: int, title: str, section_label: str = ''):
        """Create a titled surface card and return it (callers add children to it)."""
        card = QFrame(parent)
        card.setProperty("card", True)
        v = QVBoxLayout(card)
        h = QHBoxLayout()
        h.addWidget(QLabel(title, card))
        h.addStretch()
        if section_label:
            h.addWidget(QLabel(section_label, card))
        v.addLayout(h)
        self.body_layout.addWidget(card)

        return card

    def _metric_card(
        self,
        parent,
        label: str,
        value: str,
        row: int,
        col: int,
        accent: bool = False,
        accent_color: str = None,
    ):
        frame = QFrame(parent)
        frame.setProperty("panel", True)
        v = QVBoxLayout(frame)
        v.addWidget(QLabel(label, frame))

        value_color = (
            accent_color if accent_color
            else self.tokens['accent_1'] if accent
            else self.tokens['text_primary']
        )
        value_label = QLabel(value, frame)
        value_label.setStyleSheet(f"font-size:18px; font-weight:700; color:{value_color};")
        v.addWidget(value_label)
        parent.layout().addWidget(frame)
        return value_label

    def _set_table_height(self, table: ModernTable, row_count: int) -> None:
        rows = max(row_count, 1)
        header = table.header_height
        row_height = table.row_height
        frame_padding = table.table.frameWidth() * 2 + 6
        target_height = header + (rows * row_height) + frame_padding
        table.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.table.setMinimumHeight(target_height)
        table.setMinimumHeight(target_height)

    # ── Data refresh ──────────────────────────────────────────────────────────

    def refresh(self):
        now = datetime.now()
        if (now - self.last_refresh_time).total_seconds() < self.refresh_cooldown_seconds:
            return
        self.last_refresh_time = now

        errors = []

        # Revenue summary
        try:
            revenue = self.report_service.get_revenue_summary() or {}
            self.total_label.setText(f"₱ {revenue.get('total', 0):,.2f}")
            self.this_month_label.setText(f"₱ {revenue.get('this_month', 0):,.2f}")
            self.this_year_label.setText(f"₱ {revenue.get('this_year', 0):,.2f}")
        except Exception:
            self.total_label.setText('₱ 0.00')
            self.this_month_label.setText('₱ 0.00')
            self.this_year_label.setText('₱ 0.00')
            errors.append('revenue summary')

        # Stock status
        try:
            stock = self.report_service.get_stock_status_report() or {}
            self.available_stock_label.setText(str(stock.get('available', 0)))
            self.freezing_stock_label.setText(str(stock.get('freezing', 0)))
            self.sold_stock_label.setText(str(stock.get('sold', 0)))
            self.total_stock_label.setText(str(stock.get('total', 0)))
        except Exception:
            for lbl in (self.available_stock_label, self.freezing_stock_label,
                        self.sold_stock_label, self.total_stock_label):
                lbl.setText('0')
            errors.append('stock status')

        # Sales trend
        try:
            trend = self.report_service.get_sales_trend(30) or []
            rows = [
                {
                    'date':     item.get('date', 'No date'),
                    'quantity': item.get('quantity', 0),
                    'amount':   f"₱ {item.get('amount', 0):,.2f}",
                }
                for item in trend
            ]
            self.sales_table.insert_rows(rows)
            self._set_table_height(self.sales_table, len(rows))
            n = len(rows)
            self._trend_row_label.setText(f'{n} day{"s" if n != 1 else ""}')
        except Exception:
            self.sales_table.insert_rows([])
            self._set_table_height(self.sales_table, 1)
            self._trend_row_label.setText('')
            errors.append('sales trend')

        # Top products
        try:
            products = self.report_service.get_top_products(10) or []
            rows = [
                {
                    'product': p.get('product_name', 'No product name'),
                    'sales':   p.get('sale_count', 0),
                    'revenue': f"₱ {p.get('total_revenue', 0):,.2f}",
                }
                for p in products
            ]
            self.products_table.insert_rows(rows)
            self._set_table_height(self.products_table, len(rows))
            n = len(rows)
            self._products_row_label.setText(f'Top {n}' if n else 'No products yet')
        except Exception:
            self.products_table.insert_rows([])
            self._set_table_height(self.products_table, 1)
            self._products_row_label.setText('')
            errors.append('top products')

        self.status_label.setText(f"Could not load: {', '.join(errors)}" if errors else '')

    def search(self, query: str):
        self.sales_table.filter_rows(query)
        self.products_table.filter_rows(query)
