"""Build resources/dict/ecdict.sqlite from the ECDICT CSV.

Usage:
    python scripts/build_ecdict.py path/to/ecdict.csv

Source CSV: https://github.com/skywind3000/ECDICT (basic edition,
fields: word, phonetic, definition, translation, ...).
We keep only word, translation, phonetic for a lean ~50MB DB.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path


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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/build_ecdict.py <ecdict.csv>", file=sys.stderr)
        sys.exit(2)
    project_root = Path(__file__).resolve().parents[1]
    build(Path(sys.argv[1]), project_root / "resources" / "dict" / "ecdict.sqlite")
