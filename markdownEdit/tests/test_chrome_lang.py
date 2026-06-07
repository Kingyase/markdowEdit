from src.utils.chrome import _force_lang_en


def test_inserts_lang_when_missing():
    out = _force_lang_en("<!doctype html><html><body>x</body></html>")
    assert 'lang="en"' in out
    assert "<body>x</body>" in out


def test_replaces_existing_lang():
    out = _force_lang_en('<html lang="zh-CN"><body>x</body></html>')
    assert 'lang="en"' in out
    assert 'lang="zh-CN"' not in out


def test_wraps_when_no_html_tag():
    out = _force_lang_en("<p>hi</p>")
    assert out.startswith('<!doctype html><html lang="en">')
    assert "<p>hi</p>" in out
