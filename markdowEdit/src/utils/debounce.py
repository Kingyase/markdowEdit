from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class Debouncer(QObject):
    triggered = pyqtSignal()

    def __init__(self, delay_ms: int, parent: QObject | None = None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self.triggered)

    def kick(self) -> None:
        self._timer.start()
