"""XY position visualization using pyqtgraph."""

import pyqtgraph as pg
from PyQt5.QtWidgets import QGraphicsRectItem

from app.config import Axis


class XYWidget(pg.PlotWidget):
    """2D plot showing the virtual target position as a red dot.

    A light rectangle outlines the configured available area. Aspect ratio is
    locked to real-world X/Y proportions. The full rectangle is always visible,
    centered in the view with empty space on one axis when the widget shape
    doesn't match the data proportions.
    """

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings

        self.setLabel('bottom', 'X position', units='µm')
        self.setLabel('left', 'Y position', units='µm')
        self.showGrid(x=True, y=True, alpha=0.3)
        self.setBackground('w')

        self.setMouseEnabled(x=False, y=False)
        self.setMenuEnabled(False)
        self.hideButtons()

        # Light rectangle showing the available XY area
        self._area_rect = QGraphicsRectItem()
        self._area_rect.setPen(pg.mkPen(color=(150, 150, 150), width=1))
        self._area_rect.setBrush(pg.mkBrush(color=(200, 220, 240, 100)))
        self.addItem(self._area_rect)

        # Red dot for current position
        self._dot = self.plot([0], [0], pen=None, symbol='o',
                              symbolSize=10, symbolBrush=(255, 0, 0))

        # Trail of recent positions
        self._trail = self.plot([], [], pen=pg.mkPen(color=(200, 200, 200), width=1))
        self._history_x = []
        self._history_y = []
        self._max_history = 50

        self._apply_range()
        self._settings.range_changed.connect(self._apply_range)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_settings'):
            self._apply_range()

    def _apply_range(self):
        x_min, x_max = self._settings.get_range(Axis.X)
        y_min, y_max = self._settings.get_range(Axis.Y)
        x_span = x_max - x_min
        y_span = y_max - y_min

        if x_span <= 0 or y_span <= 0:
            return

        self._area_rect.setRect(x_min, y_min, x_span, y_span)

        vb = self.getPlotItem().vb

        # Apply diagram flip (visual only)
        vb.invertX(self._settings.get_flip_x())
        vb.invertY(self._settings.get_flip_y())

        vb.setAspectLocked(True, ratio=y_span / x_span)
        self.setXRange(x_min, x_max, padding=0)
        self.setYRange(y_min, y_max, padding=0)

    def update_position(self, x_um: float, y_um: float):
        self._dot.setData([x_um], [y_um])

        self._history_x.append(x_um)
        self._history_y.append(y_um)
        if len(self._history_x) > self._max_history:
            self._history_x.pop(0)
            self._history_y.pop(0)
        self._trail.setData(self._history_x, self._history_y)
