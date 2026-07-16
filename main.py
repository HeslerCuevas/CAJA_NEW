import sys
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

if sys.platform.startswith("win") and getattr(sys, "frozen", False):
    import ctypes

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from viewss.main_window import MainWindow


def _resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base.joinpath(*parts)


def _desktop_icon_path() -> Path:
    candidates = [
        _resource_path("assets", "NocturnalBarDesktopIcon.ico"),
        Path(__file__).resolve().parent / "assets" / "NocturnalBarDesktopIcon.ico",
        Path(__file__).resolve().parent.parent / "NocturnalBarDesktopIcon.png",
    ]
    return next((path for path in candidates if path.exists()), candidates[-1])


if __name__ == "__main__":
    if sys.platform.startswith("win") and getattr(sys, "frozen", False):
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Nocturnal.Caja"
        )
    app = QApplication(sys.argv)
    icon_path = _desktop_icon_path()
    app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    sys.exit(app.exec())
