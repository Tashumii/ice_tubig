from typing import Dict, Any

import customtkinter as ctk

TOKENS: Dict[str, Dict[str, str]] = {
    'dark': {
        'bg_base': '#0A0908',
        'bg_surface': '#161614',
        'bg_elevated': '#1F1E1C',
        'bg_input': '#121210',
        'bg_sidebar': '#050504',
        'accent_1': '#FF9E6D',
        'accent_2': '#FF7B4D',
        'success': '#7FD18C',
        'warning': '#FFBE5C',
        'danger': '#FF6B6B',
        'text_primary': '#F5F3F0',
        'text_secondary': '#B8AFA4',
        'text_muted': '#6B6661',
        'border': '#2A2926',
        'border_accent': '#FF9E6D44',
    },
    'light': {
        'bg_base': '#FAF6F1',
        'bg_surface': '#FFFFFF',
        'bg_elevated': '#FFF9F5',
        'bg_input': '#F2EDE9',
        'bg_sidebar': '#0A0908',
        'accent_1': '#E97845',
        'accent_2': '#D96A3C',
        'success': '#4CAF50',
        'warning': '#FB8C00',
        'danger': '#E53935',
        'text_primary': '#1A1816',
        'text_secondary': '#5D5651',
        'text_muted': '#9D968E',
        'border': '#E8E0D5',
        'border_accent': '#E9784544',
    },
}


def init_theme(theme: str = 'dark') -> Dict[str, str]:
    mode = 'Dark' if theme.lower() == 'dark' else 'Light'
    try:
        ctk.set_appearance_mode(mode)
    except Exception:
        pass
    return TOKENS.get(theme.lower(), TOKENS['dark'])


def apply_app_style(root: Any, theme: str = 'dark') -> Dict[str, str]:
    tokens = init_theme(theme)
    try:
        root.configure(fg_color=tokens['bg_base'])
    except Exception:
        root.configure(bg=tokens['bg_base'])
    return tokens
