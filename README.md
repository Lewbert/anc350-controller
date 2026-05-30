# ANC350 Controller

GUI application for controlling attocube ANC350 nanopositioners with an Xbox-compatible gamepad.

Tested with ANC350 hardware and a Gamesir Xbox-compatible gamepad.

## Features

- Gamepad control of X/Y/Z axes with dual-speed movement
- Real-time position display with XY diagram
- Per-axis amplitude, frequency, and DC voltage control
- Configurable range limits, speeds, axis inversion, and diagram flip
- Persistent settings saved across sessions

## Prerequisites

- Windows (the ANC350 driver is Windows-only)
- Python 3.8+
- Xbox-compatible gamepad
- `anc350v4.dll` v1.2.0 (included, MIT) and `libusb0.dll` v1.2.5.0 (included, LGPL v2.1)

## Installation

```bash
pip install pyqt5
```

Place `anc350v4.dll` and `libusb0.dll` in the project root, then run:

```bash
python -m app.main
```

## Building a standalone executable

```bash
pip install pyinstaller
pyinstaller ANC350_Controller.spec
```

The executable will be in `dist/`.

## Gamepad Controls

| Control | Action |
|---|---|
| **Left stick** | Move X/Y continuously in closed-loop mode |
| **Left trigger** (hold) | Activates fast speed while held |
| **D-pad** | Single-step X/Y — exits closed-loop mode and reads back the actual position from the device |
| **A** (short press) | Z forward single step — exits closed-loop |
| **A** (long press) | Z forward continuous movement |
| **B** (short press) | Z backward single step — exits closed-loop |
| **B** (long press) | Z backward continuous movement |
| **Start** | Toggle axes enable/disable |

After a D-pad or short A/B press, the controller enters **step mode**: the virtual target pauses and waits for the actual position readback from the device. Move the left stick to resume closed-loop tracking.

## Usage

1. Connect the ANC350 controller via USB
2. Connect your gamepad
3. Launch the app — it will auto-detect the ANC350 device
4. All axes are enabled automatically on startup. Press **Start** to toggle axes on/off.
5. Adjust drive parameters per axis in the **Drive Parameters** panel
6. Configure range limits and speeds via **File → Stage Settings**, based on your stage configuration

---

`anc350v4.dll` v1.2.0 from [attocube-systems/ANC350_Python_Control](https://github.com/attocube-systems/ANC350_Python_Control), used under MIT license.
`libusb0.dll` v1.2.5.0 is [libusb-win32](http://libusb-win32.sourceforge.net), used under LGPL v2.1.
Third-party licenses are in the [`licenses/`](licenses/) directory.
