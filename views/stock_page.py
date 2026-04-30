from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QHeaderView

from models.services.inventory_service import InventoryService
from models.stock import StockStatus


class StockPage(QWidget):
    def __init__(self, inventory_service: InventoryService, tokens: dict, current_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory_service = inventory_service
        self.tokens = tokens
        self.current_user = current_user
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(24)

        # Header
        title = QLabel('STOCKS', self)
        title.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: #8a9bb0;
            letter-spacing: 1px;
        """)
        root.addWidget(title)

        # Table card
        table_card = QFrame(self)
        table_card.setStyleSheet(f"""
            QFrame {{
                background: #152231;
                border: 1px solid #1e3a4f;
                border-radius: 10px;
            }}
        """)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        # Table
        self.table = QTableWidget(table_card)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['PRODUCT NAME', 'QUANTITY', 'STATUS', 'PRICE'])
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
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: #0f1923;
                alternate-background-color: #152231;
                gridline-color: #172840;
                color: #8a9bb0;
                border: none;
                font-size: 13px;
                font-weight: 400;
            }}
            QTableWidget::item {{
                padding: 0 16px;
                border-bottom: 1px solid #172840;
            }}
            QTableWidget::item:hover {{
                background: #1a2a3f;
            }}
            QTableWidget::item:selected {{
                background: #1e3a4f;
                border-left: 3px solid #e8c97a;
                color: #e8c97a;
            }}
            QHeaderView::section {{
                background: #0a1520;
                color: #4a5a6b;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                border: none;
                padding: 10px 16px;
                border-bottom: 1px solid #172840;
            }}
        """)
        
        table_layout.addWidget(self.table)
        root.addWidget(table_card, 1)

    def _create_status_chip(self, status: StockStatus) -> QWidget:
        chip = QFrame()
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(10, 3, 10, 3)
        
        label = QLabel(status.value.replace('_', ' ').title())
        
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
        
        self.table.setRowCount(len(stocks))
        
        for row, stock in enumerate(stocks):
            # Product name
            product_item = QTableWidgetItem(stock.product_name)
            product_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 0, product_item)
            
            # Quantity (using kg)
            qty_item = QTableWidgetItem(f"{stock.kg} kg")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 1, qty_item)
            
            # Status chip
            status_text = 'Available' if stock.status == StockStatus.AVAILABLE else 'Freezing' if stock.status == StockStatus.NOT_AVAILABLE else 'Sold'
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
            self.table.setItem(row, 2, status_item)
            
            # Price
            price_item = QTableWidgetItem(f"₱ {stock.price:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 3, price_item)
    
    def _hex_to_qcolor(self, hex_color: str):
        from PyQt6.QtGui import QColor
        return QColor(hex_color)