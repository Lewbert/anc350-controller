"""Stage control logic — virtual point tracking + ANC350 command dispatch."""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from app.config import (
    Axis, FREQ_XY, FREQ_Z, LONG_PRESS_MS,
    POLL_RATE, TRIGGER_THRESHOLD,
)


class StageController(QObject):
    """Bridges controller input to ANC350 commands via a virtual point model.

    Two modes (tracked independently for XY and Z):
      CL_MODE  — closed-loop: virtual point moves, stage auto-follows
      STEP_MODE — paused: after single-step, waiting for user to resume

    XY:  left-stick (continuous) / d-pad (single-step) → CL_MODE / STEP_MODE
    Z:   A/B long-press (continuous) / A/B short-press (single-step) → CL_MODE / STEP_MODE
    """

    CL_MODE   = 0
    STEP_MODE = 1

    position_updated = pyqtSignal(float, float, float)   # x_um, y_um, z_um
    velocity_updated = pyqtSignal(float, float, float)   # vx, vy, vz  (µm/s)
    axes_enabled_changed = pyqtSignal(bool)
    params_loaded = pyqtSignal(dict)                      # {axis: {amp, freq}}, dc tracking separate

    def __init__(self, positioner, settings, parent=None):
        super().__init__(parent)
        self._pos = positioner
        self._settings = settings
        self._xy_mode = self.CL_MODE
        self._z_mode = self.CL_MODE
        self._axes_enabled = False

        # Virtual target in µm
        self._tx = 0.0
        self._ty = 0.0
        self._tz = 0.0

        # DC voltage tracking (write-only API, track last-set value per axis)
        self._dc_voltage = {Axis.X: 0.0, Axis.Y: 0.0, Axis.Z: 0.0}

        # Velocity tracking (µm/s)
        self._vx = 0.0
        self._vy = 0.0
        self._vz = 0.0

        # Z closed-loop continuous movement
        self._z_direction = 0      # 0=none, 1=forward, -1=backward
        self._z_move_timer = QTimer(self)
        self._z_move_timer.timeout.connect(self._tick_z_movement)

        # Speed
        self._fast_mode = False

        # A/B long-press timers
        self._a_timer = QTimer(self)
        self._a_timer.setSingleShot(True)
        self._a_timer.timeout.connect(self._on_a_long_press)
        self._a_held = False
        self._a_was_long = False

        self._b_timer = QTimer(self)
        self._b_timer.setSingleShot(True)
        self._b_timer.timeout.connect(self._on_b_long_press)
        self._b_held = False
        self._b_was_long = False

        # Single-step readback timer
        self._step_readback_timer = QTimer(self)
        self._step_readback_timer.setSingleShot(True)
        self._step_readback_timer.timeout.connect(self._do_step_readback)

        self._pending_step_axes = []  # axes that need position readback

    # --- Connection lifecycle -------------------------------------------------

    def on_connected(self):
        """Read current state from the device after connection."""
        for ax in (Axis.X, Axis.Y, Axis.Z):
            try:
                if ax == Axis.X:
                    self._tx = self._pos.get_position_um(ax)
                elif ax == Axis.Y:
                    self._ty = self._pos.get_position_um(ax)
                else:
                    self._tz = self._pos.get_position_um(ax)
            except Exception:
                pass

        for ax in (Axis.X, Axis.Y, Axis.Z):
            try:
                self._pos.setFrequency(ax, FREQ_XY if ax != Axis.Z else FREQ_Z)
                self._pos.setTargetRange(ax, 1e-6)
            except Exception:
                pass

        self._enable_all()
        self._xy_mode = self.CL_MODE
        self._z_mode = self.CL_MODE

        # Read back and display the actual current values
        params = {}
        for ax in (Axis.X, Axis.Y, Axis.Z):
            try:
                amp = self._pos.getAmplitude(ax)
                freq = self._pos.getFrequency(ax)
                params[ax] = {'amplitude': amp, 'frequency': freq}
            except Exception:
                params[ax] = {'amplitude': 0.0, 'frequency': 0.0}

        self.params_loaded.emit(params)
        self.position_updated.emit(self._tx, self._ty, self._tz)

    def on_disconnected(self):
        self._xy_mode = self.CL_MODE
        self._z_mode = self.CL_MODE
        self._axes_enabled = False
        self.axes_enabled_changed.emit(False)
        self._a_timer.stop()
        self._b_timer.stop()
        self._z_move_timer.stop()
        self._z_direction = 0

    # --- Joystick input (XY movement) -----------------------------------------

    def on_joystick(self, lx: float, ly: float):
        """Handle joystick XY input (CL_MODE or revive from STEP_MODE)."""
        if not self._axes_enabled:
            return

        joystick_active = abs(lx) > 0.001 or abs(ly) > 0.001

        # If XY paused after single-step, only resume when joystick is moved
        if self._xy_mode == self.STEP_MODE:
            if joystick_active:
                self._resume_closed_loop()
            else:
                self.velocity_updated.emit(0.0, 0.0, self._vz)
                return

        speed = self._settings.get_fast_speed() if self._fast_mode else self._settings.get_slow_speed()
        dt = 1.0 / POLL_RATE
        move_x = lx * speed * dt
        move_y = ly * speed * dt

        # Apply axis inversion
        if self._settings.get_inverted(Axis.X):
            move_x = -move_x
        if self._settings.get_inverted(Axis.Y):
            move_y = -move_y

        self._tx += move_x
        self._ty += move_y

        # Clamp to configured range
        x_min, x_max = self._settings.get_range(Axis.X)
        y_min, y_max = self._settings.get_range(Axis.Y)
        self._tx = max(x_min, min(self._tx, x_max))
        self._ty = max(y_min, min(self._ty, y_max))

        try:
            self._pos.move_to_xy(self._tx, self._ty)
        except Exception:
            pass

        vx = lx * speed
        vy = ly * speed
        if self._settings.get_inverted(Axis.X):
            vx = -vx
        if self._settings.get_inverted(Axis.Y):
            vy = -vy
        self._vx, self._vy = vx, vy
        self.position_updated.emit(self._tx, self._ty, self._tz)
        self.velocity_updated.emit(vx, vy, self._vz)

    def on_trigger(self, value: float):
        """Left trigger: enable fast speed mode when > threshold."""
        self._fast_mode = value > TRIGGER_THRESHOLD

    # --- D-pad input (XY single-step) ----------------------------------------

    def on_dpad(self, dx: int, dy: int):
        """Handle d-pad for XY single-step movement.
        Single-step exits closed-loop, so we pause auto-move and read back.
        """
        if not self._axes_enabled or (dx == 0 and dy == 0):
            return

        self._xy_mode = self.STEP_MODE
        # Remove stale XY entries, preserve Z entries
        self._pending_step_axes = [a for a in self._pending_step_axes if a == Axis.Z]

        try:
            if dx != 0:
                dir_x = dx
                if self._settings.get_inverted(Axis.X):
                    dir_x = -dir_x
                backward = 1 if dir_x < 0 else 0
                self._pos.startSingleStep(Axis.X, backward)
                self._pending_step_axes.append(Axis.X)
            if dy != 0:
                dir_y = dy
                if self._settings.get_inverted(Axis.Y):
                    dir_y = -dir_y
                backward = 1 if dir_y < 0 else 0
                self._pos.startSingleStep(Axis.Y, backward)
                self._pending_step_axes.append(Axis.Y)
        except Exception:
            return

        # Schedule position readback after step completes
        self._step_readback_timer.start(100)

    # --- A/B button (Z axis) --------------------------------------------------

    def on_button_a(self, pressed: bool):
        """A button: Z forward. Short press = single step, long press = closed-loop."""
        if not self._axes_enabled:
            return

        if pressed:
            self._a_held = True
            self._a_was_long = False
            self._a_timer.start(LONG_PRESS_MS)
        else:
            self._a_held = False
            if self._a_timer.isActive():
                self._a_timer.stop()
                self._z_single_step(backward=0)
            elif self._a_was_long:
                self._stop_z_closed_loop()

    def on_button_b(self, pressed: bool):
        """B button: Z backward. Short press = single step, long press = closed-loop."""
        if not self._axes_enabled:
            return

        if pressed:
            self._b_held = True
            self._b_was_long = False
            self._b_timer.start(LONG_PRESS_MS)
        else:
            self._b_held = False
            if self._b_timer.isActive():
                self._b_timer.stop()
                self._z_single_step(backward=1)
            elif self._b_was_long:
                self._stop_z_closed_loop()

    def _on_a_long_press(self):
        """Start Z closed-loop movement forward."""
        if self._a_held:
            self._a_was_long = True
            self._start_z_closed_loop(direction=1)

    def _on_b_long_press(self):
        """Start Z closed-loop movement backward."""
        if self._b_held:
            self._b_was_long = True
            self._start_z_closed_loop(direction=-1)

    def _start_z_closed_loop(self, direction: int):
        """Enter Z closed-loop and begin moving the virtual target in *direction*."""
        self._z_mode = self.CL_MODE
        self._z_direction = direction
        try:
            self._pos.setTargetPosition(Axis.Z, self._tz / 1e6)
            self._pos.startAutoMove(Axis.Z, 1, 0)
        except Exception:
            pass
        self._z_move_timer.start(int(1000 / POLL_RATE))

    def _stop_z_closed_loop(self):
        """Stop Z closed-loop movement (button released). Auto-move stays active
        so the stage converges to the last target position."""
        self._z_move_timer.stop()
        self._z_direction = 0
        self._vz = 0.0
        self.velocity_updated.emit(self._vx, self._vy, self._vz)

    def _tick_z_movement(self):
        """Called by _z_move_timer each poll interval: advance Z virtual target."""
        if not self._axes_enabled or self._z_mode != self.CL_MODE:
            self._z_move_timer.stop()
            return
        if self._z_direction == 0:
            return

        z_speed = self._settings.get_z_speed()
        dt = 1.0 / POLL_RATE
        move = self._z_direction * z_speed * dt

        if self._settings.get_inverted(Axis.Z):
            move = -move

        self._tz += move

        # Clamp to configured range
        z_min, z_max = self._settings.get_range(Axis.Z)
        self._tz = max(z_min, min(self._tz, z_max))

        try:
            self._pos.setTargetPosition(Axis.Z, self._tz / 1e6)
        except Exception:
            pass

        self._vz = self._z_direction * z_speed
        if self._settings.get_inverted(Axis.Z):
            self._vz = -self._vz
        self.position_updated.emit(self._tx, self._ty, self._tz)
        self.velocity_updated.emit(self._vx, self._vy, self._vz)

    def _z_single_step(self, backward: int):
        """Trigger a Z single-step, exit closed-loop, and read back position."""
        if self._settings.get_inverted(Axis.Z):
            backward = 1 - backward

        # Stop closed-loop movement
        self._z_move_timer.stop()
        self._z_direction = 0

        # Stop Z auto-move before single step
        try:
            self._pos.startAutoMove(Axis.Z, 0, 0)
        except Exception:
            pass

        self._z_mode = self.STEP_MODE
        self._vz = 0.0
        self.velocity_updated.emit(self._vx, self._vy, 0.0)

        try:
            self._pos.startSingleStep(Axis.Z, backward)
        except Exception:
            return
        # Remove stale Z entry, preserve XY entries
        self._pending_step_axes = [a for a in self._pending_step_axes if a != Axis.Z]
        self._pending_step_axes.append(Axis.Z)
        self._step_readback_timer.start(100)

    # --- Menu button ----------------------------------------------------------

    def on_menu(self, pressed: bool):
        """Toggle axes enable/disable on button press (not release)."""
        if not pressed:
            return
        if self._axes_enabled:
            self._disable_all()
        else:
            self._enable_all()

    # --- Readback -------------------------------------------------------------

    def _do_step_readback(self):
        """Read actual position after single-step, sync virtual target."""
        for axis in self._pending_step_axes:
            try:
                pos_um = self._pos.get_position_um(axis)
                if axis == Axis.X:
                    self._tx = pos_um
                elif axis == Axis.Y:
                    self._ty = pos_um
                elif axis == Axis.Z:
                    self._tz = pos_um
            except Exception:
                pass

        self._pending_step_axes = []
        self.position_updated.emit(self._tx, self._ty, self._tz)

    def _resume_closed_loop(self):
        """Re-engage closed-loop auto-move for X and Y."""
        self._xy_mode = self.CL_MODE
        try:
            self._pos.move_to_xy(self._tx, self._ty)
        except Exception:
            pass

    # --- Parameter setters ----------------------------------------------------

    def set_amplitude(self, axis: Axis, value: float):
        try:
            self._pos.setAmplitude(axis, value)
        except Exception:
            pass

    def set_frequency(self, axis: Axis, value: float):
        try:
            self._pos.setFrequency(axis, value)
        except Exception:
            pass

    def set_dc_voltage(self, axis: Axis, value: float):
        try:
            self._pos.setDcVoltage(axis, value)
            self._dc_voltage[axis] = value
        except Exception:
            pass

    def read_current_params(self) -> dict:
        """Read current amplitude and frequency from device for all axes."""
        params = {}
        for ax in (Axis.X, Axis.Y, Axis.Z):
            try:
                amp = self._pos.getAmplitude(ax)
                freq = self._pos.getFrequency(ax)
                params[ax] = {'amplitude': amp, 'frequency': freq}
            except Exception:
                params[ax] = {'amplitude': 0.0, 'frequency': 0.0}
        return params

    def get_dc_voltage(self, axis: Axis) -> float:
        return self._dc_voltage.get(axis, 0.0)

    # --- Axis enable/disable --------------------------------------------------

    def _enable_all(self):
        if not self._pos.connected:
            return
        for ax in (Axis.X, Axis.Y, Axis.Z):
            try:
                self._pos.enable_axis(ax)
            except Exception:
                pass
        self._axes_enabled = True
        self.axes_enabled_changed.emit(True)

    def _disable_all(self):
        if not self._pos.connected:
            return
        for ax in (Axis.X, Axis.Y, Axis.Z):
            try:
                self._pos.disable_axis(ax)
            except Exception:
                pass
        self._axes_enabled = False
        self.axes_enabled_changed.emit(False)

    # --- Queries --------------------------------------------------------------

    @property
    def axes_enabled(self) -> bool:
        return self._axes_enabled

    @property
    def target_position(self) -> tuple:
        return (self._tx, self._ty, self._tz)
