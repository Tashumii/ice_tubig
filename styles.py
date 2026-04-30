from typing import Dict

# ============================================================
# DESIGN TOKENS - Professional UI System
# Following anti-generic UI/UX principles
# ============================================================

TOKENS: Dict[str, Dict[str, str]] = {
    'dark': {
        # Surfaces (60% canvas, 30% secondary, 10% accent)
        'bg_base': '#0B0A09',           # Canvas (60%)
        'bg_surface': '#151311',        # Cards (30%)
        'bg_elevated': '#1E1B18',       # Elevated panels
        'bg_input': '#1A1714',          # Input fields - distinct from surface
        'bg_sidebar': '#070605',        # Sidebar - darkest
        
        # Brand (10% accent rule - single hue family)
        'accent_1': '#FF9D5C',          # Primary CTA, active states
        'accent_2': '#FF8A47',          # Hover states
        'accent_3': '#FFB87A',          # Pressed states
        
        # Semantic colors (limited palette)
        'success': '#8FE6A8',
        'warning': '#FFC670',
        'danger': '#FF6B6B',
        
        # Text hierarchy (high contrast)
        'text_primary': '#FFFFFF',      # Pure white for maximum contrast
        'text_secondary': '#D4C9BC',    # 70% opacity equivalent
        'text_muted': '#9A8F84',        # 50% opacity equivalent
        
        # Borders (visible contrast - 10%+ darker than bg)
        'border': '#3A3530',            # Default border - clearly visible
        'border_strong': '#4A453F',     # Emphasis border
        'border_accent': '#FF9D5C44',   # Accent border with opacity
        
        # Component-specific
        'surface_muted': '#1C1916',     # Distinct from bg_elevated
        'input_border': '#4A453F',      # Strong border for inputs
        'card_border': '#3A342E',       # Card borders - visible
        
        # Table
        'table_header_bg': '#FF9D5C',
        'table_header_text': '#0A0806',
        'table_row_alt': '#1A1714',
        'table_row_hover': '#1F1C19',
        
        # Navigation
        'nav_active_bg': '#1F1C19',
        'nav_hover': '#1A1714',
        
        # Pills/Badges
        'pill_bg': '#2A2420',
        'pill_text': '#FFD4A6',
        
        # Shadows (subtle only - rgba(0,0,0,0.04-0.09))
        'shadow_xs': '0 1px 2px rgba(0, 0, 0, 0.08)',
        'shadow_sm': '0 2px 8px rgba(0, 0, 0, 0.10), 0 1px 2px rgba(0, 0, 0, 0.06)',
        'shadow_md': '0 4px 16px rgba(0, 0, 0, 0.12), 0 2px 4px rgba(0, 0, 0, 0.08)',
        'shadow_lg': '0 8px 24px rgba(0, 0, 0, 0.15), 0 4px 8px rgba(0, 0, 0, 0.10)',
        
        # Border radius scale (consistent system)
        'radius_xs': '4',
        'radius_sm': '6',
        'radius_md': '10',
        'radius_lg': '14',
        'radius_xl': '18',
        'radius_full': '9999',
        
        # Typography
        'font_family': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        'font_size_xs': '11',
        'font_size_sm': '13',
        'font_size_base': '15',
        'font_size_md': '17',
        'font_size_lg': '20',
        'font_size_xl': '24',
        'font_size_2xl': '30',
        'font_size_3xl': '40',
    },
    'light': {
        # Surfaces (60-30-10 rule)
        'bg_base': '#FAFAF9',           # Warm neutral canvas
        'bg_surface': '#FFFFFF',        # Pure white cards
        'bg_elevated': '#FFF6EF',       # Subtle warm tint
        'bg_input': '#F5F3F0',          # Distinct input background
        'bg_sidebar': '#1A1714',        # Dark sidebar for contrast
        
        # Brand (single hue family)
        'accent_1': '#E06A3C',          # Primary CTA
        'accent_2': '#C85A2F',          # Hover
        'accent_3': '#F28A4B',          # Pressed
        
        # Semantic colors
        'success': '#2D8F4D',
        'warning': '#D66A1F',
        'danger': '#C93A3A',
        
        # Text hierarchy
        'text_primary': '#1A1816',      # Near black
        'text_secondary': '#4A4540',    # 70% opacity
        'text_muted': '#7A7570',        # 50% opacity
        
        # Borders (10%+ darker than background)
        'border': '#D4C9BE',            # Clearly visible
        'border_strong': '#B8ADA0',     # Emphasis
        'border_accent': '#E06A3C44',
        
        # Component-specific
        'surface_muted': '#F5F3F0',
        'input_border': '#C4B9AE',      # Strong input borders
        'card_border': '#D2C5BA',
        
        # Table
        'table_header_bg': '#E06A3C',
        'table_header_text': '#FFFFFF',
        'table_row_alt': '#F9F5F0',
        'table_row_hover': '#FFF0E5',
        
        # Navigation
        'nav_active_bg': '#FFE8D9',
        'nav_hover': '#FFF0E5',
        
        # Pills/Badges
        'pill_bg': '#FFE0CC',
        'pill_text': '#6B3316',
        
        # Shadows (subtle)
        'shadow_xs': '0 1px 2px rgba(0, 0, 0, 0.04)',
        'shadow_sm': '0 2px 8px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03)',
        'shadow_md': '0 4px 16px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.04)',
        'shadow_lg': '0 8px 24px rgba(0, 0, 0, 0.09), 0 4px 8px rgba(0, 0, 0, 0.05)',
        
        # Border radius scale
        'radius_xs': '4',
        'radius_sm': '6',
        'radius_md': '10',
        'radius_lg': '14',
        'radius_xl': '18',
        'radius_full': '9999',
        
        # Typography
        'font_family': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        'font_size_xs': '11',
        'font_size_sm': '13',
        'font_size_base': '15',
        'font_size_md': '17',
        'font_size_lg': '20',
        'font_size_xl': '24',
        'font_size_2xl': '30',
        'font_size_3xl': '40',
    },
}


def init_theme(theme: str = "dark") -> Dict[str, str]:
    return TOKENS.get(theme.lower(), TOKENS["dark"])


def build_qss(tokens: Dict[str, str]) -> str:
    # Border radius scale (nesting rule compliant)
    radius_xs = f"{tokens['radius_xs']}px"
    radius_sm = f"{tokens['radius_sm']}px"
    radius_md = f"{tokens['radius_md']}px"
    radius_lg = f"{tokens['radius_lg']}px"
    radius_xl = f"{tokens['radius_xl']}px"
    
    # Type scale
    text_xs = f"{tokens['font_size_xs']}px"
    text_sm = f"{tokens['font_size_sm']}px"
    text_base = f"{tokens['font_size_base']}px"
    text_md = f"{tokens['font_size_md']}px"
    text_lg = f"{tokens['font_size_lg']}px"
    text_xl = f"{tokens['font_size_xl']}px"
    text_2xl = f"{tokens['font_size_2xl']}px"
    text_3xl = f"{tokens['font_size_3xl']}px"
    
    return f"""
    /* ============================================================
       PROFESSIONAL UI SYSTEM - Anti-Generic Design
       Following: Single brand hue, visible borders, subtle shadows,
       consistent radius scale, proper text hierarchy
       ============================================================ */
    
    * {{
        /* Minimum animation layer - all interactive elements */
        transition: background-color 180ms ease,
                    border-color 180ms ease,
                    color 180ms ease,
                    box-shadow 180ms ease;
    }}
    
    QWidget {{
        background: {tokens['bg_base']};
        color: {tokens['text_primary']};
        font-family: {tokens['font_family']};
        font-size: {text_base};
    }}
    
    QMainWindow {{
        background: {tokens['bg_base']};
    }}
    
    QLabel {{
        background: transparent;
        color: {tokens['text_primary']};
    }}
    
    /* Brand title - accent color with hierarchy */
    QLabel[brandTitle="true"] {{
        color: {tokens['accent_1']};
        font-size: {text_2xl};
        font-weight: 800;
        letter-spacing: 0.5px;
    }}
    
    /* Brand subtitle - secondary text */
    QLabel[brandSub="true"] {{
        color: {tokens['text_secondary']};
        font-size: {text_xs};
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }}
    
    /* Muted text */
    QLabel[muted="true"] {{
        color: {tokens['text_muted']};
        font-size: {text_sm};
    }}
    
    /* Input fields - distinct background, visible borders */
    QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {{
        background: {tokens['bg_input']};
        color: {tokens['text_primary']};
        border: 1px solid {tokens['input_border']};
        border-radius: {radius_sm};
        padding: 8px 12px;
        font-size: {text_base};
        selection-background-color: {tokens['accent_1']};
        selection-color: #FFFFFF;
    }}
    
    QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {tokens['accent_1']};
        padding: 7px 11px;
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 24px;
        subcontrol-origin: padding;
        subcontrol-position: center right;
    }}
    
    /* Primary buttons - brand accent with hover states */
    QPushButton {{
        background: {tokens['accent_1']};
        color: #FFFFFF;
        border: 1px solid {tokens['accent_2']};
        border-radius: {radius_sm};
        padding: 10px 16px;
        font-size: {text_sm};
        font-weight: 600;
        min-height: 20px;
    }}
    
    QPushButton:hover {{
        background: {tokens['accent_2']};
        border: 1px solid {tokens['accent_1']};
    }}
    
    QPushButton:pressed {{
        background: {tokens['accent_3']};
        border: 1px solid {tokens['accent_2']};
    }}
    
    QPushButton:disabled {{
        background: {tokens['surface_muted']};
        color: {tokens['text_muted']};
        border: 1px solid {tokens['border']};
    }}
    
    /* Navigation buttons - transparent with visible hover */
    QPushButton[nav="true"] {{
        text-align: left;
        padding: 12px 14px;
        border-radius: {radius_sm};
        background: transparent;
        color: {tokens['text_primary']};
        border: 1px solid transparent;
        font-size: {text_sm};
        font-weight: 500;
    }}
    
    QPushButton[nav="true"]:hover {{
        background: {tokens['nav_hover']};
        border: 1px solid {tokens['border']};
    }}
    
    /* Active navigation - brand accent */
    QPushButton[navActive="true"] {{
        background: {tokens['nav_active_bg']};
        color: {tokens['accent_1']};
        border: 1px solid {tokens['border_accent']};
        font-weight: 600;
    }}
    
    /* Danger buttons - semantic red */
    QPushButton[danger="true"] {{
        background: transparent;
        color: {tokens['danger']};
        border: 1px solid {tokens['danger']};
    }}
    
    QPushButton[danger="true"]:hover {{
        background: {tokens['danger']};
        color: #FFFFFF;
    }}
    
    /* Cards - proper surface with visible borders and shadows */
    QFrame[card="true"] {{
        background: {tokens['bg_surface']};
        border: 1px solid {tokens['card_border']};
        border-radius: {radius_md};
    }}
    
    /* Panels - distinct from cards */
    QFrame[panel="true"] {{
        background: {tokens['surface_muted']};
        border: 1px solid {tokens['border']};
        border-radius: {radius_sm};
    }}
    
    /* Shell containers - larger radius */
    QFrame[shell="true"] {{
        background: {tokens['bg_surface']};
        border: 1px solid {tokens['card_border']};
        border-radius: {radius_lg};
    }}
    
    /* Top bar */
    QFrame[topbar="true"] {{
        background: {tokens['bg_surface']};
        border: 1px solid {tokens['card_border']};
        border-radius: {radius_md};
    }}
    
    /* Pills/Badges - full radius, visible borders */
    QLabel[pill="true"] {{
        background: {tokens['pill_bg']};
        color: {tokens['pill_text']};
        border: 1px solid {tokens['border_accent']};
        border-radius: {tokens['radius_full']}px;
        padding: 5px 12px;
        font-size: {text_xs};
        font-weight: 600;
    }}
    
    /* Scroll areas */
    QScrollArea {{
        border: none;
        background: {tokens['bg_base']};
    }}
    
    QScrollBar:vertical {{
        background: {tokens['bg_base']};
        width: 10px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {tokens['border']};
        border-radius: 5px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {tokens['border_strong']};
    }}
    
    QScrollBar:horizontal {{
        background: {tokens['bg_base']};
        height: 10px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:horizontal {{
        background: {tokens['border']};
        border-radius: 5px;
        min-width: 30px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background: {tokens['border_strong']};
    }}
    
    QScrollBar::add-line, QScrollBar::sub-line {{
        border: none;
        background: none;
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
