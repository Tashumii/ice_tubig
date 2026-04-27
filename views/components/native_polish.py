from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QObject, QPropertyAnimation, Qt
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
        self.blur_anim.stop()
        self.offset_anim.stop()
        self.blur_anim.setStartValue(self.effect.blurRadius())
        self.blur_anim.setEndValue(blur_target)
        self.offset_anim.setStartValue(self.effect.yOffset())
        self.offset_anim.setEndValue(y_target)
        self.blur_anim.start()
        self.offset_anim.start()

    def eventFilter(self, watched, event):
        if watched is self.widget:
            etype = event.type()
            if etype in (event.Type.Enter, event.Type.HoverEnter):
                self._animate(self.hover_blur, self.hover_y)
            elif etype in (event.Type.Leave, event.Type.HoverLeave):
                self._animate(self.rest_blur, self.rest_y)
        return super().eventFilter(watched, event)


def apply_card_polish(root: QWidget):
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


class FadeStackedWidget(QStackedWidget):
    """QStackedWidget with lightweight fade transition."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._anim_refs = []

    def switch_to(self, widget: QWidget, duration_ms: int = 180):
        if widget is None or widget is self.currentWidget():
            return

        self.setCurrentWidget(widget)
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(duration_ms)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def _cleanup():
            widget.setGraphicsEffect(None)
            if anim in self._anim_refs:
                self._anim_refs.remove(anim)

        anim.finished.connect(_cleanup)
        self._anim_refs.append(anim)
        anim.start()
