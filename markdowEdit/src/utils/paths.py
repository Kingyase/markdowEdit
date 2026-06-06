from __future__ import annotations

import sys
from pathlib import Path


def resource_root() -> Path:
    """Locate the bundled `resources/` directory in dev and PyInstaller modes."""
    if getattr(sys, "frozen", False):
        # PyInstaller --onedir / --onefile both expose _MEIPASS
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parents[2]
    return base / "resources"


def model_path() -> Path:
    root = resource_root() / "models"
    if not root.exists():
        return root / "translate-en_zh.argosmodel"
    candidates = sorted(root.glob("translate-en_zh*.argosmodel"))
    return candidates[0] if candidates else root / "translate-en_zh.argosmodel"


def dict_path() -> Path:
    return resource_root() / "dict" / "ecdict.sqlite"
