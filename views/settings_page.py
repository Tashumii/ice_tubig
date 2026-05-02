import re
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget
import qtawesome as qta
from models.services.auth_service import AuthService
from models.services.settings_service import SettingsService
from views.components.modern_table import ModernTable
from utils import is_admin, validate_username, validate_password, normalize_shift_time


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
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        title = QLabel('Settings', self); title.setProperty('pageTitle', True)
        subtitle = QLabel('Manage theme and system preferences.', self)
        subtitle.setProperty('muted', True)
        card = QFrame(self); card.setProperty("card", True); grid = QGridLayout(card)
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
            shift_card = QFrame(self); shift_card.setProperty("card", True)
            sg = QGridLayout(shift_card)
            sg.addWidget(QLabel("SHIFT SCHEDULE", shift_card), 0, 0, 1, 2)
            sg.addWidget(QLabel("Set company-wide On Site / Time Out schedule (24h format).", shift_card), 1, 0, 1, 2)
            self.shift_start_input = QLineEdit(shift_card); self.shift_start_input.setPlaceholderText("08:00")
            self.shift_end_input = QLineEdit(shift_card); self.shift_end_input.setPlaceholderText("17:00")
            time_validator = QRegularExpressionValidator(QRegularExpression(r"^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$"), self)
            self.shift_start_input.setValidator(time_validator); self.shift_end_input.setValidator(time_validator)
            self.shift_start_input.setMaxLength(8); self.shift_end_input.setMaxLength(8)
            save_shift = QPushButton("SAVE SHIFT SCHEDULE", shift_card)
            save_shift.clicked.connect(self.save_shift_schedule)
            sg.addWidget(QLabel("Shift Start", shift_card), 2, 0); sg.addWidget(self.shift_start_input, 2, 1)
            sg.addWidget(QLabel("Shift End", shift_card), 3, 0); sg.addWidget(self.shift_end_input, 3, 1)
            sg.addWidget(save_shift, 4, 0, 1, 2)
            root.addWidget(shift_card)

            # Account management
            users_card = QFrame(self); users_card.setProperty("card", True)
            ug = QGridLayout(users_card)
            ug.addWidget(QLabel("ACCOUNT MANAGEMENT", users_card), 0, 0, 1, 2)
            ug.addWidget(QLabel("Create new admin or employee accounts.", users_card), 1, 0, 1, 2)
            self.new_username = QLineEdit(users_card); self.new_username.setPlaceholderText("New username"); self.new_username.setMaxLength(50)
            self.new_password = QLineEdit(users_card)
            self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.new_password.setPlaceholderText("Temporary password"); self.new_password.setMaxLength(128)
            self.account_type_menu = QComboBox(users_card); self.account_type_menu.addItems(["Employee", "Admin"])
            create_btn = QPushButton("CREATE ACCOUNT", users_card); create_btn.clicked.connect(self.create_account)
            ug.addWidget(QLabel("Username", users_card), 2, 0); ug.addWidget(self.new_username, 2, 1)
            ug.addWidget(QLabel("Password", users_card), 3, 0); ug.addWidget(self.new_password, 3, 1)
            ug.addWidget(QLabel("Account Type", users_card), 4, 0); ug.addWidget(self.account_type_menu, 4, 1)
            ug.addWidget(create_btn, 5, 0, 1, 2)
            self.accounts_status = QLabel("", users_card); ug.addWidget(self.accounts_status, 6, 0, 1, 2)
            root.addWidget(users_card)

            # Accounts table
            at_card = QFrame(self); at_card.setProperty("card", True); atl = QVBoxLayout(at_card)
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

    def refresh(self):
        self.theme_menu.setCurrentText('Dark' if self.settings_service.get_theme() == 'dark' else 'Light')
        if is_admin(self.current_user):
            schedule = self.settings_service.get_shift_schedule()
            self.shift_start_input.setText(str(schedule.get("shift_start_time", "08:00"))[:5])
            self.shift_end_input.setText(str(schedule.get("shift_end_time", "17:00"))[:5])
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
            self.settings_service.set_shift_schedule(start, end)
            QMessageBox.information(self, "Shift Saved", "Shift schedule updated successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Shift Schedule Error", str(exc))
