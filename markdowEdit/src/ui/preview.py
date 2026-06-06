from PyQt5.QtCore import QUrl, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMenu


class PreviewView(QWebEngineView):
    openInChromeRequested = pyqtSignal()
    saveHtmlRequested = pyqtSignal()
    savePdfRequested = pyqtSignal()
    saveWordRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_html = ""

    def show_html(self, html: str) -> None:
        if html == self._last_html:
            return
        self._last_html = html
        self.setHtml(html, QUrl("about:blank"))

    def current_html(self) -> str:
        return self._last_html

    def set_scroll_ratio(self, ratio: float) -> None:
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
