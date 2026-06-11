import sqlite3
from pathlib import Path
from typing import NamedTuple


class WordEntry(NamedTuple):
    word: str
    translation: str
    phonetic: str


class DictCache:
    """Read-only ECDICT lookup backed by SQLite."""
    # 基于 SQLite 的只读 ECDICT 查询

    def __init__(self, db_path: Path):
        """Open a read-only SQLite connection to the ECDICT database. Connection is lazy."""
        # 打开到 ECDICT 数据库的只读 SQLite 连接，延迟创建
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        """Return the SQLite connection, creating it on first access."""
        # 返回 SQLite 连接，首次访问时创建
        if self._conn is None:
            if not self._db_path.exists():
                raise FileNotFoundError(f"Dictionary not found: {self._db_path}")
            self._conn = sqlite3.connect(
                f"file:{self._db_path}?mode=ro", uri=True, check_same_thread=False
            )
        return self._conn

    def lookup(self, word: str) -> WordEntry | None:
        """Look up a word in ECDICT. Returns WordEntry or None. Case-insensitive, ASCII-only."""
        # 在 ECDICT 中查询单词。返回 WordEntry 或 None。不区分大小写，仅支持 ASCII
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
        """Close the SQLite connection if open."""
        # 关闭 SQLite 连接（如果已打开）
        if self._conn is not None:
            self._conn.close()
            self._conn = None


def init_schema(db_path: Path) -> None:
    """Create an empty ECDICT-compatible schema (used by build/import scripts)."""
    # 创建空的 ECDICT 兼容模式（用于构建/导入脚本）
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS words ("
            "word TEXT PRIMARY KEY COLLATE NOCASE, "
            "translation TEXT, "
            "phonetic TEXT)"
        )
        conn.commit()
