"""Download the Argos en→zh model into resources/models/.

Requires `argostranslate` installed. Internet is needed once at build time;
the resulting .argosmodel is bundled and the runtime is fully offline.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> int:
    import argostranslate.package as pkg

    pkg.update_package_index()
    available = pkg.get_available_packages()
    try:
        target = next(p for p in available if p.from_code == "en" and p.to_code == "zh")
    except StopIteration:
        print("No en→zh package found in the Argos index", file=sys.stderr)
        return 1

    downloaded = Path(target.download())
    out_dir = Path(__file__).resolve().parents[1] / "resources" / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / downloaded.name
    shutil.copy2(downloaded, out_path)
    print(f"Saved model to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
