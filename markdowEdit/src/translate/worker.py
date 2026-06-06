from __future__ import annotations

import hashlib
import queue
from collections import OrderedDict
from pathlib import Path

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from src.translate.engine import TranslationEngine


_active_worker: "TranslationWorker | None" = None


def get_active_worker() -> "TranslationWorker | None":
    return _active_worker


def set_active_worker(worker: "TranslationWorker | None") -> None:
    global _active_worker
    _active_worker = worker


class _LRU:
    def __init__(self, maxsize: int = 512):
        self._maxsize = maxsize
        self._d: OrderedDict[str, str] = OrderedDict()

    def get(self, key: str) -> str | None:
        if key in self._d:
            self._d.move_to_end(key)
            return self._d[key]
        return None

    def set(self, key: str, value: str) -> None:
        self._d[key] = value
        self._d.move_to_end(key)
        while len(self._d) > self._maxsize:
            self._d.popitem(last=False)


def _key(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


class TranslationWorker(QObject):
    """Background paragraph translator. Emits translated(original, translation)."""

    translated = pyqtSignal(str, str)
    failed = pyqtSignal(str)

    def __init__(self, model_path: Path):
        super().__init__()
        self._model_path = model_path
        self._engine = TranslationEngine(model_path)
        self._cache = _LRU(maxsize=512)
        self._queue: "queue.Queue[str | None]" = queue.Queue()
        self._inflight: set[str] = set()
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self._run)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._queue.put(None)
        self._thread.quit()
        self._thread.wait(2000)

    def lookup_cached(self, text: str) -> str:
        return self._cache.get(_key(text)) or ""

    def request(self, paragraphs: list[str]) -> None:
        for p in paragraphs:
            if not p.strip():
                continue
            k = _key(p)
            if self._cache.get(k) is not None or k in self._inflight:
                continue
            self._inflight.add(k)
            self._queue.put(p)

    def _run(self) -> None:
        while True:
            items = []
            item = self._queue.get()
            if item is None:
                return
            items.append(item)
            while len(items) < 32:
                try:
                    item = self._queue.get_nowait()
                    if item is None:
                        return
                    items.append(item)
                except queue.Empty:
                    break
            try:
                translated = []
                for item in items:
                    try:
                        translated.append(self._engine.translate(item))
                    except Exception as e2:
                        translated.append("")
                        self.failed.emit(f"item failed: {e2}")
            except Exception as e:
                for item in items:
                    self._inflight.discard(_key(item))
                self.failed.emit(str(e))
                continue
            for item, trans in zip(items, translated):
                self._cache.set(_key(item), trans)
                self._inflight.discard(_key(item))
                self.translated.emit(item, trans)
