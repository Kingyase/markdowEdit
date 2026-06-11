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
    """A single editor tab containing the left editor and right stacked view."""
    # 包含左侧编辑器和右侧堆叠视图的单个编辑器标签页

    contentSettled = pyqtSignal(str)
    dirtyChanged = pyqtSignal(bool)
    fileDropped = pyqtSignal(str)
    openInChromeRequested = pyqtSignal()
    saveHtmlRequested = pyqtSignal()
    savePdfRequested = pyqtSignal()
    saveWordRequested = pyqtSignal()

    def __init__(self, renderer: MarkdownRenderer, parent=None):
        """Build the split layout: editor on the left, QStackedWidget on the right."""
        # 构建分栏布局：左侧编辑器，右侧 QStackedWidget
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
        """Return the file path of the currently opened document, or None."""
        # 返回当前打开文档的文件路径，或 None
        return self._path

    @current_path.setter
    def current_path(self, p: Path | None):
        """Set the file path for this tab."""
        # 设置此标签页的文件路径
        self._path = p

    @property
    def is_dirty(self) -> bool:
        """Return True if the editor has unsaved changes."""
        # 如果编辑器有未保存更改则返回 True
        return self._dirty

    @property
    def tab_title(self) -> str:
        """Return the tab display text including dirty marker."""
        # 返回标签页显示文本（含脏标记）
        name = self._path.name if self._path else "未命名"
        mark = " *" if self._dirty else ""
        return f"{name}{mark}"

    def set_view_index(self, index: int) -> None:
        """Switch the right pane to the given view index and refresh its content."""
        # 将右侧面板切换到指定视图索引并刷新内容
        self._view_index = index
        self.right_stack.setCurrentIndex(index)
        self._refresh_right_pane()

    def current_view_index(self) -> int:
        """Return the index of the currently active right-pane view."""
        # 返回当前活动右侧面板的视图索引
        return self._view_index

    def markdown_text(self) -> str:
        """Return the current editor content as plain text."""
        # 返回当前编辑器内容为纯文本
        return self.editor.toPlainText()

    def set_markdown_text(self, text: str) -> None:
        """Replace the editor content with the given text."""
        # 用给定文本替换编辑器内容
        self.editor.setPlainText(text)

    def _on_content_settled(self, text: str) -> None:
        """Refresh the right pane when editor content stabilizes."""
        # 当编辑器内容稳定时刷新右侧面板
        self._refresh_right_pane()
        self.contentSettled.emit(text)

    def _on_text_changed(self) -> None:
        """Mark the tab as dirty when text changes."""
        # 文本变化时将标签页标记为脏
        if not self._dirty:
            self._dirty = True
            self.dirtyChanged.emit(True)

    def _refresh_right_pane(self) -> None:
        """Re-render the active view (translation or preview) with current content."""
        # 使用当前内容重新渲染活动视图（翻译或预览）
        text = self.editor.toPlainText()
        if self.right_stack.currentIndex() == VIEW_TRANSLATION:
            html = self._render_translation(text)
            self.translation_view.show_html(html)
        else:
            html = self._renderer.render(text)
            self.preview.show_html(html)

    def _render_translation(self, text: str) -> str:
        """Split text into paragraphs, look up cached translations, enqueue new ones, render."""
        # 将文本分段，查找缓存翻译，入队新段落，渲染结果
        paragraphs = split_paragraphs(text)
        worker = get_active_worker()
        if worker is None:
            translations = ["" for _ in paragraphs]
        else:
            translations = [worker.lookup_cached(p) for p in paragraphs]
            worker.request(paragraphs)
        return self._renderer.render_translation_only(translations)

    def _sync_scroll(self, _value: int) -> None:
        """Synchronize the right-pane scroll position with the editor scrollbar."""
        # 同步右侧面板滚动位置与编辑器滚动条
        bar = self.editor.verticalScrollBar()
        rng = bar.maximum() - bar.minimum()
        ratio = (bar.value() - bar.minimum()) / rng if rng > 0 else 0.0
        if self.right_stack.currentIndex() == VIEW_TRANSLATION:
            self.translation_view.set_scroll_ratio(ratio)
        else:
            self.preview.set_scroll_ratio(ratio)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accept drag events that carry file URLs."""
        # 接受携带文件 URL 的拖放事件
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle file drops and emit fileDropped for .md / .markdown / .txt files."""
        # 处理文件拖放，为 .md/.markdown/.txt 文件发送 fileDropped 信号
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                if path.endswith((".md", ".markdown", ".txt")):
                    self.fileDropped.emit(path)
                    event.acceptProposedAction()
                    return
        event.ignore()