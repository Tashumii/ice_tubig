"""
Responsive layout utilities for adaptive UI scaling.
"""
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QWidget, QApplication
from typing import Tuple


class ResponsiveHelper:
    """Helper class for responsive layouts with device-aware scaling."""

    # Breakpoints
    MOBILE_BP = 480
    TABLET_BP = 768
    DESKTOP_BP = 1024
    LARGE_BP = 1440
    XLARGE_BP = 1920

    # Device type constants
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    LARGE = "large"
    XLARGE = "xlarge"

    @staticmethod
    def _lookup(device_type, mapping, default=None):
        # Lookup data
        """Internal helper: resolve device_type and look up a value."""
        if device_type is None:
            device_type = ResponsiveHelper.get_device_type()
        return mapping.get(device_type, default)

    @staticmethod
    def get_screen_size() -> QSize:
        # Gets size
        """Get primary screen size."""
        screen = QApplication.primaryScreen()
        return screen.size() if screen else QSize(1920, 1080)

    @staticmethod
    def get_device_type(width: int = None) -> str:
        # Gets type
        """Determine device type based on screen width."""
        if width is None:
            width = ResponsiveHelper.get_screen_size().width()
        if width < ResponsiveHelper.TABLET_BP:
            return ResponsiveHelper.MOBILE
        if width < ResponsiveHelper.DESKTOP_BP:
            return ResponsiveHelper.TABLET
        if width < ResponsiveHelper.LARGE_BP:
            return ResponsiveHelper.DESKTOP
        if width < ResponsiveHelper.XLARGE_BP:
            return ResponsiveHelper.LARGE
        return ResponsiveHelper.XLARGE

    @staticmethod
    def get_responsive_size(base_size: int, device_type: str = None) -> int:
        # Gets size
        """Scale size based on device type."""
        factor = ResponsiveHelper._lookup(device_type, {
            ResponsiveHelper.MOBILE: 0.7, ResponsiveHelper.TABLET: 0.85,
            ResponsiveHelper.DESKTOP: 1.0, ResponsiveHelper.LARGE: 1.15,
            ResponsiveHelper.XLARGE: 1.3,
        }, 1.0)
        return int(base_size * factor)

    @staticmethod
    def get_responsive_font_size(base_size: int, device_type: str = None) -> int:
        # Gets size
        """Scale font size based on device type."""
        factor = ResponsiveHelper._lookup(device_type, {
            ResponsiveHelper.MOBILE: 0.8, ResponsiveHelper.TABLET: 0.9,
            ResponsiveHelper.DESKTOP: 1.0, ResponsiveHelper.LARGE: 1.1,
            ResponsiveHelper.XLARGE: 1.2,
        }, 1.0)
        return int(base_size * factor)

    @staticmethod
    def get_column_count(device_type: str = None) -> int:
        # Gets count
        """Get number of columns for grid layout."""
        return ResponsiveHelper._lookup(device_type, {
            ResponsiveHelper.MOBILE: 1, ResponsiveHelper.TABLET: 2,
            ResponsiveHelper.DESKTOP: 3, ResponsiveHelper.LARGE: 4,
            ResponsiveHelper.XLARGE: 4,
        }, 3)

    @staticmethod
    def should_show_sidebar(device_type: str = None) -> bool:
        # Should sidebar
        """Determine if sidebar should be shown."""
        dt = device_type if device_type is not None else ResponsiveHelper.get_device_type()
        return dt != ResponsiveHelper.MOBILE

    @staticmethod
    def get_window_size(device_type: str = None) -> Tuple[int, int]:
        # Gets size
        """Get recommended window size."""
        return ResponsiveHelper._lookup(device_type, {
            ResponsiveHelper.MOBILE: (360, 640), ResponsiveHelper.TABLET: (768, 1024),
            ResponsiveHelper.DESKTOP: (1100, 700), ResponsiveHelper.LARGE: (1400, 900),
            ResponsiveHelper.XLARGE: (1920, 1080),
        }, (1100, 700))

    @staticmethod
    def get_spacing(device_type: str = None) -> int:
        # Gets spacing
        """Get spacing for layouts."""
        return ResponsiveHelper._lookup(device_type, {
            ResponsiveHelper.MOBILE: 8, ResponsiveHelper.TABLET: 10,
            ResponsiveHelper.DESKTOP: 12, ResponsiveHelper.LARGE: 14,
            ResponsiveHelper.XLARGE: 16,
        }, 12)

    @staticmethod
    def get_margins(device_type: str = None) -> Tuple[int, int, int, int]:
        # Gets margins
        """Get margins for layouts (left, top, right, bottom)."""
        return ResponsiveHelper._lookup(device_type, {
            ResponsiveHelper.MOBILE: (8, 8, 8, 8), ResponsiveHelper.TABLET: (10, 10, 10, 10),
            ResponsiveHelper.DESKTOP: (12, 12, 12, 12), ResponsiveHelper.LARGE: (16, 16, 16, 16),
            ResponsiveHelper.XLARGE: (20, 20, 20, 20),
        }, (12, 12, 12, 12))


class ResponsiveWidget(QWidget):
    """Base widget with responsive capabilities."""

    def __init__(self, parent=None):
        # Initializes object
        super().__init__(parent)
        self.device_type = ResponsiveHelper.get_device_type()

    def resizeEvent(self, event):
        # Resizeevent data
        """Handle resize events."""
        super().resizeEvent(event)
        new_device_type = ResponsiveHelper.get_device_type(self.width())
        if new_device_type != self.device_type:
            self.device_type = new_device_type
            self._on_device_type_changed()

    def _on_device_type_changed(self):
        # On changed
        """Called when device type changes. Override in subclasses."""
        pass

    def get_responsive_size(self, base_size: int) -> int:
        # Gets size
        return ResponsiveHelper.get_responsive_size(base_size, self.device_type)

    def get_responsive_font_size(self, base_size: int) -> int:
        # Gets size
        return ResponsiveHelper.get_responsive_font_size(base_size, self.device_type)

    def get_column_count(self) -> int:
        # Gets count
        return ResponsiveHelper.get_column_count(self.device_type)

    def should_show_sidebar(self) -> bool:
        # Should sidebar
        return ResponsiveHelper.should_show_sidebar(self.device_type)
