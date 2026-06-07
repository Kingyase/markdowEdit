import markdown


_BASE_CSS = """
body { font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
       padding: 16px 24px; line-height: 1.6; color: #24292e; }
h1, h2, h3, h4 { border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
code { background: #f6f8fa; padding: .2em .4em; border-radius: 3px;
       font-family: Consolas, "Courier New", monospace; }
pre { background: #f6f8fa; padding: 12px; border-radius: 6px; overflow-x: auto; }
pre code { background: transparent; padding: 0; }
blockquote { border-left: 4px solid #dfe2e5; color: #6a737d; padding: 0 1em; margin: 0; }
table { border-collapse: collapse; }
th, td { border: 1px solid #dfe2e5; padding: 6px 13px; }
.translation { background: #fff8e1; padding: 8px 12px; border-radius: 4px;
               margin: 4px 0 16px; color: #5d4037; font-size: 0.95em; }
.original { margin-bottom: 4px; }
.pending { color: #999; font-style: italic; }
"""


class MarkdownRenderer:
    def __init__(self) -> None:
        self._md = markdown.Markdown(
            extensions=["extra", "fenced_code", "codehilite", "toc", "tables"],
            extension_configs={"codehilite": {"guess_lang": False, "noclasses": True}},
        )

    def render(self, text: str) -> str:
        self._md.reset()
        body = self._md.convert(text)
        return self._wrap(body)

    def render_bilingual(self, pairs: list[tuple[str, str]]) -> str:
        """Render a list of (original_md, translation_text) blocks side-by-side."""
        parts = []
        for original, translation in pairs:
            self._md.reset()
            html = self._md.convert(original)
            parts.append(f'<div class="original">{html}</div>')
            if translation:
                parts.append(f'<div class="translation">{translation}</div>')
        return self._wrap("\n".join(parts))

    def render_translation_only(self, translations: list[str]) -> str:
        """Render a sequence of translated paragraphs as standalone markdown."""
        parts = []
        for translation in translations:
            if translation:
                self._md.reset()
                parts.append(self._md.convert(translation))
            else:
                parts.append('<p class="pending">…</p>')
        return self._wrap("\n".join(parts))

    @staticmethod
    def _wrap(body: str) -> str:
        return f"<!doctype html><html><head><meta charset='utf-8'><style>{_BASE_CSS}</style></head><body>{body}</body></html>"
