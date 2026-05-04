from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QWidget,
    QGraphicsDropShadowEffect
)
import qtawesome as qta
from models.services.inventory_service import InventoryService
from models.stock import StockStatus
from utils import friendly_error, humanize_status, is_admin, is_staff
import styles

_STATUS_COLORS = {
    StockStatus.AVAILABLE: ('#0e3d2e', '#2ECC71'),     # Green — ready
    StockStatus.NOT_AVAILABLE: ('#0B2545', '#5DADE2'),  # Icy blue — freezing
    StockStatus.SOLD: ('#3d2a0f', '#F39C12'),           # Warm amber — sold
}

class StockPage(QWidget):
    def __init__(self, inventory_service, tokens, current_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory_service = inventory_service
        self.tokens = tokens
        self.current_user = current_user
        self._stock_by_id = {}
        self._apply_modern_styling()
        self._build_ui()

    def _apply_modern_styling(self):
        """Apply modern styling to buttons."""
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.tokens.get('accent_1', '#5DADE2')}, stop:1 {self.tokens.get('accent_2', '#3498DB')});
                color: white;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 1px;
                border: 2px solid transparent;
                border-radius: 8px;
                padding: 8px 16px;
                cursor: pointer;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.tokens.get('accent_2', '#3498DB')}, stop:1 #2E86C1);
                border: 2px solid rgba(255, 255, 255, 0.4);
                box-shadow: 0 0 16px rgba(93, 173, 226, 0.5);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2E86C1, stop:1 #2874A6);
                border: 2px solid rgba(255, 255, 255, 0.2);
            }}
            QPushButton:focus {{
                outline: none;
            }}
        """)

    def _add_card_shadow(self, widget):
        """Add drop shadow effect to a card widget."""
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 40))
        widget.setGraphicsEffect(shadow)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24,24,24,24); root.setSpacing(24)
        header = QHBoxLayout()
        title = QLabel('Stocks', self)
        title.setProperty('pageTitle', True)
        header.addWidget(title); header.addStretch()
        if is_admin(self.current_user):
            btn = QPushButton("Add Stock", self)
            btn.setIcon(qta.icon('fa5s.plus-circle', color=self.tokens.get('accent_1','#5DADE2')))
            btn.clicked.connect(self._show_add_stock_dialog)
            header.addWidget(btn)
        rb = QPushButton("REFRESH", self)
        rb.setIcon(qta.icon('fa5s.sync-alt', color=self.tokens.get('accent_1','#5DADE2')))
        rb.clicked.connect(self.refresh); header.addWidget(rb)
        self.sell_button = QPushButton("Record Sale", self)
        self.sell_button.setIcon(qta.icon('fa5s.cash-register', color=self.tokens.get('success','#10B981')))
        self.sell_button.clicked.connect(self._sell_selected_stock)
        self.sell_button.setEnabled(False)
        if not is_staff(self.current_user):
            self.sell_button.setToolTip("Only staff accounts can record sales.")
        header.addWidget(self.sell_button); root.addLayout(header)
        tc = QFrame(self)
        tc.setStyleSheet(f"QFrame{{background:transparent;border:1px solid {self.tokens.get('card_border','#2D3E52')};border-radius:8px;}}")
        tl = QVBoxLayout(tc); tl.setContentsMargins(0,0,0,0); tl.setSpacing(0)
        self.table = QTableWidget(tc)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Product','Weight','Status','Price'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in (1,2,3): self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1,120); self.table.setColumnWidth(2,140); self.table.setColumnWidth(3,140)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False); self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.itemSelectionChanged.connect(self._update_sell_button)
        t = self.tokens
        self.table.setStyleSheet(f"""
            QTableWidget{{background:transparent;alternate-background-color:transparent;gridline-color:transparent;color:{t.get('text_primary','#EBF5FB')};border:1px solid {t.get('card_border','#1B4F72')};border-radius:10px;font-size:13px;font-weight:400;}}
            QTableWidget::item{{padding:0 16px;border-bottom:1px solid {t.get('border','#1B4F72')};background:transparent;}}
            QTableWidget::item:hover{{background:rgba(93,173,226,0.12);color:{t.get('accent_1','#5DADE2')};}}
            QTableWidget::item:selected{{background:rgba(93,173,226,0.08);border-left:3px solid {t.get('accent_1','#5DADE2')};color:{t.get('accent_1','#5DADE2')};font-weight:600;}}
            QHeaderView::section{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {t.get('accent_2','#3498DB')},stop:1 {t.get('accent_1','#5DADE2')});color:#FFFFFF;font-size:11px;font-weight:700;letter-spacing:0.8px;border:none;padding:10px 16px;}}
        """)
        tl.addWidget(self.table); root.addWidget(tc, 1)

    def refresh(self):
        self.inventory_service.refresh_stock_availability()
        stocks = self.inventory_service.get_active_stocks()
        self._stock_by_id = {s.stock_id: s for s in stocks}
        self.table.setRowCount(len(stocks))
        for r, s in enumerate(stocks):
            pi = QTableWidgetItem(s.product_name)
            pi.setTextAlignment(Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft)
            pi.setData(Qt.ItemDataRole.UserRole, s.stock_id)
            self.table.setItem(r, 0, pi)
            wi = QTableWidgetItem(f"{s.kg} kg")
            wi.setTextAlignment(Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(r, 1, wi)
            bg, fg = _STATUS_COLORS.get(s.status, ('#3a1a10','#e87a5a'))
            si = QTableWidgetItem(f"  {humanize_status(s.status)}  ")
            si.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            si.setBackground(QColor(bg)); si.setForeground(QColor(fg))
            si.setData(Qt.ItemDataRole.UserRole, s.stock_id)
            self.table.setItem(r, 2, si)
            pri = QTableWidgetItem(f"\u20b1 {s.price:.2f}")
            pri.setTextAlignment(Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(r, 3, pri)
        self._update_sell_button()

    def search(self, query):
        q = query.lower().strip()
        for r in range(self.table.rowCount()):
            vals = [self.table.item(r,c).text() for c in range(self.table.columnCount()) if self.table.item(r,c)]
            self.table.setRowHidden(r, bool(q and q not in " ".join(vals).lower()))
        self._update_sell_button()

    def _selected_stock(self):
        sel = self.table.selectedItems()
        if not sel: return None
        pi = self.table.item(sel[0].row(), 0)
        if pi is None: return None
        try: return self._stock_by_id.get(int(pi.data(Qt.ItemDataRole.UserRole)))
        except (TypeError, ValueError): return None

    def _update_sell_button(self):
        stock = self._selected_stock()
        self.sell_button.setEnabled(bool(is_staff(self.current_user) and stock and stock.status == StockStatus.AVAILABLE))
        if not is_staff(self.current_user):
            self.sell_button.setToolTip("Only staff accounts can record sales.")
        elif stock and stock.status != StockStatus.AVAILABLE:
            self.sell_button.setToolTip("Only Ready to Sell stock can be sold.")
        else:
            self.sell_button.setToolTip("Record the selected stock as sold.")

    def _sell_selected_stock(self):
        stock = self._selected_stock()
        if stock is None:
            QMessageBox.warning(self, "Selection Required", "Select an available stock item first."); return
        if not is_staff(self.current_user):
            QMessageBox.critical(self, "Permission Denied", "Only staff accounts can record sales."); return
        if stock.status != StockStatus.AVAILABLE:
            QMessageBox.warning(self, "Not Ready", "Only Ready to Sell stock can be sold."); return
        reply = QMessageBox.question(self, "Confirm Sale",
            f"Record sale for {stock.product_name} ({stock.kg:g} kg) at \u20b1 {stock.price:,.2f}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        user_id = getattr(self.current_user, "user_id", None)
        if not isinstance(user_id, int) or user_id < 1:
            QMessageBox.warning(self, "Account Error", "Unable to identify your account."); return
        try:
            self.inventory_service.sell_stock(stock.stock_id, user_id)
            QMessageBox.information(self, "Sale Recorded", "Sale recorded successfully.")
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Sale Error", friendly_error(exc))

    def _show_add_stock_dialog(self):
        if not is_admin(self.current_user):
            QMessageBox.critical(self, "Permission Denied", "Only admin accounts can add stock."); return
        if AddStockDialog(self.inventory_service, self.tokens, self).exec() == QDialog.DialogCode.Accepted:
            self.refresh()


class AddStockDialog(QDialog):
    def __init__(self, inventory_service, tokens, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.tokens = tokens
        self.setWindowTitle("Add Stock"); self.setMinimumWidth(420)
        self.setStyleSheet(styles.build_qss(self.tokens))
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self); form = QFormLayout()
        self.product_input = QLineEdit(self); self.product_input.setText("Ice"); self.product_input.setMaxLength(80)
        form.addRow("Product", self.product_input)
        self.quantity_input = QSpinBox(self); self.quantity_input.setRange(1,10000); self.quantity_input.setValue(1)
        form.addRow("Quantity", self.quantity_input)
        self.weight_input = QDoubleSpinBox(self)
        self.weight_input.setRange(0.01,999.99); self.weight_input.setDecimals(2)
        self.weight_input.setSingleStep(0.5); self.weight_input.setValue(1.00); self.weight_input.setSuffix(" kg")
        form.addRow("Weight", self.weight_input)
        self.price_input = QDoubleSpinBox(self)
        self.price_input.setRange(0,99999999.99); self.price_input.setDecimals(2)
        self.price_input.setSingleStep(1.0); self.price_input.setValue(5.00); self.price_input.setPrefix("\u20b1 ")
        form.addRow("Price", self.price_input)
        self.freeze_input = QSpinBox(self)
        self.freeze_input.setRange(0,8760); self.freeze_input.setValue(3); self.freeze_input.setSuffix(" hours")
        form.addRow("Freeze Time", self.freeze_input)
        self.ready_now_check = QCheckBox("Ready to sell now", self)
        self.ready_now_check.toggled.connect(self._toggle_ready_now)
        form.addRow("", self.ready_now_check)
        layout.addLayout(form)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel, self)
        bb.accepted.connect(self._save); bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def _toggle_ready_now(self, checked):
        self.freeze_input.setEnabled(not checked)
        if checked: self.freeze_input.setValue(0)
        elif self.freeze_input.value() == 0: self.freeze_input.setValue(3)

    def _save(self):
        try:
            self.inventory_service.add_stock(
                self.quantity_input.value(), self.product_input.text().strip(),
                float(self.weight_input.value()), int(self.freeze_input.value()),
                float(self.price_input.value()), self.ready_now_check.isChecked())
        except Exception as exc:
            QMessageBox.warning(self, "Add Stock Error", friendly_error(exc)); return
        QMessageBox.information(self, "Stock Added", "New stock has been added and the stock list will refresh.")
        self.accept()
