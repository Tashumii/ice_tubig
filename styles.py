from typing import Dict

# ============================================================
# DESIGN TOKENS - Professional UI System
# Following anti-generic UI/UX principles
# ============================================================

TOKENS: Dict[str, Dict[str, str]] = {
    'dark': {
        # Surfaces (60% canvas, 30% secondary, 10% accent)
        'bg_base': '#111827',           # Dark gray canvas (not pure black)
        'bg_surface': '#1F2937',        # Cards
        'bg_elevated': '#374151',       # Elevated panels
        'bg_input': '#1F2937',          # Input fields
        'bg_sidebar': '#0F172A',        # Sidebar
        
        # Brand (de-saturated for dark mode)
        'accent_1': '#FB923C',          # Primary CTA
        'accent_2': '#F97316',          # Hover states
        'accent_3': '#FDBA74',          # Pressed states
        
        # Semantic colors (de-saturated)
        'success': '#6EE7B7',
        'warning': '#FCD34D',
        'danger': '#F87171',
        
        # Text hierarchy (off-white, not pure white)
        'text_primary': '#E5E7EB',      # Off-white for reduced eye strain
        'text_secondary': '#9CA3AF',    # Medium gray
        'text_muted': '#6B7280',        # Muted gray
        
        # Sidebar text (same as regular text in dark mode)
        'sidebar_text_primary': '#E5E7EB',
        'sidebar_text_secondary': '#9CA3AF',
        'sidebar_text_muted': '#6B7280',
        
        # Borders (visible contrast)
        'border': '#374151',            # Default border
        'border_strong': '#4B5563',     # Emphasis border
        'border_accent': '#FB923C44',   # Accent border with opacity
        
        # Component-specific
        'surface_muted': '#1F2937',     # Distinct from bg_elevated
        'input_border': '#4B5563',      # Strong border for inputs
        'card_border': '#374151',       # Card borders
        
        # Table
        'table_header_bg': '#FB923C',
        'table_header_text': '#111827',
        'table_row_alt': '#1F2937',
        'table_row_hover': '#374151',
        
        # Navigation
        'nav_active_bg': '#374151',
        'nav_hover': '#1F2937',
        
        # Pills/Badges
        'pill_bg': '#374151',
        'pill_text': '#FCD34D',
        
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
        'bg_base': '#F9FAFB',           # Light gray canvas
        'bg_surface': '#FFFFFF',        # Pure white cards
        'bg_elevated': '#F3F4F6',       # Subtle gray tint
        'bg_input': '#F9FAFB',          # Distinct input background
        'bg_sidebar': '#111827',        # Dark sidebar for contrast
        
        # Brand (saturated for light mode)
        'accent_1': '#EA580C',          # Primary CTA
        'accent_2': '#C2410C',          # Hover
        'accent_3': '#F97316',          # Pressed
        
        # Semantic colors
        'success': '#059669',
        'warning': '#D97706',
        'danger': '#DC2626',
        
        # Text hierarchy
        'text_primary': '#111827',      # Near black
        'text_secondary': '#4B5563',    # Medium gray
        'text_muted': '#6B7280',        # Muted gray
        
        # Sidebar text (light colors for dark sidebar)
        'sidebar_text_primary': '#E5E7EB',    # Light text for dark sidebar
        'sidebar_text_secondary': '#9CA3AF',  # Medium gray for dark sidebar
        'sidebar_text_muted': '#6B7280',      # Muted for dark sidebar
        
        # Borders (10%+ darker than background)
        'border': '#E5E7EB',            # Clearly visible
        'border_strong': '#D1D5DB',     # Emphasis
        'border_accent': '#EA580C44',
        
        # Component-specific
        'surface_muted': '#F3F4F6',
        'input_border': '#D1D5DB',      # Strong input borders
        'card_border': '#E5E7EB',
        
        # Table
        'table_header_bg': '#EA580C',
        'table_header_text': '#FFFFFF',
        'table_row_alt': '#F9FAFB',
        'table_row_hover': '#FEF3C7',
        
        # Navigation
        'nav_active_bg': '#FEF3C7',
        'nav_hover': '#FEF9C3',
        
        # Pills/Badges
        'pill_bg': '#FEF3C7',
        'pill_text': '#92400E',
        
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
