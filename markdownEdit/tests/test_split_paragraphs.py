from src.render.paragraphs import split_paragraphs


def test_blank_line_splits():
    text = "first\n\nsecond\n\nthird"
    assert split_paragraphs(text) == ["first", "second", "third"]


def test_fenced_code_kept_as_one_block():
    text = "intro\n\n```py\na = 1\n\nb = 2\n```\n\nouter"
    blocks = split_paragraphs(text)
    assert blocks[0] == "intro"
    assert blocks[1].startswith("```py") and blocks[1].endswith("```")
    assert "a = 1" in blocks[1] and "b = 2" in blocks[1]
    assert blocks[2] == "outer"


def test_trailing_text_kept():
    assert split_paragraphs("only one") == ["only one"]
