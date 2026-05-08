import os
from typing import Callable, Dict, Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget,
)
import qtawesome as qta
from models.services.auth_service import AuthService
from models.user import User
from database import DatabaseError
from utils import validate_username, validate_password

# Resolve image paths relative to project root
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOGO_PATH = os.path.join(_BASE_DIR, 'images', 'logo.png')



class LoginPage(QWidget):
    def __init__(
        self, master, auth_service: AuthService, tokens: Optional[Dict[str, str]] = None,
        on_login_success: Callable[[User], None] = None, initial_error: str = '',
        *args, **kwargs,
    ):
        super().__init__(master, *args, **kwargs)
        self.auth_service = auth_service
        self.tokens = tokens or {}
        self.on_login_success = on_login_success
        self.initial_error = initial_error
        self._build_ui()

    def _build_ui(self):
        """Build the Mr. Ice Buddha branded login page."""
        # Transparent so parent BackgroundWidget's icy image shows through
        self.setStyleSheet('background: transparent;')

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── Central column container ──────────────────────────────────────
        center_column = QVBoxLayout()
        center_column.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        center_column.setSpacing(0)

        # ── Logo ──────────────────────────────────────────────────────────
        logo_label = QLabel(self)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_pixmap = QPixmap(_LOGO_PATH)
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(
                280, 120, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        logo_label.setStyleSheet("background: transparent; border: none; margin-bottom: 8px;")
        center_column.addWidget(logo_label)

        # ── Glassmorphism login card ──────────────────────────────────────
        login_card = QFrame(self)
        login_card.setObjectName("loginCard")
        login_card.setMaximumWidth(460)
        login_card.setMinimumWidth(380)
        login_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        login_card.setStyleSheet(f"""
            QFrame#loginCard {{
                background: {self.tokens.get('bg_surface', 'rgba(240, 245, 250, 0.88)')};
                border-radius: 22px;
                border: 1px solid {self.tokens.get('card_border', 'rgba(255, 255, 255, 0.6)')};
            }}
        """)

        # Card shadow
        card_shadow = QGraphicsDropShadowEffect(login_card)
        card_shadow.setBlurRadius(40)
        card_shadow.setOffset(0, 8)
        card_shadow.setColor(Qt.GlobalColor.darkGray)
        login_card.setGraphicsEffect(card_shadow)

        card_layout = QVBoxLayout(login_card)
        card_layout.setContentsMargins(36, 32, 36, 28)
        card_layout.setSpacing(10)

        # Welcome text
        welcome_label = QLabel("WELCOME TO", login_card)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setProperty('sectionLabel', True)
        welcome_label.setStyleSheet("background: transparent;")
        card_layout.addWidget(welcome_label)

        brand_label = QLabel("MR. ICE BUDDHA", login_card)
        brand_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_label.setProperty('brandTitle', True)
        brand_label.setStyleSheet("background: transparent; margin-bottom: 12px;")
        card_layout.addWidget(brand_label)

        # Error label
        self.error_label = QLabel(self.initial_error, login_card)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet(f"""
            color: {self.tokens.get('danger', '#FF6B5B')}; font-size: 11px; font-weight: 500;
            background: transparent; padding: 0 4px;
        """)
        card_layout.addWidget(self.error_label)

        # ── Username field ────────────────────────────────────────────────
        self.username_input = self._create_input_field(
            login_card, "USERNAME", 'fa5s.user', echo_password=False)
        card_layout.addWidget(self.username_input)

        card_layout.addSpacing(4)

        # ── Password field ────────────────────────────────────────────────
        self.password_input = self._create_input_field(
            login_card, "PASSWORD", 'fa5s.lock', echo_password=True)
        card_layout.addWidget(self.password_input)

        card_layout.addSpacing(12)

        # ── Login button ──────────────────────────────────────────────────
        login_button = QPushButton("LOGIN", login_card)
        login_button.setObjectName("loginButton")
        login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        login_button.setMinimumHeight(48)
        login_button.setStyleSheet("""
            QPushButton#loginButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #64B8E0, stop:1 #3FA9D6);
                color: white;
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 3px;
                border: 2px solid transparent;
                border-radius: 24px;
                padding: 12px 0;
                cursor: pointer;
            }
            QPushButton#loginButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3FA9D6, stop:1 #2E7FAD);
                border: 2px solid rgba(255, 255, 255, 0.5);
                box-shadow: 0 0 24px rgba(100, 184, 224, 0.6);
            }
            QPushButton#loginButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2E7FAD, stop:1 #1E5A7E);
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton#loginButton:focus {
                outline: none;
            }
        """)
        login_button.clicked.connect(self._on_login_clicked)

        # Button shadow
        btn_shadow = QGraphicsDropShadowEffect(login_button)
        btn_shadow.setBlurRadius(20)
        btn_shadow.setOffset(0, 6)
        btn_shadow.setColor(Qt.GlobalColor.darkCyan)
        login_button.setGraphicsEffect(btn_shadow)
        card_layout.addWidget(login_button)

        card_layout.addSpacing(8)

        # Connect return key
        self.username_input.findChild(QLineEdit).returnPressed.connect(self._on_login_clicked)
        self.password_input.findChild(QLineEdit).returnPressed.connect(self._on_login_clicked)

        center_column.addWidget(login_card, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ── Footer contact info ───────────────────────────────────────────
        center_column.addSpacing(24)

        phone_label = QLabel("09619852250", self)
        phone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        phone_label.setProperty('cardTitle', True)
        phone_label.setStyleSheet("background: transparent; letter-spacing: 1px;")
        center_column.addWidget(phone_label)

        address_label = QLabel(
            "KAPITO ISKO ST., BRGY 2 POBLACION, LIAN, BATANGAS", self)
        address_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        address_label.setWordWrap(True)
        address_label.setProperty('muted', True)
        address_label.setStyleSheet("background: transparent; letter-spacing: 1.5px;")
        center_column.addWidget(address_label)

        outer.addLayout(center_column)

    def _create_input_field(self, parent, placeholder: str, icon_name: str,
                            echo_password: bool = False) -> QFrame:
        """Create a styled input field with icon, matching the icy design."""
        container = QFrame(parent)
        container.setObjectName("inputContainer")
        container.setStyleSheet(f"""
            QFrame#inputContainer {{
                background: {self.tokens.get('bg_input', 'rgba(220, 230, 240, 0.6)')};
                border-radius: 28px;
                border: 2px solid {self.tokens.get('input_border', 'rgba(200, 215, 230, 0.8)')};
            }}
            QFrame#inputContainer:hover {{
                border: 2px solid {self.tokens.get('accent_1', 'rgba(100, 184, 224, 0.8)')};
                background: {self.tokens.get('bg_elevated', 'rgba(220, 235, 250, 0.8)')};
                box-shadow: 0 0 16px {self.tokens.get('accent_1', 'rgba(100, 184, 224, 0.3)')};
            }}
        """)
        container.setMinimumHeight(52)

        row = QHBoxLayout(container)
        row.setContentsMargins(18, 0, 18, 0)
        row.setSpacing(12)

        icon_label = QLabel(container)
        icon_label.setPixmap(
            qta.icon(icon_name, color=self.tokens.get('text_secondary', '#7f8c9b')).pixmap(QSize(22, 22)))
        icon_label.setStyleSheet("background: transparent; border: none;")
        row.addWidget(icon_label)

        line_edit = QLineEdit(container)
        line_edit.setPlaceholderText(placeholder)
        line_edit.setMaxLength(128 if echo_password else 50)
        if echo_password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        line_edit.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {self.tokens.get('text_primary', '#2c3e50')};
                font-size: 14px;
                font-weight: 500;
                letter-spacing: 1.5px;
                padding: 14px 0;
            }}
            QLineEdit::placeholder {{
                color: {self.tokens.get('text_muted', '#8899aa')};
                letter-spacing: 2px;
            }}
        """)
        row.addWidget(line_edit, 1)

        if echo_password:
            toggle_btn = QPushButton(container)
            toggle_btn.setIcon(qta.icon('fa5s.snowflake', color=self.tokens.get('accent_1', '#64B8E0')))
            toggle_btn.setIconSize(QSize(20, 20))
            toggle_btn.setFlat(True)
            toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            toggle_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    padding: 4px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: rgba(100, 184, 224, 0.15);
                }
                QPushButton:pressed {
                    background: rgba(100, 184, 224, 0.25);
                }
            """)
            toggle_btn.setCheckable(True)
            toggle_btn.toggled.connect(
                lambda checked, le=line_edit: le.setEchoMode(
                    QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))
            row.addWidget(toggle_btn)

        return container

    # ── Login logic (unchanged) ───────────────────────────────────────────

    def _on_login_clicked(self):
        """Handle login button click using shared validators."""
        username_text = self._get_username()
        password_text = self._get_password()

        is_valid, error_msg = validate_username(username_text)
        if not is_valid:
            self._show_validation_error(error_msg)
            return
        is_valid, error_msg = validate_password(password_text)
        if not is_valid:
            self._show_validation_error(error_msg)
            return

        try:
            user = self.auth_service.authenticate(username_text.strip(), password_text)
        except DatabaseError as exc:
            self._show_error(f'Authentication service unavailable: {exc}')
            return
        except Exception as exc:
            self._show_error('Login failed')
            QMessageBox.critical(self, 'Login Error', str(exc))
            return

        if user:
            self._show_error('')
            if callable(self.on_login_success):
                self.on_login_success(user)
        else:
            self._show_error('Invalid username or password')

    def _get_username(self) -> str:
        return self.username_input.findChild(QLineEdit).text()

    def _get_password(self) -> str:
        return self.password_input.findChild(QLineEdit).text()

    def _show_validation_error(self, message: str) -> None:
        self._show_error(message)
        QMessageBox.warning(self, 'Validation', message)

    def _show_error(self, message: str):
        """Display error message."""
        self.error_label.setText(message)

    def clear_fields(self):
        """Clear all input fields."""
        self.username_input.findChild(QLineEdit).clear()
        self.password_input.findChild(QLineEdit).clear()
        self.error_label.setText('')
