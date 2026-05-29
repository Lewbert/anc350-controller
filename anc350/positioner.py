"""Positioner class — Pythonic interface to the ANC350 device."""

import ctypes
import threading

from anc350 import _dll as _dll


class Positioner:
    """Controller for a single ANC350 positioner device.

    Usage:
        pos = Positioner()
        count = pos.discover()
        pos.connect(devNo=0)
        # ... use methods ...
        pos.disconnect()
    """

    def __init__(self):
        self._device = None
        self._lock = threading.Lock()

    # --- Core lifecycle --------------------------------------------------

    def discover(self, ifaces: int = 3) -> int:
        """Search for connected ANC350 devices.

        Args:
            ifaces: Interfaces to search. 0=None, 1=USB, 2=ethernet, 3=all.

        Returns:
            Number of devices found.
        """
        devCount = ctypes.c_int()
        with self._lock:
            _dll.discover(ifaces, ctypes.byref(devCount))
        return devCount.value

    def connect(self, devNo: int = 0) -> None:
        """Connect to a discovered device by index.

        Args:
            devNo: Device index (0-based). Must be < devCount from discover().
        """
        device = ctypes.c_void_p()
        with self._lock:
            _dll.connect(devNo, ctypes.byref(device))
        self._device = device

    def disconnect(self) -> None:
        """Close the connection to the device."""
        if self._device is not None:
            with self._lock:
                _dll.disconnect(self._device)
            self._device = None

    @property
    def connected(self) -> bool:
        return self._device is not None

    # --- Convenience methods ----------------------------------------------

    def enable_axis(self, axis: int) -> None:
        """Enable voltage output for a single axis (auto-disable on EOT)."""
        self.setAxisOutput(axis, 1, 1)

    def disable_axis(self, axis: int) -> None:
        """Disable voltage output for a single axis."""
        self.setAxisOutput(axis, 0, 0)

    def get_position_um(self, axis: int) -> float:
        """Get current position in micrometers."""
        return self.getPosition(axis) * 1e6

    def move_to_xy(self, x_um: float, y_um: float) -> None:
        """Set target and start auto-move for X and Y axes (closed-loop)."""
        self.setTargetPosition(0, x_um / 1e6)
        self.setTargetPosition(1, y_um / 1e6)
        self.startAutoMove(0, 1, 0)
        self.startAutoMove(1, 1, 0)

    # --- Device info ------------------------------------------------------

    def getDeviceInfo(self, devNo: int = 0) -> tuple[int, int, str, str, int]:
        """Get info about a device. Returns (devType, id, serialNo, address, connected)."""
        devType = ctypes.c_int()
        id_ = ctypes.c_int()
        serialNo = ctypes.create_string_buffer(16)
        address = ctypes.create_string_buffer(16)
        connected = ctypes.c_int()
        with self._lock:
            _dll.getDeviceInfo(devNo, ctypes.byref(devType), ctypes.byref(id_),
                              ctypes.byref(serialNo), ctypes.byref(address),
                              ctypes.byref(connected))
        return (devType.value, id_.value,
                serialNo.value.decode('utf-8').rstrip('\x00'),
                address.value.decode('utf-8').rstrip('\x00'),
                connected.value)

    def getDeviceConfig(self) -> tuple[int, int, int, int]:
        """Read static device config. Returns (featureSync, featureLockin, featureDuty, featureApp)."""
        features = ctypes.c_int()
        with self._lock:
            _dll.getDeviceConfig(self._device, features)
        f = features.value
        return (f & 0x01, (f & 0x02) >> 1, (f & 0x04) >> 2, (f & 0x08) >> 3)

    def getFirmwareVersion(self) -> int:
        """Get firmware version number."""
        version = ctypes.c_int()
        with self._lock:
            _dll.getFirmwareVersion(self._device, ctypes.byref(version))
        return version.value

    # --- Axis status & output ---------------------------------------------

    def getAxisStatus(self, axis: int) -> tuple[int, int, int, int, int, int, int]:
        """Returns (connected, enabled, moving, target, eotFwd, eotBwd, error)."""
        connected = ctypes.c_int()
        enabled = ctypes.c_int()
        moving = ctypes.c_int()
        target = ctypes.c_int()
        eotFwd = ctypes.c_int()
        eotBwd = ctypes.c_int()
        error = ctypes.c_int()
        with self._lock:
            _dll.getAxisStatus(self._device, axis,
                              ctypes.byref(connected), ctypes.byref(enabled),
                              ctypes.byref(moving), ctypes.byref(target),
                              ctypes.byref(eotFwd), ctypes.byref(eotBwd),
                              ctypes.byref(error))
        return (connected.value, enabled.value, moving.value, target.value,
                eotFwd.value, eotBwd.value, error.value)

    def setAxisOutput(self, axis: int, enable: int, autoDisable: int) -> None:
        """Enable/disable voltage output for an axis."""
        with self._lock:
            _dll.setAxisOutput(self._device, axis, enable, autoDisable)

    # --- Motion -----------------------------------------------------------

    def getPosition(self, axis: int) -> float:
        """Get current position in meters (linear) or degrees (rotator)."""
        position = ctypes.c_double()
        with self._lock:
            _dll.getPosition(self._device, axis, ctypes.byref(position))
        return position.value

    def setTargetPosition(self, axis: int, target: float) -> None:
        """Set target position for automatic motion (meters or degrees)."""
        with self._lock:
            _dll.setTargetPosition(self._device, axis, ctypes.c_double(target))

    def setTargetRange(self, axis: int, targetRg: float) -> None:
        """Set target range — defines when target is considered reached (m or deg)."""
        with self._lock:
            _dll.setTargetRange(self._device, axis, ctypes.c_double(targetRg))

    def startAutoMove(self, axis: int, enable: int, relative: int) -> None:
        """Start/stop automatic movement following target position.

        Args:
            enable: 1 to start, 0 to stop.
            relative: 0 for absolute target, 1 for relative.
        """
        with self._lock:
            _dll.startAutoMove(self._device, axis, enable, relative)

    def startSingleStep(self, axis: int, backward: int) -> None:
        """Trigger a single step in the given direction.

        Args:
            backward: 0 for forward, 1 for backward.
        """
        with self._lock:
            _dll.startSingleStep(self._device, axis, backward)

    def startContinuousMove(self, axis: int, start: int, backward: int) -> None:
        """Start or stop continuous motion.

        Args:
            start: 1 to start, 0 to stop.
            backward: 0 for forward, 1 for backward.
        """
        with self._lock:
            _dll.startContinousMove(self._device, axis, start, backward)

    # --- Parameters -------------------------------------------------------

    def getAmplitude(self, axis: int) -> float:
        """Get amplitude in volts."""
        amplitude = ctypes.c_double()
        with self._lock:
            _dll.getAmplitude(self._device, axis, ctypes.byref(amplitude))
        return amplitude.value

    def setAmplitude(self, axis: int, amplitude: float) -> None:
        """Set amplitude in volts (internal resolution 1 mV)."""
        with self._lock:
            _dll.setAmplitude(self._device, axis, ctypes.c_double(amplitude))

    def getFrequency(self, axis: int) -> float:
        """Get frequency in Hz."""
        frequency = ctypes.c_double()
        with self._lock:
            _dll.getFrequency(self._device, axis, ctypes.byref(frequency))
        return frequency.value

    def setFrequency(self, axis: int, frequency: float) -> None:
        """Set frequency in Hz (internal resolution 1 Hz)."""
        with self._lock:
            _dll.setFrequency(self._device, axis, ctypes.c_double(frequency))

    def setDcVoltage(self, axis: int, voltage: float) -> None:
        """Set DC level on the voltage output (volts, resolution 1 mV)."""
        with self._lock:
            _dll.setDcVoltage(self._device, axis, ctypes.c_double(voltage))

    # --- Actuator ---------------------------------------------------------

    def getActuatorName(self, axis: int) -> str:
        """Get name of the currently selected actuator."""
        name = ctypes.create_string_buffer(20)
        with self._lock:
            _dll.getActuatorName(self._device, axis, ctypes.byref(name))
        return name.value.decode('utf-8').rstrip('\x00')

    def getActuatorType(self, axis: int) -> int:
        """Get actuator type: 0=linear, 1=goniometer, 2=rotator."""
        type_ = ctypes.c_int()
        with self._lock:
            _dll.getActuatorType(self._device, axis, ctypes.byref(type_))
        return type_.value

    def selectActuator(self, axis: int, actuator: int) -> None:
        """Select actuator from presets (0-255)."""
        with self._lock:
            _dll.selectActuator(self._device, axis, actuator)

    def measureCapacitance(self, axis: int) -> float:
        """Measure piezo motor capacitance (takes a few seconds). Returns Farads."""
        cap = ctypes.c_double()
        with self._lock:
            _dll.measureCapacitance(self._device, axis, ctypes.byref(cap))
        return cap.value

    # --- Persistence ------------------------------------------------------

    def saveParams(self) -> None:
        """Save parameters to device flash memory."""
        with self._lock:
            _dll.saveParams(self._device)

    # --- Trigger configuration --------------------------------------------

    def configureExtTrigger(self, axis: int, mode: int) -> None:
        """Configure external trigger. mode: 0=disable, 1=quadrature, 2=trigger."""
        with self._lock:
            _dll.configureExtTrigger(self._device, axis, mode)

    def configureAQuadBIn(self, axis: int, enable: int, resolution: float) -> None:
        """Configure A-Quad-B input for target position (resolution in m)."""
        with self._lock:
            _dll.configureAQuadBIn(self._device, axis, enable, ctypes.c_double(resolution))

    def configureAQuadBOut(self, axis: int, enable: int, resolution: float, clock: float) -> None:
        """Configure A-Quad-B output of current position."""
        with self._lock:
            _dll.configureAQuadBOut(self._device, axis, enable,
                                    ctypes.c_double(resolution), ctypes.c_double(clock))

    def configureNslTrigger(self, enable: int) -> None:
        """Enable NSL input as trigger source."""
        with self._lock:
            _dll.configureNslTrigger(self._device, enable)

    def configureNslTriggerAxis(self, axis: int) -> None:
        """Select axis for NSL trigger."""
        with self._lock:
            _dll.configureNslTriggerAxis(self._device, axis)

    def configureRngTrigger(self, axis: int, lower: int, upper: int) -> None:
        """Configure range trigger lower/upper bounds (nm)."""
        with self._lock:
            _dll.configureRngTrigger(self._device, axis, lower, upper)

    def configureRngTriggerEps(self, axis: int, epsilon: int) -> None:
        """Configure range trigger hysteresis (nm / mdeg)."""
        with self._lock:
            _dll.configureRngTriggerEps(self._device, axis, epsilon)

    def configureRngTriggerPol(self, axis: int, polarity: int) -> None:
        """Configure range trigger polarity: 0=low, 1=high."""
        with self._lock:
            _dll.configureRngTriggerPol(self._device, axis, polarity)
