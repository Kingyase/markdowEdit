import re
from pathlib import Path

from PyQt5.QtCore import QEvent, QObject, QPoint
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QPlainTextEdit, QToolTip

from src.translate.dict_cache import DictCache


_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")


class HoverTranslator(QObject):
    """Show a Chinese gloss tooltip when the mouse hovers an English word."""

    def __init__(self, editor: QPlainTextEdit, dict_path: Path):
        super().__init__(editor)
        self._editor = editor
        self._cache = DictCache(dict_path)
        self._editor.viewport().setMouseTracking(True)
        self._editor.viewport().installEventFilter(self)
        self._last_word: str | None = None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove and obj is self._editor.viewport():
            self._handle_move(event.pos())
        elif event.type() == QEvent.Leave:
            QToolTip.hideText()
            self._last_word = None
        return False

    def _handle_move(self, pos: QPoint) -> None:
        cursor = self._editor.cursorForPosition(pos)
        cursor.select(QTextCursor.WordUnderCursor)
        word = cursor.selectedText()
        if not word or not _WORD_RE.fullmatch(word):
            if self._last_word is not None:
                QToolTip.hideText()
                self._last_word = None
            return
        if word == self._last_word:
            return
        self._last_word = word
        try:
            entry = self._cache.lookup(word)
        except FileNotFoundError:
            return
        if entry is None or not entry.translation:
            QToolTip.hideText()
            return
        text = entry.translation.replace("\\n", "\n")
        if entry.phonetic:
            text = f"[{entry.phonetic}]\n{text}"
        global_pos = self._editor.viewport().mapToGlobal(pos)
        QToolTip.showText(global_pos, text, self._editor.viewport())
