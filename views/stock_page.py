from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta

from models.services.inventory_service import InventoryService
from models.stock import StockStatus
from utils import friendly_error, humanize_status


class StockPage(QWidget):
    def __init__(self, inventory_service: InventoryService, tokens: dict, current_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory_service = inventory_service
        self.tokens = tokens
        self.current_user = current_user
        self._stock_by_id = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(24)

        # Header
        header = QHBoxLayout()
        title = QLabel('Stocks', self)
        title.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: #8a9bb0;
            letter-spacing: 1px;
        """)
        header.addWidget(title)
        header.addStretch()

        if self._is_admin():
            self.add_button = QPushButton("Add Stock", self)
            self.add_button.setIcon(qta.icon('fa5s.plus-circle', color=self.tokens.get('accent_1', '#FF9500')))
            self.add_button.clicked.connect(self._show_add_stock_dialog)
            header.addWidget(self.add_button)

        self.refresh_button = QPushButton("REFRESH", self)
        self.refresh_button.setIcon(qta.icon('fa5s.sync-alt', color=self.tokens.get('accent_1', '#FF9500')))
        self.refresh_button.clicked.connect(self.refresh)
        header.addWidget(self.refresh_button)

        self.sell_button = QPushButton("Record Sale", self)
        self.sell_button.setIcon(qta.icon('fa5s.cash-register', color=self.tokens.get('success', '#10B981')))
        self.sell_button.clicked.connect(self._sell_selected_stock)
        self.sell_button.setEnabled(False)
        if not self._is_staff():
            self.sell_button.setToolTip("Only staff accounts can record sales.")
        header.addWidget(self.sell_button)
        root.addLayout(header)

        # Table card
        table_card = QFrame(self)
        table_card.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: 1px solid {self.tokens.get('card_border', '#2D3E52')};
                border-radius: 8px;
            }}
        """)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        # Table
        self.table = QTableWidget(table_card)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Product', 'Weight', 'Status', 'Price'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 140)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.itemSelectionChanged.connect(self._update_sell_button)
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: transparent;
                alternate-background-color: transparent;
                gridline-color: {self.tokens.get('border', '#2D3E52')};
                color: {self.tokens.get('text_primary', '#F0F4F8')};
                border: none;
                font-size: 13px;
                font-weight: 400;
            }}
            QTableWidget::item {{
                padding: 0 16px;
                border-bottom: 1px solid {self.tokens.get('border', '#2D3E52')};
                background: transparent;
            }}
            QTableWidget::item:hover {{
                background: {self.tokens.get('table_row_hover', '#1A2A42')};
                color: {self.tokens.get('accent_2', '#3B82F6')};
            }}
            QTableWidget::item:selected {{
                background: transparent;
                border-left: 3px solid {self.tokens.get('accent_2', '#3B82F6')};
                color: {self.tokens.get('accent_2', '#3B82F6')};
                font-weight: 600;
            }}
            QHeaderView::section {{
                background: transparent;
                color: {self.tokens.get('text_secondary', '#9CA3AF')};
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                border: none;
                padding: 10px 16px;
                border-bottom: 1px solid {self.tokens.get('border', '#2D3E52')};
            }}
        """)
        
        table_layout.addWidget(self.table)
        root.addWidget(table_card, 1)

    def _create_status_chip(self, status: StockStatus) -> QWidget:
        chip = QFrame()
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(10, 3, 10, 3)
        
        label = QLabel(humanize_status(status))
        
        if status == StockStatus.AVAILABLE:
            bg = '#1a3a2a'
            text = '#4ecfba'
        elif status == StockStatus.NOT_AVAILABLE:
            bg = '#0f1e2f'
            text = '#5a9fd4'
        else:
            bg = '#3a1a10'
            text = '#e87a5a'
        
        chip.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: 20px;
            }}
        """)
        label.setStyleSheet(f"""
            QLabel {{
                color: {text};
                font-size: 11px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        
        chip_layout.addWidget(label)
        return chip

    def refresh(self):
        self.inventory_service.refresh_stock_availability()
        stocks = self.inventory_service.get_active_stocks()
        self._stock_by_id = {stock.stock_id: stock for stock in stocks}
        
        self.table.setRowCount(len(stocks))
        
        for row, stock in enumerate(stocks):
            # Product name
            product_item = QTableWidgetItem(stock.product_name)
            product_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            product_item.setData(Qt.ItemDataRole.UserRole, stock.stock_id)
            self.table.setItem(row, 0, product_item)
            
            # Quantity (using kg)
            qty_item = QTableWidgetItem(f"{stock.kg} kg")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 1, qty_item)
            
            # Status chip
            status_text = humanize_status(stock.status)
            if stock.status == StockStatus.AVAILABLE:
                bg = '#1a3a2a'
                text = '#4ecfba'
            elif stock.status == StockStatus.NOT_AVAILABLE:
                bg = '#0f1e2f'
                text = '#5a9fd4'
            else:
                bg = '#3a1a10'
                text = '#e87a5a'
            
            status_item = QTableWidgetItem(f"  {status_text}  ")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setBackground(self._hex_to_qcolor(bg))
            status_item.setForeground(self._hex_to_qcolor(text))
            status_item.setData(Qt.ItemDataRole.UserRole, stock.stock_id)
            self.table.setItem(row, 2, status_item)
            
            # Price
            price_item = QTableWidgetItem(f"₱ {stock.price:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 3, price_item)
        self._update_sell_button()
    
    def _hex_to_qcolor(self, hex_color: str):
        from PyQt6.QtGui import QColor
        return QColor(hex_color)

    def search(self, query: str):
        """Search and filter stocks by all visible stock fields."""
        query_lower = query.lower().strip()
        for row in range(self.table.rowCount()):
            values = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    values.append(item.text())
            self.table.setRowHidden(row, bool(query_lower and query_lower not in " ".join(values).lower()))
        self._update_sell_button()

    def _is_admin(self) -> bool:
        roles = getattr(self.current_user, "roles", []) or []
        return "admin" in roles

    def _is_staff(self) -> bool:
        roles = getattr(self.current_user, "roles", []) or []
        return "staff" in roles

    def _selected_stock(self):
        selected = self.table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        product_item = self.table.item(row, 0)
        if product_item is None:
            return None
        stock_id = product_item.data(Qt.ItemDataRole.UserRole)
        try:
            return self._stock_by_id.get(int(stock_id))
        except (TypeError, ValueError):
            return None

    def _update_sell_button(self):
        stock = self._selected_stock()
        can_sell = bool(self._is_staff() and stock and stock.status == StockStatus.AVAILABLE)
        self.sell_button.setEnabled(can_sell)
        if not self._is_staff():
            self.sell_button.setToolTip("Only staff accounts can record sales.")
        elif stock and stock.status != StockStatus.AVAILABLE:
            self.sell_button.setToolTip("Only Ready to Sell stock can be sold.")
        else:
            self.sell_button.setToolTip("Record the selected stock as sold.")

    def _sell_selected_stock(self):
        stock = self._selected_stock()
        if stock is None:
            QMessageBox.warning(self, "Selection Required", "Select an available stock item first.")
            return
        if not self._is_staff():
            QMessageBox.critical(self, "Permission Denied", "Only staff accounts can record sales.")
            return
        if stock.status != StockStatus.AVAILABLE:
            QMessageBox.warning(self, "Not Ready", "Only Ready to Sell stock can be sold.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Sale",
            f"Record sale for {stock.product_name} ({stock.kg:g} kg) at ₱ {stock.price:,.2f}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        user_id = getattr(self.current_user, "user_id", None)
        if not isinstance(user_id, int) or user_id < 1:
            QMessageBox.warning(self, "Account Error", "Unable to identify your account.")
            return
        try:
            self.inventory_service.sell_stock(stock.stock_id, user_id)
            QMessageBox.information(self, "Sale Recorded", "Sale recorded successfully.")
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Sale Error", friendly_error(exc))

    def _show_add_stock_dialog(self):
        if not self._is_admin():
            QMessageBox.critical(self, "Permission Denied", "Only admin accounts can add stock.")
            return

        dialog = AddStockDialog(self.inventory_service, self.tokens, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()


class AddStockDialog(QDialog):
    def __init__(self, inventory_service: InventoryService, tokens: dict, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.tokens = tokens
        self.setWindowTitle("Add Stock")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.product_input = QLineEdit(self)
        self.product_input.setText("Ice")
        self.product_input.setMaxLength(80)
        form.addRow("Product", self.product_input)

        self.quantity_input = QSpinBox(self)
        self.quantity_input.setRange(1, 10000)
        self.quantity_input.setValue(1)
        form.addRow("Quantity", self.quantity_input)

        self.weight_input = QDoubleSpinBox(self)
        self.weight_input.setRange(0.01, 999.99)
        self.weight_input.setDecimals(2)
        self.weight_input.setSingleStep(0.5)
        self.weight_input.setValue(1.00)
        self.weight_input.setSuffix(" kg")
        form.addRow("Weight", self.weight_input)

        self.price_input = QDoubleSpinBox(self)
        self.price_input.setRange(0, 99999999.99)
        self.price_input.setDecimals(2)
        self.price_input.setSingleStep(1.0)
        self.price_input.setValue(5.00)
        self.price_input.setPrefix("₱ ")
        form.addRow("Price", self.price_input)

        self.freeze_input = QSpinBox(self)
        self.freeze_input.setRange(0, 8760)
        self.freeze_input.setValue(3)
        self.freeze_input.setSuffix(" hours")
        form.addRow("Freeze Time", self.freeze_input)

        self.ready_now_check = QCheckBox("Ready to sell now", self)
        self.ready_now_check.toggled.connect(self._toggle_ready_now)
        form.addRow("", self.ready_now_check)

        layout.addLayout(form)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        button_box.accepted.connect(self._save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _toggle_ready_now(self, checked: bool):
        self.freeze_input.setEnabled(not checked)
        if checked:
            self.freeze_input.setValue(0)
        elif self.freeze_input.value() == 0:
            self.freeze_input.setValue(3)

    def _save(self):
        product_name = self.product_input.text().strip()
        try:
            self.inventory_service.add_stock(
                self.quantity_input.value(),
                product_name,
                float(self.weight_input.value()),
                int(self.freeze_input.value()),
                float(self.price_input.value()),
                self.ready_now_check.isChecked(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "Add Stock Error", friendly_error(exc))
            return

        QMessageBox.information(self, "Stock Added", "New stock has been added and the stock list will refresh.")
        self.accept()
