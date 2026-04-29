from datetime import datetime, timedelta
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from models.services.inventory_service import InventoryService
from models.stock import StockStatus
from views.components.modern_table import ModernTable


class StockPage(QWidget):
    def __init__(self, inventory_service: InventoryService, tokens: dict, current_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory_service = inventory_service
        self.tokens = tokens
        self.current_user = current_user
        self._countdown_targets = {}
        self.setStyleSheet(f"background:{self.tokens['bg_base']};")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # ── Header ───────────────────────────────────────────────────────────
        title = QLabel('Stock Management', self)
        title.setStyleSheet("font-size:24px; font-weight:700;")
        subtitle = QLabel('Add inventory, monitor freeze cycles, and dispatch ready items.', self)
        subtitle.setStyleSheet(f"color:{self.tokens['text_secondary']};")
        root.addWidget(title)
        root.addWidget(subtitle)

        # ── KPI strip ────────────────────────────────────────────────────────
        kpi_frame = QFrame(self)
        kpi_frame.setProperty("card", True)
        kpi_layout = QGridLayout(kpi_frame)

        self._available_card = self._metric_card(kpi_layout, 'Available', 'N/A', 0, accent_color=self.tokens['success'])
        self._freezing_card = self._metric_card(kpi_layout, 'Freezing', 'N/A', 1, accent_color=self.tokens['accent_1'])
        self._total_card = self._metric_card(kpi_layout, 'Total Items', 'N/A', 2)
        self._value_card = self._metric_card(kpi_layout, 'Stock Value', '₱ 0.00', 3)
        root.addWidget(kpi_frame)

        # ── Add stock form ───────────────────────────────────────────────────
        form_card = QFrame(self)
        form_card.setProperty("card", True)
        form_layout = QGridLayout(form_card)

        form_layout.addWidget(QLabel('Add Stock', form_card), 0, 0, 1, 5)
        self.quantity_entry = QLineEdit(form_card); self.quantity_entry.setPlaceholderText('Qty')
        self.product_entry = QLineEdit(form_card); self.product_entry.setPlaceholderText('Product')
        self.weight_entry = QLineEdit(form_card); self.weight_entry.setPlaceholderText('Weight kg')
        self.price_entry = QLineEdit(form_card); self.price_entry.setPlaceholderText('Price')
        self.freeze_entry = QLineEdit(form_card); self.freeze_entry.setPlaceholderText('Freeze hrs')
        self.quantity_entry.setValidator(QIntValidator(1, 10000, self))
        self.quantity_entry.setMaxLength(5)
        self.product_entry.setMaxLength(80)
        weight_validator = QDoubleValidator(0.01, 999.99, 2, self)
        weight_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.weight_entry.setValidator(weight_validator)
        price_validator = QDoubleValidator(0.0, 99999999.99, 2, self)
        price_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.price_entry.setValidator(price_validator)
        self.freeze_entry.setValidator(QIntValidator(0, 8760, self))
        self.freeze_entry.setMaxLength(4)
        for col, entry in enumerate([self.quantity_entry, self.product_entry, self.weight_entry, self.price_entry, self.freeze_entry]):
            form_layout.addWidget(entry, 1, col)
        freeze_btn = QPushButton('Freeze', form_card)
        freeze_btn.clicked.connect(lambda: self._add_stock(False))
        ready_btn = QPushButton('Mark Ready', form_card)
        ready_btn.clicked.connect(lambda: self._add_stock(True))
        form_layout.addWidget(freeze_btn, 2, 0, 1, 2)
        form_layout.addWidget(ready_btn, 2, 2, 1, 2)
        root.addWidget(form_card)

        # ── Table ────────────────────────────────────────────────────────────
        table_frame = QFrame(self)
        table_frame.setProperty("card", True)
        table_layout = QVBoxLayout(table_frame)

        table_header = QHBoxLayout()
        table_header.addWidget(QLabel('Active Inventory', table_frame))
        table_header.addStretch()
        self._row_count_label = QLabel('', table_frame)
        table_header.addWidget(self._row_count_label)
        self.sell_button = QPushButton('Sell Selected', table_frame)
        self.sell_button.clicked.connect(self._sell_selected)
        table_header.addWidget(self.sell_button)
        table_layout.addLayout(table_header)

        columns = ('id', 'added', 'product', 'weight', 'price', 'cycle', 'status', 'eta')
        self.stock_table = ModernTable(table_frame, columns=columns, tokens=self.tokens)
        table_layout.addWidget(self.stock_table)
        root.addWidget(table_frame, 1)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _metric_card(self, parent, title: str, value: str, col: int, accent_color: str = None):
        frame = QFrame(self)
        frame.setProperty("panel", True)
        layout = QVBoxLayout(frame)
        value_label = QLabel(value, frame)
        value_label.setStyleSheet(f"font-size:22px; font-weight:700; color:{accent_color or self.tokens['text_primary']};")
        layout.addWidget(value_label)
        layout.addWidget(QLabel(title, frame))
        parent.addWidget(frame, 0, col)
        return value_label

    def _parse_int(self, value: str, field: str) -> int:
        text = (value or '').strip()
        if not text:
            raise ValueError(f'{field} is required.')
        try:
            return int(text)
        except Exception as exc:
            raise ValueError(f'{field} must be a whole number.') from exc

    def _parse_float(self, value: str, field: str) -> float:
        text = (value or '').strip()
        if not text:
            raise ValueError(f'{field} is required.')
        try:
            return float(text)
        except Exception as exc:
            raise ValueError(f'{field} must be a number.') from exc

    # ── Actions ──────────────────────────────────────────────────────────────

    def _add_stock(self, instant: bool):
        try:
            quantity = self._parse_int(self.quantity_entry.text(), 'Quantity')
            if quantity < 1:
                raise ValueError('Quantity must be at least 1.')
            if quantity > 10000:
                raise ValueError('Quantity is too large (max 10,000).')

            product_name = (self.product_entry.text() or '').strip() or 'Ice'
            if len(product_name) > 80:
                raise ValueError('Product name must be 80 characters or fewer.')

            kg = self._parse_float(self.weight_entry.text(), 'Weight (kg)')
            if kg <= 0:
                raise ValueError('Weight must be a positive number.')
            if kg > 999.99:
                raise ValueError('Weight must be 999.99 kg or less.')

            price = self._parse_float(self.price_entry.text(), 'Price')
            if price < 0:
                raise ValueError('Price cannot be negative.')
            if price > 99999999.99:
                raise ValueError('Price is too large.')

            freeze_hours = 0
            if not instant:
                freeze_hours = self._parse_int(self.freeze_entry.text(), 'Freeze duration (hours)')
                if freeze_hours < 0:
                    raise ValueError('Freeze duration must be 0 or greater.')
                if freeze_hours > 8760:
                    raise ValueError('Freeze duration is too long (max 8,760 hours).')

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
            QMessageBox.critical(self, 'Error', str(exc))

    def refresh(self):
        self.inventory_service.refresh_stock_availability()
        self._countdown_targets.clear()

        rows = []
        available_count = 0
        freezing_count = 0
        total_value = 0.0

        for stock in self.inventory_service.get_active_stocks():
            eta = 'READY'
            if stock.status == StockStatus.NOT_AVAILABLE:
                target = stock.time_added + timedelta(hours=stock.freeze_duration_hours)
                self._countdown_targets[stock.stock_id] = target
                eta = self._format_remaining(target)
                freezing_count += 1
            else:
                available_count += 1

            total_value += stock.price

            rows.append({
                '_iid': str(stock.stock_id),
                'id': f'#{stock.stock_id}',
                'added': stock.time_added.strftime('%Y-%m-%d %H:%M:%S'),
                'product': stock.product_name,
                'weight': f'{stock.kg} kg',
                'price': f'₱ {stock.price:.2f}',
                'cycle': f'{stock.freeze_duration_hours} hr',
                'status': stock.status.value,
                'eta': eta,
            })

        self.stock_table.insert_rows(rows)

        total = len(rows)
        self._available_card.setText(str(available_count))
        self._freezing_card.setText(str(freezing_count))
        self._total_card.setText(str(total))
        self._value_card.setText(f'₱ {total_value:,.2f}')
        self._row_count_label.setText(f'{total} item{"s" if total != 1 else ""}')

    def _sell_selected(self):
        selection = self.stock_table.selection()
        if not selection:
            QMessageBox.warning(self, 'Selection Required', 'Select a stock item to sell.')
            return

        try:
            stock_id = int(selection[0])
        except Exception:
            QMessageBox.warning(self, 'Selection Error', 'Selected row is invalid.')
            return
        try:
            sold_by_user_id = getattr(self.current_user, "user_id", None)
            self.inventory_service.sell_stock(stock_id, sold_by_user_id)
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, 'Error', str(exc))

    def update_countdowns(self):
        for stock_id, target in list(self._countdown_targets.items()):
            if self.stock_table.exists(str(stock_id)):
                self.stock_table.set(str(stock_id), 'eta', self._format_remaining(target))

    def _format_remaining(self, target: datetime) -> str:
        now = datetime.now()
        if now >= target:
            return 'READY'
        remaining = int((target - now).total_seconds())
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours:02d}:{minutes:02d}:{seconds:02d}'