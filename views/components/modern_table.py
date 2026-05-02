from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QSizePolicy

COLUMN_LABELS = {
    "sale_id": "Sale #", "stock_id": "Stock #", "user_id": "User #",
    "sold_at": "Sold At", "actual_in": "Time In", "actual_out": "Time Out",
    "expected_in": "Expected In", "expected_out": "Expected Out",
    "sales_count": "Sales", "created_at": "Created", "is_read": "Read",
    "seller": "Staff", "employee": "Staff", "event": "Activity",
    "severity": "Type", "details": "Details", "time": "Time",
    "staff": "Staff", "date": "Date", "status": "Status",
    "product": "Product", "weight": "Weight", "price": "Price",
    "shift": "Shift", "revenue": "Revenue", "sales": "Sales",
    "quantity": "Qty", "amount": "Amount",
}


class ModernTable(QWidget):
    def __init__(self, master, columns, tokens, column_widths=None,
                 row_height=40, header_height=44, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.tokens = tokens
        self.columns = list(columns)
        self.column_widths = column_widths or {}
        self.row_height = row_height
        self.header_height = header_height
        self._data = []
        self._iid_map = {}
        self._iid_counter = 0
        self._selected_iid = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.table = QTableWidget(self)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(
            [COLUMN_LABELS.get(c, c.replace("_", " ").title()) for c in self.columns])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setFixedHeight(self.header_height)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.setSortingEnabled(True)
        self.table.itemSelectionChanged.connect(self._sync_selection)
        self.table.setMouseTracking(True)
        self.table.itemEntered.connect(self._on_item_hover)

        if self.column_widths:
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            for idx, col in enumerate(self.columns):
                if col in self.column_widths:
                    self.table.setColumnWidth(idx, self.column_widths[col])
        else:
            for idx in range(len(self.columns)):
                self.table.horizontalHeader().setSectionResizeMode(idx, QHeaderView.ResizeMode.Stretch)

        self._apply_style()
        layout.addWidget(self.table)

    def _apply_style(self):
        t = self.tokens
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: transparent;
                color: {t.get('text_primary', '#EBF5FB')};
                gridline-color: transparent;
                border: 1px solid {t.get('card_border', '#1B4F72')};
                border-radius: 10px;
                selection-background-color: transparent;
                alternate-background-color: transparent;
                padding: 2px;
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border: none;
                border-bottom: 1px solid {t.get('border', '#1B4F72')};
                background: transparent;
            }}
            QTableWidget::item:hover {{
                background-color: rgba(93, 173, 226, 0.12);
                color: {t.get('accent_1', '#5DADE2')};
            }}
            QTableWidget::item:selected {{
                color: {t.get('accent_1', '#5DADE2')};
                background: rgba(93, 173, 226, 0.08);
                border-left: 3px solid {t.get('accent_1', '#5DADE2')};
                font-weight: 600;
            }}
            QHeaderView::section {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t.get('accent_2', '#3498DB')}, stop:1 {t.get('accent_1', '#5DADE2')});
                color: #FFFFFF;
                border: none;
                padding: 10px 12px;
                font-weight: 700;
                font-size: 12px;
                letter-spacing: 0.5px;
            }}
            QHeaderView::section:first {{
                border-top-left-radius: 10px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: 10px;
            }}
            QHeaderView::section:hover {{
                background: {t.get('accent_2', '#3498DB')};
            }}
        """)

    def clear(self):
        self._data = []; self._iid_map.clear(); self._selected_iid = None
        self.table.setRowCount(0)

    def insert_rows(self, rows):
        self._data = []; self._iid_map = {}
        for row in rows:
            iid = str(row.get("_iid", self._iid_counter))
            if "_iid" not in row:
                self._iid_counter += 1
            row_copy = dict(row); row_copy["_iid"] = iid
            self._data.append(row_copy); self._iid_map[iid] = row_copy

        self.table.setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self._data))
        for r_idx, row in enumerate(self._data):
            for c_idx, col in enumerate(self.columns):
                item = QTableWidgetItem(str(row.get(col, "")))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, row["_iid"])
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r_idx, c_idx, item)
        self.table.setUpdatesEnabled(True)
        self.table.setSortingEnabled(True)
        self.table.viewport().update()
        self._restore_selection()

    def append_row(self, row):
        self.insert_rows(list(self._data) + [row])

    def insert(self, parent, index, iid=None, values=None):
        row = {}; values = values or ()
        for idx, col in enumerate(self.columns):
            row[col] = values[idx] if idx < len(values) else ""
        row["_iid"] = str(iid if iid is not None else self._iid_counter)
        if iid is None: self._iid_counter += 1
        self.append_row(row); return row["_iid"]

    def get_children(self):
        return [r.get("_iid") for r in self._data]

    def delete(self, *items):
        remove = {str(i) for i in items}
        self.insert_rows([r for r in self._data if str(r.get("_iid")) not in remove])

    def selection(self):
        return [self._selected_iid] if self._selected_iid else []

    def selection_set(self, iid):
        self._selected_iid = str(iid); self._restore_selection()

    def exists(self, iid):
        return str(iid) in self._iid_map

    def set(self, iid, column, value):
        iid = str(iid)
        if iid not in self._iid_map: return False
        self._iid_map[iid][column] = value
        for r_idx in range(self.table.rowCount()):
            item = self.table.item(r_idx, 0)
            if item and str(item.data(Qt.ItemDataRole.UserRole)) == iid:
                c_idx = self.columns.index(column)
                target = self.table.item(r_idx, c_idx)
                if target is None:
                    target = QTableWidgetItem(); self.table.setItem(r_idx, c_idx, target)
                target.setText(str(value)); return True
        return False

    def filter_rows(self, query):
        text = (query or "").strip().lower()
        for r_idx in range(self.table.rowCount()):
            if not text:
                self.table.setRowHidden(r_idx, False); continue
            values = [self.table.item(r_idx, c).text() for c in range(self.table.columnCount()) if self.table.item(r_idx, c)]
            self.table.setRowHidden(r_idx, text not in " ".join(values).lower())

    def _sync_selection(self):
        selected = self.table.selectedItems()
        self._selected_iid = str(selected[0].data(Qt.ItemDataRole.UserRole)) if selected else None

    def _restore_selection(self):
        if not self._selected_iid: return
        for r_idx in range(self.table.rowCount()):
            item = self.table.item(r_idx, 0)
            if item and str(item.data(Qt.ItemDataRole.UserRole)) == self._selected_iid:
                self.table.selectRow(r_idx); break

    def _on_item_hover(self, item):
        if item:
            col = item.column()
            column_name = self.columns[col] if col < len(self.columns) else ""
            label = COLUMN_LABELS.get(column_name, column_name.replace('_', ' ').title())
            item.setToolTip(f"<b>{label}</b><br/>{item.text()}")
