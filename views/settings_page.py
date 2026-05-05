import re
from PyQt6.QtCore import QRegularExpression, Qt
from PyQt6.QtGui import QRegularExpressionValidator, QColor
from PyQt6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget, QGraphicsDropShadowEffect, QScrollArea, QTableWidget, QTableWidgetItem, QDialog, QDialogButtonBox
import qtawesome as qta
from models.services.auth_service import AuthService
from models.services.settings_service import SettingsService
from views.components.modern_table import ModernTable
from utils import is_admin, validate_username, validate_password, normalize_shift_time, format_time_12h


class SettingsPage(QWidget):
    def __init__(self, settings_service, auth_service, current_user, on_save, tokens, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_service = settings_service
        self.auth_service = auth_service
        self.current_user = current_user
        self.on_save = on_save
        self.tokens = tokens
        self._selected_user_id = None
        self.setStyleSheet("background:transparent;")
        self._apply_modern_styling()
        self._build_ui()
        # Load staff members after UI is built
        if is_admin(current_user):
            self._load_staff_dropdown()

    def _apply_modern_styling(self):
        """Apply modern glassmorphic styling to all cards and components."""
        self.setStyleSheet(f"""
            QWidget {{ background: transparent; }}
            QFrame[card="true"] {{
                background: {self.tokens.get('bg_surface', 'rgba(8, 20, 38, 0.92)')};
                border: 1px solid {self.tokens.get('card_border', 'rgba(100, 184, 224, 0.25)')};
                border-radius: 12px;
                padding: 0px;
            }}
            QLabel[pageTitle="true"] {{
                color: {self.tokens.get('text_primary', '#EDF6FC')};
                font-size: 28px;
                font-weight: 700;
                background: transparent;
            }}
            QLabel[cardTitle="true"] {{
                color: {self.tokens.get('text_primary', '#EDF6FC')};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }}
            QLabel[muted="true"] {{
                color: {self.tokens.get('text_muted', '#5F9CC0')};
                font-size: 13px;
                background: transparent;
            }}
            QLineEdit {{
                background: {self.tokens.get('bg_input', 'rgba(6, 16, 32, 0.88)')};
                border: 1px solid {self.tokens.get('input_border', 'rgba(100, 184, 224, 0.40)')};
                border-radius: 6px;
                color: {self.tokens.get('text_primary', '#EDF6FC')};
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.tokens.get('accent_1', '#64B8E0')};
            }}
            QComboBox {{
                background: {self.tokens.get('bg_input', 'rgba(6, 16, 32, 0.88)')};
                border: 1px solid {self.tokens.get('input_border', 'rgba(100, 184, 224, 0.40)')};
                border-radius: 6px;
                color: {self.tokens.get('text_primary', '#EDF6FC')};
                padding: 6px 10px;
                font-size: 13px;
            }}
            QComboBox:focus {{
                border: 2px solid {self.tokens.get('accent_1', '#64B8E0')};
            }}
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.tokens.get('accent_1', '#64B8E0')}, stop:1 {self.tokens.get('accent_2', '#3FA9D6')});
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
                    stop:0 {self.tokens.get('accent_2', '#3FA9D6')}, stop:1 #2E7FAD);
                border: 2px solid rgba(255, 255, 255, 0.4);
                box-shadow: 0 0 16px rgba(100, 184, 224, 0.6);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2E7FAD, stop:1 #1E5A7E);
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
        title = QLabel('Settings', self); title.setProperty('pageTitle', True)
        subtitle = QLabel('Manage theme and system preferences.', self)
        subtitle.setProperty('muted', True)
        card = QFrame(self); card.setProperty("card", True); self._add_card_shadow(card); grid = QGridLayout(card); grid.setContentsMargins(20, 16, 20, 16)
        grid.addWidget(QLabel('APP THEME', card), 0, 0)
        grid.addWidget(QLabel('Switch between dark mode and light mode.', card), 1, 0)
        self.theme_menu = QComboBox(card); self.theme_menu.addItems(['Light', 'Dark'])
        grid.addWidget(self.theme_menu, 0, 1, 2, 1)
        save_btn = QPushButton('SAVE CHANGES', card)
        save_btn.setIcon(qta.icon('fa5s.check-circle', color=self.tokens['success']))
        save_btn.clicked.connect(self.save_settings)
        grid.addWidget(save_btn, 2, 0, 1, 2)
        root.addWidget(title); root.addWidget(subtitle); root.addWidget(card)

        if is_admin(self.current_user):
            # Shift schedule
            shift_card = QFrame(self); shift_card.setProperty("card", True); self._add_card_shadow(shift_card)
            sg = QGridLayout(shift_card); sg.setContentsMargins(20, 16, 20, 16)
            sg.addWidget(QLabel("SHIFT SCHEDULE", shift_card), 0, 0, 1, 2)
            sg.addWidget(QLabel("Set company-wide On Site / Time Out schedule (24h format).", shift_card), 1, 0, 1, 2)
            
            # Morning shift inputs
            self.shift_start_input = QLineEdit(shift_card); self.shift_start_input.setPlaceholderText("08:00")
            self.shift_end_input = QLineEdit(shift_card); self.shift_end_input.setPlaceholderText("17:00")
            time_validator = QRegularExpressionValidator(QRegularExpression(r"^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$"), self)
            self.shift_start_input.setValidator(time_validator); self.shift_end_input.setValidator(time_validator)
            self.shift_start_input.setMaxLength(8); self.shift_end_input.setMaxLength(8)
            self.shift_start_input.setMinimumHeight(32); self.shift_end_input.setMinimumHeight(32)
            self.shift_start_input.setMinimumWidth(150); self.shift_end_input.setMinimumWidth(150)
            
            # Night shift inputs
            self.night_shift_start_input = QLineEdit(shift_card); self.night_shift_start_input.setPlaceholderText("20:00 (optional)")
            self.night_shift_end_input = QLineEdit(shift_card); self.night_shift_end_input.setPlaceholderText("04:00 (optional)")
            self.night_shift_start_input.setValidator(time_validator); self.night_shift_end_input.setValidator(time_validator)
            self.night_shift_start_input.setMaxLength(8); self.night_shift_end_input.setMaxLength(8)
            self.night_shift_start_input.setMinimumHeight(32); self.night_shift_end_input.setMinimumHeight(32)
            self.night_shift_start_input.setMinimumWidth(150); self.night_shift_end_input.setMinimumWidth(150)
            
            save_shift = QPushButton("SAVE SHIFT SCHEDULE", shift_card)
            save_shift.clicked.connect(self.save_shift_schedule)
            sg.addWidget(QLabel("Morning Shift Start", shift_card), 2, 0); sg.addWidget(self.shift_start_input, 2, 1)
            sg.addWidget(QLabel("Morning Shift End", shift_card), 3, 0); sg.addWidget(self.shift_end_input, 3, 1)
            sg.addWidget(QLabel("Night Shift Start", shift_card), 4, 0); sg.addWidget(self.night_shift_start_input, 4, 1)
            sg.addWidget(QLabel("Night Shift End", shift_card), 5, 0); sg.addWidget(self.night_shift_end_input, 5, 1)
            sg.addWidget(save_shift, 6, 0, 1, 2)
            root.addWidget(shift_card)

            # Per-staff shift schedule
            staff_shift_card = QFrame(self); staff_shift_card.setProperty("card", True); self._add_card_shadow(staff_shift_card)
            staff_shift_card.setMinimumHeight(350)
            staff_sg = QGridLayout(staff_shift_card); staff_sg.setContentsMargins(20, 16, 20, 16); staff_sg.setSpacing(12)
            staff_sg.addWidget(QLabel("STAFF SHIFT SCHEDULE", staff_shift_card), 0, 0, 1, 3)
            staff_sg.addWidget(QLabel("Set custom shift times for specific staff members.", staff_shift_card), 1, 0, 1, 3)
            
            # Staff selection combo
            self.staff_select = QComboBox(staff_shift_card)
            self.staff_select.setMinimumHeight(32)
            self.staff_select.currentIndexChanged.connect(self._on_staff_selected)
            staff_sg.addWidget(QLabel("Select Staff Member", staff_shift_card), 2, 0); staff_sg.addWidget(self.staff_select, 2, 1, 1, 2)
            
            # Shift preset dropdown
            self.staff_shift_preset = QComboBox(staff_shift_card)
            self.staff_shift_preset.setMinimumHeight(32)
            self.staff_shift_preset.addItem("Custom", None)
            self.staff_shift_preset.addItem("Morning (8:00 AM - 5:00 PM)", ("08:00", "17:00", None, None))
            self.staff_shift_preset.addItem("Afternoon (12:00 PM - 8:00 PM)", ("12:00", "20:00", None, None))
            self.staff_shift_preset.addItem("Evening (4:00 PM - 12:00 AM)", ("16:00", "00:00", None, None))
            self.staff_shift_preset.addItem("Night (8:00 PM - 4:00 AM)", ("20:00", "04:00", None, None))
            self.staff_shift_preset.currentIndexChanged.connect(self._on_shift_preset_changed)
            staff_sg.addWidget(QLabel("Quick Shift Preset", staff_shift_card), 3, 0); staff_sg.addWidget(self.staff_shift_preset, 3, 1, 1, 2)
            
            # Staff shift time inputs
            self.staff_shift_start = QLineEdit(staff_shift_card); self.staff_shift_start.setPlaceholderText("08:00")
            self.staff_shift_end = QLineEdit(staff_shift_card); self.staff_shift_end.setPlaceholderText("17:00")
            self.staff_night_start = QLineEdit(staff_shift_card); self.staff_night_start.setPlaceholderText("(optional)")
            self.staff_night_end = QLineEdit(staff_shift_card); self.staff_night_end.setPlaceholderText("(optional)")
            self.staff_shift_start.setValidator(time_validator); self.staff_shift_end.setValidator(time_validator)
            self.staff_night_start.setValidator(time_validator); self.staff_night_end.setValidator(time_validator)
            
            # Set sizes for staff shift inputs
            for input_field in [self.staff_shift_start, self.staff_shift_end, self.staff_night_start, self.staff_night_end]:
                input_field.setMinimumHeight(32)
                input_field.setMinimumWidth(150)
            
            staff_sg.addWidget(QLabel("Morning Shift Start", staff_shift_card), 4, 0); staff_sg.addWidget(self.staff_shift_start, 4, 1, 1, 2)
            staff_sg.addWidget(QLabel("Morning Shift End", staff_shift_card), 5, 0); staff_sg.addWidget(self.staff_shift_end, 5, 1, 1, 2)
            staff_sg.addWidget(QLabel("Night Shift Start", staff_shift_card), 6, 0); staff_sg.addWidget(self.staff_night_start, 6, 1, 1, 2)
            staff_sg.addWidget(QLabel("Night Shift End", staff_shift_card), 7, 0); staff_sg.addWidget(self.staff_night_end, 7, 1, 1, 2)
            
            staff_shift_buttons = QHBoxLayout()
            save_staff_shift = QPushButton("SAVE STAFF SHIFT", staff_shift_card)
            save_staff_shift.clicked.connect(self.save_staff_shift_schedule)
            clear_staff_shift = QPushButton("USE GLOBAL SHIFT", staff_shift_card)
            clear_staff_shift.clicked.connect(self.clear_staff_shift_schedule)
            staff_shift_buttons.addWidget(save_staff_shift); staff_shift_buttons.addWidget(clear_staff_shift)
            staff_sg.addLayout(staff_shift_buttons, 8, 0, 1, 3)
            root.addWidget(staff_shift_card)

            # Account management
            users_card = QFrame(self); users_card.setProperty("card", True); self._add_card_shadow(users_card)
            ug = QGridLayout(users_card); ug.setContentsMargins(20, 16, 20, 16)
            ug.addWidget(QLabel("ACCOUNT MANAGEMENT", users_card), 0, 0, 1, 2)
            ug.addWidget(QLabel("Create new admin or employee accounts.", users_card), 1, 0, 1, 2)
            self.new_username = QLineEdit(users_card); self.new_username.setPlaceholderText("New username"); self.new_username.setMaxLength(50)
            self.new_username.setMinimumHeight(32); self.new_username.setMinimumWidth(150)
            self.new_password = QLineEdit(users_card)
            self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.new_password.setPlaceholderText("Temporary password"); self.new_password.setMaxLength(128)
            self.new_password.setMinimumHeight(32); self.new_password.setMinimumWidth(150)
            self.account_type_menu = QComboBox(users_card); self.account_type_menu.addItems(["Employee", "Admin"])
            self.account_type_menu.setMinimumHeight(32); self.account_type_menu.setMinimumWidth(150)
            create_btn = QPushButton("CREATE ACCOUNT", users_card); create_btn.clicked.connect(self.create_account)
            ug.addWidget(QLabel("Username", users_card), 2, 0); ug.addWidget(self.new_username, 2, 1)
            ug.addWidget(QLabel("Password", users_card), 3, 0); ug.addWidget(self.new_password, 3, 1)
            ug.addWidget(QLabel("Account Type", users_card), 4, 0); ug.addWidget(self.account_type_menu, 4, 1)
            ug.addWidget(create_btn, 5, 0, 1, 2)
            self.accounts_status = QLabel("", users_card); ug.addWidget(self.accounts_status, 6, 0, 1, 2)
            root.addWidget(users_card)

            # Accounts table
            at_card = QFrame(self); at_card.setProperty("card", True); self._add_card_shadow(at_card); atl = QVBoxLayout(at_card); atl.setContentsMargins(20, 16, 20, 16)
            ah = QHBoxLayout(); ah.addWidget(QLabel("USER ACCOUNTS (ADMIN)", at_card)); ah.addStretch()
            self.accounts_count = QLabel("", at_card); ah.addWidget(self.accounts_count); atl.addLayout(ah)
            self.accounts_table = ModernTable(at_card,
                columns=("user_id","username","roles","status","created_at"), tokens=self.tokens)
            atl.addWidget(self.accounts_table)
            actions = QHBoxLayout()
            self.toggle_status_btn = QPushButton("DISABLE / ENABLE", at_card)
            self.toggle_status_btn.clicked.connect(self.toggle_selected_account_status)
            self.reset_password_input = QLineEdit(at_card)
            self.reset_password_input.setPlaceholderText("New password for selected user")
            self.reset_password_input.setEchoMode(QLineEdit.EchoMode.Password); self.reset_password_input.setMaxLength(128)
            self.reset_password_btn = QPushButton("RESET PASSWORD", at_card)
            self.reset_password_btn.clicked.connect(self.reset_selected_account_password)
            refresh_btn = QPushButton("REFRESH", at_card); refresh_btn.clicked.connect(self.refresh_accounts_table)
            actions.addWidget(self.toggle_status_btn); actions.addWidget(self.reset_password_input, 1)
            actions.addWidget(self.reset_password_btn); actions.addWidget(refresh_btn)
            atl.addLayout(actions); root.addWidget(at_card)
        root.addStretch()

    def _load_staff_dropdown(self):
        """Load staff members into the staff select dropdown."""
        try:
            self.staff_select.blockSignals(True)
            self.staff_select.clear()
            staff_list = self.settings_service.get_all_staff_with_shifts()
            if staff_list:
                for staff in staff_list:
                    display_text = f"{staff['username']}"
                    if staff['is_custom']:
                        display_text += " (custom)"
                    self.staff_select.addItem(display_text, staff['user_id'])
                self.staff_select.blockSignals(False)
                self._on_staff_selected(0)
            else:
                self.staff_select.blockSignals(False)
                self.staff_select.addItem("No staff members found", None)
        except Exception as exc:
            self.staff_select.blockSignals(False)
            QMessageBox.warning(self, 'Error', f'Failed to load staff list: {exc}')

    def refresh(self):
        self.theme_menu.setCurrentText('Dark' if self.settings_service.get_theme() == 'dark' else 'Light')
        if is_admin(self.current_user):
            schedule = self.settings_service.get_shift_schedule()
            # Show times in 24h format for input, but display 12h in labels
            self.shift_start_input.setText(str(schedule.get("shift_start_time", "08:00:00"))[:5])
            self.shift_end_input.setText(str(schedule.get("shift_end_time", "17:00:00"))[:5])
            
            # Load night shift schedule if available
            night_start = schedule.get("night_shift_start_time")
            night_end = schedule.get("night_shift_end_time")
            self.night_shift_start_input.setText(str(night_start)[:5] if night_start and night_start != "None" else "")
            self.night_shift_end_input.setText(str(night_end)[:5] if night_end and night_end != "None" else "")
            
            # Reload staff members
            self._load_staff_dropdown()
            self.refresh_accounts_table()

    def search(self, query):
        if is_admin(self.current_user) and hasattr(self, "accounts_table"):
            self.accounts_table.filter_rows(query)

    def save_settings(self):
        selected = self.theme_menu.currentText().lower()
        try:
            self.settings_service.set_theme(selected)
            if callable(self.on_save): self.on_save(selected)
            QMessageBox.information(self, 'Saved', 'Theme settings applied.')
        except Exception as exc:
            QMessageBox.critical(self, 'Save Error', str(exc))

    def create_account(self):
        if not is_admin(self.current_user):
            QMessageBox.critical(self, "Permission Denied", "Only admin can create accounts."); return
        try:
            ok, err = validate_username(self.new_username.text())
            if not ok: raise ValueError(err)
            ok, err = validate_password(self.new_password.text())
            if not ok: raise ValueError(err)
        except ValueError as exc:
            QMessageBox.warning(self, "Validation", str(exc)); return
        username = self.new_username.text().strip()
        password = self.new_password.text()
        account_type = self.account_type_menu.currentText().strip().lower()
        try:
            self.auth_service.create_account(self.current_user, username, password, account_type)
            self.new_username.clear(); self.new_password.clear()
            QMessageBox.information(self, "Account Created", f"{account_type.title()} account created for '{username}'.")
            self.refresh_accounts_table()
        except PermissionError as exc:
            QMessageBox.critical(self, "Permission Denied", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Create Account Error", str(exc))

    def refresh_accounts_table(self):
        if not is_admin(self.current_user): return
        try:
            rows = self.auth_service.list_accounts(self.current_user)
            table_rows = [{"_iid": str(r["user_id"]), "user_id": str(r["user_id"]),
                "username": r["username"], "roles": r["roles"] or "staff",
                "status": "Active" if r["is_active"] else "Disabled",
                "created_at": r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else "-"}
                for r in rows]
            self.accounts_table.insert_rows(table_rows)
            self.accounts_count.setText(f"{len(table_rows)} users")
            self.accounts_status.setText("")
        except Exception as exc:
            self.accounts_status.setText(f"Unable to load accounts: {exc}")

    def _get_selected_user_id(self):
        sel = self.accounts_table.selection()
        if not sel: return None
        try: return int(sel[0])
        except Exception: return None

    def toggle_selected_account_status(self):
        uid = self._get_selected_user_id()
        if uid is None:
            QMessageBox.warning(self, "Selection Required", "Select an account from the table."); return
        try:
            accounts = self.auth_service.list_accounts(self.current_user)
            target = next((a for a in accounts if a["user_id"] == uid), None)
            if not target: raise ValueError("Selected account no longer exists.")
            next_state = not target["is_active"]
            self.auth_service.set_account_active(self.current_user, uid, next_state)
            QMessageBox.information(self, "Account Updated",
                f"Account '{target['username']}' is now {'Active' if next_state else 'Disabled'}.")
            self.refresh_accounts_table()
        except Exception as exc:
            QMessageBox.critical(self, "Account Update Error", str(exc))

    def reset_selected_account_password(self):
        uid = self._get_selected_user_id()
        if uid is None:
            QMessageBox.warning(self, "Selection Required", "Select an account from the table."); return
        try:
            ok, err = validate_password(self.reset_password_input.text())
            if not ok: raise ValueError(err)
        except ValueError as exc:
            QMessageBox.warning(self, "Validation", str(exc)); return
        try:
            self.auth_service.reset_account_password(self.current_user, uid, self.reset_password_input.text())
            self.reset_password_input.clear()
            QMessageBox.information(self, "Password Reset", "Password has been reset successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Password Reset Error", str(exc))

    def save_shift_schedule(self):
        if not is_admin(self.current_user):
            QMessageBox.critical(self, "Permission Denied", "Only admin can set shift schedule."); return
        try:
            start = normalize_shift_time(self.shift_start_input.text())
            end = normalize_shift_time(self.shift_end_input.text())
            if start == end: raise ValueError("Shift start and end cannot be the same.")
            if start > end: raise ValueError("Shift end must be later than shift start.")
            
            # Handle night shift (optional)
            night_start = None
            night_end = None
            night_start_text = self.night_shift_start_input.text().strip()
            night_end_text = self.night_shift_end_input.text().strip()
            
            if night_start_text or night_end_text:
                if not night_start_text or not night_end_text:
                    raise ValueError("If setting night shift, both start and end times must be provided.")
                night_start = normalize_shift_time(night_start_text)
                night_end = normalize_shift_time(night_end_text)
                if night_start == night_end: 
                    raise ValueError("Night shift start and end cannot be the same.")
                if night_start > night_end: 
                    raise ValueError("Night shift end must be later than night shift start.")
            
            self.settings_service.set_shift_schedule(start, end, night_start, night_end)
            QMessageBox.information(self, "Shift Saved", "Shift schedule updated successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Shift Schedule Error", str(exc))

    def _on_staff_selected(self, index):
        """Load shift schedule for selected staff member."""
        if index < 0 or self.staff_select.count() == 0:
            return
        user_id = self.staff_select.currentData()
        if not user_id:
            return
        try:
            schedule = self.settings_service.get_staff_shift_schedule(user_id)
            # Display in 24h format for input, with 12h format shown in placeholders
            if schedule.get('is_custom'):
                self.staff_shift_start.setText(str(schedule['shift_start_time'])[:5] if schedule['shift_start_time'] else "")
                self.staff_shift_end.setText(str(schedule['shift_end_time'])[:5] if schedule['shift_end_time'] else "")
                self.staff_night_start.setText(str(schedule['night_shift_start_time'])[:5] if schedule['night_shift_start_time'] else "")
                self.staff_night_end.setText(str(schedule['night_shift_end_time'])[:5] if schedule['night_shift_end_time'] else "")
                self.staff_shift_start.setPlaceholderText(f"e.g. {format_time_12h('08:00')}")
                self.staff_shift_end.setPlaceholderText(f"e.g. {format_time_12h('17:00')}")
                self.staff_night_start.setPlaceholderText(f"e.g. {format_time_12h('20:00')} (optional)")
                self.staff_night_end.setPlaceholderText(f"e.g. {format_time_12h('04:00')} (optional)")
            else:
                # Show global schedule as placeholder
                global_schedule = self.settings_service.get_shift_schedule()
                self.staff_shift_start.setPlaceholderText(f"Global: {format_time_12h(str(global_schedule['shift_start_time'])[:5])}")
                self.staff_shift_end.setPlaceholderText(f"Global: {format_time_12h(str(global_schedule['shift_end_time'])[:5])}")
                self.staff_night_start.setPlaceholderText(f"Global: {format_time_12h(str(global_schedule['night_shift_start_time'])[:5]) if global_schedule['night_shift_start_time'] else 'Not set'}")
                self.staff_night_end.setPlaceholderText(f"Global: {format_time_12h(str(global_schedule['night_shift_end_time'])[:5]) if global_schedule['night_shift_end_time'] else 'Not set'}")
                self.staff_shift_start.clear()
                self.staff_shift_end.clear()
                self.staff_night_start.clear()
                self.staff_night_end.clear()
        except Exception as exc:
            QMessageBox.warning(self, 'Error', f'Failed to load staff shift: {exc}')

    def _on_shift_preset_changed(self, index):
        """Auto-fill time fields when a shift preset is selected."""
        if index < 0:
            return
        preset_data = self.staff_shift_preset.currentData()
        
        # If preset is None, user selected "Custom" - do nothing
        if preset_data is None:
            return
        
        # Unpack preset data
        start, end, night_start, night_end = preset_data
        
        # Auto-fill the fields
        self.staff_shift_start.setText(start if start else "")
        self.staff_shift_end.setText(end if end else "")
        self.staff_night_start.setText(night_start if night_start else "")
        self.staff_night_end.setText(night_end if night_end else "")

    def save_staff_shift_schedule(self):
        """Save custom shift schedule for selected staff member."""
        if not is_admin(self.current_user):
            QMessageBox.critical(self, "Permission Denied", "Only admin can set staff shift schedule."); return
        
        user_id = self.staff_select.currentData()
        if not user_id:
            QMessageBox.warning(self, "Selection Required", "Please select a staff member."); return
        
        try:
            start = normalize_shift_time(self.staff_shift_start.text())
            end = normalize_shift_time(self.staff_shift_end.text())
            if start == end: raise ValueError("Shift start and end cannot be the same.")
            if start > end: raise ValueError("Shift end must be later than shift start.")
            
            # Handle night shift (optional)
            night_start = None
            night_end = None
            night_start_text = self.staff_night_start.text().strip()
            night_end_text = self.staff_night_end.text().strip()
            
            if night_start_text or night_end_text:
                if not night_start_text or not night_end_text:
                    raise ValueError("If setting night shift, both start and end times must be provided.")
                night_start = normalize_shift_time(night_start_text)
                night_end = normalize_shift_time(night_end_text)
                if night_start == night_end: 
                    raise ValueError("Night shift start and end cannot be the same.")
                if night_start > night_end: 
                    raise ValueError("Night shift end must be later than night shift start.")
            
            self.settings_service.set_staff_shift_schedule(user_id, start, end, night_start, night_end)
            username = self.staff_select.currentText()
            QMessageBox.information(self, "Shift Saved", f"Custom shift schedule saved for {username}.")
            self._on_staff_selected(self.staff_select.currentIndex())
        except Exception as exc:
            QMessageBox.critical(self, "Save Shift Error", str(exc))

    def clear_staff_shift_schedule(self):
        """Clear custom shift schedule and use global for selected staff."""
        if not is_admin(self.current_user):
            QMessageBox.critical(self, "Permission Denied", "Only admin can manage staff shifts."); return
        
        user_id = self.staff_select.currentData()
        if not user_id:
            QMessageBox.warning(self, "Selection Required", "Please select a staff member."); return
        
        try:
            self.settings_service.set_staff_shift_schedule(user_id, None, None, None, None)
            username = self.staff_select.currentText()
            QMessageBox.information(self, "Shift Cleared", f"{username} will now use global shift schedule.")
            self._on_staff_selected(self.staff_select.currentIndex())
        except Exception as exc:
            QMessageBox.critical(self, "Clear Shift Error", str(exc))
