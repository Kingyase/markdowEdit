def split_paragraphs(text: str) -> list[str]:
    """Split markdown text on blank lines, preserving fenced code blocks intact."""
    blocks: list[str] = []
    buf: list[str] = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            buf.append(line)
            continue
        if not in_fence and not line.strip():
            if buf:
                blocks.append("\n".join(buf))
                buf = []
        else:
            buf.append(line)
    if buf:
        blocks.append("\n".join(buf))
    return blocks
