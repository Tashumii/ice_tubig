from typing import Any, Callable, Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from services.auth_service import AuthService
from models.user import User
from database import DatabaseError


class LoginPage(QWidget):
    def __init__(
        self,
        master,
        auth_service: AuthService,
        tokens: Optional[Dict[str, str]] = None,
        on_login_success: Callable[[User], None] = None,
        initial_error: str = '',
        *args,
        **kwargs,
    ):
        super().__init__(master, *args, **kwargs)
        self.auth_service = auth_service
        default_tokens = {
            'bg_base': '#FAF6F1',
            'bg_surface': '#FFFFFF',
            'bg_input': '#F2EDE9',
            'accent_1': '#E97845',
            'accent_2': '#D96A3C',
            'text_primary': '#1A1816',
            'text_secondary': '#5D5651',
            'text_muted': '#9D968E',
            'border': '#E8E0D5',
            'danger': '#E53935',
        }
        self.tokens = {**default_tokens, **(tokens or {})}
        self.on_login_success = on_login_success
        self.initial_error = initial_error
        self.setStyleSheet(f"background:{self.tokens['bg_base']};")
        self._build_ui()

    def _build_ui(self):
        """Build login page UI."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame(self)
        card.setFixedWidth(520)
        card.setProperty("card", True)
        grid = QGridLayout(card)
        grid.setContentsMargins(24, 20, 24, 20)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        title = QLabel("ICETUBIG", card)
        title.setStyleSheet(f"color:{self.tokens['accent_1']}; font-size:34px; font-weight:700;")
        subtitle = QLabel("Inventory Management System", card)
        subtitle.setStyleSheet(f"color:{self.tokens['text_secondary']}; font-size:11px;")
        self.error_label = QLabel(self.initial_error, card)
        self.error_label.setStyleSheet(f"color:{self.tokens['danger']}; font-size:11px;")

        self.username_entry = QLineEdit(card)
        self.username_entry.setPlaceholderText("Enter username")
        self.password_entry = QLineEdit(card)
        self.password_entry.setPlaceholderText("Enter password")
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.remember_checkbox = QCheckBox("Remember me", card)
        forgot = QLabel("Forgot?", card)
        forgot.setStyleSheet(f"color:{self.tokens['accent_2']};")
        login_button = QPushButton("Login", card)
        login_button.clicked.connect(self._on_login_clicked)

        grid.addWidget(title, 0, 0, 1, 2)
        grid.addWidget(subtitle, 1, 0, 1, 2)
        grid.addWidget(self.error_label, 2, 0, 1, 2)
        grid.addWidget(QLabel("Username", card), 3, 0, 1, 2)
        grid.addWidget(self.username_entry, 4, 0, 1, 2)
        grid.addWidget(QLabel("Password", card), 5, 0, 1, 2)
        grid.addWidget(self.password_entry, 6, 0, 1, 2)
        grid.addWidget(self.remember_checkbox, 7, 0)
        grid.addWidget(forgot, 7, 1, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(login_button, 8, 0, 1, 2)

        self.username_entry.returnPressed.connect(self._on_login_clicked)
        self.password_entry.returnPressed.connect(self._on_login_clicked)
        outer.addWidget(card)

    def _on_login_clicked(self, event: Any = None):
        """Handle login button click (event optional)."""
        username = self.username_entry.text().strip()
        password = self.password_entry.text()

        if not username:
            self._show_error('Username is required')
            QMessageBox.warning(self, 'Validation', 'Username is required')
            return

        if not password:
            self._show_error('Password is required')
            QMessageBox.warning(self, 'Validation', 'Password is required')
            return

        try:
            user = self.auth_service.authenticate(username, password)
        except DatabaseError as exc:
            self._show_error(f'Authentication service unavailable: {exc}')
            return
        except Exception as exc:
            self._show_error('Login failed')
            QMessageBox.critical(self, 'Login Error', str(exc))
            return

        if user:
            self._show_error('')  # Clear error
            if callable(self.on_login_success):
                self.on_login_success(user)
        else:
            self._show_error('Invalid username or password')

    def _show_error(self, message: str):
        """Display error message."""
        self.error_label.setText(message)

    def clear_fields(self):
        """Clear all input fields."""
        self.username_entry.clear()
        self.password_entry.clear()
        self.error_label.setText('')
