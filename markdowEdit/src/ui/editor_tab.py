from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import QSplitter, QStackedWidget, QVBoxLayout, QWidget

from src.render.md_renderer import MarkdownRenderer
from src.render.paragraphs import split_paragraphs
from src.translate.worker import get_active_worker
from src.ui.editor import MarkdownEditor
from src.ui.preview import PreviewView
from src.ui.translation_view import TranslationView

VIEW_TRANSLATION = 0
VIEW_PREVIEW = 1


class EditorTab(QWidget):
    contentSettled = pyqtSignal(str)
    dirtyChanged = pyqtSignal(bool)
    fileDropped = pyqtSignal(str)
    openInChromeRequested = pyqtSignal()
    saveHtmlRequested = pyqtSignal()
    savePdfRequested = pyqtSignal()
    saveWordRequested = pyqtSignal()

    def __init__(self, renderer: MarkdownRenderer, parent=None):
        super().__init__(parent)
        self._renderer = renderer
        self._path: Path | None = None
        self._dirty = False
        self._view_index = VIEW_PREVIEW

        self.editor = MarkdownEditor(self)
        self.preview = PreviewView(self)
        self.translation_view = TranslationView(self)

        self.right_stack = QStackedWidget(self)
        self.right_stack.insertWidget(VIEW_TRANSLATION, self.translation_view)
        self.right_stack.insertWidget(VIEW_PREVIEW, self.preview)

        self.editor.contentSettled.connect(self._on_content_settled)
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.verticalScrollBar().valueChanged.connect(self._sync_scroll)

        self.preview.openInChromeRequested.connect(self.openInChromeRequested)
        self.preview.saveHtmlRequested.connect(self.saveHtmlRequested)
        self.preview.savePdfRequested.connect(self.savePdfRequested)
        self.preview.saveWordRequested.connect(self.saveWordRequested)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.right_stack)
        splitter.setSizes([600, 600])
        splitter.setChildrenCollapsible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self.right_stack.setCurrentIndex(self._view_index)

        self.setAcceptDrops(True)

    @property
    def current_path(self) -> Path | None:
        return self._path

    @current_path.setter
    def current_path(self, p: Path | None):
        self._path = p

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    @property
    def tab_title(self) -> str:
        name = self._path.name if self._path else "未命名"
        mark = " *" if self._dirty else ""
        return f"{name}{mark}"

    def set_view_index(self, index: int) -> None:
        self._view_index = index
        self.right_stack.setCurrentIndex(index)
        self._refresh_right_pane()

    def current_view_index(self) -> int:
        return self._view_index

    def markdown_text(self) -> str:
        return self.editor.toPlainText()

    def set_markdown_text(self, text: str) -> None:
        self.editor.setPlainText(text)

    def _on_content_settled(self, text: str) -> None:
        self._refresh_right_pane()
        self.contentSettled.emit(text)

    def _on_text_changed(self) -> None:
        if not self._dirty:
            self._dirty = True
            self.dirtyChanged.emit(True)

    def _refresh_right_pane(self) -> None:
        text = self.editor.toPlainText()
        if self.right_stack.currentIndex() == VIEW_TRANSLATION:
            html = self._render_translation(text)
            self.translation_view.show_html(html)
        else:
            html = self._renderer.render(text)
            self.preview.show_html(html)

    def _render_translation(self, text: str) -> str:
        paragraphs = split_paragraphs(text)
        worker = get_active_worker()
        if worker is None:
            translations = ["" for _ in paragraphs]
        else:
            translations = [worker.lookup_cached(p) for p in paragraphs]
            worker.request(paragraphs)
        return self._renderer.render_translation_only(translations)

    def _sync_scroll(self, _value: int) -> None:
        bar = self.editor.verticalScrollBar()
        rng = bar.maximum() - bar.minimum()
        ratio = (bar.value() - bar.minimum()) / rng if rng > 0 else 0.0
        if self.right_stack.currentIndex() == VIEW_TRANSLATION:
            self.translation_view.set_scroll_ratio(ratio)
        else:
            self.preview.set_scroll_ratio(ratio)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                if path.endswith((".md", ".markdown", ".txt")):
                    self.fileDropped.emit(path)
                    event.acceptProposedAction()
                    return
        event.ignore()