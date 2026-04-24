import customtkinter as ctk
from typing import Callable, Optional, Dict
from services.auth_service import AuthService
from models.user import User

class LoginPage(ctk.CTkFrame):
    def __init__(
        self,
        auth_service: AuthService,
        tokens: Dict[str, str],
        on_login_success: Callable[[User], None] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.auth_service = auth_service
        self.tokens = tokens
        self.on_login_success = on_login_success
        self.configure(fg_color=self.tokens['bg_base'])
        self._build_ui()

    def _build_ui(self):
        """Build login page UI."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Center container
        container = ctk.CTkFrame(
            self,
            fg_color=self.tokens['bg_surface'],
            corner_radius=16,
            border_color=self.tokens['border'],
            border_width=1,
        )
        container.grid(row=0, column=0, padx=40, pady=40, sticky='', ipadx=60, ipady=60)
        container.grid_rowconfigure(6, weight=1)

        # Logo/Title
        title = ctk.CTkLabel(
            container,
            text='ICETUBIG',
            font=ctk.CTkFont(size=32, weight='bold'),
            text_color=self.tokens['accent_1'],
        )
        title.grid(row=0, column=0, columnspan=2, pady=(0, 8))

        subtitle = ctk.CTkLabel(
            container,
            text='Inventory Management System',
            font=ctk.CTkFont(size=14),
            text_color=self.tokens['text_secondary'],
        )
        subtitle.grid(row=1, column=0, columnspan=2, pady=(0, 24))

        # Error message label (initially hidden)
        self.error_label = ctk.CTkLabel(
            container,
            text='',
            font=ctk.CTkFont(size=12),
            text_color=self.tokens['danger'],
        )
        self.error_label.grid(row=2, column=0, columnspan=2, pady=(0, 12))

        # Username field
        username_label = ctk.CTkLabel(
            container,
            text='Username',
            font=ctk.CTkFont(size=13),
            text_color=self.tokens['text_secondary'],
        )
        username_label.grid(row=3, column=0, sticky='w', pady=(0, 4))

        self.username_entry = ctk.CTkEntry(
            container,
            placeholder_text='Enter username',
            fg_color=self.tokens['bg_input'],
            border_color=self.tokens['border'],
            text_color=self.tokens['text_primary'],
            placeholder_text_color=self.tokens['text_muted'],
        )
        self.username_entry.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0, 16))

        # Password field
        password_label = ctk.CTkLabel(
            container,
            text='Password',
            font=ctk.CTkFont(size=13),
            text_color=self.tokens['text_secondary'],
        )
        password_label.grid(row=5, column=0, sticky='w', pady=(0, 4))

        self.password_entry = ctk.CTkEntry(
            container,
            placeholder_text='Enter password',
            show='•',
            fg_color=self.tokens['bg_input'],
            border_color=self.tokens['border'],
            text_color=self.tokens['text_primary'],
            placeholder_text_color=self.tokens['text_muted'],
        )
        self.password_entry.grid(row=6, column=0, columnspan=2, sticky='ew', pady=(0, 16))

        # Remember me checkbox
        self.remember_var = ctk.BooleanVar(value=False)
        remember_checkbox = ctk.CTkCheckBox(
            container,
            text='Remember me',
            variable=self.remember_var,
            fg_color=self.tokens['accent_1'],
            text_color=self.tokens['text_secondary'],
            font=ctk.CTkFont(size=12),
        )
        remember_checkbox.grid(row=7, column=0, columnspan=2, sticky='w', pady=(0, 24))

        # Login button
        login_button = ctk.CTkButton(
            container,
            text='Login',
            command=self._on_login_clicked,
            fg_color=self.tokens['accent_1'],
            hover_color=self.tokens['accent_2'],
            text_color=self.tokens['bg_base'],
            font=ctk.CTkFont(size=14, weight='bold'),
            height=40,
        )
        login_button.grid(row=8, column=0, columnspan=2, sticky='ew', pady=(0, 12))

        # Bind Enter key to login
        self.username_entry.bind('<Return>', lambda e: self._on_login_clicked())
        self.password_entry.bind('<Return>', lambda e: self._on_login_clicked())

    def _on_login_clicked(self):
        """Handle login button click."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username:
            self._show_error('Username is required')
            return

        if not password:
            self._show_error('Password is required')
            return

        # Authenticate
        user = self.auth_service.authenticate(username, password)
        if user:
            self._show_error('')  # Clear error
            if self.on_login_success:
                self.on_login_success(user)
        else:
            self._show_error('Invalid username or password')

    def _show_error(self, message: str):
        """Display error message."""
        self.error_label.configure(text=message)

    def clear_fields(self):
        """Clear all input fields."""
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.error_label.configure(text='')
