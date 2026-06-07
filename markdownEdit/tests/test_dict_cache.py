import sqlite3
import time

import pytest

from src.translate.dict_cache import DictCache, init_schema


@pytest.fixture
def cache(tmp_path):
    db = tmp_path / "ec.sqlite"
    init_schema(db)
    with sqlite3.connect(db) as conn:
        conn.executemany(
            "INSERT INTO words VALUES (?, ?, ?)",
            [
                ("hello", "你好", "həˈləʊ"),
                ("world", "世界", "wɜːld"),
            ],
        )
        conn.commit()
    return DictCache(db)


def test_lookup_hits(cache):
    entry = cache.lookup("hello")
    assert entry is not None
    assert entry.translation == "你好"


def test_lookup_case_insensitive(cache):
    assert cache.lookup("HELLO").translation == "你好"


def test_lookup_miss(cache):
    assert cache.lookup("zzznotaword") is None


def test_non_ascii_returns_none(cache):
    assert cache.lookup("你好") is None


def test_lookup_is_fast(cache):
    start = time.perf_counter()
    for _ in range(100):
        cache.lookup("hello")
    elapsed_ms = (time.perf_counter() - start) * 1000 / 100
    assert elapsed_ms < 30
