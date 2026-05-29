"""Dialog for configuring all stage settings."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox,
    QLineEdit, QCheckBox, QLabel, QFrame,
)

from app.config import Axis


class SettingsDialog(QDialog):
    """Modal dialog to edit range limits, speeds, inversion, and diagram flip."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stage Settings")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._settings = settings

        layout = QVBoxLayout(self)
        float_validator = QDoubleValidator(-100000.0, 100000.0, 6)
        speed_validator = QDoubleValidator(0.1, 2000.0, 1)

        # --- Range limits ---
        layout.addWidget(QLabel("Range Limits"))
        range_form = QFormLayout()
        self._range_inputs = {}

        for axis in (Axis.X, Axis.Y, Axis.Z):
            lo, hi = settings.get_range(axis)
            lo_edit = QLineEdit(str(lo))
            lo_edit.setValidator(float_validator)
            hi_edit = QLineEdit(str(hi))
            hi_edit.setValidator(float_validator)
            range_form.addRow(f"{axis.name} Min (µm):", lo_edit)
            range_form.addRow(f"{axis.name} Max (µm):", hi_edit)
            self._range_inputs[axis] = (lo_edit, hi_edit)

        layout.addLayout(range_form)

        # --- Speed ---
        line_s = QFrame()
        line_s.setFrameShape(QFrame.HLine)
        line_s.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line_s)
        layout.addWidget(QLabel("Movement Speed"))

        speed_form = QFormLayout()
        self._slow_edit = QLineEdit(str(settings.get_slow_speed()))
        self._slow_edit.setValidator(speed_validator)
        speed_form.addRow("Slow speed (µm/s):", self._slow_edit)

        self._fast_edit = QLineEdit(str(settings.get_fast_speed()))
        self._fast_edit.setValidator(speed_validator)
        speed_form.addRow("Fast speed (µm/s):", self._fast_edit)
        layout.addLayout(speed_form)

        # --- Axis inversion ---
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1)
        layout.addWidget(QLabel("Axis Inversion"))
        invert_form = QFormLayout()
        self._invert_boxes = {}

        for axis in (Axis.X, Axis.Y, Axis.Z):
            cb = QCheckBox(f"Invert {axis.name} axis")
            cb.setChecked(settings.get_inverted(axis))
            invert_form.addRow(cb)
            self._invert_boxes[axis] = cb

        layout.addLayout(invert_form)

        # --- Diagram flip ---
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)
        layout.addWidget(QLabel("Diagram Display"))
        flip_form = QFormLayout()
        self._flip_x_cb = QCheckBox("Flip X direction")
        self._flip_x_cb.setChecked(settings.get_flip_x())
        flip_form.addRow(self._flip_x_cb)
        self._flip_y_cb = QCheckBox("Flip Y direction")
        self._flip_y_cb.setChecked(settings.get_flip_y())
        flip_form.addRow(self._flip_y_cb)
        layout.addLayout(flip_form)

        # --- Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        for axis in (Axis.X, Axis.Y, Axis.Z):
            lo_edit, hi_edit = self._range_inputs[axis]
            try:
                lo = max(-100000.0, min(100000.0, float(lo_edit.text())))
                hi = max(-100000.0, min(100000.0, float(hi_edit.text())))
            except ValueError:
                return
            if lo >= hi:
                return
            lo_edit.setText(f"{lo:.1f}")
            hi_edit.setText(f"{hi:.1f}")
            self._settings.set_range(axis, lo, hi)
            self._settings.set_inverted(axis, self._invert_boxes[axis].isChecked())

        try:
            slow = max(0.1, min(2000.0, float(self._slow_edit.text())))
            fast = max(0.1, min(2000.0, float(self._fast_edit.text())))
        except ValueError:
            return
        self._slow_edit.setText(f"{slow:.1f}")
        self._fast_edit.setText(f"{fast:.1f}")
        self._settings.set_slow_speed(slow)
        self._settings.set_fast_speed(fast)

        self._settings.set_flip_x(self._flip_x_cb.isChecked())
        self._settings.set_flip_y(self._flip_y_cb.isChecked())
        self._settings.save()
        self.accept()
