from typing import Dict

TOKENS: Dict[str, Dict[str, str]] = {
    'dark': {
        'bg_base': '#0B0A09',
        'bg_surface': '#151311',
        'bg_elevated': '#1E1B18',
        'bg_input': '#121110',
        'bg_sidebar': '#070605',
        'accent_1': '#F28A4B',
        'accent_2': '#E06A3C',
        'accent_3': '#F5C27A',
        'success': '#7EDC98',
        'warning': '#F3B562',
        'danger': '#E25555',
        'text_primary': '#F7F1E8',
        'text_secondary': '#C8BFB2',
        'text_muted': '#8A8177',
        'border': '#2B2621',
        'border_accent': '#F28A4B33',
        # design tokens
        'radius_sm': '8',
        'radius_md': '12',
        'radius_lg': '20',
        'card_elevation': '#11100F',
        'surface_muted': '#191614',
        'shadow': '#00000066',
        'font_family': 'Space Grotesk',
        'font_size_base': '13',
        'nav_active_bg': '#1B1816',
        'nav_hover': '#151311',
        'pill_bg': '#221C18',
        'pill_text': '#F7D2A6',
        'input_border': '#332C26',
        'card_border': '#312B26',
        'table_header_bg': '#F28A4B',
        'table_header_text': '#1A110B',
        'table_row_alt': '#171412',
    },
    'light': {
        'bg_base': '#F7F3EE',
        'bg_surface': '#FFFFFF',
        'bg_elevated': '#FFF6EF',
        'bg_input': '#F1ECE6',
        'bg_sidebar': '#171412',
        'accent_1': '#F28A4B',
        'accent_2': '#E06A3C',
        'accent_3': '#F5C27A',
        'success': '#35A865',
        'warning': '#E07A25',
        'danger': '#D64545',
        'text_primary': '#1A1816',
        'text_secondary': '#5E5750',
        'text_muted': '#9D968E',
        'border': '#E4D9CE',
        'border_accent': '#F28A4B33',
        # design tokens
        'radius_sm': '8',
        'radius_md': '12',
        'radius_lg': '20',
        'card_elevation': '#F6F0EA',
        'surface_muted': '#FBF7F4',
        'shadow': '#00000022',
        'font_family': 'Space Grotesk',
        'font_size_base': '13',
        'nav_active_bg': '#FFF1E7',
        'nav_hover': '#FFF6EF',
        'pill_bg': '#FCEBDD',
        'pill_text': '#7B3A16',
        'input_border': '#E1D5CA',
        'card_border': '#E2D5CA',
        'table_header_bg': '#F28A4B',
        'table_header_text': '#1A110B',
        'table_row_alt': '#FAF4EE',
    },
}


def init_theme(theme: str = "dark") -> Dict[str, str]:
    return TOKENS.get(theme.lower(), TOKENS["dark"])


def build_qss(tokens: Dict[str, str]) -> str:
    radius_xs = "4px"
    radius_sm = "6px"
    radius_md = "10px"
    radius_lg = "14px"
    text_xs = "11px"
    text_sm = "13px"
    text_base = "15px"
    text_lg = "20px"
    text_xl = "24px"
    return f"""
    /* ============================================================
       DESIGN TOKENS (PyQt mapping)
       ============================================================ */
    QWidget {{
        background: {tokens['bg_base']};
        color: {tokens['text_primary']};
        font-family: {tokens.get('font_family', 'Sans Serif')};
        font-size: {text_base};
    }}
    QMainWindow {{
        background: {tokens['bg_base']};
    }}
    QLabel {{
        background: transparent;
    }}
    QLabel[brandTitle="true"] {{
        color: {tokens['accent_1']};
        font-size: {text_xl};
        font-weight: 800;
        letter-spacing: 1px;
    }}
    QLabel[brandSub="true"] {{
        color: {tokens['text_secondary']};
        font-size: {text_xs};
        font-weight: 700;
        letter-spacing: 2px;
    }}
    QLabel[muted="true"] {{
        color: {tokens['text_muted']};
        font-size: {text_xs};
    }}
    QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {{
        background: {tokens['bg_input']};
        color: {tokens['text_primary']};
        border: 1px solid {tokens.get('input_border', '#C9BCAF')};
        border-radius: {radius_sm};
        padding: 6px 10px;
    }}
    QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {tokens['accent_1']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 22px;
    }}
    QPushButton {{
        background: {tokens['accent_1']};
        color: #FFFFFF;
        border: 1px solid {tokens['accent_2']};
        border-radius: {radius_sm};
        padding: 8px 14px;
        font-size: {text_sm};
        font-weight: 700;
        min-height: 18px;
    }}
    QPushButton:hover {{
        background: {tokens['accent_2']};
        color: #FFFFFF;
        border: 1px solid {tokens['accent_3']};
    }}
    QPushButton:pressed {{
        background: {tokens['accent_3']};
        color: #FFFFFF;
        border: 1px solid {tokens['accent_2']};
    }}
    QPushButton:disabled {{
        background: {tokens.get('surface_muted', tokens['bg_elevated'])};
        color: {tokens['text_muted']};
        border: 1px solid {tokens['border']};
    }}
    QPushButton[nav="true"] {{
        text-align: left;
        padding: 10px 12px;
        border-radius: {radius_sm};
        background: transparent;
        color: {tokens['text_secondary']};
        border: 1px solid transparent;
    }}
    QPushButton[nav="true"]:hover {{
        background: {tokens.get('nav_hover', tokens['bg_elevated'])};
        color: {tokens['text_primary']};
        border: 1px solid {tokens['border']};
    }}
    QPushButton[navActive="true"] {{
        background: {tokens.get('nav_active_bg', tokens['bg_elevated'])};
        color: {tokens['accent_1']};
        border: 1px solid {tokens.get('border_accent', tokens['border'])};
        font-weight: 700;
    }}
    QPushButton[danger="true"] {{
        background: transparent;
        color: {tokens['danger']};
        border: 1px solid {tokens['danger']};
    }}
    QPushButton[danger="true"]:hover {{
        background: {tokens['danger']};
        color: #FFFFFF;
    }}
    QFrame[card="true"] {{
        background: {tokens['bg_surface']};
        border: 1px solid {tokens.get('card_border', '#CDBFB1')};
        border-radius: {radius_md};
    }}
    QFrame[panel="true"] {{
        background: {tokens.get('surface_muted', tokens['bg_elevated'])};
        border: 1px solid {tokens.get('border', '#D3C6B8')};
        border-radius: {radius_sm};
    }}
    QFrame[shell="true"] {{
        background: {tokens['bg_surface']};
        border: 1px solid {tokens.get('card_border', '#CDBFB1')};
        border-radius: {radius_lg};
    }}
    QFrame[topbar="true"] {{
        background: {tokens['bg_surface']};
        border: 1px solid {tokens.get('card_border', '#CDBFB1')};
        border-radius: {radius_md};
    }}
    QLabel[pill="true"] {{
        background: {tokens.get('pill_bg', tokens['bg_elevated'])};
        color: {tokens.get('pill_text', tokens['text_secondary'])};
        border: 1px solid {tokens.get('border_accent', tokens['border'])};
        border-radius: {radius_lg};
        padding: 4px 10px;
        font-size: {text_xs};
        font-weight: 700;
    }}
    QScrollArea {{
        border: none;
        background: {tokens['bg_base']};
    }}
    QStackedWidget {{
        background: transparent;
    }}
    """


def apply_app_style(app, theme: str = "dark") -> Dict[str, str]:
    tokens = init_theme(theme)
    try:
        app.setStyleSheet(build_qss(tokens))
    except Exception:
        pass
    return tokens
