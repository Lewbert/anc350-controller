"""Device status panel — shows ANC350 and gamepad connection state."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QPushButton,
)

_GREEN = "#228B22"
_RED   = "#CC0000"
_GRAY  = "#808080"


class DevicePanel(QWidget):
    """Bottom bar showing connection status for ANC350 and game controller."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        # ANC350 side
        self._anc_led = QLabel("●")
        self._anc_led.setStyleSheet(f"color: {_RED}; font-size: 14px;")
        self._anc_label = QLabel("ANC350: No device")
        self._anc_label.setStyleSheet(f"color: {_GRAY};")
        self._anc_combo = QComboBox()
        self._anc_combo.setEnabled(False)
        self._anc_combo.setMinimumWidth(180)
        self._anc_combo.setVisible(False)
        self._reconnect_btn = QPushButton("Scan")
        self._reconnect_btn.setFixedWidth(50)

        layout.addWidget(self._anc_led)
        layout.addWidget(self._anc_label)
        layout.addWidget(self._anc_combo)
        layout.addWidget(self._reconnect_btn)

        layout.addSpacing(30)

        # Gamepad side
        self._pad_led = QLabel("●")
        self._pad_led.setStyleSheet(f"color: {_RED}; font-size: 14px;")
        self._pad_label = QLabel("Gamepad: No controller")
        self._pad_label.setStyleSheet(f"color: {_GRAY};")
        layout.addWidget(self._pad_led)
        layout.addWidget(self._pad_label)

        layout.addStretch()

    def set_anc_connected(self, name: str, devices: list = None):
        """Show ANC350 as connected. `devices` is a list of (index, label) for the dropdown."""
        self._anc_led.setStyleSheet(f"color: {_GREEN}; font-size: 14px;")
        self._anc_label.setStyleSheet(f"color: {_GREEN};")
        self._anc_label.setText(f"ANC350: {name}")

        if devices and len(devices) > 1:
            self._anc_combo.clear()
            for idx, label in devices:
                self._anc_combo.addItem(label, idx)
            self._anc_combo.setVisible(True)
        else:
            self._anc_combo.setVisible(False)

    def set_anc_disconnected(self):
        self._anc_led.setStyleSheet(f"color: {_RED}; font-size: 14px;")
        self._anc_label.setStyleSheet(f"color: {_GRAY};")
        self._anc_label.setText("ANC350: No device")
        self._anc_combo.clear()
        self._anc_combo.setVisible(False)

    def set_gamepad_connected(self, name: str):
        self._pad_led.setStyleSheet(f"color: {_GREEN}; font-size: 14px;")
        self._pad_label.setStyleSheet(f"color: {_GREEN};")
        self._pad_label.setText(f"Gamepad: {name}")

    def set_gamepad_disconnected(self):
        self._pad_led.setStyleSheet(f"color: {_RED}; font-size: 14px;")
        self._pad_label.setStyleSheet(f"color: {_GRAY};")
        self._pad_label.setText("Gamepad: No controller")
