"""Open arbitrary HTML in Google Chrome so its built-in translate prompt fires.

Strategy: Chrome's auto-translate banner triggers when the page's declared
language differs from the user's UI language. We persist the current HTML to
a temp file with ``<html lang="en">`` and launch Chrome on it.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path


def _candidate_paths() -> list[Path]:
    """Return common Chrome executable install paths based on environment variables."""
    # 返回基于环境变量的常见 Chrome 可执行文件安装路径
    paths = []
    for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            paths.append(Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe")
    return paths


def _find_chrome_via_registry() -> str | None:
    """Locate Chrome executable via Windows Registry App Paths."""
    # 通过 Windows 注册表 App Paths 定位 Chrome 可执行文件
    if sys.platform != "win32":
        return None
    try:
        import winreg
    except ImportError:
        return None
    keys = [
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
    ]
    for root, path in keys:
        try:
            with winreg.OpenKey(root, path) as k:
                val, _ = winreg.QueryValueEx(k, None)
                if val and Path(val).exists():
                    return val
        except OSError:
            continue
    return None


def find_chrome() -> str | None:
    """Return path to Chrome executable, checking registry then candidate paths."""
    # 返回 Chrome 可执行文件路径，优先查注册表，其次查候选路径
    via_reg = _find_chrome_via_registry()
    if via_reg:
        return via_reg
    for p in _candidate_paths():
        if p.exists():
            return str(p)
    return None


_HTML_TAG_RE = re.compile(r"<html(\s[^>]*)?>", re.IGNORECASE)


def _force_lang_en(html: str) -> str:
    """Force <html lang="en"> attribute to trigger Chrome translate prompt."""
    # 强制设置 <html lang="en"> 属性以触发 Chrome 翻译提示
    def replace(match: re.Match) -> str:
        attrs = match.group(1) or ""
        if re.search(r"\blang\s*=", attrs, re.IGNORECASE):
            return re.sub(r'\blang\s*=\s*"[^"]*"', 'lang="en"', match.group(0), count=1, flags=re.IGNORECASE)
        return f"<html{attrs} lang=\"en\">"

    new_html, n = _HTML_TAG_RE.subn(replace, html, count=1)
    if n == 0:
        return '<!doctype html><html lang="en">' + html + "</html>"
    return new_html


def open_html_in_chrome_translate(html: str) -> tuple[bool, str]:
    """Persist html to a temp file and open it. Returns (used_chrome, message)."""
    # 将 html 持久化到临时文件并打开。返回 (是否使用 Chrome, 消息)
    html = _force_lang_en(html)
    fd, name = tempfile.mkstemp(prefix="markdownedit_preview_", suffix=".html")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html)
    file_uri = Path(name).as_uri()

    chrome = find_chrome()
    if chrome:
        try:
            subprocess.Popen([chrome, "--lang=zh-CN", file_uri], close_fds=True)
            return True, f"已用 Chrome 打开:{name}"
        except OSError as e:
            return False, f"启动 Chrome 失败:{e}"

    if webbrowser.open(file_uri):
        return False, f"未检测到 Chrome,已用默认浏览器打开:{name}"
    return False, f"无法打开浏览器,文件位于:{name}"
