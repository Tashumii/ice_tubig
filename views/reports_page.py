from views.components.modern_table import ModernTable
from typing import Dict
from models.services.report_service import ReportService
from datetime import datetime, timedelta
import qtawesome as qta
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget
from utils import format_currency


class ReportsPage(QWidget):
    def __init__(self, report_service, tokens, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_service = report_service
        self.tokens = tokens
        self.last_refresh_time = datetime.now() - timedelta(seconds=2)
        self.refresh_cooldown_seconds = 1
        self.setStyleSheet("background:transparent;")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        header = QHBoxLayout(); left = QVBoxLayout()
        title = QLabel('Reports', self); title.setProperty('pageTitle', True)
        subtitle = QLabel('Revenue, sales trends, inventory status, and performance analytics.', self)
        subtitle.setProperty('muted', True)
        self.status_label = QLabel('', self); self.status_label.setStyleSheet(f"color:{self.tokens['danger']};font-weight:600;")
        left.addWidget(title); left.addWidget(subtitle); left.addWidget(self.status_label)
        rb = QPushButton('REFRESH', self)
        rb.setIcon(qta.icon('fa5s.sync-alt', color=self.tokens['accent_1']))
        rb.clicked.connect(self.refresh)
        header.addLayout(left); header.addStretch(); header.addWidget(rb)
        root.addLayout(header)

        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        body = QWidget(scroll); self.body_layout = QVBoxLayout(body)
        scroll.setWidget(body); root.addWidget(scroll, 1)

        self._build_revenue_card(body)
        self._build_stock_status_card(body)
        self._build_sales_trend_table(body)
        self._build_top_products_table(body)

    def _build_revenue_card(self, parent):
        card = self._section_card(parent, 'Revenue Summary', 'ALL TIME')
        card.layout().setSpacing(8)
        self.total_label = self._metric_card(card, 'Total Revenue', '\u20b1 0.00', accent=True)
        self.this_month_label = self._metric_card(card, 'This Month', '\u20b1 0.00')
        self.this_year_label = self._metric_card(card, 'This Year', '\u20b1 0.00')

    def _build_stock_status_card(self, parent):
        card = self._section_card(parent, 'Stock Status', 'CURRENT')
        card.layout().setSpacing(8)
        self.available_stock_label = self._metric_card(card, 'Ready to Sell', '0', accent_color=self.tokens['success'])
        self.freezing_stock_label = self._metric_card(card, 'Freezing', '0', accent_color=self.tokens['accent_1'])
        self.sold_stock_label = self._metric_card(card, 'Sold', '0')
        self.total_stock_label = self._metric_card(card, 'Total', '0')

    def _build_sales_trend_table(self, parent):
        card = self._section_card(parent, 'Sales Trend', 'LAST 30 DAYS')
        self._trend_row_label = QLabel('', card); card.layout().addWidget(self._trend_row_label)
        self.sales_table = ModernTable(card, columns=('date','quantity','amount'), tokens=self.tokens)
        card.layout().addWidget(self.sales_table)
        self._set_table_height(self.sales_table, 6)

    def _build_top_products_table(self, parent):
        card = self._section_card(parent, 'Top Products', 'BY REVENUE')
        self._products_row_label = QLabel('', card); card.layout().addWidget(self._products_row_label)
        self.products_table = ModernTable(card, columns=('product','sales','revenue'), tokens=self.tokens)
        card.layout().addWidget(self.products_table)
        self._set_table_height(self.products_table, 6)

    def _section_card(self, parent, title, section_label=''):
        card = QFrame(parent); card.setProperty("card", True)
        v = QVBoxLayout(card); h = QHBoxLayout()
        tl = QLabel(title, card); tl.setProperty('cardTitle', True)
        h.addWidget(tl); h.addStretch()
        if section_label:
            sl = QLabel(section_label, card); sl.setProperty('sectionLabel', True)
            h.addWidget(sl)
        v.addLayout(h); self.body_layout.addWidget(card)
        return card

    def _metric_card(self, parent, label, value, accent=False, accent_color=None):
        frame = QFrame(parent); frame.setProperty("panel", True)
        v = QVBoxLayout(frame)
        lbl = QLabel(label, frame); lbl.setProperty('kpiLabel', True); v.addWidget(lbl)
        val = QLabel(value, frame); val.setProperty('kpiValue', True)
        if accent_color:
            val.setStyleSheet(f"font-size:18px;font-weight:800;color:{accent_color};")
        elif accent:
            val.setStyleSheet(f"font-size:18px;font-weight:800;color:{self.tokens['accent_1']};")
        v.addWidget(val); parent.layout().addWidget(frame)
        return val

    def _set_table_height(self, table, row_count):
        rows = max(row_count, 1)
        target = table.header_height + (rows * table.row_height) + table.table.frameWidth()*2 + 6
        table.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.table.setMinimumHeight(target); table.setMinimumHeight(target)

    def refresh(self):
        now = datetime.now()
        if (now - self.last_refresh_time).total_seconds() < self.refresh_cooldown_seconds: return
        self.last_refresh_time = now; errors = []

        try:
            rev = self.report_service.get_revenue_summary() or {}
            self.total_label.setText(format_currency(rev.get('total', 0)))
            self.this_month_label.setText(format_currency(rev.get('this_month', 0)))
            self.this_year_label.setText(format_currency(rev.get('this_year', 0)))
        except Exception:
            for l in (self.total_label, self.this_month_label, self.this_year_label): l.setText('\u20b1 0.00')
            errors.append('revenue summary')

        try:
            st = self.report_service.get_stock_status_report() or {}
            self.available_stock_label.setText(str(st.get('available', 0)))
            self.freezing_stock_label.setText(str(st.get('freezing', 0)))
            self.sold_stock_label.setText(str(st.get('sold', 0)))
            self.total_stock_label.setText(str(st.get('total', 0)))
        except Exception:
            for l in (self.available_stock_label, self.freezing_stock_label, self.sold_stock_label, self.total_stock_label):
                l.setText('0')
            errors.append('stock status')

        try:
            trend = self.report_service.get_sales_trend(30) or []
            rows = [{'date': i.get('date','No date'), 'quantity': i.get('quantity',0),
                     'amount': format_currency(i.get('amount',0))} for i in trend]
            self.sales_table.insert_rows(rows); self._set_table_height(self.sales_table, len(rows))
            n = len(rows); self._trend_row_label.setText(f'{n} day{"s" if n != 1 else ""}')
        except Exception:
            self.sales_table.insert_rows([]); self._set_table_height(self.sales_table, 1)
            self._trend_row_label.setText(''); errors.append('sales trend')

        try:
            products = self.report_service.get_top_products(10) or []
            rows = [{'product': p.get('product_name','No product name'), 'sales': p.get('sale_count',0),
                     'revenue': format_currency(p.get('total_revenue',0))} for p in products]
            self.products_table.insert_rows(rows); self._set_table_height(self.products_table, len(rows))
            n = len(rows); self._products_row_label.setText(f'Top {n}' if n else 'No products yet')
        except Exception:
            self.products_table.insert_rows([]); self._set_table_height(self.products_table, 1)
            self._products_row_label.setText(''); errors.append('top products')

        self.status_label.setText(f"Could not load: {', '.join(errors)}" if errors else '')

    def search(self, query):
        self.sales_table.filter_rows(query); self.products_table.filter_rows(query)
