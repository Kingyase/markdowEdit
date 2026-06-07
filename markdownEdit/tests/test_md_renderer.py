from src.render.md_renderer import MarkdownRenderer


def test_render_basic_html():
    html = MarkdownRenderer().render("# Hello\n\nworld")
    assert "<h1" in html and "Hello" in html
    assert "<p>world</p>" in html


def test_fenced_code_renders_pre():
    md = "```python\nprint('hi')\n```"
    html = MarkdownRenderer().render(md)
    assert "<pre" in html or "<code" in html


def test_render_bilingual_pairs():
    pairs = [("Hello", "你好"), ("World", "")]
    html = MarkdownRenderer().render_bilingual(pairs)
    assert "Hello" in html and "你好" in html
    assert "World" in html
    assert html.count('class="translation"') == 1


def test_render_translation_only_marks_pending():
    html = MarkdownRenderer().render_translation_only(["你好", "", "世界"])
    assert "你好" in html and "世界" in html
    assert html.count('class="pending"') == 1
