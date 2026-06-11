from __future__ import annotations
from pathlib import Path
from typing import Iterable


def _unwrap_translation(t):
    """Strip CachedTranslation wrapper to access the underlying PackageTranslation."""
    # 剥离 CachedTranslation 包装层以访问底层的 PackageTranslation
    from argostranslate.translate import CachedTranslation, PackageTranslation

    while isinstance(t, CachedTranslation):
        t = t.underlying
    if not isinstance(t, PackageTranslation):
        raise TypeError(f"Expected PackageTranslation, got {type(t)}")
    return t


class TranslationEngine:
    """Wraps Argos Translate for English to Chinese paragraph-level translation."""
    # 封装 Argos Translate 用于英译中段落级翻译

    def __init__(self, model_path: Path):
        """Load the Argos model, install it, and initialize the CTranslate2 translator."""
        # 加载 Argos 模型，安装并初始化 CTranslate2 翻译器
        import argostranslate.package
        import argostranslate.translate

        if not model_path.exists():
            raise FileNotFoundError(f"Argos model not found: {model_path}")

        argostranslate.package.install_from_path(str(model_path))
        langs = argostranslate.translate.get_installed_languages()
        try:
            en = next(l for l in langs if l.code == "en")
            zh = next(l for l in langs if l.code in ("zh", "zh_Hans"))
        except StopIteration as e:
            raise RuntimeError("Argos en→zh model is not installed correctly") from e
        self._t = en.get_translation(zh)
        self._load_translator()

    def _load_translator(self) -> None:
        """Lazily create the underlying CTranslate2 Translator instance."""
        # 延迟创建底层 CTranslate2 Translator 实例
        from argostranslate import settings

        pkg_t = _unwrap_translation(self._t)
        if pkg_t.translator is None:
            import ctranslate2

            pkg_t.translator = ctranslate2.Translator(
                str(pkg_t.pkg.package_path / "model"),
                device=getattr(settings, "device", "cpu"),
                inter_threads=getattr(settings, "inter_threads", 1),
                intra_threads=getattr(settings, "intra_threads", 0),
                compute_type=getattr(settings, "compute_type", "default"),
            )

    def translate(self, text: str) -> str:
        """Translate a single text string. Returns empty string for blank input."""
        # 翻译单个文本字符串。空白输入返回空字符串
        if not text or not text.strip():
            return ""
        return self._t.translate(text)

    def translate_many(self, texts: Iterable[str]) -> list[str]:
        """Batch-translate multiple texts by merging sentences into a single CTranslate2 call."""
        # 将多个文本的句子合并到一次 CTranslate2 调用中批量翻译
        texts = list(texts)

        from argostranslate import settings

        pkg_t = _unwrap_translation(self._t)
        if pkg_t.translator is None:
            import ctranslate2

            pkg_t.translator = ctranslate2.Translator(
                str(pkg_t.pkg.package_path / "model"),
                device=getattr(settings, "device", "gpu"),
                inter_threads=getattr(settings, "inter_threads", 1),
                intra_threads=getattr(settings, "intra_threads", 0),
                compute_type=getattr(settings, "compute_type", "default"),
            )

        sentencizer = pkg_t.sentencizer
        translator = pkg_t.translator
        tokenizer = pkg_t.pkg.tokenizer
        target_prefix_text = pkg_t.pkg.target_prefix

        all_tokenized: list[list[str]] = []
        boundaries: list[int] = []
        for text in texts:
            if not text or not text.strip():
                boundaries.append(0)
                continue
            sentences = sentencizer.split_sentences(text)
            boundaries.append(len(sentences))
            for s in sentences:
                all_tokenized.append(tokenizer.encode(s))

        if not all_tokenized:
            return [""] * len(texts)

        target_prefix = None
        if target_prefix_text:
            target_prefix = [[target_prefix_text]] * len(all_tokenized)

        translated_batches = translator.translate_batch(
            all_tokenized,
            target_prefix=target_prefix,
            replace_unknowns=True,
            max_batch_size=getattr(settings, "batch_size", 0),
            batch_type="tokens",
            beam_size=1,
            num_hypotheses=1,
            length_penalty=0.2,
            return_scores=True,
        )

        result: list[str] = []
        sent_idx = 0
        for count in boundaries:
            if count == 0:
                result.append("")
                continue
            tokens: list[str] = []
            for _ in range(count):
                tokens.extend(translated_batches[sent_idx].hypotheses[0])
                sent_idx += 1
            value = tokenizer.decode(tokens)
            if target_prefix_text and value.startswith(target_prefix_text):
                value = value[len(target_prefix_text):]
            if len(value) > 0 and value[0] == " ":
                value = value[1:]
            result.append(value)
        return result
