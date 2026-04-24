import tkinter as tk
import customtkinter as ctk
from typing import List

from models.sale import Sale
from services.inventory_service import InventoryService
from services.sales_service import SalesService


class DashboardPage(ctk.CTkFrame):
    def __init__(
        self,
        inventory_service: InventoryService,
        sales_service: SalesService,
        tokens: dict,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.inventory_service = inventory_service
        self.sales_service = sales_service
        self.tokens = tokens
        self.configure(fg_color=self.tokens['bg_base'])
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text='Dashboard',
            font=ctk.CTkFont(size=24, weight='bold'),
            text_color=self.tokens['text_primary'],
        )
        title.grid(row=0, column=0, sticky='w', pady=(0, 8))

        subtitle = ctk.CTkLabel(
            self,
            text='Real-time stock availability, sales performance, and activity trends.',
            font=ctk.CTkFont(size=12),
            text_color=self.tokens['text_secondary'],
        )
        subtitle.grid(row=1, column=0, sticky='w', pady=(0, 20))

        self.summary_frame = ctk.CTkFrame(
            self,
            fg_color=self.tokens['bg_surface'],
            corner_radius=12,
            border_color=self.tokens['border'],
            border_width=1,
        )
        self.summary_frame.grid(row=2, column=0, sticky='ew', pady=(0, 16))
        self.summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.available_label = self._metric_item('Available')
        self.freezing_label = self._metric_item('Freezing')
        self.sold_label = self._metric_item('Sold')
        self.activity_label = self._metric_item('Events')

        self.available_label.grid(row=0, column=0, sticky='ew', padx=10, pady=16)
        self.freezing_label.grid(row=0, column=1, sticky='ew', padx=10, pady=16)
        self.sold_label.grid(row=0, column=2, sticky='ew', padx=10, pady=16)
        self.activity_label.grid(row=0, column=3, sticky='ew', padx=10, pady=16)

        self.comparison_frame = ctk.CTkFrame(
            self,
            fg_color=self.tokens['bg_surface'],
            corner_radius=12,
            border_color=self.tokens['border'],
            border_width=1,
        )
        self.comparison_frame.grid(row=3, column=0, sticky='ew', pady=(0, 16))
        self.comparison_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.this_month_label = self._metric_item('This Month')
        self.last_month_label = self._metric_item('Last Month')
        self.this_year_label = self._metric_item('This Year')
        self.last_year_label = self._metric_item('Last Year')

        self.this_month_label.grid(row=0, column=0, sticky='ew', padx=10, pady=16)
        self.last_month_label.grid(row=0, column=1, sticky='ew', padx=10, pady=16)
        self.this_year_label.grid(row=0, column=2, sticky='ew', padx=10, pady=16)
        self.last_year_label.grid(row=0, column=3, sticky='ew', padx=10, pady=16)

        breakdown_frame = ctk.CTkFrame(
            self,
            fg_color=self.tokens['bg_surface'],
            corner_radius=12,
            border_color=self.tokens['border'],
            border_width=1,
        )
        breakdown_frame.grid(row=4, column=0, sticky='ew', pady=(0, 16))
        breakdown_frame.grid_columnconfigure(0, weight=1)

        breakdown_title = ctk.CTkLabel(
            breakdown_frame,
            text='Sales Breakdown',
            font=ctk.CTkFont(size=18, weight='bold'),
            text_color=self.tokens['text_primary'],
        )
        breakdown_title.grid(row=0, column=0, sticky='w', padx=16, pady=(16, 8))

        self.breakdown_text = ctk.CTkLabel(
            breakdown_frame,
            text='Loading...',
            justify='left',
            text_color=self.tokens['text_secondary'],
        )
        self.breakdown_text.grid(row=1, column=0, sticky='w', padx=16, pady=(0, 16))

        self.chart_canvas = tk.Canvas(
            self,
            bg=self.tokens['bg_elevated'],
            highlightthickness=0,
            height=260,
        )
        self.chart_canvas.grid(row=5, column=0, sticky='ew')

        self.refresh_button = ctk.CTkButton(
            self,
            text='REFRESH',
            command=self.refresh,
            fg_color=self.tokens['accent_1'],
            hover_color=self.tokens['accent_2'],
            text_color=self.tokens['bg_base'],
            corner_radius=8,
            width=120,
        )
        self.refresh_button.grid(row=6, column=0, sticky='e', pady=(12, 0))

    def _metric_item(self, title: str):
        frame = ctk.CTkFrame(
            self,
            fg_color=self.tokens['bg_elevated'],
            corner_radius=10,
            border_color=self.tokens['border'],
            border_width=1,
        )
        value_label = ctk.CTkLabel(
            frame,
            text='—',
            font=ctk.CTkFont(size=24, weight='bold'),
            text_color=self.tokens['text_primary'],
        )
        title_label = ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=10, weight='bold'),
            text_color=self.tokens['text_secondary'],
        )
        value_label.pack(anchor='w', padx=16, pady=(16, 4))
        title_label.pack(anchor='w', padx=16, pady=(0, 16))
        frame.value_label = value_label
        return frame

    def refresh(self):
        self.inventory_service.refresh_stock_availability()
        summary = self.inventory_service.get_dashboard_summary()
        self.available_label.value_label.configure(text=str(summary.available_count))
        self.freezing_label.value_label.configure(text=str(summary.freezing_count))
        self.sold_label.value_label.configure(text=str(summary.sold_count))
        self.activity_label.value_label.configure(text=str(summary.activity_count))

        comparison = self.inventory_service.get_sales_comparison()
        self.this_month_label.value_label.configure(text=self._format_currency(comparison.current_month))
        self.last_month_label.value_label.configure(text=self._format_currency(comparison.previous_month))
        self.this_year_label.value_label.configure(text=self._format_currency(comparison.current_year))
        self.last_year_label.value_label.configure(text=self._format_currency(comparison.previous_year))

        monthly = self.sales_service.get_revenue_by_month(12)
        yearly = self.sales_service.get_revenue_by_year(5)
        self.breakdown_text.configure(text=self._format_sales_breakdown(monthly, yearly))
        self._draw_chart(self.sales_service.get_sales_history())

    def _format_currency(self, amount: float) -> str:
        try:
            return f'₱ {float(amount):,.2f}'
        except Exception:
            return '₱ 0.00'

    def _format_sales_breakdown(self, monthly, yearly):
        monthly_text = '\n'.join(f'{period}: {self._format_currency(total)}' for period, total in monthly) or 'No monthly sales data'
        yearly_text = '\n'.join(f'{year}: {self._format_currency(total)}' for year, total in yearly) or 'No yearly sales data'
        return f'Monthly revenue:\n{monthly_text}\n\nYearly revenue:\n{yearly_text}'

    def _draw_chart(self, sales: List[Sale]):
        self.chart_canvas.delete('all')
        points = self._aggregate_weekly_sales(sales)
        if not points:
            self.chart_canvas.create_text(
                20,
                120,
                anchor='w',
                text='No recent sales data',
                fill=self.tokens['text_secondary'],
                font=('Inter', 12),
            )
            return

        width = max(self.chart_canvas.winfo_width(), 800)
        height = 260
        margin = 24
        chart_width = width - margin * 2
        chart_height = height - margin * 2
        values = [value for _, value in points]
        max_value = max(max(values), 10.0) * 1.2
        step = chart_width / max(len(points) - 1, 1)

        coords = []
        for index, (_, value) in enumerate(points):
            x = margin + index * step
            y = margin + chart_height - (value / max_value) * chart_height
            coords.append((x, y))

        for i in range(1, len(coords)):
            self.chart_canvas.create_line(
                coords[i - 1][0],
                coords[i - 1][1],
                coords[i][0],
                coords[i][1],
                fill=self.tokens['accent_1'],
                width=2,
            )

        for x, y in coords:
            self.chart_canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=self.tokens['accent_1'], outline='')

        for idx, (date, _) in enumerate(points):
            self.chart_canvas.create_text(
                margin + idx * step,
                height - margin + 8,
                text=date.strftime('%b %d'),
                fill=self.tokens['text_muted'],
                font=('Inter', 9),
            )

    def _aggregate_weekly_sales(self, sales: List[Sale]):
        from datetime import datetime, timedelta

        now = datetime.now()
        totals = {}
        for offset in range(6, -1, -1):
            date_key = (now - timedelta(days=offset)).date()
            totals[date_key] = 0.0

        for sale in sales:
            if sale.sold_at.date() in totals:
                totals[sale.sold_at.date()] += sale.price
        return list(totals.items())
