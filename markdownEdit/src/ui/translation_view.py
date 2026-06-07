"""Right-pane views. Both share the same editor on the left; what differs is
the rendering on the right pane.

- TranslationView: renders Chinese-only paragraph translations.
- PreviewView (existing): renders full Markdown HTML preview.
"""
from __future__ import annotations

from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView


class TranslationView(QWebEngineView):
    """Pure Chinese translation render. Uses MarkdownRenderer.render_translation_only."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_html = ""

    def show_html(self, html: str) -> None:
        if html == self._last_html:
            return
        self._last_html = html
        self.setHtml(html, QUrl("about:blank"))

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
