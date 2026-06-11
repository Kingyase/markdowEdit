from __future__ import annotations

import sys
from pathlib import Path


def resource_root() -> Path:
    """Locate the bundled `resources/` directory in dev and PyInstaller modes."""
    # 在开发环境和 PyInstaller 模式下定位 bundled resources 目录
    if getattr(sys, "frozen", False):
        # PyInstaller --onedir / --onefile both expose _MEIPASS
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parents[2]
    return base / "resources"


def model_path() -> Path:
    """Return path to the first Argos translation model matching the wildcard pattern."""
    # 返回第一个匹配通配符模式的 Argos 翻译模型路径
    root = resource_root() / "models"
    if not root.exists():
        return root / "translate-en_zh.argosmodel"
    candidates = sorted(root.glob("translate-en_zh*.argosmodel"))
    return candidates[0] if candidates else root / "translate-en_zh.argosmodel"


def dict_path() -> Path:
    """Return path to the ECDICT SQLite dictionary."""
    # 返回 ECDICT SQLite 词典路径
    return resource_root() / "dict" / "ecdict.sqlite"
