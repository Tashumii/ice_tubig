from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class ModernTable(QWidget):
    def __init__(
        self,
        master: Optional[QWidget],
        columns: List[str],
        tokens: Dict[str, str],
        column_widths: Optional[Dict[str, int]] = None,
        row_height: int = 36,
        header_height: int = 40,
        *args,
        **kwargs,
    ):
        super().__init__(master, *args, **kwargs)
        self.tokens = tokens
        self.columns = list(columns)
        self.column_widths = column_widths or {}
        self.row_height = row_height
        self.header_height = header_height
        self._data: List[Dict[str, Any]] = []
        self._iid_map: Dict[str, Dict[str, Any]] = {}
        self._iid_counter = 0
        self._selected_iid: Optional[str] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table = QTableWidget(self)
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels([c.replace("_", " ").title() for c in self.columns])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setFixedHeight(self.header_height)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.setSortingEnabled(True)
        self.table.itemSelectionChanged.connect(self._sync_selection)

        for idx, col in enumerate(self.columns):
            if col in self.column_widths:
                self.table.setColumnWidth(idx, self.column_widths[col])

        self._apply_style()
        layout.addWidget(self.table)

    def _apply_style(self):
        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                background: {self.tokens.get('bg_surface', '#ffffff')};
                color: {self.tokens.get('text_primary', '#111111')};
                gridline-color: {self.tokens.get('border', '#dddddd')};
                border: 1px solid {self.tokens.get('card_border', self.tokens.get('border', '#dddddd'))};
                border-radius: 12px;
                selection-background-color: {self.tokens.get('pill_bg', self.tokens.get('bg_elevated', '#f5f5f5'))};
                alternate-background-color: {self.tokens.get('table_row_alt', self.tokens.get('surface_muted', '#fafafa'))};
                padding: 2px;
            }}
            QTableWidget::item {{
                padding: 6px 8px;
                border: none;
            }}
            QTableWidget::item:selected {{
                color: {self.tokens.get('text_primary', '#111111')};
            }}
            QHeaderView::section {{
                background: {self.tokens.get('table_header_bg', self.tokens.get('accent_1', '#E97845'))};
                color: {self.tokens.get('table_header_text', '#ffffff')};
                border: none;
                padding: 8px;
                font-weight: 700;
                letter-spacing: 0.4px;
            }}
            """
        )

    def clear(self):
        self._data = []
        self._iid_map.clear()
        self._selected_iid = None
        self.table.setRowCount(0)

    def insert_rows(self, rows: List[Dict[str, Any]]):
        self._data = []
        self._iid_map = {}

        for row in rows:
            iid = str(row.get("_iid", self._iid_counter))
            if "_iid" not in row:
                self._iid_counter += 1
            row_copy = dict(row)
            row_copy["_iid"] = iid
            self._data.append(row_copy)
            self._iid_map[iid] = row_copy

        self.table.setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self._data))

        for r_idx, row in enumerate(self._data):
            for c_idx, col in enumerate(self.columns):
                item = QTableWidgetItem(str(row.get(col, "")))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, row["_iid"])
                if c_idx == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r_idx, c_idx, item)

        self.table.setUpdatesEnabled(True)
        self.table.setSortingEnabled(True)
        self.table.viewport().update()
        self._restore_selection()

    def append_row(self, row: Dict[str, Any]):
        rows = list(self._data)
        rows.append(row)
        self.insert_rows(rows)

    def insert(self, parent, index, iid: Optional[str] = None, values: Optional[tuple] = None):
        row = {}
        values = values or ()
        for idx, col in enumerate(self.columns):
            row[col] = values[idx] if idx < len(values) else ""
        row["_iid"] = str(iid if iid is not None else self._iid_counter)
        if iid is None:
            self._iid_counter += 1
        self.append_row(row)
        return row["_iid"]

    def get_children(self):
        return [r.get("_iid") for r in self._data]

    def delete(self, *items):
        remove = {str(i) for i in items}
        self.insert_rows([r for r in self._data if str(r.get("_iid")) not in remove])

    def selection(self):
        return [self._selected_iid] if self._selected_iid else []

    def selection_set(self, iid: str):
        iid = str(iid)
        self._selected_iid = iid
        self._restore_selection()

    def exists(self, iid: str) -> bool:
        return str(iid) in self._iid_map

    def set(self, iid: str, column: str, value: Any):
        iid = str(iid)
        if iid not in self._iid_map:
            return False
        self._iid_map[iid][column] = value
        for r_idx in range(self.table.rowCount()):
            item = self.table.item(r_idx, 0)
            if item and str(item.data(Qt.ItemDataRole.UserRole)) == iid:
                c_idx = self.columns.index(column)
                target = self.table.item(r_idx, c_idx)
                if target is None:
                    target = QTableWidgetItem()
                    self.table.setItem(r_idx, c_idx, target)
                target.setText(str(value))
                return True
        return False

    def _sync_selection(self):
        selected = self.table.selectedItems()
        if not selected:
            self._selected_iid = None
            return
        self._selected_iid = str(selected[0].data(Qt.ItemDataRole.UserRole))

    def _restore_selection(self):
        if not self._selected_iid:
            return
        for r_idx in range(self.table.rowCount()):
            item = self.table.item(r_idx, 0)
            if item and str(item.data(Qt.ItemDataRole.UserRole)) == self._selected_iid:
                self.table.selectRow(r_idx)
                break
