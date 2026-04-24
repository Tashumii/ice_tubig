import tkinter.messagebox as messagebox
from tkinter import ttk
import customtkinter as ctk
from datetime import datetime, timedelta

from services.inventory_service import InventoryService
from models.stock import StockStatus


class StockPage(ctk.CTkFrame):
    def __init__(self, inventory_service: InventoryService, tokens: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory_service = inventory_service
        self.tokens = tokens
        self._countdown_targets = {}
        self.configure(fg_color=self.tokens['bg_base'])
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text='Stock Management',
            font=ctk.CTkFont(size=24, weight='bold'),
            text_color=self.tokens['text_primary'],
        )
        title.grid(row=0, column=0, sticky='w', pady=(0, 4))

        subtitle = ctk.CTkLabel(
            self,
            text='Add inventory, monitor freeze cycles, and dispatch ready items.',
            font=ctk.CTkFont(size=12),
            text_color=self.tokens['text_secondary'],
        )
        subtitle.grid(row=1, column=0, sticky='w', pady=(0, 20))

        form_frame = ctk.CTkFrame(
            self,
            fg_color=self.tokens['bg_surface'],
            corner_radius=12,
            border_color=self.tokens['border'],
            border_width=1,
        )
        form_frame.grid(row=2, column=0, sticky='ew', pady=(0, 16))
        form_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.quantity_entry = ctk.CTkEntry(form_frame, placeholder_text='Qty', fg_color=self.tokens['bg_input'])
        self.product_entry = ctk.CTkEntry(form_frame, placeholder_text='Product', fg_color=self.tokens['bg_input'])
        self.weight_entry = ctk.CTkEntry(form_frame, placeholder_text='Weight kg', fg_color=self.tokens['bg_input'])
        self.price_entry = ctk.CTkEntry(form_frame, placeholder_text='Price', fg_color=self.tokens['bg_input'])
        self.freeze_entry = ctk.CTkEntry(form_frame, placeholder_text='Hrs', fg_color=self.tokens['bg_input'])

        self.quantity_entry.grid(row=0, column=0, padx=10, pady=16, sticky='ew')
        self.product_entry.grid(row=0, column=1, padx=10, pady=16, sticky='ew')
        self.weight_entry.grid(row=0, column=2, padx=10, pady=16, sticky='ew')
        self.price_entry.grid(row=0, column=3, padx=10, pady=16, sticky='ew')
        self.freeze_entry.grid(row=0, column=4, padx=10, pady=16, sticky='ew')

        add_button = ctk.CTkButton(
            form_frame,
            text='Freeze',
            command=lambda: self._add_stock(False),
            fg_color=self.tokens['accent_1'],
            hover_color=self.tokens['accent_2'],
            text_color=self.tokens['bg_base'],
        )
        ready_button = ctk.CTkButton(
            form_frame,
            text='Mark Ready',
            command=lambda: self._add_stock(True),
            fg_color=self.tokens['success'],
            hover_color=self.tokens['success'],
            text_color=self.tokens['bg_base'],
        )
        add_button.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 16), sticky='ew')
        ready_button.grid(row=1, column=2, columnspan=2, padx=10, pady=(0, 16), sticky='ew')

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

        columns = ('id', 'added', 'product', 'weight', 'price', 'cycle', 'status', 'eta')
        self.stock_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)
        headings = [
            ('id', 'ID', 60),
            ('added', 'Added', 140),
            ('product', 'Product', 160),
            ('weight', 'Weight', 90),
            ('price', 'Price', 100),
            ('cycle', 'Cycle', 80),
            ('status', 'Status', 100),
            ('eta', 'ETA', 120),
        ]
        for key, title, width in headings:
            self.stock_table.heading(key, text=title)
            self.stock_table.column(key, width=width, anchor='center')

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.stock_table.yview)
        self.stock_table.configure(yscrollcommand=scrollbar.set)
        self.stock_table.grid(row=0, column=0, sticky='nsew', padx=(16, 0), pady=16)
        scrollbar.grid(row=0, column=1, sticky='ns', padx=(0, 16), pady=16)

        self.sell_button = ctk.CTkButton(
            self,
            text='Sell Selected',
            command=self._sell_selected,
            fg_color=self.tokens['success'],
            hover_color=self.tokens['success'],
            text_color=self.tokens['bg_base'],
        )
        self.sell_button.grid(row=4, column=0, pady=(12, 0), sticky='e')

    def _parse_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def _parse_float(self, value, default=0.0):
        try:
            return float(value)
        except Exception:
            return default

    def _add_stock(self, instant: bool):
        try:
            quantity = max(1, self._parse_int(self.quantity_entry.get(), 1))
            product_name = self.product_entry.get().strip() or 'Ice'
            kg = self._parse_float(self.weight_entry.get(), 0.0)
            price = self._parse_float(self.price_entry.get(), 0.0)
            freeze_hours = 0 if instant else self._parse_int(self.freeze_entry.get(), 3)

            self.inventory_service.add_stock(
                quantity=quantity,
                product_name=product_name,
                kg=kg,
                freeze_duration_hours=freeze_hours,
                price=price,
                instant=instant,
            )
            self.refresh()
        except Exception as exc:
            messagebox.showerror('Error', str(exc))

    def refresh(self):
        self.inventory_service.refresh_stock_availability()
        self.stock_table.delete(*self.stock_table.get_children())
        self._countdown_targets.clear()

        for stock in self.inventory_service.get_active_stocks():
            eta = 'READY'
            if stock.status == StockStatus.NOT_AVAILABLE:
                target = stock.time_added + timedelta(hours=stock.freeze_duration_hours)
                self._countdown_targets[stock.stock_id] = target
                eta = self._format_remaining(target)

            self.stock_table.insert(
                '',
                'end',
                iid=str(stock.stock_id),
                values=(
                    f'#{stock.stock_id}',
                    stock.time_added.strftime('%Y-%m-%d %H:%M:%S'),
                    stock.product_name,
                    f'{stock.kg} kg',
                    f'₱ {stock.price:.2f}',
                    f'{stock.freeze_duration_hours} hr',
                    stock.status.value,
                    eta,
                ),
            )

    def _sell_selected(self):
        selection = self.stock_table.selection()
        if not selection:
            messagebox.showwarning('Selection Required', 'Select a stock item to sell.')
            return

        stock_id = int(selection[0])
        try:
            self.inventory_service.sell_stock(stock_id)
            self.refresh()
        except Exception as exc:
            messagebox.showerror('Error', str(exc))

    def update_countdowns(self):
        for stock_id, target in self._countdown_targets.items():
            if self.stock_table.exists(str(stock_id)):
                self.stock_table.set(str(stock_id), 'eta', self._format_remaining(target))

    def _format_remaining(self, target: datetime):
        now = datetime.now()
        if now >= target:
            return 'READY'
        remaining = int((target - now).total_seconds())
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours:02d}:{minutes:02d}:{seconds:02d}'
