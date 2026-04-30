"""
Responsive layout utilities for adaptive UI scaling.
"""
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QWidget, QApplication
from typing import Tuple


class ResponsiveBreakpoints:
    """Screen size breakpoints for responsive design."""
    MOBILE = 480
    TABLET = 768
    DESKTOP = 1024
    LARGE = 1440
    XLARGE = 1920


class DeviceType:
    """Device type enumeration."""
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    LARGE = "large"
    XLARGE = "xlarge"


class ResponsiveHelper:
    """Helper class for responsive layouts."""
    
    @staticmethod
    def get_screen_size() -> QSize:
        """Get primary screen size."""
        screen = QApplication.primaryScreen()
        if screen:
            return screen.size()
        return QSize(1920, 1080)
    
    @staticmethod
    def get_device_type(width: int = None) -> str:
        """Determine device type based on width."""
        if width is None:
            width = ResponsiveHelper.get_screen_size().width()
        
        if width < ResponsiveBreakpoints.MOBILE:
            return DeviceType.MOBILE
        elif width < ResponsiveBreakpoints.TABLET:
            return DeviceType.MOBILE
        elif width < ResponsiveBreakpoints.DESKTOP:
            return DeviceType.TABLET
        elif width < ResponsiveBreakpoints.LARGE:
            return DeviceType.DESKTOP
        elif width < ResponsiveBreakpoints.XLARGE:
            return DeviceType.LARGE
        else:
            return DeviceType.XLARGE
    
    @staticmethod
    def get_responsive_size(base_size: int, device_type: str = None) -> int:
        """Scale size based on device type."""
        if device_type is None:
            device_type = ResponsiveHelper.get_device_type()
        
        scale_factors = {
            DeviceType.MOBILE: 0.7,
            DeviceType.TABLET: 0.85,
            DeviceType.DESKTOP: 1.0,
            DeviceType.LARGE: 1.15,
            DeviceType.XLARGE: 1.3,
        }
        
        return int(base_size * scale_factors.get(device_type, 1.0))
    
    @staticmethod
    def get_responsive_font_size(base_size: int, device_type: str = None) -> int:
        """Scale font size based on device type."""
        if device_type is None:
            device_type = ResponsiveHelper.get_device_type()
        
        scale_factors = {
            DeviceType.MOBILE: 0.8,
            DeviceType.TABLET: 0.9,
            DeviceType.DESKTOP: 1.0,
            DeviceType.LARGE: 1.1,
            DeviceType.XLARGE: 1.2,
        }
        
        return int(base_size * scale_factors.get(device_type, 1.0))
    
    @staticmethod
    def get_column_count(device_type: str = None) -> int:
        """Get number of columns for grid layout."""
        if device_type is None:
            device_type = ResponsiveHelper.get_device_type()
        
        columns = {
            DeviceType.MOBILE: 1,
            DeviceType.TABLET: 2,
            DeviceType.DESKTOP: 3,
            DeviceType.LARGE: 4,
            DeviceType.XLARGE: 4,
        }
        
        return columns.get(device_type, 3)
    
    @staticmethod
    def should_show_sidebar(device_type: str = None) -> bool:
        """Determine if sidebar should be shown."""
        if device_type is None:
            device_type = ResponsiveHelper.get_device_type()
        
        return device_type not in [DeviceType.MOBILE]
    
    @staticmethod
    def get_window_size(device_type: str = None) -> Tuple[int, int]:
        """Get recommended window size."""
        if device_type is None:
            device_type = ResponsiveHelper.get_device_type()
        
        sizes = {
            DeviceType.MOBILE: (360, 640),
            DeviceType.TABLET: (768, 1024),
            DeviceType.DESKTOP: (1100, 700),
            DeviceType.LARGE: (1400, 900),
            DeviceType.XLARGE: (1920, 1080),
        }
        
        return sizes.get(device_type, (1100, 700))
    
    @staticmethod
    def get_spacing(device_type: str = None) -> int:
        """Get spacing for layouts."""
        if device_type is None:
            device_type = ResponsiveHelper.get_device_type()
        
        spacing = {
            DeviceType.MOBILE: 8,
            DeviceType.TABLET: 10,
            DeviceType.DESKTOP: 12,
            DeviceType.LARGE: 14,
            DeviceType.XLARGE: 16,
        }
        
        return spacing.get(device_type, 12)
    
    @staticmethod
    def get_margins(device_type: str = None) -> Tuple[int, int, int, int]:
        """Get margins for layouts (left, top, right, bottom)."""
        if device_type is None:
            device_type = ResponsiveHelper.get_device_type()
        
        margins = {
            DeviceType.MOBILE: (8, 8, 8, 8),
            DeviceType.TABLET: (10, 10, 10, 10),
            DeviceType.DESKTOP: (12, 12, 12, 12),
            DeviceType.LARGE: (16, 16, 16, 16),
            DeviceType.XLARGE: (20, 20, 20, 20),
        }
        
        return margins.get(device_type, (12, 12, 12, 12))


class ResponsiveWidget(QWidget):
    """Base widget with responsive capabilities."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.device_type = ResponsiveHelper.get_device_type()
        self._setup_responsive()
    
    def _setup_responsive(self):
        """Setup responsive behavior."""
        pass
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        new_device_type = ResponsiveHelper.get_device_type(self.width())
        if new_device_type != self.device_type:
            self.device_type = new_device_type
            self._on_device_type_changed()
    
    def _on_device_type_changed(self):
        """Called when device type changes."""
        pass
    
    def get_responsive_size(self, base_size: int) -> int:
        """Get responsive size."""
        return ResponsiveHelper.get_responsive_size(base_size, self.device_type)
    
    def get_responsive_font_size(self, base_size: int) -> int:
        """Get responsive font size."""
        return ResponsiveHelper.get_responsive_font_size(base_size, self.device_type)
    
    def get_column_count(self) -> int:
        """Get column count for this device."""
        return ResponsiveHelper.get_column_count(self.device_type)
    
    def should_show_sidebar(self) -> bool:
        """Check if sidebar should be shown."""
        return ResponsiveHelper.should_show_sidebar(self.device_type)
