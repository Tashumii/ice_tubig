from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QObject, QPropertyAnimation, Qt, QParallelAnimationGroup, QPoint
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QStackedWidget, QWidget


class ElevationController(QObject):
    """Adds subtle hover elevation to a widget using native shadow animation."""

    def __init__(
        self,
        widget: QWidget,
        rest_blur: float = 10.0,
        hover_blur: float = 16.0,
        rest_y: float = 1.0,
        hover_y: float = 3.0,
        alpha: int = 28,
        duration_ms: int = 180,
    ):
        # Initializes object
        super().__init__(widget)
        self.widget = widget
        self.rest_blur = rest_blur
        self.hover_blur = hover_blur
        self.rest_y = rest_y
        self.hover_y = hover_y

        effect = QGraphicsDropShadowEffect(widget)
        effect.setColor(QColor(0, 0, 0, alpha))
        effect.setBlurRadius(rest_blur)
        effect.setOffset(0.0, rest_y)
        widget.setGraphicsEffect(effect)
        self.effect = effect

        self.blur_anim = QPropertyAnimation(self.effect, b"blurRadius", self)
        self.blur_anim.setDuration(duration_ms)
        self.blur_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.offset_anim = QPropertyAnimation(self.effect, b"yOffset", self)
        self.offset_anim.setDuration(duration_ms)
        self.offset_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        widget.installEventFilter(self)

    def _animate(self, blur_target: float, y_target: float):
        # Animate data
        self.blur_anim.stop()
        self.offset_anim.stop()
        self.blur_anim.setStartValue(self.effect.blurRadius())
        self.blur_anim.setEndValue(blur_target)
        self.offset_anim.setStartValue(self.effect.yOffset())
        self.offset_anim.setEndValue(y_target)
        self.blur_anim.start()
        self.offset_anim.start()

    def eventFilter(self, watched, event):
        # Eventfilter data
        if watched is self.widget:
            etype = event.type()
            if etype in (event.Type.Enter, event.Type.HoverEnter):
                self._animate(self.hover_blur, self.hover_y)
            elif etype in (event.Type.Leave, event.Type.HoverLeave):
                self._animate(self.rest_blur, self.rest_y)
        return super().eventFilter(watched, event)


def apply_card_polish(root: QWidget):
    # Apply polish
    """Apply subtle elevation to structural surfaces."""
    targets = [root] + root.findChildren(QFrame)
    root._elevation_refs = getattr(root, "_elevation_refs", [])
    for widget in targets:
        if not isinstance(widget, QFrame):
            continue
        if widget.property("card"):
            root._elevation_refs.append(ElevationController(widget, rest_blur=10, hover_blur=16, rest_y=1, hover_y=3, alpha=28))
        elif widget.property("panel"):
            root._elevation_refs.append(ElevationController(widget, rest_blur=6, hover_blur=10, rest_y=1, hover_y=2, alpha=22))
        elif widget.property("shell") or widget.property("topbar"):
            root._elevation_refs.append(ElevationController(widget, rest_blur=8, hover_blur=12, rest_y=1, hover_y=2, alpha=24))


class ButtonPressAnimation(QObject):
    """Add press animation to buttons."""
    
    def __init__(self, button):
        # Initializes object
        super().__init__(button)
        self.button = button
        self.original_style = button.styleSheet()
        button.installEventFilter(self)
    
    def eventFilter(self, watched, event):
        # Eventfilter data
        if watched is self.button:
            if event.type() == event.Type.MouseButtonPress:
                self.button.setStyleSheet(self.original_style + " QPushButton { transform: scale(0.95); }")
            elif event.type() == event.Type.MouseButtonRelease:
                self.button.setStyleSheet(self.original_style)
        return super().eventFilter(watched, event)


class FadeStackedWidget(QStackedWidget):
    """QStackedWidget with smooth fade and slide transition."""

    def __init__(self, *args, **kwargs):
        # Initializes object
        super().__init__(*args, **kwargs)
        self._anim_refs = []
        self._previous_index = 0

    def switch_to(self, widget: QWidget, duration_ms: int = 300):
        # Switch to
        """Switch to widget with fade and slide animation."""
        if widget is None or widget is self.currentWidget():
            return

        # Get current and new index
        new_index = self.indexOf(widget)
        if new_index == -1:
            return
        
        old_widget = self.currentWidget()
        direction = 1 if new_index > self._previous_index else -1
        self._previous_index = new_index

        # Set up new widget
        self.setCurrentWidget(widget)
        
        # Create opacity effect for fade
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0.0)

        # Create animations
        fade_anim = QPropertyAnimation(opacity_effect, b"opacity", self)
        fade_anim.setDuration(duration_ms)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _cleanup():
            # Cleanup data
            widget.setGraphicsEffect(None)
            if fade_anim in self._anim_refs:
                self._anim_refs.remove(fade_anim)

        fade_anim.finished.connect(_cleanup)
        self._anim_refs.append(fade_anim)
        fade_anim.start()
