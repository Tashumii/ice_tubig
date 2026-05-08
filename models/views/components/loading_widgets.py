"""
Animated loading spinner and progress indicators.
"""
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtWidgets import QWidget
import math


class LoadingSpinner(QWidget):
    """Animated circular loading spinner."""
    
    def __init__(self, tokens: dict, size: int = 40, parent=None):
        super().__init__(parent)
        self.tokens = tokens
        self.size = size
        self.angle = 0
        self.setFixedSize(size, size)
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate)
        
    def start(self):
        """Start the spinner animation."""
        self.timer.start(30)  # ~33 FPS
        self.show()
    
    def stop(self):
        """Stop the spinner animation."""
        self.timer.stop()
        self.hide()
    
    def _rotate(self):
        """Rotate the spinner."""
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """Draw the spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw spinning arc
        color = QColor(self.tokens.get('accent_1', '#64B8E0'))
        pen = QPen(color, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        rect = QRectF(3, 3, self.size - 6, self.size - 6)
        painter.drawArc(rect, self.angle * 16, 120 * 16)


class PulsingDot(QWidget):
    """Pulsing dot indicator."""
    
    def __init__(self, tokens: dict, size: int = 12, parent=None):
        super().__init__(parent)
        self.tokens = tokens
        self.size = size
        self.scale = 1.0
        self.growing = True
        self.setFixedSize(size * 2, size * 2)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._pulse)
    
    def start(self):
        """Start pulsing."""
        self.timer.start(50)
        self.show()
    
    def stop(self):
        """Stop pulsing."""
        self.timer.stop()
        self.hide()
    
    def _pulse(self):
        """Pulse animation step."""
        if self.growing:
            self.scale += 0.05
            if self.scale >= 1.3:
                self.growing = False
        else:
            self.scale -= 0.05
            if self.scale <= 0.7:
                self.growing = True
        self.update()
    
    def paintEvent(self, event):
        """Draw the pulsing dot."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color = QColor(self.tokens.get('success', '#7EDC98'))
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        center = self.width() // 2
        radius = int(self.size * self.scale / 2)
        painter.drawEllipse(center - radius, center - radius, radius * 2, radius * 2)


class ProgressBar(QWidget):
    """Animated progress bar."""
    
    def __init__(self, tokens: dict, parent=None):
        super().__init__(parent)
        self.tokens = tokens
        self.progress = 0.0
        self.target_progress = 0.0
        self.setMinimumHeight(6)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
    
    def set_progress(self, value: float):
        """Set progress (0.0 to 1.0)."""
        self.target_progress = max(0.0, min(1.0, value))
        if not self.timer.isActive():
            self.timer.start(16)
    
    def _animate(self):
        """Animate progress smoothly."""
        diff = self.target_progress - self.progress
        if abs(diff) < 0.01:
            self.progress = self.target_progress
            self.timer.stop()
        else:
            self.progress += diff * 0.2
        self.update()
    
    def paintEvent(self, event):
        """Draw the progress bar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        bg_color = QColor(self.tokens.get('bg_elevated', '#1E1B18'))
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 3, 3)
        
        # Progress
        if self.progress > 0:
            progress_color = QColor(self.tokens.get('accent_1', '#64B8E0'))
            painter.setBrush(progress_color)
            progress_width = int(self.width() * self.progress)
            painter.drawRoundedRect(0, 0, progress_width, self.height(), 3, 3)
