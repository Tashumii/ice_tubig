from collections import defaultdict
import tkinter.ttk as ttk
import customtkinter as ctk

from services.sales_service import SalesService


class SalesPage(ctk.CTkFrame):
    def __init__(self, sales_service: SalesService, tokens: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sales_service = sales_service
        self.tokens = tokens
        self.configure(fg_color=self.tokens['bg_base'])
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text='Sales History',
            font=ctk.CTkFont(size=24, weight='bold'),
            text_color=self.tokens['text_primary'],
        )
        title.grid(row=0, column=0, sticky='w', pady=(0, 4))

        subtitle = ctk.CTkLabel(
            self,
            text='Revenue, transaction logs, and product-size breakdowns.',
            font=ctk.CTkFont(size=12),
            text_color=self.tokens['text_secondary'],
        )
        subtitle.grid(row=1, column=0, sticky='w', pady=(0, 20))

        summary_frame = ctk.CTkFrame(
            self,
            fg_color=self.tokens['bg_surface'],
            corner_radius=12,
            border_color=self.tokens['border'],
            border_width=1,
        )
        summary_frame.grid(row=2, column=0, sticky='ew', pady=(0, 16))
        summary_frame.grid_columnconfigure(1, weight=1)

        self.total_revenue_label = ctk.CTkLabel(
            summary_frame,
            text='₱ 0.00',
            font=ctk.CTkFont(size=18, weight='bold'),
            text_color=self.tokens['success'],
        )
        self.total_revenue_label.grid(row=0, column=0, sticky='w', padx=16, pady=14)

        self.kg_revenue_label = ctk.CTkLabel(
            summary_frame,
            text='no data',
            text_color=self.tokens['text_secondary'],
        )
        self.kg_revenue_label.grid(row=0, column=1, sticky='w', padx=16, pady=14)

        table_frame = ctk.CTkFrame(
            self,
            fg_color=self.tokens['bg_surface'],
            corner_radius=12,
            border_color=self.tokens['border'],
            border_width=1,
        )
        table_frame.grid(row=3, column=0, sticky='nsew')
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        columns = ('sale_id', 'stock_id', 'added', 'sold_at', 'product', 'price', 'weight')
        self.sales_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        headings = [
            ('sale_id', 'Sale ID', 80),
            ('stock_id', 'Stock ID', 80),
            ('added', 'Added', 150),
            ('sold_at', 'Sold At', 150),
            ('product', 'Product', 160),
            ('price', 'Price', 100),
            ('weight', 'Weight', 90),
        ]
        for key, title, width in headings:
            self.sales_table.heading(key, text=title)
            self.sales_table.column(key, width=width, anchor='center')

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.sales_table.yview)
        self.sales_table.configure(yscrollcommand=scrollbar.set)
        self.sales_table.grid(row=0, column=0, sticky='nsew', padx=(16, 0), pady=16)
        scrollbar.grid(row=0, column=1, sticky='ns', padx=(0, 16), pady=16)

    def refresh(self):
        self.sales_table.delete(*self.sales_table.get_children())
        total_revenue = 0.0
        kg_revenue = defaultdict(float)

        for sale in self.sales_service.get_sales_history():
            self.sales_table.insert(
                '',
                'end',
                values=(
                    f'#{sale.sale_id}',
                    f'#{sale.stock_id}',
                    sale.added.strftime('%b %d, %Y %I:%M %p'),
                    sale.sold_at.strftime('%b %d, %Y %I:%M %p'),
                    sale.product_name,
                    f'₱ {sale.price:.2f}',
                    f'{sale.kg} kg',
                ),
            )
            total_revenue += sale.price
            kg_revenue[sale.kg] += sale.price

        self.total_revenue_label.configure(text=f'₱ {total_revenue:,.2f}')
        if kg_revenue:
            self.kg_revenue_label.configure(
                text='  ·  '.join(f'{kg:g} kg → ₱{amount:,.2f}' for kg, amount in sorted(kg_revenue.items()))
            )
        else:
            self.kg_revenue_label.configure(text='no data')
