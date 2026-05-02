import os
from typing import Dict

# ============================================================
# DESIGN TOKENS — Mr. Ice Buddha · Icy Blue Brand System
# Typography-first, high-contrast, frosted glass aesthetic
# ============================================================

_BG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', 'background_login.png')

TOKENS: Dict[str, Dict[str, str]] = {
    'dark': {
        # Surfaces — frosted dark navy (high opacity so text is readable)
        'bg_base': '#0B1929',
        'bg_surface': 'rgba(8, 20, 38, 0.92)',       # Cards: dark frosted glass
        'bg_elevated': 'rgba(16, 32, 58, 0.90)',      # Elevated panels
        'bg_input': 'rgba(6, 16, 32, 0.88)',           # Input fields
        'bg_sidebar': '#061020',                        # Sidebar: solid dark
        'bg_login': _BG_PATH,

        # Brand — Ice Buddha Blue
        'accent_1': '#5DADE2',
        'accent_2': '#3498DB',
        'accent_3': '#85C1E9',

        # Semantic colors
        'success': '#2ECC71',
        'warning': '#F39C12',
        'danger': '#E74C3C',

        # Text hierarchy — HIGH CONTRAST on dark frosted cards
        'text_primary': '#EDF6FC',       # Near-white with blue tint
        'text_secondary': '#93C5E8',     # Soft sky blue — readable
        'text_muted': '#5F9CC0',         # Muted steel blue

        # Sidebar text
        'sidebar_text_primary': '#EDF6FC',
        'sidebar_text_secondary': '#93C5E8',
        'sidebar_text_muted': '#5499C7',

        # Borders — visible against frosted dark
        'border': 'rgba(93, 173, 226, 0.25)',
        'border_strong': 'rgba(93, 173, 226, 0.40)',
        'border_accent': 'rgba(93, 173, 226, 0.35)',

        # Component
        'surface_muted': 'rgba(10, 24, 48, 0.85)',
        'input_border': 'rgba(93, 173, 226, 0.30)',
        'card_border': 'rgba(93, 173, 226, 0.20)',

        # Table
        'table_header_bg': '#2E86C1',
        'table_header_text': '#FFFFFF',
        'table_row_alt': 'rgba(8, 20, 38, 0.50)',
        'table_row_hover': 'rgba(93, 173, 226, 0.15)',

        # Navigation
        'nav_active_bg': '#2E86C1',
        'nav_hover': 'rgba(93, 173, 226, 0.12)',

        # Pills
        'pill_bg': 'rgba(93, 173, 226, 0.15)',
        'pill_text': '#5DADE2',

        # Shadows
        'shadow_xs': '0 1px 3px rgba(0,0,0,0.20)',
        'shadow_sm': '0 2px 10px rgba(0,0,0,0.25)',
        'shadow_md': '0 4px 20px rgba(0,0,0,0.30)',
        'shadow_lg': '0 8px 30px rgba(0,0,0,0.35)',

        # Radius
        'radius_xs': '4', 'radius_sm': '6', 'radius_md': '12',
        'radius_lg': '16', 'radius_xl': '20', 'radius_full': '9999',

        # Typography
        'font_family': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        'font_size_xs': '11', 'font_size_sm': '13', 'font_size_base': '14',
        'font_size_md': '16', 'font_size_lg': '20', 'font_size_xl': '24',
        'font_size_2xl': '28', 'font_size_3xl': '36',
    },
    'light': {
        # Surfaces — frosted white glass
        'bg_base': '#E8F4FD',
        'bg_surface': 'rgba(255, 255, 255, 0.88)',
        'bg_elevated': 'rgba(230, 244, 253, 0.85)',
        'bg_input': 'rgba(255, 255, 255, 0.70)',
        'bg_sidebar': '#061020',
        'bg_login': _BG_PATH,

        # Brand
        'accent_1': '#2E86C1',
        'accent_2': '#1A5276',
        'accent_3': '#5DADE2',

        # Semantic
        'success': '#1E8449',
        'warning': '#D68910',
        'danger': '#CB4335',

        # Text — dark on white glass
        'text_primary': '#0A1F33',
        'text_secondary': '#1B4F72',
        'text_muted': '#5D6D7E',

        # Sidebar text
        'sidebar_text_primary': '#EDF6FC',
        'sidebar_text_secondary': '#93C5E8',
        'sidebar_text_muted': '#5499C7',

        # Borders
        'border': 'rgba(46, 134, 193, 0.25)',
        'border_strong': 'rgba(46, 134, 193, 0.40)',
        'border_accent': 'rgba(46, 134, 193, 0.30)',

        # Component
        'surface_muted': 'rgba(214, 234, 248, 0.70)',
        'input_border': 'rgba(46, 134, 193, 0.30)',
        'card_border': 'rgba(46, 134, 193, 0.20)',

        # Table
        'table_header_bg': '#2E86C1',
        'table_header_text': '#FFFFFF',
        'table_row_alt': 'rgba(235, 245, 251, 0.50)',
        'table_row_hover': 'rgba(93, 173, 226, 0.12)',

        # Nav
        'nav_active_bg': '#2E86C1',
        'nav_hover': 'rgba(93, 173, 226, 0.12)',

        # Pills
        'pill_bg': 'rgba(93, 173, 226, 0.15)',
        'pill_text': '#1A5276',

        # Shadows
        'shadow_xs': '0 1px 3px rgba(44,62,80,0.08)',
        'shadow_sm': '0 2px 10px rgba(44,62,80,0.10)',
        'shadow_md': '0 4px 20px rgba(44,62,80,0.12)',
        'shadow_lg': '0 8px 30px rgba(44,62,80,0.15)',

        # Radius
        'radius_xs': '4', 'radius_sm': '6', 'radius_md': '12',
        'radius_lg': '16', 'radius_xl': '20', 'radius_full': '9999',

        # Typography
        'font_family': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        'font_size_xs': '11', 'font_size_sm': '13', 'font_size_base': '14',
        'font_size_md': '16', 'font_size_lg': '20', 'font_size_xl': '24',
        'font_size_2xl': '28', 'font_size_3xl': '36',
    },
}


def init_theme(theme: str = "dark") -> Dict[str, str]:
    return TOKENS.get(theme.lower(), TOKENS["dark"])


def build_qss(tokens: Dict[str, str]) -> str:
    r_sm = f"{tokens['radius_sm']}px"
    r_md = f"{tokens['radius_md']}px"
    r_lg = f"{tokens['radius_lg']}px"
    t_xs = f"{tokens['font_size_xs']}px"
    t_sm = f"{tokens['font_size_sm']}px"
    t_base = f"{tokens['font_size_base']}px"
    t_md = f"{tokens['font_size_md']}px"
    t_lg = f"{tokens['font_size_lg']}px"
    t_xl = f"{tokens['font_size_xl']}px"
    t_2xl = f"{tokens['font_size_2xl']}px"

    return f"""
    /* ============================================================
       Mr. Ice Buddha · Frosted Glass Typography System
       High-contrast text on semi-transparent dark panels
       ============================================================ */

    * {{
        transition: background-color 180ms ease,
                    border-color 180ms ease,
                    color 180ms ease;
    }}

    QWidget {{
        background: transparent;
        color: {tokens['text_primary']};
        font-family: {tokens['font_family']};
        font-size: {t_base};
    }}

    QMainWindow {{
        background: {tokens['bg_base']};
    }}

    /* ── Typography hierarchy ────────────────────────────────── */

    QLabel {{
        background: transparent;
        color: {tokens['text_primary']};
        font-weight: 400;
    }}

    QLabel[brandTitle="true"] {{
        color: {tokens['accent_1']};
        font-size: {t_2xl};
        font-weight: 800;
        letter-spacing: 0.5px;
    }}

    QLabel[brandSub="true"] {{
        color: {tokens['text_secondary']};
        font-size: {t_xs};
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }}

    QLabel[muted="true"] {{
        color: {tokens['text_muted']};
        font-size: {t_sm};
        font-weight: 400;
    }}

    QLabel[pageTitle="true"] {{
        font-size: {t_xl};
        font-weight: 700;
        color: {tokens['text_primary']};
        letter-spacing: 0.3px;
    }}

    QLabel[cardTitle="true"] {{
        font-size: {t_md};
        font-weight: 700;
        color: {tokens['text_primary']};
    }}

    QLabel[sectionLabel="true"] {{
        font-size: {t_xs};
        font-weight: 700;
        color: {tokens['text_secondary']};
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }}

    QLabel[kpiValue="true"] {{
        font-size: {t_xl};
        font-weight: 800;
        color: {tokens['accent_1']};
    }}

    QLabel[kpiLabel="true"] {{
        font-size: {t_xs};
        font-weight: 600;
        color: {tokens['text_secondary']};
        letter-spacing: 0.5px;
    }}

    /* ── Inputs ──────────────────────────────────────────────── */

    QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QListWidget {{
        background: {tokens['bg_input']};
        color: {tokens['text_primary']};
        border: 1px solid {tokens['input_border']};
        border-radius: {r_sm};
        padding: 10px 14px;
        font-size: {t_base};
        font-weight: 500;
        selection-background-color: {tokens['accent_1']};
        selection-color: #FFFFFF;
    }}

    QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {tokens['accent_1']};
        padding: 9px 13px;
    }}

    QLineEdit::placeholder {{
        color: {tokens['text_muted']};
        font-weight: 400;
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
        subcontrol-origin: padding;
        subcontrol-position: center right;
    }}

    QSpinBox, QDoubleSpinBox {{
        background: {tokens['bg_input']};
        color: {tokens['text_primary']};
        border: 1px solid {tokens['input_border']};
        border-radius: {r_sm};
        padding: 8px 12px;
        font-size: {t_base};
    }}

    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {tokens['accent_1']};
    }}

    /* ── Buttons ─────────────────────────────────────────────── */

    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {tokens['accent_1']}, stop:1 {tokens['accent_2']});
        color: #FFFFFF;
        border: none;
        border-radius: {r_sm};
        padding: 10px 18px;
        font-size: {t_sm};
        font-weight: 600;
        min-height: 20px;
        letter-spacing: 0.3px;
    }}

    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {tokens['accent_2']}, stop:1 {tokens['accent_1']});
    }}

    QPushButton:pressed {{
        background: {tokens['accent_3']};
    }}

    QPushButton:disabled {{
        background: {tokens['surface_muted']};
        color: {tokens['text_muted']};
        border: 1px solid {tokens['border']};
    }}

    QPushButton[nav="true"] {{
        text-align: left;
        padding: 12px 14px;
        border-radius: {r_sm};
        background: transparent;
        color: {tokens['sidebar_text_secondary']};
        border: 1px solid transparent;
        font-size: {t_sm};
        font-weight: 500;
    }}

    QPushButton[nav="true"]:hover {{
        background: {tokens['nav_hover']};
        border: 1px solid {tokens['border']};
        color: {tokens['sidebar_text_primary']};
    }}

    QPushButton[navActive="true"] {{
        background: {tokens['nav_active_bg']};
        color: #FFFFFF;
        border: 1px solid {tokens['border_accent']};
        font-weight: 600;
    }}

    QPushButton[danger="true"] {{
        background: transparent;
        color: {tokens['danger']};
        border: 1px solid {tokens['danger']};
        font-weight: 600;
    }}

    QPushButton[danger="true"]:hover {{
        background: {tokens['danger']};
        color: #FFFFFF;
    }}

    QPushButton[primary="true"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {tokens['accent_1']}, stop:1 {tokens['accent_2']});
        color: #FFFFFF;
        font-weight: 700;
        border-radius: {r_md};
        padding: 12px 24px;
    }}

    QPushButton[secondary="true"] {{
        background: transparent;
        color: {tokens['accent_1']};
        border: 1px solid {tokens['accent_1']};
        font-weight: 600;
    }}

    QPushButton[secondary="true"]:hover {{
        background: {tokens['accent_1']};
        color: #FFFFFF;
    }}

    /* ── Cards & Panels — Frosted glass with strong borders ─── */

    QFrame[card="true"] {{
        background: {tokens['bg_surface']};
        border: 1px solid {tokens['card_border']};
        border-radius: {r_md};
    }}

    QFrame[panel="true"] {{
        background: {tokens['surface_muted']};
        border: 1px solid {tokens['border']};
        border-radius: {r_sm};
    }}

    QFrame[shell="true"] {{
        background: {tokens['bg_surface']};
        border: 1px solid {tokens['card_border']};
        border-radius: {r_lg};
    }}

    QFrame[topbar="true"] {{
        background: {tokens['bg_elevated']};
        border: 1px solid {tokens['card_border']};
        border-radius: {r_md};
    }}

    QLabel[pill="true"] {{
        background: {tokens['pill_bg']};
        color: {tokens['pill_text']};
        border: 1px solid {tokens['border_accent']};
        border-radius: {tokens['radius_full']}px;
        padding: 5px 14px;
        font-size: {t_xs};
        font-weight: 700;
        letter-spacing: 0.5px;
    }}

    /* ── Scroll areas ────────────────────────────────────────── */

    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical {{
        background: {tokens['border_strong']};
        border-radius: 4px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {tokens['accent_1']};
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        border-radius: 4px;
    }}

    QScrollBar::handle:horizontal {{
        background: {tokens['border_strong']};
        border-radius: 4px;
        min-width: 30px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {tokens['accent_1']};
    }}

    QScrollBar::add-line, QScrollBar::sub-line {{
        border: none;
        background: none;
    }}

    QStackedWidget {{
        background: transparent;
    }}

    /* ── Dialogs ─────────────────────────────────────────────── */

    QDialog {{
        background: {tokens['bg_base']};
        border: 1px solid {tokens['card_border']};
        border-radius: {r_md};
    }}

    QDialogButtonBox QPushButton {{
        min-width: 90px;
    }}

    /* ── Checkboxes ──────────────────────────────────────────── */

    QCheckBox {{
        color: {tokens['text_primary']};
        spacing: 8px;
        font-weight: 500;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {tokens['border_strong']};
        border-radius: 4px;
        background: {tokens['bg_input']};
    }}

    QCheckBox::indicator:checked {{
        background: {tokens['accent_1']};
        border-color: {tokens['accent_1']};
    }}

    /* ── List widgets ────────────────────────────────────────── */

    QListWidget {{
        background: transparent;
        border: none;
        outline: none;
    }}

    QListWidget::item {{
        border: none;
        padding: 2px 0;
    }}

    QListWidget::item:selected {{
        background: transparent;
    }}

    /* ── Message boxes ───────────────────────────────────────── */

    QMessageBox {{
        background: {tokens['bg_surface']};
    }}

    QMessageBox QLabel {{
        color: {tokens['text_primary']};
        font-size: {t_base};
        font-weight: 500;
    }}
    """


def apply_app_style(app, theme: str = "dark") -> Dict[str, str]:
    tokens = init_theme(theme)
    try:
        app.setStyleSheet(build_qss(tokens))
    except Exception:
        pass
    return tokens
