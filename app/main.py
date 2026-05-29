"""Entry point for the ANC350 Stage Controller application."""

import os
import sys

# Ensure project root is on sys.path (for `python app/main.py` usage)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Ensure DLLs are findable before any anc350 import
os.add_dll_directory(_project_root)


def main():
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("ANC350 Stage Controller")
    app.setOrganizationName("attocube")
    app.setStyle("Fusion")

    # App icon
    from PyQt5.QtGui import QIcon
    _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    app_icon = QIcon(_icon_path)
    app.setWindowIcon(app_icon)

    from app.config import AppSettings
    from app.main_window import MainWindow

    settings = AppSettings()
    window = MainWindow(settings)
    window.setWindowIcon(app_icon)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
