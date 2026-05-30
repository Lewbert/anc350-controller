"""Application constants and persistent settings."""

from enum import IntEnum

from PyQt5.QtCore import QObject, QSettings, pyqtSignal

# --- Axes --------------------------------------------------------------------

class Axis(IntEnum):
    X = 0
    Y = 1
    Z = 2

# --- Stage defaults ----------------------------------------------------------

DEFAULT_RANGE_MIN = 0.0     # µm
DEFAULT_RANGE_MAX = 5000.0  # µm

FREQ_XY = 1000.0  # Hz
FREQ_Z  = 500.0   # Hz

# --- Movement speeds ---------------------------------------------------------

SLOW_SPEED = 100.0   # µm/s (joystick only)
FAST_SPEED = 500.0   # µm/s (trigger + joystick)
Z_SPEED    = 100.0   # µm/s (A/B long-press closed-loop)
DEAD_ZONE  = 0.1     # fraction of full joystick range

# --- Controller --------------------------------------------------------------

LONG_PRESS_MS     = 500    # ms threshold for A/B long-press
POLL_RATE         = 20     # Hz
TRIGGER_THRESHOLD = 0.5    # fraction of trigger pull for fast mode

# --- Device reconnection -----------------------------------------------------

RECONNECT_SCAN_MS = 2000   # ms between device scans

# --- Parameter limits --------------------------------------------------------

AMPLITUDE_MIN, AMPLITUDE_MAX   = 0.0, 60.0   # V
DC_VOLTAGE_MIN, DC_VOLTAGE_MAX = 0.0, 60.0   # V
FREQUENCY_MIN, FREQUENCY_MAX   = 0.0, 2000.0  # Hz

# --- XInput button masks -----------------------------------------------------

class XButton:
    DPAD_UP    = 0x0001
    DPAD_DOWN  = 0x0002
    DPAD_LEFT  = 0x0004
    DPAD_RIGHT = 0x0008
    START      = 0x0010  # Menu button
    BACK       = 0x0020  # View button
    L_THUMB    = 0x0040
    R_THUMB    = 0x0080
    L_SHOULDER = 0x0100
    R_SHOULDER = 0x0200
    A          = 0x1000
    B          = 0x2000
    X          = 0x4000
    Y          = 0x8000

# --- Persistent settings -----------------------------------------------------

class AppSettings(QObject):
    """Per-axis range and inversion configuration persisted via QSettings."""

    range_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._qsettings = QSettings("attocube", "ANC350_Controller")
        self._ranges = {
            Axis.X: [DEFAULT_RANGE_MIN, DEFAULT_RANGE_MAX],
            Axis.Y: [DEFAULT_RANGE_MIN, DEFAULT_RANGE_MAX],
            Axis.Z: [DEFAULT_RANGE_MIN, DEFAULT_RANGE_MAX],
        }
        self._inverted = {Axis.X: False, Axis.Y: False, Axis.Z: False}
        self._flip_x = False
        self._flip_y = False
        self._slow_speed = SLOW_SPEED
        self._fast_speed = FAST_SPEED
        self._z_speed = Z_SPEED
        self.load()

    def get_range(self, axis: Axis) -> tuple[float, float]:
        lo, hi = self._ranges[axis]
        return lo, hi

    def set_range(self, axis: Axis, lo: float, hi: float) -> None:
        self._ranges[axis] = [float(lo), float(hi)]

    def get_inverted(self, axis: Axis) -> bool:
        return self._inverted.get(axis, False)

    def set_inverted(self, axis: Axis, invert: bool) -> None:
        self._inverted[axis] = bool(invert)

    def get_flip_x(self) -> bool:
        return self._flip_x

    def set_flip_x(self, flip: bool) -> None:
        self._flip_x = bool(flip)

    def get_flip_y(self) -> bool:
        return self._flip_y

    def set_flip_y(self, flip: bool) -> None:
        self._flip_y = bool(flip)

    def get_slow_speed(self) -> float:
        return self._slow_speed

    def set_slow_speed(self, value: float) -> None:
        self._slow_speed = float(value)

    def get_fast_speed(self) -> float:
        return self._fast_speed

    def set_fast_speed(self, value: float) -> None:
        self._fast_speed = float(value)

    def get_z_speed(self) -> float:
        return self._z_speed

    def set_z_speed(self, value: float) -> None:
        self._z_speed = float(value)

    def save(self) -> None:
        """Persist current settings to disk."""
        for axis in (Axis.X, Axis.Y, Axis.Z):
            lo, hi = self._ranges[axis]
            self._qsettings.setValue(f"range/{axis.name}/min", lo)
            self._qsettings.setValue(f"range/{axis.name}/max", hi)
            self._qsettings.setValue(f"invert/{axis.name}", self._inverted[axis])
        self._qsettings.setValue("diagram/flip_x", self._flip_x)
        self._qsettings.setValue("diagram/flip_y", self._flip_y)
        self._qsettings.setValue("speed/slow", self._slow_speed)
        self._qsettings.setValue("speed/fast", self._fast_speed)
        self._qsettings.setValue("speed/z", self._z_speed)
        self.range_changed.emit()

    def load(self) -> None:
        """Load settings from disk (uses defaults for missing keys)."""
        for axis in (Axis.X, Axis.Y, Axis.Z):
            lo = self._qsettings.value(f"range/{axis.name}/min", DEFAULT_RANGE_MIN, type=float)
            hi = self._qsettings.value(f"range/{axis.name}/max", DEFAULT_RANGE_MAX, type=float)
            self._ranges[axis] = [lo, hi]
            self._inverted[axis] = self._qsettings.value(f"invert/{axis.name}", False, type=bool)
        self._flip_x = self._qsettings.value("diagram/flip_x", False, type=bool)
        self._flip_y = self._qsettings.value("diagram/flip_y", False, type=bool)
        self._slow_speed = self._qsettings.value("speed/slow", SLOW_SPEED, type=float)
        self._fast_speed = self._qsettings.value("speed/fast", FAST_SPEED, type=float)
        self._z_speed = self._qsettings.value("speed/z", Z_SPEED, type=float)
