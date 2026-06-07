import sqlite3
from pathlib import Path
from typing import NamedTuple


class WordEntry(NamedTuple):
    word: str
    translation: str
    phonetic: str


class DictCache:
    """Read-only ECDICT lookup backed by SQLite."""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            if not self._db_path.exists():
                raise FileNotFoundError(f"Dictionary not found: {self._db_path}")
            self._conn = sqlite3.connect(
                f"file:{self._db_path}?mode=ro", uri=True, check_same_thread=False
            )
        return self._conn

    def lookup(self, word: str) -> WordEntry | None:
        if not word or not word.isascii():
            return None
        cur = self._connect().execute(
            "SELECT word, translation, phonetic FROM words WHERE word = ? COLLATE NOCASE LIMIT 1",
            (word,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return WordEntry(row[0], row[1] or "", row[2] or "")

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None


def init_schema(db_path: Path) -> None:
    """Create an empty ECDICT-compatible schema (used by build/import scripts)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS words ("
            "word TEXT PRIMARY KEY COLLATE NOCASE, "
            "translation TEXT, "
            "phonetic TEXT)"
        )
        conn.commit()
