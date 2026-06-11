"""Build resources/dict/ecdict.sqlite from the ECDICT CSV.

Usage:
    python scripts/build_ecdict.py [path/to/ecdict.csv]

If no CSV path is given, the script will download the ECDICT basic edition
from GitHub automatically.

Source CSV: https://github.com/skywind3000/ECDICT
Fields kept: word, translation, phonetic
"""
from __future__ import annotations

import csv
import sqlite3
import sys
import urllib.request
from pathlib import Path


ECDICT_URL = "https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv"


def _download_csv(url: str, dest: Path) -> None:
    """Download the ECDICT CSV to dest, showing a simple progress indicator."""
    print(f"Downloading {url} ...")
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    print(f"Downloaded {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def build(csv_path: Path, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    conn = sqlite3.connect(out_path)
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute(
        "CREATE TABLE words ("
        "word TEXT PRIMARY KEY COLLATE NOCASE, "
        "translation TEXT, "
        "phonetic TEXT)"
    )

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = (
            (
                (row.get("word") or "").strip(),
                (row.get("translation") or "").strip(),
                (row.get("phonetic") or "").strip(),
            )
            for row in reader
        )
        rows = (r for r in rows if r[0] and r[1])
        conn.executemany("INSERT OR REPLACE INTO words VALUES (?, ?, ?)", rows)

    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    print(f"Wrote {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")


def main():
    project_root = Path(__file__).resolve().parents[1]
    out_path = project_root / "resources" / "dict" / "ecdict.sqlite"

    if len(sys.argv) >= 2:
        csv_path = Path(sys.argv[1])
        if not csv_path.exists():
            print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
            sys.exit(1)
    else:
        csv_path = project_root / "resources" / "dict" / "ecdict.csv"
        if not csv_path.exists():
            _download_csv(ECDICT_URL, csv_path)
        else:
            print(f"Using cached CSV: {csv_path}")

    build(csv_path, out_path)


if __name__ == "__main__":
    main()
