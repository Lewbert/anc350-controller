"""Parameter control panel — amplitude, DC voltage, frequency per axis."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit,
)

from app.config import (
    Axis, AMPLITUDE_MIN, AMPLITUDE_MAX, DC_VOLTAGE_MIN, DC_VOLTAGE_MAX,
    FREQUENCY_MIN, FREQUENCY_MAX,
)

_PARAM_AMP = "amplitude"
_PARAM_DC  = "dc_voltage"
_PARAM_FREQ = "frequency"


class ParamPanel(QGroupBox):
    """Textbox controls for amplitude, DC voltage, and frequency per axis."""

    amplitude_changed = pyqtSignal(Axis, float)
    frequency_changed = pyqtSignal(Axis, float)
    dc_voltage_changed = pyqtSignal(Axis, float)

    def __init__(self, parent=None):
        super().__init__("Drive Parameters", parent)

        layout = QVBoxLayout(self)

        self._tabs = QTabWidget()
        self._inputs = {}  # axis -> {param_key: QLineEdit}

        param_specs = [
            (_PARAM_AMP,  "Amplitude (V)",   AMPLITUDE_MIN, AMPLITUDE_MAX, self.amplitude_changed),
            (_PARAM_DC,   "DC Voltage (V)",  DC_VOLTAGE_MIN, DC_VOLTAGE_MAX, self.dc_voltage_changed),
            (_PARAM_FREQ, "Frequency (Hz)",  FREQUENCY_MIN, FREQUENCY_MAX,  self.frequency_changed),
        ]

        for axis in (Axis.X, Axis.Y, Axis.Z):
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            self._inputs[axis] = {}

            for key, name, vmin, vmax, signal in param_specs:
                row, edit = self._make_param_row(name, vmin, vmax, axis, signal)
                tab_layout.addLayout(row)
                self._inputs[axis][key] = edit

            tab_layout.addStretch()
            self._tabs.addTab(tab, axis.name)

        layout.addWidget(self._tabs)

    def _make_param_row(self, name, vmin, vmax, axis, signal):
        row = QHBoxLayout()

        label = QLabel(name)
        label.setFixedWidth(110)
        row.addWidget(label)

        decimals = 1 if vmax <= 60 else 0
        validator = QDoubleValidator(vmin, vmax, decimals)

        edit = QLineEdit(str(vmin))
        edit.setValidator(validator)
        edit.setFixedWidth(80)
        edit.editingFinished.connect(
            lambda ed=edit, ax=axis, sig=signal, lo=vmin, hi=vmax: self._on_edit(ed, ax, sig, lo, hi))

        row.addWidget(edit)
        row.addStretch()
        return row, edit

    def _on_edit(self, edit, axis, signal, vmin, vmax):
        try:
            val = float(edit.text())
        except ValueError:
            val = vmin
        val = max(vmin, min(val, vmax))
        if key := next((k for k, v in self._inputs.get(axis, {}).items() if v is edit), None):
            decimals = 0 if key == _PARAM_FREQ else 1
            edit.setText(f"{val:.{decimals}f}")
        signal.emit(axis, val)

    def set_values(self, axis: Axis, amplitude: float, frequency: float, dc_voltage: float = 0.0):
        """Set displayed values without emitting signals (called on connect)."""
        inputs = self._inputs.get(axis, {})
        for key, val in [(_PARAM_AMP, amplitude), (_PARAM_FREQ, frequency), (_PARAM_DC, dc_voltage)]:
            edit = inputs.get(key)
            if edit:
                edit.blockSignals(True)
                edit.setText(f"{val:.1f}" if key != _PARAM_FREQ else f"{val:.0f}")
                edit.blockSignals(False)
