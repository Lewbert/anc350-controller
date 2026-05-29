"""Main application window — assembles all widgets and wires signals."""

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter,
    QMenuBar, QAction, QPushButton,
)

from anc350 import Positioner, ANC350Error

from app.config import Axis, RECONNECT_SCAN_MS, AppSettings
from app.xy_widget import XYWidget
from app.position_display import PositionDisplay, VelocityDisplay
from app.param_panel import ParamPanel
from app.settings_dialog import SettingsDialog
from app.device_panel import DevicePanel
from app.controller_thread import ControllerThread
from app.stage_controller import StageController


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._pos = Positioner()
        self._devices = []  # list of (devNo, label) for dropdown

        self.setWindowTitle("ANC350 Stage Controller")
        self.resize(900, 600)

        self._setup_menu()

        # Central area
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(4)

        splitter = QSplitter(Qt.Horizontal)

        # Left: XY widget
        self._xy_widget = XYWidget(settings)
        splitter.addWidget(self._xy_widget)

        # Right: position + parameters
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._pos_display = PositionDisplay()
        right_layout.addWidget(self._pos_display)

        self._vel_display = VelocityDisplay()
        right_layout.addWidget(self._vel_display)

        self._param_panel = ParamPanel()
        right_layout.addWidget(self._param_panel)

        settings_btn = QPushButton("Stage Settings...")
        settings_btn.clicked.connect(self._open_range_settings)
        right_layout.addWidget(settings_btn)
        right_layout.addStretch()

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter)

        # Bottom: device status (fixed height)
        self._device_panel = DevicePanel()
        self._device_panel.setFixedHeight(40)
        root_layout.addWidget(self._device_panel)

        # Stage controller
        self._stage = StageController(self._pos, settings, self)
        self._stage.position_updated.connect(self._pos_display.update_position)
        self._stage.position_updated.connect(
            lambda x, y, z: self._xy_widget.update_position(x, y))
        self._stage.velocity_updated.connect(
            lambda vx, vy, vz: self._vel_display.update_velocity(vx, vy))
        self._stage.axes_enabled_changed.connect(self._pos_display.set_axes_enabled)
        self._stage.axes_enabled_changed.connect(self._vel_display.set_axes_enabled)
        self._stage.params_loaded.connect(self._on_params_loaded)

        # Controller thread
        self._controller_thread = ControllerThread(self)
        self._controller_thread.joystick_moved.connect(self._stage.on_joystick)
        self._controller_thread.trigger_value.connect(self._stage.on_trigger)
        self._controller_thread.dpad_direction.connect(self._stage.on_dpad)
        self._controller_thread.button_a_state.connect(self._stage.on_button_a)
        self._controller_thread.button_b_state.connect(self._stage.on_button_b)
        self._controller_thread.button_menu_state.connect(self._stage.on_menu)
        self._controller_thread.gamepad_connected.connect(
            self._device_panel.set_gamepad_connected)
        self._controller_thread.gamepad_disconnected.connect(
            self._device_panel.set_gamepad_disconnected)
        self._controller_thread.start()

        # Param panel signals
        self._param_panel.amplitude_changed.connect(self._stage.set_amplitude)
        self._param_panel.frequency_changed.connect(self._stage.set_frequency)
        self._param_panel.dc_voltage_changed.connect(self._stage.set_dc_voltage)

        # Device panel
        self._device_panel._reconnect_btn.clicked.connect(self._scan_anc350)
        self._device_panel._anc_combo.currentIndexChanged.connect(self._on_device_changed)

        # Reconnection timer
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setInterval(RECONNECT_SCAN_MS)
        self._reconnect_timer.timeout.connect(self._scan_anc350)
        self._reconnect_timer.start()

        # Initial scan
        self._scan_anc350()

    # --- Menu -----------------------------------------------------------------

    def _setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        range_action = QAction("Stage Settings...", self)
        range_action.triggered.connect(self._open_range_settings)
        file_menu.addAction(range_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    # --- ANC350 device management ----------------------------------------------

    def _scan_anc350(self):
        """Scan for ANC350 devices and auto-connect if found."""
        if self._pos.connected:
            # Check connection health
            try:
                self._pos.getFirmwareVersion()
                return
            except ANC350Error:
                self._pos.disconnect()
                self._on_anc_disconnected()

        try:
            count = self._pos.discover()
        except Exception:
            return

        if count == 0:
            self._on_anc_disconnected()
            return

        # Build device list
        self._devices = []
        for i in range(count):
            try:
                _, _, serial, address, _ = self._pos.getDeviceInfo(i)
                label = f"{serial} ({address})" if serial else f"Device {i} ({address})"
                self._devices.append((i, label))
            except Exception:
                self._devices.append((i, f"Device {i}"))

        # Auto-connect to first device
        self._connect_to(0)

    def _connect_to(self, dev_no: int):
        try:
            self._pos.connect(dev_no)
            self._device_panel.set_anc_connected(
                self._devices[dev_no][1] if dev_no < len(self._devices) else f"Device {dev_no}",
                self._devices
            )
            self._stage.on_connected()
        except Exception:
            self._on_anc_disconnected()

    def _on_anc_disconnected(self):
        self._stage.on_disconnected()
        self._device_panel.set_anc_disconnected()

    def _on_device_changed(self, idx: int):
        if idx < 0:
            return
        dev_no = self._device_panel._anc_combo.itemData(idx)
        if dev_no is not None:
            self._pos.disconnect()
            self._connect_to(dev_no)

    # --- Parameter handling ----------------------------------------------------

    def _on_params_loaded(self, params: dict):
        """Display device parameters after connection."""
        for axis, values in params.items():
            dc = self._stage.get_dc_voltage(axis)
            self._param_panel.set_values(axis, values['amplitude'], values['frequency'], dc)

    def _open_range_settings(self):
        dialog = SettingsDialog(self._settings, self)
        dialog.exec_()

    # --- Shutdown --------------------------------------------------------------

    def closeEvent(self, event):
        self._controller_thread.stop()
        self._controller_thread.wait(2000)
        try:
            if self._pos.connected:
                for ax in (Axis.X, Axis.Y, Axis.Z):
                    self._pos.disable_axis(ax)
                self._pos.disconnect()
        except Exception:
            pass
        super().closeEvent(event)
