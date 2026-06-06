import sys
from pathlib import Path

# Import ctranslate2 BEFORE Qt to avoid DLL loading issues on Windows
# (Qt changes the DLL search path, causing torch's c10.dll to fail)
try:
    import ctranslate2
    from ctranslate2 import converters, models, specs
except Exception:
    pass

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from src import APP_NAME
from src.ui.main_window import MainWindow


def main() -> int:
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("MarkdownEdit")
    icon_path = str(Path(__file__).parent.parent / "resources" / "app_icon.ico")
    app.setWindowIcon(QIcon(icon_path))
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
