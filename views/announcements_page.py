from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton, QScrollArea,
    QTextEdit, QVBoxLayout, QWidget
)
import qtawesome as qta
from models.services.announcement_service import AnnouncementService
from models.user import User
from views.components.native_polish import apply_card_polish


class AnnouncementsPage(QWidget):
    def __init__(self, announcement_service: AnnouncementService, current_user: User, tokens: dict, parent=None):
        super().__init__(parent)
        self.announcement_service = announcement_service
        self.current_user = current_user
        self.tokens = tokens
        self.is_admin = 'admin' in (current_user.roles if current_user else [])
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel('Announcements')
        title.setProperty('pageTitle', True)
        header.addWidget(title)
        header.addStretch()

        if self.is_admin:
            create_btn = QPushButton('+ Create Announcement')
            create_btn.setIcon(qta.icon('fa5s.plus-circle', color=self.tokens.get('accent_1', '#FF9500')))
            create_btn.setProperty('primary', True)
            create_btn.clicked.connect(self._show_create_dialog)
            header.addWidget(create_btn)

        layout.addLayout(header)

        # Announcements list
        self.list_widget = QListWidget(self)
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.itemClicked.connect(self._on_announcement_clicked)
        layout.addWidget(self.list_widget)

    def refresh(self):
        """Refresh announcements list."""
        self.list_widget.clear()
        try:
            if self.is_admin:
                announcements = self.announcement_service.get_all_announcements(self.current_user)
                for ann in announcements:
                    item = QListWidgetItem(self.list_widget)
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        f"{ann.title} {ann.message} {ann.created_by} {ann.created_at}",
                    )
                    widget = self._create_admin_announcement_widget(ann)
                    item.setSizeHint(widget.sizeHint())
                    self.list_widget.addItem(item)
                    self.list_widget.setItemWidget(item, widget)
            else:
                announcements = self.announcement_service.get_announcements_for_user(self.current_user)
                for ann in announcements:
                    item = QListWidgetItem(self.list_widget)
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        f"{ann.title} {ann.message} {ann.created_by} {ann.created_at}",
                    )
                    widget = self._create_user_announcement_widget(ann)
                    item.setSizeHint(widget.sizeHint())
                    self.list_widget.addItem(item)
                    self.list_widget.setItemWidget(item, widget)
        except Exception as exc:
            QMessageBox.warning(self, 'Error', f'Failed to load announcements: {exc}')

    def search(self, query: str):
        text = (query or "").strip().lower()
        for idx in range(self.list_widget.count()):
            item = self.list_widget.item(idx)
            haystack = str(item.data(Qt.ItemDataRole.UserRole) or "").lower()
            item.setHidden(bool(text and text not in haystack))

    def _create_user_announcement_widget(self, announcement) -> QWidget:
        """Create widget for user view."""
        widget = QFrame(self)
        widget.setProperty('card', True)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Title row
        title_row = QHBoxLayout()
        title_label = QLabel(announcement.title)
        title_label.setProperty('cardTitle', True)
        title_row.addWidget(title_label)
        
        if not announcement.is_read:
            unread_badge = QLabel('NEW')
            unread_badge.setProperty('pill', True)
            unread_badge.setStyleSheet(f"background:{self.tokens.get('accent_2', '#3B82F6')};color:white;padding:2px 8px;border-radius:10px;font-weight:600;font-size:11px;")
            title_row.addWidget(unread_badge)
        
        title_row.addStretch()
        layout.addLayout(title_row)

        # Message
        message_label = QLabel(announcement.message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        # Footer
        footer = QHBoxLayout()
        footer_text = QLabel(f"From: {announcement.created_by} • {announcement.created_at.strftime('%b %d, %Y %I:%M %p')}")
        footer_text.setProperty('muted', True)
        footer.addWidget(footer_text)
        footer.addStretch()
        
        if not announcement.is_read:
            mark_read_btn = QPushButton('Mark as Read')
            mark_read_btn.setProperty('secondary', True)
            mark_read_btn.clicked.connect(lambda: self._mark_as_read(announcement.announcement_id))
            footer.addWidget(mark_read_btn)
        
        layout.addLayout(footer)
        apply_card_polish(widget)
        return widget

    def _create_admin_announcement_widget(self, announcement) -> QWidget:
        """Create widget for admin view."""
        widget = QFrame(self)
        widget.setProperty('card', True)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Title row
        title_row = QHBoxLayout()
        title_label = QLabel(announcement.title)
        title_label.setProperty('cardTitle', True)
        title_row.addWidget(title_label)
        title_row.addStretch()
        
        delete_btn = QPushButton('Delete')
        delete_btn.setProperty('danger', True)
        delete_btn.clicked.connect(lambda: self._delete_announcement(announcement.announcement_id))
        title_row.addWidget(delete_btn)
        
        layout.addLayout(title_row)

        # Message
        message_label = QLabel(announcement.message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        # Stats
        stats_text = QLabel(f"Recipients: {announcement.recipient_count} • Read: {announcement.read_count}")
        stats_text.setProperty('muted', True)
        layout.addWidget(stats_text)

        # Footer
        footer_text = QLabel(f"Created by: {announcement.created_by} • {announcement.created_at.strftime('%b %d, %Y %I:%M %p')}")
        footer_text.setProperty('muted', True)
        layout.addWidget(footer_text)

        apply_card_polish(widget)
        return widget

    def _on_announcement_clicked(self, item):
        """Handle announcement click."""
        pass

    def _mark_as_read(self, announcement_id: int):
        """Mark announcement as read."""
        try:
            self.announcement_service.mark_as_read(self.current_user, announcement_id)
            QTimer.singleShot(100, self.refresh)
        except Exception as exc:
            QMessageBox.warning(self, 'Error', f'Failed to mark as read: {exc}')

    def _delete_announcement(self, announcement_id: int):
        """Delete announcement."""
        reply = QMessageBox.question(
            self, 'Confirm Delete',
            'Are you sure you want to delete this announcement?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.announcement_service.delete_announcement(self.current_user, announcement_id)
                QTimer.singleShot(100, self.refresh)
            except Exception as exc:
                QMessageBox.warning(self, 'Error', f'Failed to delete announcement: {exc}')

    def _show_create_dialog(self):
        """Show create announcement dialog."""
        dialog = CreateAnnouncementDialog(self.announcement_service, self.current_user, self.tokens, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QTimer.singleShot(100, self.refresh)


class CreateAnnouncementDialog(QDialog):
    def __init__(self, announcement_service: AnnouncementService, current_user: User, tokens: dict, parent=None):
        super().__init__(parent)
        self.announcement_service = announcement_service
        self.current_user = current_user
        self.tokens = tokens
        self.setWindowTitle('Create Announcement')
        self.setMinimumWidth(500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title_label = QLabel('Title:')
        self.title_input = QTextEdit(self)
        self.title_input.setMaximumHeight(60)
        self.title_input.setPlaceholderText('Enter announcement title (max 200 characters)')
        layout.addWidget(title_label)
        layout.addWidget(self.title_input)

        # Message
        message_label = QLabel('Message:')
        self.message_input = QTextEdit(self)
        self.message_input.setPlaceholderText('Enter announcement message')
        layout.addWidget(message_label)
        layout.addWidget(self.message_input)

        # Recipients
        recipients_label = QLabel('Send to:')
        layout.addWidget(recipients_label)

        self.recipient_combo = QComboBox(self)
        self.recipient_combo.addItem('All Staff', 'all')
        self.recipient_combo.addItem('Specific Staff', 'specific')
        self.recipient_combo.currentIndexChanged.connect(self._on_recipient_type_changed)
        layout.addWidget(self.recipient_combo)

        # Staff list (hidden by default)
        self.staff_list_widget = QListWidget(self)
        self.staff_list_widget.setMaximumHeight(150)
        self.staff_list_widget.hide()
        layout.addWidget(self.staff_list_widget)

        # Load staff list
        self._load_staff_list()

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_staff_list(self):
        """Load staff users for selection."""
        try:
            staff_list = self.announcement_service.get_staff_list(self.current_user)
            for staff in staff_list:
                item = QListWidgetItem(staff['username'])
                item.setData(Qt.ItemDataRole.UserRole, staff['user_id'])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.staff_list_widget.addItem(item)
        except Exception as exc:
            QMessageBox.warning(self, 'Error', f'Failed to load staff list: {exc}')

    def _on_recipient_type_changed(self, index):
        """Show/hide staff list based on recipient type."""
        recipient_type = self.recipient_combo.currentData()
        self.staff_list_widget.setVisible(recipient_type == 'specific')

    def _on_accept(self):
        """Create announcement."""
        title = self.title_input.toPlainText().strip()
        message = self.message_input.toPlainText().strip()
        recipient_type = self.recipient_combo.currentData()

        if not title:
            QMessageBox.warning(self, 'Validation Error', 'Title is required.')
            return

        if not message:
            QMessageBox.warning(self, 'Validation Error', 'Message is required.')
            return

        specific_user_ids = None
        if recipient_type == 'specific':
            specific_user_ids = []
            for i in range(self.staff_list_widget.count()):
                item = self.staff_list_widget.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    specific_user_ids.append(item.data(Qt.ItemDataRole.UserRole))
            
            if not specific_user_ids:
                QMessageBox.warning(self, 'Validation Error', 'Please select at least one staff member.')
                return

        try:
            self.announcement_service.create_announcement(
                self.current_user,
                title,
                message,
                recipient_type,
                specific_user_ids
            )
            QMessageBox.information(self, 'Success', 'Announcement created successfully.')
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, 'Error', f'Failed to create announcement: {exc}')
