# Agents.md — MarkdownEdit

## Project structure

All source code lives under `markdownEdit/`. The repo root only has a README and a subdirectory — always work inside `markdownEdit/`.

## Quick start

```bash
cd markdownEdit
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/fetch_argos_model.py          # ~67MB translation model
python scripts/build_ecdict.py path\to\ecdict.csv  # ~50MB dictionary
```

## Run

```bash
python -m src.main                           # always from markdownEdit/
# or double-click run.bat (auto-detects .venv or venv)
```

## Critical import order (Windows)

In `src/main.py`, `import ctranslate2` **must** appear before any PyQt5 imports. Qt changes the DLL search path on Windows, causing torch's `c10.dll` to fail with `WinError 1114`.

## Tests

```bash
pytest                                      # from markdownEdit/
```

`tests/conftest.py` inserts the project root into `sys.path` automatically. 15 tests covering MD rendering, dictionary lookup, paragraph splitting, Chrome lang injection. No UI tests (manual smoke test only).

## Two-layer translation

| Layer | Scope | Engine | Latency |
|-------|-------|--------|---------|
| Paragraph (NMT) | Full sentences, batch up to 32 | Argos Translate (CTranslate2) | ~0.04–0.15s after model load |
| Word (dictionary) | Single word hover ≥500ms | ECDICT SQLite (read-only URI) | <30ms |

Translation runs in a background `QThread` with LRU cache (512 entries) and inflight dedup. Emitted results are debounced 150ms before updating the UI.

## Views

| Shortcut | View | Right pane |
|----------|------|------------|
| `Ctrl+1` | Translation | Left: source, Right: Chinese translation |
| `Ctrl+2` | Preview | Left: source, Right: rendered HTML |

Default view is translation; falls back to preview if Argos model is missing.

## Resource paths

- Dev: `resources/models/translate-en_zh*.argosmodel` (wildcard match), `resources/dict/ecdict.sqlite`
- PyInstaller: `sys._MEIPASS` / `resources/...`
- Graceful degradation: missing model → disable translation view; missing dict → disable hover tooltip, status bar notice

## Build

```bash
pyinstaller build/markdownedit.spec
# output: dist/markdownedit/markdownedit.exe + _internal/ (~1.5GB due to argostranslate deps)
```

## Gotchas

- **Windows x64 only** — requires Python 3.10+ 64-bit, Windows 10/11
- **No linter, typechecker, or CI config** — the repo has none (no `.github/workflows`, no `pyproject.toml`, no `.gitignore`)
- **Worker uses per-item translation**, not `translate_many()` batch (see changelog01.txt: thread safety)
- **Model installs to `~/.argos-translate/packages/`** on first load — this is a side effect of `argostranslate.package.install_from_path()`
- Dictionary uses `sqlite3.connect("file:...?mode=ro", uri=True)` — read-only, cross-thread safe
