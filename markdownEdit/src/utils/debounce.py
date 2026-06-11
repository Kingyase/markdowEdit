from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class Debouncer(QObject):
    """QTimer-based debouncer that emits triggered after a quiet period."""
    triggered = pyqtSignal()

    def __init__(self, delay_ms: int, parent: QObject | None = None):
        """Initialize with a delay in milliseconds. Fires once input stops for that duration."""
        # 以毫秒延迟初始化。输入停止该时长后触发
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self.triggered)

    def kick(self) -> None:
        """Reset the timer. Call on every input event."""
        # 重置定时器。每次输入事件时调用
        self._timer.start()
