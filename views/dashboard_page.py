from typing import List
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
import qtawesome as qta
from models.sale import Sale
from models.services.inventory_service import InventoryService
from models.services.sales_service import SalesService
from utils import clean_display_text, format_currency, humanize_name, humanize_status, is_admin
from views.components.modern_table import ModernTable
from views.components.animated_charts import AnimatedPieChart
from views.components.loading_widgets import LoadingSpinner


class DailyRevenueBarChart(QWidget):
    """Bar chart showing daily revenue over a date range."""
    def __init__(self, tokens, parent=None):
        super().__init__(parent)
        self.tokens = tokens; self.points = []; self.setMinimumHeight(220)

    def set_points(self, points):
        self.points = points or []; self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(self.tokens.get('bg_surface', '#081426')))
        if not self.points:
            painter.setPen(QColor(self.tokens.get('text_muted', '#5F9CC0')))
            painter.drawText(20, self.height() // 2, "No recent sales data"); return
        values = [float(v or 0) for _, v in self.points]
        max_val = max(values) if values else 0
        if max_val <= 0:
            painter.setPen(QColor(self.tokens.get('text_muted', '#5F9CC0')))
            painter.drawText(20, self.height() // 2, "No revenue recorded in the last 30 days"); return
        left, right, top, bottom = 48, 14, 18, 28
        w, h = max(self.width()-left-right, 1), max(self.height()-top-bottom, 1)
        grid_pen = QPen(QColor(self.tokens.get('border', '#2B2621'))); grid_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)
        for i in range(5): painter.drawLine(left, int(top + h*i/4), left+w, int(top + h*i/4))
        count = max(len(self.points), 1)
        gap = max(int(w * 0.01), 2); bar_w = max(int((w - gap*(count-1))/count), 3)
        bar_color = QColor(self.tokens.get('accent_1', '#5DADE2'))
        painter.setPen(QPen(bar_color)); painter.setBrush(bar_color)
        for i, (day, val) in enumerate(self.points):
            bh = int((val/max_val)*(h-4)); x = left + i*(bar_w+gap); y = top + h - bh
            painter.drawRoundedRect(x, y, bar_w, bh, 4, 4)
        painter.setPen(QColor(self.tokens.get('text_secondary', '#93C5E8')))
        step = max(len(self.points)//6, 1)
        for i, (day, _) in enumerate(self.points):
            if i % step != 0 and i != len(self.points)-1: continue
            label = day.strftime('%b %d') if hasattr(day, 'strftime') else str(day)
            tw = painter.fontMetrics().horizontalAdvance(label)
            painter.drawText(int(left + i*(bar_w+gap) + (bar_w-tw)/2), top+h+18, label)
        painter.drawText(left, top-4, f"\u20b1 {max_val:,.0f}")


class DashboardPage(QWidget):
    def __init__(self, inventory_service, sales_service, tokens, current_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory_service = inventory_service
        self.sales_service = sales_service
        self.tokens = tokens; self.current_user = current_user
        self.setStyleSheet("background:transparent;")
        self._build_ui()
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.refresh)
        self.auto_refresh_timer.start(30000)
        self.refresh()

    def closeEvent(self, event):
        self.auto_refresh_timer.stop(); super().closeEvent(event)

    def _build_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll = QScrollArea(self); scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;}QScrollBar:vertical{width:0px;}QScrollBar:horizontal{height:0px;}")
        content = QWidget(); root = QVBoxLayout(content)
        root.setContentsMargins(0,0,0,0); root.setSpacing(12)
        scroll.setWidget(content)
        main = QVBoxLayout(self); main.setContentsMargins(0,0,0,0); main.addWidget(scroll)

        # Header
        hf = QFrame(self); hl = QHBoxLayout(hf); ll = QVBoxLayout()
        t = QLabel('Dashboard', hf); t.setProperty('pageTitle', True)
        s = QLabel('Real-time stock availability, sales performance, and activity trends.', hf)
        s.setProperty('muted', True)
        self.refresh_button = QPushButton('REFRESH', hf); self.refresh_button.clicked.connect(self.refresh)
        ll.addWidget(t); ll.addWidget(s); hl.addLayout(ll); hl.addStretch(); hl.addWidget(self.refresh_button)
        root.addWidget(hf)

        # Inventory status
        inv_card = QFrame(self); inv_card.setProperty("card", True)
        inv = QGridLayout(inv_card)
        il = QLabel('INVENTORY STATUS', inv_card); il.setProperty('sectionLabel', True)
        inv.addWidget(il, 0, 0, 1, 4)
        self.available_label = self._metric_item(inv, 'Ready to Sell', 1, 0, self.tokens['success'])
        self.freezing_label = self._metric_item(inv, 'Freezing', 1, 1, self.tokens['accent_1'])
        self.sold_label = self._metric_item(inv, 'Sold', 1, 2)
        self.activity_label = self._metric_item(inv, 'Activity', 1, 3)
        root.addWidget(inv_card)

        # Revenue comparison
        cmp = QFrame(self); cmp.setProperty("card", True); cl = QGridLayout(cmp)
        clbl = QLabel('REVENUE COMPARISON', cmp); clbl.setProperty('sectionLabel', True)
        cl.addWidget(clbl, 0, 0, 1, 4)
        self.this_month_label = self._metric_item(cl, 'This Month', 1, 0, self.tokens['accent_1'])
        self.last_month_label = self._metric_item(cl, 'Last Month', 1, 1)
        self.this_year_label = self._metric_item(cl, 'This Year', 1, 2, self.tokens['accent_1'])
        self.last_year_label = self._metric_item(cl, 'Last Year', 1, 3)
        root.addWidget(cmp)

        # Admin notifications
        self.notifications_card = QFrame(self); self.notifications_card.setProperty("card", True)
        nl = QVBoxLayout(self.notifications_card); nh = QHBoxLayout()
        nt = QLabel("Staff Activity Notifications", self.notifications_card)
        nt.setProperty('cardTitle', True)
        self.notifications_count = QLabel("", self.notifications_card)
        self.notifications_count.setProperty('muted', True)
        nh.addWidget(nt); nh.addStretch(); nh.addWidget(self.notifications_count); nl.addLayout(nh)
        self.notifications_table = ModernTable(self.notifications_card,
            columns=("time","event","staff","details","severity"), tokens=self.tokens)
        nl.addWidget(self.notifications_table)
        if is_admin(self.current_user): root.addWidget(self.notifications_card)

        # Sales breakdown
        bd = QFrame(self); bd.setProperty("card", True); bdl = QVBoxLayout(bd)
        bdt = QLabel('Sales Breakdown', bd); bdt.setProperty('cardTitle', True)
        self.breakdown_text = QLabel('Loading\u2026', bd)
        self.breakdown_text.setProperty('muted', True)
        self.breakdown_text.setWordWrap(True)
        bdl.addWidget(bdt); bdl.addWidget(self.breakdown_text); root.addWidget(bd)

        # Pie charts row
        charts_row = QHBoxLayout()
        for attr, title in [('stock_pie_chart', 'Stock Distribution'), ('revenue_pie_chart', 'Revenue by Product')]:
            card = QFrame(self); card.setProperty("card", True); cl = QVBoxLayout(card)
            ct = QLabel(title, card); ct.setProperty('cardTitle', True); cl.addWidget(ct)
            chart = AnimatedPieChart(self.tokens, card); cl.addWidget(chart); charts_row.addWidget(card)
            setattr(self, attr, chart)
        root.addLayout(charts_row)

        # Revenue chart
        cc = QFrame(self); cc.setProperty("card", True); ccl = QVBoxLayout(cc)
        ch = QHBoxLayout()
        cht = QLabel("Total Revenue (30 Days)", cc); cht.setProperty('cardTitle', True)
        self.chart_total_label = QLabel("\u20b1 0.00", cc)
        self.chart_total_label.setProperty('kpiValue', True)
        ch.addWidget(cht); ch.addStretch(); ch.addWidget(self.chart_total_label); ccl.addLayout(ch)
        self.chart_canvas = DailyRevenueBarChart(self.tokens, cc); ccl.addWidget(self.chart_canvas)
        root.addWidget(cc)

        # Data tables
        tw = QHBoxLayout()
        rc = QFrame(self); rc.setProperty("card", True); rl = QVBoxLayout(rc)
        rs_label = QLabel("Recent Sales", rc); rs_label.setProperty('cardTitle', True)
        rl.addWidget(rs_label)
        self.recent_sales_table = ModernTable(rc, columns=("sale_id","seller","product","shift","price","sold_at"), tokens=self.tokens)
        rc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        rl.addWidget(self.recent_sales_table); tw.addWidget(rc, 2)
        sc = QFrame(self); sc.setProperty("card", True); sl = QVBoxLayout(sc)
        ss_label = QLabel("Live Stock Snapshot", sc); ss_label.setProperty('cardTitle', True)
        sl.addWidget(ss_label)
        self.stock_snapshot_table = ModernTable(sc, columns=("stock_id","product","status","weight","price"), tokens=self.tokens)
        sc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sl.addWidget(self.stock_snapshot_table); tw.addWidget(sc, 1)
        tw.setStretch(0, 2); tw.setStretch(1, 1); root.addLayout(tw, 1)

    def _metric_item(self, parent_grid, title, row, col, accent=None):
        frame = QFrame(self); frame.setProperty("card", True); layout = QVBoxLayout(frame)
        frame.setProperty("panel", True)
        val = QLabel("—", frame); val.setProperty('kpiValue', True)
        if accent:
            val.setStyleSheet(f"font-size:22px;font-weight:800;color:{accent};")
        lbl = QLabel(title, frame); lbl.setProperty('kpiLabel', True)
        layout.addWidget(val); layout.addWidget(lbl); frame.value_label = val
        parent_grid.addWidget(frame, row, col); return frame

    def refresh(self):
        self.inventory_service.refresh_stock_availability()
        summary = self.inventory_service.get_dashboard_summary()
        self.available_label.value_label.setText(str(summary.available_count))
        self.freezing_label.value_label.setText(str(summary.freezing_count))
        self.sold_label.value_label.setText(str(summary.sold_count))
        self.activity_label.value_label.setText(str(summary.activity_count))
        comp = self.inventory_service.get_sales_comparison()
        self.this_month_label.value_label.setText(format_currency(comp.current_month))
        self.last_month_label.value_label.setText(format_currency(comp.previous_month))
        self.this_year_label.value_label.setText(format_currency(comp.current_year))
        self.last_year_label.value_label.setText(format_currency(comp.previous_year))
        monthly = self.sales_service.get_revenue_by_month(12)
        yearly = self.sales_service.get_revenue_by_year(5)
        self.breakdown_text.setText(self._format_breakdown(monthly, yearly))
        sales_history = self.sales_service.get_sales_history()
        if not is_admin(self.current_user):
            username = getattr(self.current_user, "username", "")
            sales_history = [s for s in sales_history if s.sold_by_username == username]
        self._draw_chart(sales_history, 30)
        self._refresh_data_tables(sales_history)
        self._refresh_pie_charts(summary, sales_history)
        if is_admin(self.current_user): self._refresh_notifications()

    def _format_breakdown(self, monthly, yearly):
        ml = '\n'.join(f'  {p}   {format_currency(t)}' for p, t in monthly) or '  No monthly data'
        yl = '\n'.join(f'  {y}   {format_currency(t)}' for y, t in yearly) or '  No yearly data'
        return f'Monthly\n{ml}\n\nYearly\n{yl}'

    def _draw_chart(self, sales, days=30):
        points = self._aggregate_daily_sales(sales, days)
        self.chart_total_label.setText(format_currency(sum(v for _, v in points)))
        self.chart_canvas.set_points(points)

    def _refresh_data_tables(self, sales):
        self.recent_sales_table.insert_rows([{
            "sale_id": f"#{s.sale_id}", "seller": humanize_name(s.sold_by_username),
            "product": s.product_name, "shift": humanize_name(s.shift_name, "No shift"),
            "price": format_currency(s.price), "sold_at": s.sold_at.strftime("%b %d %I:%M %p"),
        } for s in sales[:8]])
        self.stock_snapshot_table.insert_rows([{
            "stock_id": f"#{st.stock_id}", "product": st.product_name,
            "status": humanize_status(st.status), "weight": f"{st.kg:g} kg",
            "price": format_currency(st.price),
        } for st in self.inventory_service.get_active_stocks()[:10]])

    def _refresh_notifications(self):
        notifications = self.sales_service.get_admin_notifications(10)
        rows = [{"_iid": str(i["notification_id"]), "time": i["created_at"],
                 "event": clean_display_text(i["title"]), "staff": humanize_name(i["username"], "System"),
                 "details": clean_display_text(i["message"]), "severity": humanize_status(i["severity"])}
                for i in notifications]
        self.notifications_table.insert_rows(rows)
        self.notifications_count.setText(f"{len(rows)} recent notification{'s' if len(rows) != 1 else ''}")

    def search(self, query):
        self.recent_sales_table.filter_rows(query)
        self.stock_snapshot_table.filter_rows(query)
        if is_admin(self.current_user): self.notifications_table.filter_rows(query)

    def _aggregate_daily_sales(self, sales, days=30):
        from datetime import datetime, timedelta
        now = datetime.now(); totals = {}
        for offset in range(max(int(days),1)-1, -1, -1):
            totals[(now - timedelta(days=offset)).date()] = 0.0
        for s in sales:
            if s.sold_at.date() in totals: totals[s.sold_at.date()] += s.price
        return list(totals.items())

    def _refresh_pie_charts(self, summary, sales_history):
        self.stock_pie_chart.set_data([
            ('Ready to Sell', summary.available_count, self.tokens.get('success', '#2ECC71')),
            ('Freezing', summary.freezing_count, self.tokens.get('accent_1', '#5DADE2')),
            ('Sold', summary.sold_count, self.tokens.get('text_muted', '#7FB3D8'))])
        from collections import defaultdict
        product_rev = defaultdict(float)
        for s in sales_history: product_rev[s.product_name] += s.price
        sorted_prods = sorted(product_rev.items(), key=lambda x: x[1], reverse=True)[:5]
        colors = [self.tokens.get(k, d) for k, d in [('accent_1','#5DADE2'),('accent_3','#85C1E9'),
            ('success','#2ECC71'),('warning','#F39C12'),('text_secondary','#AED6F1')]]
        rev_data = [(p, r, colors[i % len(colors)]) for i, (p, r) in enumerate(sorted_prods)]
        self.revenue_pie_chart.set_data(rev_data if rev_data else
            [('No sales yet', 1, self.tokens.get('text_muted', '#7FB3D8'))])
