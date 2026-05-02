from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton, QScrollArea,
    QTextEdit, QVBoxLayout, QWidget
)
import qtawesome as qta
from models.services.announcement_service import AnnouncementService
from models.user import User
from utils import is_admin
from views.components.native_polish import apply_card_polish
import styles


class AnnouncementsPage(QWidget):
    def __init__(self, announcement_service, current_user, tokens, parent=None):
        super().__init__(parent)
        self.announcement_service = announcement_service
        self.current_user = current_user
        self.tokens = tokens
        self._user_is_admin = is_admin(current_user)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(10,10,10,10); layout.setSpacing(10)
        header = QHBoxLayout()
        title = QLabel('Announcements'); title.setProperty('pageTitle', True)
        header.addWidget(title); header.addStretch()
        if self._user_is_admin:
            create_btn = QPushButton('+ Create Announcement')
            create_btn.setIcon(qta.icon('fa5s.plus-circle', color=self.tokens.get('accent_1','#5DADE2')))
            create_btn.setProperty('primary', True)
            create_btn.clicked.connect(self._show_create_dialog)
            header.addWidget(create_btn)
        layout.addLayout(header)
        self.list_widget = QListWidget(self)
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.itemClicked.connect(self._on_announcement_clicked)
        layout.addWidget(self.list_widget)

    def refresh(self):
        self.list_widget.clear()
        try:
            announcements = (self.announcement_service.get_all_announcements(self.current_user)
                if self._user_is_admin else self.announcement_service.get_announcements_for_user(self.current_user))
            for ann in announcements:
                item = QListWidgetItem(self.list_widget)
                item.setData(Qt.ItemDataRole.UserRole, f"{ann.title} {ann.message} {ann.created_by} {ann.created_at}")
                widget = (self._create_admin_announcement_widget(ann) if self._user_is_admin
                    else self._create_user_announcement_widget(ann))
                item.setSizeHint(widget.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)
        except Exception as exc:
            QMessageBox.warning(self, 'Error', f'Failed to load announcements: {exc}')

    def search(self, query):
        text = (query or "").strip().lower()
        for idx in range(self.list_widget.count()):
            item = self.list_widget.item(idx)
            item.setHidden(bool(text and text not in str(item.data(Qt.ItemDataRole.UserRole) or "").lower()))

    def _create_user_announcement_widget(self, ann):
        widget = QFrame(self); widget.setProperty('card', True)
        layout = QVBoxLayout(widget); layout.setContentsMargins(12,10,12,10); layout.setSpacing(6)
        title_row = QHBoxLayout()
        tl = QLabel(ann.title); tl.setProperty('cardTitle', True); title_row.addWidget(tl)
        if not ann.is_read:
            badge = QLabel('NEW'); badge.setProperty('pill', True)
            badge.setStyleSheet(f"background:{self.tokens.get('accent_2','#3B82F6')};color:white;padding:2px 8px;border-radius:10px;font-weight:600;font-size:11px;")
            title_row.addWidget(badge)
        title_row.addStretch(); layout.addLayout(title_row)
        msg = QLabel(ann.message); msg.setWordWrap(True); layout.addWidget(msg)
        footer = QHBoxLayout()
        ft = QLabel(f"From: {ann.created_by} \u2022 {ann.created_at.strftime('%b %d, %Y %I:%M %p')}")
        ft.setProperty('muted', True); footer.addWidget(ft); footer.addStretch()
        if not ann.is_read:
            mr = QPushButton('Mark as Read'); mr.setProperty('secondary', True)
            mr.clicked.connect(lambda: self._mark_as_read(ann.announcement_id)); footer.addWidget(mr)
        layout.addLayout(footer); apply_card_polish(widget); return widget

    def _create_admin_announcement_widget(self, ann):
        widget = QFrame(self); widget.setProperty('card', True)
        layout = QVBoxLayout(widget); layout.setContentsMargins(12,10,12,10); layout.setSpacing(6)
        title_row = QHBoxLayout()
        tl = QLabel(ann.title); tl.setProperty('cardTitle', True)
        title_row.addWidget(tl); title_row.addStretch()
        del_btn = QPushButton('Delete'); del_btn.setProperty('danger', True)
        del_btn.clicked.connect(lambda: self._delete_announcement(ann.announcement_id))
        title_row.addWidget(del_btn); layout.addLayout(title_row)
        msg = QLabel(ann.message); msg.setWordWrap(True); layout.addWidget(msg)
        stats = QLabel(f"Recipients: {ann.recipient_count} \u2022 Read: {ann.read_count}")
        stats.setProperty('muted', True); layout.addWidget(stats)
        ft = QLabel(f"Created by: {ann.created_by} \u2022 {ann.created_at.strftime('%b %d, %Y %I:%M %p')}")
        ft.setProperty('muted', True); layout.addWidget(ft)
        apply_card_polish(widget); return widget

    def _on_announcement_clicked(self, item): pass

    def _mark_as_read(self, announcement_id):
        try:
            self.announcement_service.mark_as_read(self.current_user, announcement_id)
            QTimer.singleShot(100, self.refresh)
        except Exception as exc:
            QMessageBox.warning(self, 'Error', f'Failed to mark as read: {exc}')

    def _delete_announcement(self, announcement_id):
        if QMessageBox.question(self, 'Confirm Delete', 'Are you sure you want to delete this announcement?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                self.announcement_service.delete_announcement(self.current_user, announcement_id)
                QTimer.singleShot(100, self.refresh)
            except Exception as exc:
                QMessageBox.warning(self, 'Error', f'Failed to delete announcement: {exc}')

    def _show_create_dialog(self):
        if CreateAnnouncementDialog(self.announcement_service, self.current_user, self.tokens, self).exec() == QDialog.DialogCode.Accepted:
            QTimer.singleShot(100, self.refresh)


class CreateAnnouncementDialog(QDialog):
    def __init__(self, announcement_service, current_user, tokens, parent=None):
        super().__init__(parent)
        self.announcement_service = announcement_service
        self.current_user = current_user; self.tokens = tokens
        self.setWindowTitle('Create Announcement'); self.setMinimumWidth(500)
        self.setStyleSheet(styles.build_qss(self.tokens))
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(10)
        layout.addWidget(QLabel('Title:'))
        self.title_input = QTextEdit(self); self.title_input.setMaximumHeight(60)
        self.title_input.setPlaceholderText('Enter announcement title (max 200 characters)')
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel('Message:'))
        self.message_input = QTextEdit(self)
        self.message_input.setPlaceholderText('Enter announcement message')
        layout.addWidget(self.message_input)
        layout.addWidget(QLabel('Send to:'))
        self.recipient_combo = QComboBox(self)
        self.recipient_combo.addItem('All Staff', 'all')
        self.recipient_combo.addItem('Specific Staff', 'specific')
        self.recipient_combo.currentIndexChanged.connect(self._on_recipient_type_changed)
        layout.addWidget(self.recipient_combo)
        self.staff_list_widget = QListWidget(self); self.staff_list_widget.setMaximumHeight(150)
        self.staff_list_widget.hide(); layout.addWidget(self.staff_list_widget)
        self._load_staff_list()
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._on_accept); bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def _load_staff_list(self):
        try:
            for staff in self.announcement_service.get_staff_list(self.current_user):
                item = QListWidgetItem(staff['username'])
                item.setData(Qt.ItemDataRole.UserRole, staff['user_id'])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.staff_list_widget.addItem(item)
        except Exception as exc:
            QMessageBox.warning(self, 'Error', f'Failed to load staff list: {exc}')

    def _on_recipient_type_changed(self, index):
        self.staff_list_widget.setVisible(self.recipient_combo.currentData() == 'specific')

    def _on_accept(self):
        title = self.title_input.toPlainText().strip()
        message = self.message_input.toPlainText().strip()
        recipient_type = self.recipient_combo.currentData()
        if not title:
            QMessageBox.warning(self, 'Validation Error', 'Title is required.'); return
        if not message:
            QMessageBox.warning(self, 'Validation Error', 'Message is required.'); return
        specific_user_ids = None
        if recipient_type == 'specific':
            specific_user_ids = [self.staff_list_widget.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.staff_list_widget.count())
                if self.staff_list_widget.item(i).checkState() == Qt.CheckState.Checked]
            if not specific_user_ids:
                QMessageBox.warning(self, 'Validation Error', 'Please select at least one staff member.'); return
        try:
            self.announcement_service.create_announcement(self.current_user, title, message, recipient_type, specific_user_ids)
            QMessageBox.information(self, 'Success', 'Announcement created successfully.')
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, 'Error', f'Failed to create announcement: {exc}')
