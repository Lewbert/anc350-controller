"""Internal ctypes bindings for anc350v4.dll."""

import ctypes
from ctypes import wintypes
import os as _os
import sys as _sys

# --- DLL discovery -----------------------------------------------------------

def _find_dll_dir():
    if getattr(_sys, 'frozen', False):
        return _sys._MEIPASS
    else:
        return _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

_dll_dir = _find_dll_dir()
_os.add_dll_directory(_dll_dir)
_dll = ctypes.WinDLL(_os.path.join(_dll_dir, 'anc350v4.dll'))

# --- Error codes -------------------------------------------------------------

ANC_Ok            =  0
ANC_Error         = -1
ANC_Timeout       =  1
ANC_NotConnected  =  2
ANC_DriverError   =  3
ANC_DeviceLocked  =  7
ANC_Unknown       =  8
ANC_NoDevice      =  9
ANC_NoAxis        = 10
ANC_OutOfRange    = 11
ANC_NotAvailable  = 12

# --- Exception hierarchy -----------------------------------------------------

class ANC350Error(Exception):
    """Base exception for ANC350 errors."""
    def __init__(self, code, func_name):
        self.code = code
        self.func_name = func_name
        super().__init__(f"ANC350 error {code} in {func_name}")

class ANC350TimeoutError(ANC350Error):       pass
class ANC350NotConnectedError(ANC350Error):  pass
class ANC350DriverError(ANC350Error):        pass
class ANC350DeviceLockedError(ANC350Error):  pass
class ANC350UnknownError(ANC350Error):       pass
class ANC350NoDeviceError(ANC350Error):      pass
class ANC350NoAxisError(ANC350Error):        pass
class ANC350OutOfRangeError(ANC350Error):    pass
class ANC350NotAvailableError(ANC350Error):  pass

_ERROR_MAP = {
    ANC_Ok:             None,
    ANC_Error:          ANC350Error,
    ANC_Timeout:        ANC350TimeoutError,
    ANC_NotConnected:   ANC350NotConnectedError,
    ANC_DriverError:    ANC350DriverError,
    ANC_DeviceLocked:   ANC350DeviceLockedError,
    ANC_Unknown:        ANC350UnknownError,
    ANC_NoDevice:       ANC350NoDeviceError,
    ANC_NoAxis:         ANC350NoAxisError,
    ANC_OutOfRange:     ANC350OutOfRangeError,
    ANC_NotAvailable:   ANC350NotAvailableError,
}

def _check_error(code, func, args):
    if code == ANC_Ok:
        return code
    exc_cls = _ERROR_MAP.get(code, ANC350Error)
    raise exc_cls(code, func.__name__)

# --- DLL function bindings ---------------------------------------------------

# Type aliases
_DWORD = wintypes.DWORD
_INT32 = ctypes.c_int32

# Discover
discover = _dll.ANC_discover
discover.argtypes = [_INT32, ctypes.POINTER(_INT32)]
discover.restype = _INT32
discover.errcheck = _check_error

# GetDeviceInfo
getDeviceInfo = _dll.ANC_getDeviceInfo
getDeviceInfo.argtypes = [
    _INT32,                                          # devNo
    ctypes.POINTER(_INT32),                          # devType
    ctypes.POINTER(_INT32),                          # id
    ctypes.POINTER(ctypes.c_char * 16),              # serialNo
    ctypes.POINTER(ctypes.c_char * 16),              # address
    ctypes.POINTER(_INT32),                          # connected
]
getDeviceInfo.restype = _INT32
getDeviceInfo.errcheck = _check_error

# Connect
connect = _dll.ANC_connect
connect.argtypes = [_INT32, ctypes.POINTER(ctypes.c_void_p)]
connect.restype = _INT32
connect.errcheck = _check_error

# Disconnect
disconnect = _dll.ANC_disconnect
disconnect.argtypes = [ctypes.c_void_p]
disconnect.restype = _INT32
disconnect.errcheck = _check_error

# GetDeviceConfig
getDeviceConfig = _dll.ANC_getDeviceConfig
getDeviceConfig.argtypes = [ctypes.c_void_p, ctypes.POINTER(_INT32)]
getDeviceConfig.restype = _INT32
getDeviceConfig.errcheck = _check_error

# GetAxisStatus
getAxisStatus = _dll.ANC_getAxisStatus
getAxisStatus.argtypes = [
    ctypes.c_void_p,                  # device
    _INT32,                            # axisNo
    ctypes.POINTER(_INT32),            # connected
    ctypes.POINTER(_INT32),            # enabled
    ctypes.POINTER(_INT32),            # moving
    ctypes.POINTER(_INT32),            # target
    ctypes.POINTER(_INT32),            # eotFwd
    ctypes.POINTER(_INT32),            # eotBwd
    ctypes.POINTER(_INT32),            # error
]
getAxisStatus.restype = _INT32
getAxisStatus.errcheck = _check_error

# SetAxisOutput
setAxisOutput = _dll.ANC_setAxisOutput
setAxisOutput.argtypes = [ctypes.c_void_p, _INT32, _INT32, _INT32]
setAxisOutput.restype = _INT32
setAxisOutput.errcheck = _check_error

# SetAmplitude / GetAmplitude
setAmplitude = _dll.ANC_setAmplitude
setAmplitude.argtypes = [ctypes.c_void_p, _INT32, ctypes.c_double]
setAmplitude.restype = _INT32
setAmplitude.errcheck = _check_error

getAmplitude = _dll.ANC_getAmplitude
getAmplitude.argtypes = [ctypes.c_void_p, _INT32, ctypes.POINTER(ctypes.c_double)]
getAmplitude.restype = _INT32
getAmplitude.errcheck = _check_error

# SetFrequency / GetFrequency
setFrequency = _dll.ANC_setFrequency
setFrequency.argtypes = [ctypes.c_void_p, _INT32, ctypes.c_double]
setFrequency.restype = _INT32
setFrequency.errcheck = _check_error

getFrequency = _dll.ANC_getFrequency
getFrequency.argtypes = [ctypes.c_void_p, _INT32, ctypes.POINTER(ctypes.c_double)]
getFrequency.restype = _INT32
getFrequency.errcheck = _check_error

# SetDcVoltage (no getter in the DLL)
setDcVoltage = _dll.ANC_setDcVoltage
setDcVoltage.argtypes = [ctypes.c_void_p, _INT32, ctypes.c_double]
setDcVoltage.restype = _INT32
setDcVoltage.errcheck = _check_error

# StartSingleStep
startSingleStep = _dll.ANC_startSingleStep
startSingleStep.argtypes = [ctypes.c_void_p, _INT32, _INT32]
startSingleStep.restype = _INT32
startSingleStep.errcheck = _check_error

# StartContinousMove (note: the DLL has the typo "Continous")
startContinousMove = _dll.ANC_startContinousMove
startContinousMove.argtypes = [ctypes.c_void_p, _INT32, _INT32, _INT32]
startContinousMove.restype = _INT32
startContinousMove.errcheck = _check_error

# StartAutoMove
startAutoMove = _dll.ANC_startAutoMove
startAutoMove.argtypes = [ctypes.c_void_p, _INT32, _INT32, _INT32]
startAutoMove.restype = _INT32
startAutoMove.errcheck = _check_error

# SetTargetPosition / GetPosition
setTargetPosition = _dll.ANC_setTargetPosition
setTargetPosition.argtypes = [ctypes.c_void_p, _INT32, ctypes.c_double]
setTargetPosition.restype = _INT32
setTargetPosition.errcheck = _check_error

setTargetRange = _dll.ANC_setTargetRange
setTargetRange.argtypes = [ctypes.c_void_p, _INT32, ctypes.c_double]
setTargetRange.restype = _INT32
setTargetRange.errcheck = _check_error

getPosition = _dll.ANC_getPosition
getPosition.argtypes = [ctypes.c_void_p, _INT32, ctypes.POINTER(ctypes.c_double)]
getPosition.restype = _INT32
getPosition.errcheck = _check_error

# GetFirmwareVersion
getFirmwareVersion = _dll.ANC_getFirmwareVersion
getFirmwareVersion.argtypes = [ctypes.c_void_p, ctypes.POINTER(_INT32)]
getFirmwareVersion.restype = _INT32
getFirmwareVersion.errcheck = _check_error

# ConfigureExtTrigger
configureExtTrigger = _dll.ANC_configureExtTrigger
configureExtTrigger.argtypes = [ctypes.c_void_p, _INT32, _INT32]
configureExtTrigger.restype = _INT32
configureExtTrigger.errcheck = _check_error

# ConfigureAQuadBIn
configureAQuadBIn = _dll.ANC_configureAQuadBIn
configureAQuadBIn.argtypes = [ctypes.c_void_p, _INT32, _INT32, ctypes.c_double]
configureAQuadBIn.restype = _INT32
configureAQuadBIn.errcheck = _check_error

# ConfigureAQuadBOut
configureAQuadBOut = _dll.ANC_configureAQuadBOut
configureAQuadBOut.argtypes = [ctypes.c_void_p, _INT32, _INT32, ctypes.c_double, ctypes.c_double]
configureAQuadBOut.restype = _INT32
configureAQuadBOut.errcheck = _check_error

# ConfigureRngTriggerPol
configureRngTriggerPol = _dll.ANC_configureRngTriggerPol
configureRngTriggerPol.argtypes = [ctypes.c_void_p, _INT32, _INT32]
configureRngTriggerPol.restype = _INT32
configureRngTriggerPol.errcheck = _check_error

# ConfigureRngTrigger
configureRngTrigger = _dll.ANC_configureRngTrigger
configureRngTrigger.argtypes = [ctypes.c_void_p, _INT32, _INT32, _INT32]
configureRngTrigger.restype = _INT32
configureRngTrigger.errcheck = _check_error

# ConfigureRngTriggerEps
configureRngTriggerEps = _dll.ANC_configureRngTriggerEps
configureRngTriggerEps.argtypes = [ctypes.c_void_p, _INT32, _INT32]
configureRngTriggerEps.restype = _INT32
configureRngTriggerEps.errcheck = _check_error

# ConfigureNslTrigger
configureNslTrigger = _dll.ANC_configureNslTrigger
configureNslTrigger.argtypes = [ctypes.c_void_p, _INT32]
configureNslTrigger.restype = _INT32
configureNslTrigger.errcheck = _check_error

# ConfigureNslTriggerAxis
configureNslTriggerAxis = _dll.ANC_configureNslTriggerAxis
configureNslTriggerAxis.argtypes = [ctypes.c_void_p, _INT32, _INT32]
configureNslTriggerAxis.restype = _INT32
configureNslTriggerAxis.errcheck = _check_error

# SelectActuator
selectActuator = _dll.ANC_selectActuator
selectActuator.argtypes = [ctypes.c_void_p, _INT32, _INT32]
selectActuator.restype = _INT32
selectActuator.errcheck = _check_error

# GetActuatorName
getActuatorName = _dll.ANC_getActuatorName
getActuatorName.argtypes = [ctypes.c_void_p, _INT32, ctypes.POINTER(ctypes.c_char * 20)]
getActuatorName.restype = _INT32
getActuatorName.errcheck = _check_error

# GetActuatorType
getActuatorType = _dll.ANC_getActuatorType
getActuatorType.argtypes = [ctypes.c_void_p, _INT32, ctypes.POINTER(_INT32)]
getActuatorType.restype = _INT32
getActuatorType.errcheck = _check_error

# MeasureCapacitance
measureCapacitance = _dll.ANC_measureCapacitance
measureCapacitance.argtypes = [ctypes.c_void_p, _INT32, ctypes.POINTER(ctypes.c_double)]
measureCapacitance.restype = _INT32
measureCapacitance.errcheck = _check_error

# SaveParams
saveParams = _dll.ANC_saveParams
saveParams.argtypes = [ctypes.c_void_p]
saveParams.restype = _INT32
saveParams.errcheck = _check_error
