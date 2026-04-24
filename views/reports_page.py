import customtkinter as ctk
from tkinter import ttk
from typing import Dict
from services.report_service import ReportService
from datetime import datetime, timedelta

class ReportsPage(ctk.CTkFrame):
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
        self.last_refresh_time = datetime.now() - timedelta(seconds=2)  # Allow initial refresh
        self.refresh_cooldown_seconds = 1  # Minimum seconds between refreshes
        self.configure(fg_color=self.tokens['bg_base'])
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """Build reports page UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color=self.tokens['bg_base'])
        header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        header_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header_frame,
            text='Reports',
            font=ctk.CTkFont(size=24, weight='bold'),
            text_color=self.tokens['text_primary'],
        )
        title.grid(row=0, column=0, sticky='w')

        subtitle = ctk.CTkLabel(
            header_frame,
            text='Revenue, sales trends, inventory status, and performance analytics.',
            font=ctk.CTkFont(size=12),
            text_color=self.tokens['text_secondary'],
        )
        subtitle.grid(row=1, column=0, sticky='w', pady=(4, 0))

        # Buttons frame
        button_frame = ctk.CTkFrame(header_frame, fg_color=self.tokens['bg_base'])
        button_frame.grid(row=0, column=1, rowspan=2, sticky='e', padx=(12, 0))

        refresh_button = ctk.CTkButton(
            button_frame,
            text='Refresh',
            command=self.refresh,
            fg_color=self.tokens['accent_1'],
            hover_color=self.tokens['accent_2'],
            text_color=self.tokens['bg_base'],
            width=100,
        )
        refresh_button.grid(row=0, column=0, padx=(0, 8))

        # Content scroll frame
        scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=self.tokens['bg_base'],
            label_text='',
        )
        scroll_frame.grid(row=1, column=0, sticky='nsew', pady=(0, 0))
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Revenue Summary Card
        self._build_revenue_card(scroll_frame)

        # Sales Trend Table
        self._build_sales_trend_table(scroll_frame)

        # Stock Status Card
        self._build_stock_status_card(scroll_frame)

        # Top Products Table
        self._build_top_products_table(scroll_frame)

    def _build_revenue_card(self, parent):
        """Build revenue summary card."""
        card = ctk.CTkFrame(
            parent,
            fg_color=self.tokens['bg_surface'],
            corner_radius=12,
            border_color=self.tokens['border'],
            border_width=1,
        )
        card.grid(row=0, column=0, sticky='ew', pady=(0, 16), padx=0)
        card.grid_columnconfigure((0, 1, 2), weight=1)

        title = ctk.CTkLabel(
            card,
            text='Revenue Summary',
            font=ctk.CTkFont(size=16, weight='bold'),
            text_color=self.tokens['text_primary'],
        )
        title.grid(row=0, column=0, columnspan=3, sticky='w', padx=16, pady=(16, 12))

        self.total_label = self._metric_card(card, 'Total Revenue', '0.00', 0, 0)
        self.this_month_label = self._metric_card(card, 'This Month', '0.00', 0, 1)
        self.this_year_label = self._metric_card(card, 'This Year', '0.00', 0, 2)

    def _metric_card(self, parent, label: str, value: str, row: int, col: int):
        """Create a metric card."""
        frame = ctk.CTkFrame(parent, fg_color=self.tokens['bg_elevated'], corner_radius=8)
        frame.grid(row=row + 1, column=col, sticky='ew', padx=8, pady=(0, 16))
        frame.grid_columnconfigure(0, weight=1)

        label_widget = ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=self.tokens['text_secondary'],
        )
        label_widget.grid(row=0, column=0, sticky='w', padx=12, pady=(8, 0))

        value_label = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=18, weight='bold'),
            text_color=self.tokens['accent_1'],
        )
        value_label.grid(row=1, column=0, sticky='w', padx=12, pady=(4, 12))

        return value_label

    def _build_sales_trend_table(self, parent):
        """Build sales trend table."""
        card = ctk.CTkFrame(
            parent,
            fg_color=self.tokens['bg_surface'],
            corner_radius=12,
            border_color=self.tokens['border'],
            border_width=1,
        )
        card.grid(row=1, column=0, sticky='ew', pady=(0, 16), padx=0)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            card,
            text='Sales Trend (Last 30 Days)',
            font=ctk.CTkFont(size=16, weight='bold'),
            text_color=self.tokens['text_primary'],
        )
        title.grid(row=0, column=0, sticky='w', padx=16, pady=(16, 12))

        columns = ('date', 'quantity', 'amount')
        self.sales_tree = ttk.Treeview(card, columns=columns, show='headings', height=8)

        self.sales_tree.column('date', width=100)
        self.sales_tree.column('quantity', width=80)
        self.sales_tree.column('amount', width=100)

        self.sales_tree.heading('date', text='Date')
        self.sales_tree.heading('quantity', text='Qty')
        self.sales_tree.heading('amount', text='Amount')

        self.sales_tree.grid(row=1, column=0, sticky='nsew', padx=12, pady=(0, 12))

    def _build_stock_status_card(self, parent):
        """Build stock status breakdown card."""
        card = ctk.CTkFrame(
            parent,
            fg_color=self.tokens['bg_surface'],
            corner_radius=12,
            border_color=self.tokens['border'],
            border_width=1,
        )
        card.grid(row=2, column=0, sticky='ew', pady=(0, 16), padx=0)
        card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        title = ctk.CTkLabel(
            card,
            text='Stock Status',
            font=ctk.CTkFont(size=16, weight='bold'),
            text_color=self.tokens['text_primary'],
        )
        title.grid(row=0, column=0, columnspan=4, sticky='w', padx=16, pady=(16, 12))

        self.available_stock_label = self._metric_card(card, 'Available', '0', 0, 0)
        self.freezing_stock_label = self._metric_card(card, 'Freezing', '0', 0, 1)
        self.sold_stock_label = self._metric_card(card, 'Sold', '0', 0, 2)
        self.total_stock_label = self._metric_card(card, 'Total', '0', 0, 3)

    def _build_top_products_table(self, parent):
        """Build top products table."""
        card = ctk.CTkFrame(
            parent,
            fg_color=self.tokens['bg_surface'],
            corner_radius=12,
            border_color=self.tokens['border'],
            border_width=1,
        )
        card.grid(row=3, column=0, sticky='ew', pady=(0, 16), padx=0)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            card,
            text='Top Products',
            font=ctk.CTkFont(size=16, weight='bold'),
            text_color=self.tokens['text_primary'],
        )
        title.grid(row=0, column=0, sticky='w', padx=16, pady=(16, 12))

        columns = ('product', 'sales', 'revenue')
        self.products_tree = ttk.Treeview(card, columns=columns, show='headings', height=8)

        self.products_tree.column('product', width=150)
        self.products_tree.column('sales', width=80)
        self.products_tree.column('revenue', width=100)

        self.products_tree.heading('product', text='Product')
        self.products_tree.heading('sales', text='Sales')
        self.products_tree.heading('revenue', text='Revenue')

        self.products_tree.grid(row=1, column=0, sticky='nsew', padx=12, pady=(0, 12))

    def refresh(self):
        """Refresh all report data with cooldown throttling."""
        # Throttle rapid refresh calls
        now = datetime.now()
        if (now - self.last_refresh_time).total_seconds() < self.refresh_cooldown_seconds:
            return
        self.last_refresh_time = now

        try:
            # Revenue summary
            revenue = self.report_service.get_revenue_summary()
            if not revenue:
                raise ValueError("Failed to fetch revenue data")
            self.total_label.configure(text=f"₱{revenue.get('total', 0):,.2f}")
            self.this_month_label.configure(text=f"₱{revenue.get('this_month', 0):,.2f}")
            self.this_year_label.configure(text=f"₱{revenue.get('this_year', 0):,.2f}")

            # Sales trend
            for item in self.sales_tree.get_children():
                self.sales_tree.delete(item)
            
            trend = self.report_service.get_sales_trend(30)
            if trend is None:
                trend = []
            for item in trend:
                self.sales_tree.insert('', 'end', values=(
                    item.get('date', 'N/A'),
                    item.get('quantity', 0),
                    f"₱{item.get('amount', 0):,.2f}",
                ))

            # Stock status
            stock_status = self.report_service.get_stock_status_report()
            if not stock_status:
                raise ValueError("Failed to fetch stock status")
            self.available_stock_label.configure(text=str(stock_status.get('available', 0)))
            self.freezing_stock_label.configure(text=str(stock_status.get('freezing', 0)))
            self.sold_stock_label.configure(text=str(stock_status.get('sold', 0)))
            self.total_stock_label.configure(text=str(stock_status.get('total', 0)))

            # Top products
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            
            products = self.report_service.get_top_products(10)
            if products is None:
                products = []
            for product in products:
                self.products_tree.insert('', 'end', values=(
                    product.get('product_name', 'Unknown'),
                    product.get('sale_count', 0),
                    f"₱{product.get('total_revenue', 0):,.2f}",
                ))
        except Exception as e:
            # Log error but don't crash
            import sys
            print(f"Error refreshing reports: {e}", file=sys.stderr)
