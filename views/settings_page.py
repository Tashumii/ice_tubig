from PyQt6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from services.auth_service import AuthService
from services.settings_service import SettingsService
from views.components.modern_table import ModernTable


class SettingsPage(QWidget):
    def __init__(
        self,
        settings_service: SettingsService,
        auth_service: AuthService,
        current_user,
        on_save,
        tokens: dict,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.settings_service = settings_service
        self.auth_service = auth_service
        self.current_user = current_user
        self.on_save = on_save
        self.tokens = tokens
        self._selected_user_id = None
        self.setStyleSheet(f"background:{self.tokens['bg_base']};")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        title = QLabel('Settings', self)
        title.setStyleSheet("font-size:24px; font-weight:700;")
        subtitle = QLabel('Manage theme and system preferences.', self)
        subtitle.setStyleSheet(f"color:{self.tokens['text_secondary']};")
        card = QFrame(self)
        card.setProperty("card", True)
        grid = QGridLayout(card)
        grid.addWidget(QLabel('APP THEME', card), 0, 0)
        grid.addWidget(QLabel('Switch between dark mode and light mode.', card), 1, 0)
        self.theme_menu = QComboBox(card)
        self.theme_menu.addItems(['Light', 'Dark'])
        grid.addWidget(self.theme_menu, 0, 1, 2, 1)
        self.save_button = QPushButton('SAVE CHANGES', card)
        self.save_button.clicked.connect(self.save_settings)
        grid.addWidget(self.save_button, 2, 0, 1, 2)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(card)

        if self._is_admin():
            shift_card = QFrame(self)
            shift_card.setProperty("card", True)
            shift_grid = QGridLayout(shift_card)
            shift_grid.addWidget(QLabel("SHIFT SCHEDULE", shift_card), 0, 0, 1, 2)
            shift_grid.addWidget(QLabel("Set company-wide On Site / Time Out schedule (24h format).", shift_card), 1, 0, 1, 2)
            self.shift_start_input = QLineEdit(shift_card)
            self.shift_start_input.setPlaceholderText("08:00")
            self.shift_end_input = QLineEdit(shift_card)
            self.shift_end_input.setPlaceholderText("17:00")
            self.save_shift_btn = QPushButton("SAVE SHIFT SCHEDULE", shift_card)
            self.save_shift_btn.clicked.connect(self.save_shift_schedule)
            shift_grid.addWidget(QLabel("Shift Start", shift_card), 2, 0)
            shift_grid.addWidget(self.shift_start_input, 2, 1)
            shift_grid.addWidget(QLabel("Shift End", shift_card), 3, 0)
            shift_grid.addWidget(self.shift_end_input, 3, 1)
            shift_grid.addWidget(self.save_shift_btn, 4, 0, 1, 2)
            root.addWidget(shift_card)

            users_card = QFrame(self)
            users_card.setProperty("card", True)
            users_grid = QGridLayout(users_card)
            users_grid.addWidget(QLabel("ACCOUNT MANAGEMENT", users_card), 0, 0, 1, 2)
            users_grid.addWidget(QLabel("Create new admin or employee accounts.", users_card), 1, 0, 1, 2)

            self.new_username = QLineEdit(users_card)
            self.new_username.setPlaceholderText("New username")
            self.new_password = QLineEdit(users_card)
            self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.new_password.setPlaceholderText("Temporary password")
            self.account_type_menu = QComboBox(users_card)
            self.account_type_menu.addItems(["Employee", "Admin"])
            self.create_user_button = QPushButton("CREATE ACCOUNT", users_card)
            self.create_user_button.clicked.connect(self.create_account)

            users_grid.addWidget(QLabel("Username", users_card), 2, 0)
            users_grid.addWidget(self.new_username, 2, 1)
            users_grid.addWidget(QLabel("Password", users_card), 3, 0)
            users_grid.addWidget(self.new_password, 3, 1)
            users_grid.addWidget(QLabel("Account Type", users_card), 4, 0)
            users_grid.addWidget(self.account_type_menu, 4, 1)
            users_grid.addWidget(self.create_user_button, 5, 0, 1, 2)
            self.accounts_status = QLabel("", users_card)
            users_grid.addWidget(self.accounts_status, 6, 0, 1, 2)
            root.addWidget(users_card)

            accounts_table_card = QFrame(self)
            accounts_table_card.setProperty("card", True)
            accounts_layout = QVBoxLayout(accounts_table_card)
            header = QHBoxLayout()
            header.addWidget(QLabel("USER ACCOUNTS (ADMIN)", accounts_table_card))
            header.addStretch()
            self.accounts_count = QLabel("", accounts_table_card)
            header.addWidget(self.accounts_count)
            accounts_layout.addLayout(header)

            self.accounts_table = ModernTable(
                accounts_table_card,
                columns=("user_id", "username", "roles", "status", "created_at"),
                tokens=self.tokens,
            )
            accounts_layout.addWidget(self.accounts_table)

            actions = QHBoxLayout()
            self.toggle_status_btn = QPushButton("DISABLE / ENABLE", accounts_table_card)
            self.toggle_status_btn.clicked.connect(self.toggle_selected_account_status)
            self.reset_password_input = QLineEdit(accounts_table_card)
            self.reset_password_input.setPlaceholderText("New password for selected user")
            self.reset_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.reset_password_btn = QPushButton("RESET PASSWORD", accounts_table_card)
            self.reset_password_btn.clicked.connect(self.reset_selected_account_password)
            self.refresh_accounts_btn = QPushButton("REFRESH", accounts_table_card)
            self.refresh_accounts_btn.clicked.connect(self.refresh_accounts_table)

            actions.addWidget(self.toggle_status_btn)
            actions.addWidget(self.reset_password_input, 1)
            actions.addWidget(self.reset_password_btn)
            actions.addWidget(self.refresh_accounts_btn)
            accounts_layout.addLayout(actions)
            root.addWidget(accounts_table_card)
        root.addStretch()

    def refresh(self):
        theme = self.settings_service.get_theme()
        self.theme_menu.setCurrentText('Dark' if theme == 'dark' else 'Light')
        if self._is_admin():
            schedule = self.settings_service.get_shift_schedule()
            self.shift_start_input.setText(str(schedule.get("shift_start_time", "08:00"))[:5])
            self.shift_end_input.setText(str(schedule.get("shift_end_time", "17:00"))[:5])
            self.refresh_accounts_table()

    def save_settings(self):
        selected = self.theme_menu.currentText().lower()
        try:
            self.settings_service.set_theme(selected)
            if callable(self.on_save):
                self.on_save(selected)
            QMessageBox.information(self, 'Saved', 'Theme settings applied.')
        except Exception as exc:
            QMessageBox.critical(self, 'Save Error', str(exc))

    def _is_admin(self) -> bool:
        roles = getattr(self.current_user, "roles", []) or []
        return "admin" in roles

    def create_account(self):
        if not self._is_admin():
            QMessageBox.critical(self, "Permission Denied", "Only admin can create accounts.")
            return
        username = self.new_username.text().strip()
        password = self.new_password.text()
        account_type = self.account_type_menu.currentText().strip().lower()
        try:
            self.auth_service.create_account(self.current_user, username, password, account_type)
            self.new_username.clear()
            self.new_password.clear()
            QMessageBox.information(self, "Account Created", f"{account_type.title()} account created for '{username}'.")
            self.refresh_accounts_table()
        except PermissionError as exc:
            QMessageBox.critical(self, "Permission Denied", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Create Account Error", str(exc))

    def refresh_accounts_table(self):
        if not self._is_admin():
            return
        try:
            rows = self.auth_service.list_accounts(self.current_user)
            table_rows = []
            for row in rows:
                table_rows.append({
                    "_iid": str(row["user_id"]),
                    "user_id": str(row["user_id"]),
                    "username": row["username"],
                    "roles": row["roles"] or "staff",
                    "status": "Active" if row["is_active"] else "Disabled",
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M") if row["created_at"] else "-",
                })
            self.accounts_table.insert_rows(table_rows)
            self.accounts_count.setText(f"{len(table_rows)} users")
            self.accounts_status.setText("")
        except Exception as exc:
            self.accounts_status.setText(f"Unable to load accounts: {exc}")

    def _get_selected_user_id(self):
        selection = self.accounts_table.selection()
        if not selection:
            return None
        try:
            return int(selection[0])
        except Exception:
            return None

    def toggle_selected_account_status(self):
        target_user_id = self._get_selected_user_id()
        if target_user_id is None:
            QMessageBox.warning(self, "Selection Required", "Select an account from the table.")
            return

        try:
            accounts = self.auth_service.list_accounts(self.current_user)
            target = next((a for a in accounts if a["user_id"] == target_user_id), None)
            if not target:
                raise ValueError("Selected account no longer exists.")
            next_state = not target["is_active"]
            self.auth_service.set_account_active(self.current_user, target_user_id, next_state)
            QMessageBox.information(
                self,
                "Account Updated",
                f"Account '{target['username']}' is now {'Active' if next_state else 'Disabled'}.",
            )
            self.refresh_accounts_table()
        except Exception as exc:
            QMessageBox.critical(self, "Account Update Error", str(exc))

    def reset_selected_account_password(self):
        target_user_id = self._get_selected_user_id()
        if target_user_id is None:
            QMessageBox.warning(self, "Selection Required", "Select an account from the table.")
            return
        new_password = self.reset_password_input.text()
        if not new_password:
            QMessageBox.warning(self, "Validation", "Enter a new password first.")
            return

        try:
            self.auth_service.reset_account_password(self.current_user, target_user_id, new_password)
            self.reset_password_input.clear()
            QMessageBox.information(self, "Password Reset", "Password has been reset successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Password Reset Error", str(exc))

    def save_shift_schedule(self):
        if not self._is_admin():
            QMessageBox.critical(self, "Permission Denied", "Only admin can set shift schedule.")
            return
        start = self.shift_start_input.text().strip()
        end = self.shift_end_input.text().strip()
        try:
            self.settings_service.set_shift_schedule(start, end)
            QMessageBox.information(self, "Shift Saved", "Shift schedule updated successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Shift Schedule Error", str(exc))
