from PyQt5.QtCore import QUrl, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMenu


class PreviewView(QWebEngineView):
    """HTML preview pane with a context menu for export and Chrome translate."""
    # HTML 预览面板，带导出和 Chrome 翻译的右键菜单

    openInChromeRequested = pyqtSignal()
    saveHtmlRequested = pyqtSignal()
    savePdfRequested = pyqtSignal()
    saveWordRequested = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the preview with an empty last-html cache."""
        # 初始化预览视图，缓存为空
        super().__init__(parent)
        self._last_html = ""

    def show_html(self, html: str) -> None:
        """Display HTML content; skips update if content is unchanged."""
        # 显示 HTML 内容；内容未变化时跳过更新
        if html == self._last_html:
            return
        self._last_html = html
        self.setHtml(html, QUrl("about:blank"))

    def current_html(self) -> str:
        """Return the last rendered HTML string."""
        # 返回最后渲染的 HTML 字符串
        return self._last_html

    def set_scroll_ratio(self, ratio: float) -> None:
        """Set the page scroll position as a ratio (0.0–1.0)."""
        # 按比例（0.0–1.0）设置页面滚动位置
        ratio = max(0.0, min(1.0, ratio))
        js = (
            "(function(){"
            "var d=document.documentElement, b=document.body;"
            "var max=Math.max(d.scrollHeight,b.scrollHeight)-window.innerHeight;"
            f"window.scrollTo(0, max*{ratio});"
            "})();"
        )
        self.page().runJavaScript(js)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Show a right-click menu with export and Chrome translate options."""
        # 显示包含导出和 Chrome 翻译选项的右键菜单
        menu = QMenu(self)
        act_html = menu.addAction("保存为 HTML")
        act_html.triggered.connect(self.saveHtmlRequested.emit)
        act_pdf = menu.addAction("保存为 PDF")
        act_pdf.triggered.connect(self.savePdfRequested.emit)
        act_word = menu.addAction("保存为 Word")
        act_word.triggered.connect(self.saveWordRequested.emit)
        menu.addSeparator()
        act_chrome = menu.addAction("用 Chrome 打开并翻译")
        act_chrome.triggered.connect(self.openInChromeRequested.emit)
        menu.exec_(event.globalPos())
