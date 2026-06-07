from __future__ import annotations
from pathlib import Path
from typing import Iterable


def _unwrap_translation(t):
    from argostranslate.translate import CachedTranslation, PackageTranslation

    while isinstance(t, CachedTranslation):
        t = t.underlying
    if not isinstance(t, PackageTranslation):
        raise TypeError(f"Expected PackageTranslation, got {type(t)}")
    return t


class TranslationEngine:
    """Wraps Argos Translate for English to Chinese paragraph-level translation."""

    def __init__(self, model_path: Path):
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
            raise RuntimeError("Argos en->zh model is not installed correctly") from e
        self._t = en.get_translation(zh)
        self._load_translator()

    def translate(self, text: str) -> str:
        if not text or not text.strip():
            return ""
        return self._t.translate(text)

    def _load_translator(self) -> None:
        from argostranslate import settings
        import ctranslate2

        pkg_t = _unwrap_translation(self._t)
        if pkg_t.translator is None:
            pkg_t.translator = ctranslate2.Translator(
                str(pkg_t.pkg.package_path / "model"),
                device=settings.device,
                inter_threads=settings.inter_threads,
                intra_threads=settings.intra_threads,
                compute_type=settings.compute_type,
            )

    def translate_many(self, texts: Iterable[str]) -> list[str]:
        texts = list(texts)

        from argostranslate import settings

        pkg_t = _unwrap_translation(self._t)

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
            max_batch_size=settings.batch_size,
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
