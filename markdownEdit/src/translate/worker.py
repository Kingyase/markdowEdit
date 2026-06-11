from __future__ import annotations

import hashlib
import queue
from collections import OrderedDict
from pathlib import Path

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from src.translate.engine import TranslationEngine


_active_worker: "TranslationWorker | None" = None


def get_active_worker() -> "TranslationWorker | None":
    """Return the currently active TranslationWorker singleton."""
    # 返回当前活跃的 TranslationWorker 单例
    return _active_worker


def set_active_worker(worker: "TranslationWorker | None") -> None:
    """Set the active TranslationWorker singleton. Used during init / teardown."""
    # 设置当前活跃的 TranslationWorker 单例，用于初始化/销毁
    global _active_worker
    _active_worker = worker


class _LRU:
    """Simple LRU cache backed by OrderedDict."""
    # 基于 OrderedDict 的简单 LRU 缓存

    def __init__(self, maxsize: int = 512):
        """Initialize LRU cache with a maximum number of entries."""
        # 初始化 LRU 缓存，设置最大条目数
        self._maxsize = maxsize
        self._d: OrderedDict[str, str] = OrderedDict()

    def get(self, key: str) -> str | None:
        """Retrieve a value; promotes entry to most-recently-used."""
        # 获取值；将该条目提升为最近使用
        if key in self._d:
            self._d.move_to_end(key)
            return self._d[key]
        return None

    def set(self, key: str, value: str) -> None:
        """Insert or update a cache entry; evicts oldest if over capacity."""
        # 插入或更新缓存条目；超出容量时淘汰最旧的
        self._d[key] = value
        self._d.move_to_end(key)
        while len(self._d) > self._maxsize:
            self._d.popitem(last=False)


def _key(text: str) -> str:
    """Return MD5 hex digest of text for use as cache key."""
    # 返回文本的 MD5 十六进制摘要，用作缓存键
    return hashlib.md5(text.encode("utf-8")).hexdigest()


class TranslationWorker(QObject):
    """Background paragraph translator. Emits translated(original, translation)."""
    # 后台段落翻译器。发送 translated(原文, 译文) 信号

    translated = pyqtSignal(str, str)
    failed = pyqtSignal(str)

    def __init__(self, model_path: Path):
        """Initialize the worker, its LRU cache, and move it to a dedicated QThread."""
        # 初始化工作器及其 LRU 缓存，并将其移至专用 QThread
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
        """Start the background translation thread."""
        # 启动后台翻译线程
        self._thread.start()

    def stop(self) -> None:
        """Signal the worker to stop and wait for the thread to finish."""
        # 通知工作器停止并等待线程结束
        self._queue.put(None)
        self._thread.quit()
        self._thread.wait(2000)

    def lookup_cached(self, text: str) -> str:
        """Return cached translation for text, or empty string if not found."""
        # 返回文本的缓存翻译结果，未找到则返回空字符串
        return self._cache.get(_key(text)) or ""

    def request(self, paragraphs: list[str]) -> None:
        """Enqueue unseen paragraphs for translation, skipping blank/cached/inflight items."""
        # 将未见过的段落加入翻译队列，跳过空白/已缓存/正在处理的项目
        for p in paragraphs:
            if not p.strip():
                continue
            k = _key(p)
            if self._cache.get(k) is not None or k in self._inflight:
                continue
            self._inflight.add(k)
            self._queue.put(p)

    def _run(self) -> None:
        """Main loop: drain up to 32 items from queue, translate each, emit results."""
        # 主循环：从队列中取出最多 32 条，逐条翻译，发送结果信号
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
