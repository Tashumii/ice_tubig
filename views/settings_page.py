import tkinter.messagebox as messagebox
import customtkinter as ctk

from services.settings_service import SettingsService


class SettingsPage(ctk.CTkFrame):
    def __init__(self, settings_service: SettingsService, on_save, tokens: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_service = settings_service
        self.on_save = on_save
        self.tokens = tokens
        self.configure(fg_color=self.tokens['bg_base'])
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text='Settings',
            font=ctk.CTkFont(size=24, weight='bold'),
            text_color=self.tokens['text_primary'],
        )
        title.grid(row=0, column=0, sticky='w', pady=(0, 4))

        subtitle = ctk.CTkLabel(
            self,
            text='Manage theme and system preferences.',
            font=ctk.CTkFont(size=12),
            text_color=self.tokens['text_secondary'],
        )
        subtitle.grid(row=1, column=0, sticky='w', pady=(0, 20))

        card = ctk.CTkFrame(
            self,
            fg_color=self.tokens['bg_surface'],
            corner_radius=12,
            border_color=self.tokens['border'],
            border_width=1,
        )
        card.grid(row=2, column=0, sticky='ew')
        card.grid_columnconfigure(1, weight=1)

        label = ctk.CTkLabel(
            card,
            text='APP THEME',
            font=ctk.CTkFont(size=10, weight='bold'),
            text_color=self.tokens['text_secondary'],
        )
        label.grid(row=0, column=0, sticky='w', padx=16, pady=(16, 4))

        description = ctk.CTkLabel(
            card,
            text='Switch between dark mode and light mode.',
            font=ctk.CTkFont(size=10),
            text_color=self.tokens['text_muted'],
        )
        description.grid(row=1, column=0, sticky='w', padx=16, pady=(0, 16))

        self.theme_menu = ctk.CTkOptionMenu(
            card,
            values=['Light', 'Dark'],
            fg_color=self.tokens['bg_input'],
            button_color=self.tokens['bg_surface'],
            dropdown_fg_color=self.tokens['bg_surface'],
            text_color=self.tokens['text_primary'],
            width=140,
        )
        self.theme_menu.grid(row=0, column=1, rowspan=2, sticky='e', padx=16)

        self.save_button = ctk.CTkButton(
            card,
            text='SAVE CHANGES',
            command=self.save_settings,
            fg_color=self.tokens['accent_1'],
            hover_color=self.tokens['accent_2'],
            text_color=self.tokens['bg_base'],
            width=160,
        )
        self.save_button.grid(row=2, column=0, columnspan=2, pady=(0, 16))

    def refresh(self):
        theme = self.settings_service.get_theme()
        self.theme_menu.set('Dark' if theme == 'dark' else 'Light')

    def save_settings(self):
        selected = self.theme_menu.get().lower()
        try:
            self.settings_service.set_theme(selected)
            if callable(self.on_save):
                self.on_save(selected)
        except Exception as exc:
            messagebox.showerror('Save Error', str(exc))
