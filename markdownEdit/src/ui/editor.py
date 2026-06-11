from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QPlainTextEdit

from src.utils.debounce import Debouncer


class MarkdownEditor(QPlainTextEdit):
    """Plain-text editor that debounces textChanged into a stable signal."""
    # 将 textChanged 信号防抖为稳定信号的纯文本编辑器

    contentSettled = pyqtSignal(str)

    def __init__(self, parent=None, debounce_ms: int = 150):
        """Set up line wrapping and a debouncer for the textChanged signal."""
        # 设置自动换行和 textChanged 信号的防抖器
        super().__init__(parent)
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.setTabChangesFocus(False)
        self.setAcceptDrops(False)
        self._debouncer = Debouncer(debounce_ms, self)
        self._debouncer.triggered.connect(self._emit_settled)
        self.textChanged.connect(self._debouncer.kick)

    def _emit_settled(self) -> None:
        """Emit the settled signal with the current editor content."""
        # 发送当前编辑器内容的 settled 信号
        self.contentSettled.emit(self.toPlainText())
