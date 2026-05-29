"""XInput gamepad polling via ctypes — zero extra dependencies."""

import ctypes
from ctypes import wintypes

from PyQt5.QtCore import QThread, pyqtSignal

from app.config import DEAD_ZONE, POLL_RATE, XButton

# --- XInput structs ----------------------------------------------------------

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ('wButtons',      wintypes.WORD),
        ('bLeftTrigger',  ctypes.c_ubyte),
        ('bRightTrigger', ctypes.c_ubyte),
        ('sThumbLX',      ctypes.c_short),
        ('sThumbLY',      ctypes.c_short),
        ('sThumbRX',      ctypes.c_short),
        ('sThumbRY',      ctypes.c_short),
    ]

class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ('dwPacketNumber', wintypes.DWORD),
        ('Gamepad',        XINPUT_GAMEPAD),
    ]

# --- Load XInput DLL ---------------------------------------------------------

_xinput = None
for _name in ('xinput1_4', 'xinput1_3', 'xinput9_1_0'):
    try:
        _xinput = ctypes.windll.LoadLibrary(_name)
        break
    except OSError:
        continue

if _xinput is None:
    raise OSError("XInput DLL not found — is DirectX installed?")

_XInputGetState = _xinput.XInputGetState
_XInputGetState.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
_XInputGetState.restype = wintypes.DWORD

ERROR_SUCCESS            = 0
ERROR_DEVICE_NOT_CONNECTED = 1167

def _read_state(user_index=0):
    state = XINPUT_STATE()
    result = _XInputGetState(user_index, ctypes.byref(state))
    if result == ERROR_SUCCESS:
        return True, state
    return False, None

# --- QThread -----------------------------------------------------------------

class ControllerThread(QThread):
    """Polls Xbox controller state via XInput and emits Qt signals."""

    joystick_moved   = pyqtSignal(float, float)    # lx, ly  [-1.0, 1.0]
    trigger_value    = pyqtSignal(float)            # left trigger  [0.0, 1.0]
    button_a_state   = pyqtSignal(bool)
    button_b_state   = pyqtSignal(bool)
    button_menu_state = pyqtSignal(bool)
    dpad_direction   = pyqtSignal(int, int)         # dx, dy  in {-1, 0, 1}
    gamepad_connected    = pyqtSignal(str)
    gamepad_disconnected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._was_connected = False
        self._prev_a = False
        self._prev_b = False
        self._prev_menu = False
        self._prev_dx = 0
        self._prev_dy = 0

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            connected, state = _read_state(0)

            if not connected:
                if self._was_connected:
                    self.gamepad_disconnected.emit()
                    self._was_connected = False
                    self._prev_a = False
                    self._prev_b = False
                    self._prev_menu = False
                    self._prev_dx = 0
                    self._prev_dy = 0
                self.msleep(2000)
                continue

            if not self._was_connected:
                self.gamepad_connected.emit("Xbox Controller")
                self._was_connected = True

            gp = state.Gamepad

            # Thumbsticks: normalize [-32768, 32767] -> [-1.0, 1.0]
            lx = gp.sThumbLX / 32767.0
            ly = gp.sThumbLY / 32767.0
            if abs(lx) < DEAD_ZONE: lx = 0.0
            if abs(ly) < DEAD_ZONE: ly = 0.0
            self.joystick_moved.emit(lx, ly)

            # Left trigger: [0, 255] -> [0.0, 1.0]
            lt = gp.bLeftTrigger / 255.0
            self.trigger_value.emit(lt)

            # D-pad (XInput maps d-pad to button bits, not a hat switch)
            btns = gp.wButtons
            dx = 0
            dy = 0
            if btns & XButton.DPAD_UP:    dy = 1
            if btns & XButton.DPAD_DOWN:  dy = -1
            if btns & XButton.DPAD_LEFT:  dx = -1
            if btns & XButton.DPAD_RIGHT: dx = 1
            if dx != self._prev_dx or dy != self._prev_dy:
                self.dpad_direction.emit(dx, dy)
                self._prev_dx = dx
                self._prev_dy = dy

            # A button
            a = bool(btns & XButton.A)
            if a != self._prev_a:
                self.button_a_state.emit(a)
                self._prev_a = a

            # B button
            b = bool(btns & XButton.B)
            if b != self._prev_b:
                self.button_b_state.emit(b)
                self._prev_b = b

            # Menu (Start) button
            m = bool(btns & XButton.START)
            if m != self._prev_menu:
                self.button_menu_state.emit(m)
                self._prev_menu = m

            self.msleep(int(1000 / POLL_RATE))

        # Clear state on stop
        if self._was_connected:
            self.gamepad_disconnected.emit()
