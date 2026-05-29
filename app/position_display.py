"""XYZ position readout panel."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGroupBox, QFormLayout, QLabel

from app.config import Axis

_ENABLED_COLOR = "#228B22"
_DISABLED_COLOR = "#808080"

_STYLE = "font-family: Consolas, monospace; font-size: 14px;"


class PositionDisplay(QGroupBox):
    """Shows current XYZ coordinates in µm."""

    def __init__(self, parent=None):
        super().__init__("Position", parent)

        layout = QFormLayout(self)

        self._labels = {}
        for axis in (Axis.X, Axis.Y, Axis.Z):
            label = QLabel("0.0 µm")
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setStyleSheet(f"{_STYLE}color: {_ENABLED_COLOR};")
            layout.addRow(f"{axis.name}:", label)
            self._labels[axis] = label

    def update_position(self, x_um: float, y_um: float, z_um: float):
        self._labels[Axis.X].setText(f"{x_um:.1f} µm")
        self._labels[Axis.Y].setText(f"{y_um:.1f} µm")
        self._labels[Axis.Z].setText(f"{z_um:.1f} µm")

    def set_axes_enabled(self, enabled: bool):
        color = _ENABLED_COLOR if enabled else _DISABLED_COLOR
        for label in self._labels.values():
            label.setStyleSheet(f"{_STYLE}color: {color};")


class VelocityDisplay(QGroupBox):
    """Shows current XY velocity in µm/s."""

    def __init__(self, parent=None):
        super().__init__("Velocity", parent)

        layout = QFormLayout(self)

        self._labels = {}
        for axis in (Axis.X, Axis.Y):
            label = QLabel("0.0 µm/s")
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setStyleSheet(f"{_STYLE}color: {_ENABLED_COLOR};")
            layout.addRow(f"{axis.name}:", label)
            self._labels[axis] = label

    def update_velocity(self, vx: float, vy: float):
        self._labels[Axis.X].setText(f"{vx:.1f} µm/s")
        self._labels[Axis.Y].setText(f"{vy:.1f} µm/s")

    def set_axes_enabled(self, enabled: bool):
        color = _ENABLED_COLOR if enabled else _DISABLED_COLOR
        for label in self._labels.values():
            label.setStyleSheet(f"{_STYLE}color: {color};")
