from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QPlainTextEdit

from src.utils.debounce import Debouncer


class MarkdownEditor(QPlainTextEdit):
    """Plain-text editor that debounces textChanged into a stable signal."""

    contentSettled = pyqtSignal(str)

    def __init__(self, parent=None, debounce_ms: int = 150):
        super().__init__(parent)
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.setTabChangesFocus(False)
        self.setAcceptDrops(False)
        self._debouncer = Debouncer(debounce_ms, self)
        self._debouncer.triggered.connect(self._emit_settled)
        self.textChanged.connect(self._debouncer.kick)

    def _emit_settled(self) -> None:
        self.contentSettled.emit(self.toPlainText())
