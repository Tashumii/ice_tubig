"""
Animated Pie Chart Widget with hover tooltips for PyQt6.
"""
from typing import List, Tuple, Optional
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PyQt6.QtWidgets import QWidget, QToolTip
import math


class AnimatedPieChart(QWidget):
    """Interactive pie chart with animations and hover tooltips."""
    
    def __init__(self, tokens: dict, parent=None):
        super().__init__(parent)
        self.tokens = tokens
        self.data: List[Tuple[str, float, str]] = []  # (label, value, color)
        self.total = 0.0
        self.animation_progress = 0.0
        self.hovered_segment = -1
        self.segment_angles: List[Tuple[float, float]] = []  # (start_angle, span_angle)
        
        self.setMinimumSize(300, 300)
        self.setMouseTracking(True)
        
        # Animation
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animate_step)
        
    def set_data(self, data: List[Tuple[str, float, str]]):
        """
        Set chart data and trigger animation.
        
        Args:
            data: List of (label, value, color_hex) tuples
        """
        self.data = data
        self.total = sum(value for _, value, _ in data)
        self.animation_progress = 0.0
        self.hovered_segment = -1
        self._calculate_angles()
        
        # Start animation
        self.animation_timer.start(16)  # ~60 FPS
        
    def _calculate_angles(self):
        """Calculate start and span angles for each segment."""
        self.segment_angles = []
        current_angle = 90.0  # Start at top
        
        for label, value, color in self.data:
            if self.total > 0:
                span = (value / self.total) * 360.0
            else:
                span = 0.0
            self.segment_angles.append((current_angle, span))
            current_angle += span
    
    def _animate_step(self):
        """Animation step for smooth chart rendering."""
        self.animation_progress += 0.05
        if self.animation_progress >= 1.0:
            self.animation_progress = 1.0
            self.animation_timer.stop()
        self.update()
    
    def paintEvent(self, event):
        """Draw the pie chart with animations."""
        if not self.data or self.total <= 0:
            self._draw_empty_state()
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate chart area
        size = min(self.width(), self.height()) - 60
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2
        
        # Draw segments
        for i, ((label, value, color), (start_angle, span_angle)) in enumerate(zip(self.data, self.segment_angles)):
            # Apply animation
            animated_span = span_angle * self.animation_progress
            
            # Expand hovered segment
            offset = 0
            segment_size = size
            if i == self.hovered_segment:
                offset = 10
                segment_size = size + 5
            
            # Calculate offset position
            mid_angle = math.radians(start_angle + animated_span / 2)
            offset_x = int(offset * math.cos(mid_angle))
            offset_y = int(-offset * math.sin(mid_angle))
            
            # Draw segment
            painter.setBrush(QColor(color))
            painter.setPen(QPen(QColor(self.tokens.get('bg_base', '#0B0A09')), 2))
            
            rect = QRect(x + offset_x, y + offset_y, segment_size, segment_size)
            painter.drawPie(rect, int(start_angle * 16), int(animated_span * 16))
        
        # Draw center circle (donut style)
        center_size = int(size * 0.5)
        center_x = x + (size - center_size) // 2
        center_y = y + (size - center_size) // 2
        painter.setBrush(QColor(self.tokens.get('bg_surface', '#151311')))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center_x, center_y, center_size, center_size)
        
        # Draw center text
        painter.setPen(QColor(self.tokens.get('text_primary', '#F7F1E8')))
        font = QFont(self.tokens.get('font_family', 'Sans Serif'), 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRect(center_x, center_y, center_size, center_size), 
                        Qt.AlignmentFlag.AlignCenter, f"{int(self.total)}\nTotal")
        
        # Draw legend
        self._draw_legend(painter)
    
    def _draw_legend(self, painter: QPainter):
        """Draw chart legend."""
        legend_x = 10
        legend_y = self.height() - 20 - (len(self.data) * 25)
        
        painter.setFont(QFont(self.tokens.get('font_family', 'Sans Serif'), 10))
        
        for i, (label, value, color) in enumerate(self.data):
            y = legend_y + (i * 25)
            
            # Color box
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(legend_x, y, 15, 15, 3, 3)
            
            # Label and value
            painter.setPen(QColor(self.tokens.get('text_secondary', '#C8BFB2')))
            percentage = (value / self.total * 100) if self.total > 0 else 0
            text = f"{label}: {int(value)} ({percentage:.1f}%)"
            painter.drawText(legend_x + 20, y + 12, text)
    
    def _draw_empty_state(self):
        """Draw empty state when no data."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setPen(QColor(self.tokens.get('text_muted', '#8A8177')))
        painter.setFont(QFont(self.tokens.get('font_family', 'Sans Serif'), 12))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data available")
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement for hover effects."""
        if not self.data or self.total <= 0:
            return
        
        # Calculate chart center
        size = min(self.width(), self.height()) - 60
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Get mouse position relative to center
        dx = event.pos().x() - center_x
        dy = event.pos().y() - center_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Check if mouse is within chart area
        outer_radius = size / 2
        inner_radius = size / 4
        
        if distance < inner_radius or distance > outer_radius:
            if self.hovered_segment != -1:
                self.hovered_segment = -1
                self.update()
                QToolTip.hideText()
            return
        
        # Calculate angle
        angle = math.degrees(math.atan2(-dy, dx))
        if angle < 0:
            angle += 360
        
        # Normalize to start from top (90 degrees)
        angle = (90 - angle) % 360
        
        # Find which segment is hovered
        old_hovered = self.hovered_segment
        self.hovered_segment = -1
        
        for i, (start_angle, span_angle) in enumerate(self.segment_angles):
            end_angle = (start_angle + span_angle) % 360
            
            # Handle wrap-around
            if start_angle <= end_angle:
                if start_angle <= angle <= end_angle:
                    self.hovered_segment = i
                    break
            else:
                if angle >= start_angle or angle <= end_angle:
                    self.hovered_segment = i
                    break
        
        # Update if hover changed
        if old_hovered != self.hovered_segment:
            self.update()
            
            # Show tooltip
            if self.hovered_segment >= 0:
                label, value, _ = self.data[self.hovered_segment]
                percentage = (value / self.total * 100) if self.total > 0 else 0
                tooltip = f"<b>{label}</b><br/>Value: {int(value)}<br/>Percentage: {percentage:.1f}%"
                QToolTip.showText(event.globalPosition().toPoint(), tooltip, self)
            else:
                QToolTip.hideText()
    
    def leaveEvent(self, event):
        """Handle mouse leave."""
        if self.hovered_segment != -1:
            self.hovered_segment = -1
            self.update()
            QToolTip.hideText()
