# MarkdownEdit v0.1.0 功能文档

> 轻量 Markdown 编辑器，内置离线英译中。仅支持 64 位 Windows 10/11。

---

## 1. 总览

| 模块 | 技术 |
|---|---|
| 语言/运行时 | Python 3.10+ (64-bit) |
| GUI | PyQt5 5.15 + PyQtWebEngine |
| Markdown 渲染 | `markdown` + `Pygments` 代码高亮 |
| 段落级翻译 | Argos Translate (CTranslate2) — 神经网络 en→zh |
| 单词级翻译 | ECDICT SQLite 词典(~77 万词条) |
| 文档导出 | `python-docx` 1.2.0 (Word 导出) |
| 打包 | PyInstaller (`--onedir`)，单一 64 位产物 |

启动后默认进入**翻译对照视图**；若 Argos 模型缺失，自动回退到渲染预览。

---

## 2. 已实现功能

### 2.1 文件操作

| 项 | 快捷键 | 行为 |
|---|---|---|
| 新建 | `Ctrl+N` | 清空编辑器，有未保存改动会弹窗确认 |
| 打开 | `Ctrl+O` | UTF-8 读取 `.md` / `.markdown` / `.txt`；**打开后自动切到渲染预览视图** |
| 保存 | `Ctrl+S` | 未命名时触发"另存为" |
| 另存为 | `Ctrl+Shift+S` | 写入路径并加入"最近文件" |
| 关闭标签页 | `Ctrl+W` | 关闭当前标签页，有未保存改动会弹窗确认 |
| 退出 | `Ctrl+Q` | 有未保存改动会拦截关闭 |
| 最近文件 | — | 持久化 8 项(`QSettings("MarkdownEdit"，"App")`) |

修改后标签页标题显示 `*` 脏标记。

### 2.2 多标签页管理

编辑器支持完整的多标签页 MDI 界面：

| 特性 | 实现 |
|---|---|
| 新建标签页 | `_cc_new_tab()` 创建新标签页，包含编辑器 + 右栏 `QStackedWidget` |
| 关闭标签页 | `_cc_close_tab()` 逐个关闭，最后一个关闭时自动创建新标签页 |
| 脏标记 | `_cc_on_tab_dirty_chnged()` 在标签页标题前添加 `*` |
| 窗口标题同步 | `_cc_on_curren_tab_chnged()` 切换标签页时更新窗口标题 |
| 关闭窗口 | `_cc_onfirm_discard()` 遍历**所有**标签页检查未保存改动 |
| UI 配置 | `QabWidget` 可关闭 (`setabsClosable`)、可拖动 (`setMovable`)、文档模式 (`setDocumenMode`) |

### 2.3 拖放打开文件

支持从系统文件管理器拖放文件到编辑器窗口：
- **窗口级别**：`MainWindow.dragEneterEvent()` + `dropEvent()`，过滤 `.md` / `.markdown` / `.txt` 扩展名，自动在新标签页中打开
- **标签页级别**：每个 `EdiorTab` 也有独立的 `dragEneterEvent()` / `dropEvent()`，通过 `fileDropped` 信号向上传播

### 2.4 实时编辑与右栏渲染

- 编辑器(`MarkdownEdior`)是 `QPlainTexEdit` 子类
- `texChnged` 走 150ms 防抖(`Debouncer`)，触发 `contenSetled` 信号
- 防抖延迟可通过构造参数 `debounce_ms: int = 150` 配置
- 右栏使用 `QStackedWidget` 承载两个视图，通过 `QAcionGroup` 互斥切换，`Ctrl+1` / `Ctrl+2` 切换：

| 视图 | 索引 | 作用 |
|---|---|---|
| **翻译对照(默认)** | `VIEW_RANSLATION = 0` | 左原文，右纯中文译文(段落级神经网络翻译) |
| **渲染预览** | `VIEW_PREVIEW = 1` | 左原文，右 HTML 渲染(GitHub 风格 CSS) |

- 编辑器垂直滚动条按比例同步到当前激活的右侧视图

### 2.5 离线翻译

#### 段落级(神经网络)

- 引擎：Argos Translate `translat-en_zh*.argosmodel`(通配匹配，~67MB，内置)
- 流程：`spit_paragaphs` 按空行切段(围栏代码块整体保留，同时支持反引号 `` ` `` 和波浪线 `~~~`) → MD5 作 key 查 LRU 512 条 → 未命中入 `queu.Queu` → 后台 `QThred` 调 `engin.translat`(批量处理，最多 **32** 段一次 `translat_bach` 调用) → `pyqSignl(原文，译文)` 回主线程
- 译文回主线程后经 **150ms 防抖定时器** 去抖刷新右侧翻译窗格，避免高频刷新
- 翻译尚未到达的段落显示 `…` 占位(`.pending` 灰色斜体)

#### 单词级(词典悬停)

- 数据：ECDICT SQLite，~62MB，77 万词条，含 `word / transltion / phonetid`
- 触发：鼠标在编辑器英文单词上悬停 ≥500ms
- 渲染：`QToolTip` 弹出 `[音标]\n释义`
- 命中查淘稳定 ≤30ms(只读 URl 模式打开 SQlite，跨线程安全)

### 2.6 导出功能

预览视图右键菜单提供三种导出格式：

| 格式 | 右键菜单 | 实现 |
|---|---|---|
| HTML | "保存为 HTML" | `Path().write_text(html， encoding="utf-8")` |
| PDF | "保存为 PDF" | `QWebEngineView.page().printToPdf(path)` |
| Word | "保存为 Word" | `python-docx`：按 `##` / `###` 拆分，逐行渲染 Markdown |

通过 `saveHtmRequeted`、`savePdfRequeted`、`saveWordRequeted` 三个 `pyqtSignl` 从 `PreviwView` 传播到 `MainWindow`。

### 2.7 用 Chrome 打开并翻译(渲染预览右键菜单)

- 仅在**渲染预览**视图右键菜单可见 → "用 Chrome 打开并翻译"
- 实现：
  1. 取当前预览 HTML
  2. 强制注入 `<html lang="en">`(Chrome 自动翻译触发条件之一)
  3. 写入 `%TEMP%/markdownedit_preview_*.html`
  4. 通过注册表 / 标准目录定位 `chrome.exe`，以 `--lang=zh-CN` 启动
- Chrome 缺失时回退到默认浏览器，状态栏给出提示

### 2.8 关于对话框 / 状态栏

- `帮助 → 关于`：显示 `MarkdownEdit v0.1.0` + 简介
- 状态栏：保存提示、翻译失败、模型 / 词典缺失提示等(均带超时)
  - 词典缺失：`"悬停词典未找到 (resources/dict/ecdict.sqlite)，悬停翻译已禁用"`(8000ms)
  - 模型缺失：禁用翻译操作，工具提示 `"Argos 模型未找到 (resources/models/translate-en_zh*.argosmodel)"`

---

## 3. 项目结构

```
markdowEdit/
├── src/
│   ├── __init__.py                # 版本常量 (0.1.0)
│   ├── main.py                    # QApplication 入口
│   ├── ui/
│   │   ├── main_window.py         # QMainWindow + 菜单 + 标签页管理 + 文件操作 + 导出
│   │   ├── editor.py              # MarkdownEditor(可配防抖 contentSettled)
│   │   ├── editor_tab.py          # EditorTab(左侧编辑器 + 右侧 QStackedWidget 的 QSplitter)
│   │   ├── preview.py             # PreviewView + 右键 openInChromeRequested / 导出信号
│   │   └── translation_view.py    # TranslationView(纯译文 QWebEngineView)
│   ├── render/
│   │   ├── md_renderer.py         # render / render_bilingual / render_translation_only
│   │   └── paragraphs.py          # split_paragraphs(代码块保护，支持 ``` 和 ~~~)
│   ├── translate/
│   │   ├── engine.py              # TranslationEngine(Argos 包装)
│   │   ├── worker.py              # QThread + LRU + 队列 + 批量 32 段 + active worker
│   │   ├── dict_cache.py          # SQLite 只读查询
│   │   └── hover.py               # HoverTranslator(eventFilter + QToolTip)
│   └── utils/
│       ├── debounce.py            # QTimer 防抖
│       ├── paths.py               # 资源定位(支持 PyInstaller _MEIPASS，模型通配匹配)
│       └── chrome.py              # find_chrome / _force_lang_en / open_html_in_chrome_translate
├── resources/
│   ├── models/translate-en_zh*.argosmodel    # ~67 MB
│   └── dict/ecdict.sqlite                    # ~62 MB
├── scripts/
│   ├── build_ecdict.py            # CSV → SQLite
│   └── fetch_argos_model.py       # 下载 Argos 模型
├── build/                         # PyInstaller 配置(生成目录)
├── tests/                         # 15 个单测，pytest
│   └── conftest.py                # 测试路径基础设施
├── requirements.txt
├── run.bat                        # 一键启动脚本(自动检测虚拟环境)
└── README.md
```

---

## 4. 关键设计取舍

1. **多标签页架构**：支持同时编辑多个文件，每个标签页维护独立的编辑器 + 右栏 `QStackedWidget` 状态，通过 `QTabWidget` 统一管理。
2. **共享一个编辑器，右栏切视图**：翻译对照与渲染预览共用同一份编辑内容，通过 `QStackedWidget` 切换右栏渲染，避免双套状态。
3. **两层翻译**：神经网络只服务段落，悬停看单词走词典快路径(<30ms)，不阻塞 UI 也不抢占翻译队列。段落翻译采用批量处理(最多 32 段)，配合独立 150ms 刷新防抖定时器。
4. **资源缺失优雅降级**：`Argos 模型缺失 → 翻译对照视图禁用，默认改为渲染预览；ECDICT 缺失 → 悬停翻译禁用，状态栏提示详细原因`，主体仍可用。
5. **PyInstaller 资源解析**：`utils/paths.py` 中通过 `sys._MEIPASS` 同时支持开发模式与冻结产物，无需运行时解压。模型路径使用通配模式 `translate-en_zh*.argosmodel`，兼容多版本。
6. **Chrome 翻译触发**：不依赖 Chrome 命令行 API，用最稳的方式 — 改写 `<html lang="en">` + 启动参数 `--lang=zh-CN`，让 Chrome 自带的"翻译此页"提示自动出现。

---

## 5. 测试矩阵

`pytest tests/` — 15 用例全过：

| 文件 | 覆盖 |
|---|---|
| `test_md_renderer.py` (4) | 基本渲染、围栏代码、双栏对照、占位符 |
| `test_dict_cache.py` (5) | 命中、大小写不敏感、未命中、非 ASCII、性能 ≤30ms |
| `test_split_paragraphs.py` (3) | 空行切分、代码块整块保留(含波浪线围栏)、单段 |
| `test_chrome_lang.py` (3) | lang 注入、覆写、无 html 标签时包裹 |

基础设施：`conftest.py` 自动将项目根目录插入 `sys.path`，支持从任意目录运行测试。

未自动化：PyQt5 UI(交互成本高，改用手动 smoke test)。

---

## 6. 运行 / 打包

```bash
# 安装依赖
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

# 准备资源(已生成，跳过)
# python scripts/fetch_argos_model.py
# python scripts/build_ecdict.py path/to/ecdict.csv

# 开发运行(方式一：直接启动)
python -m src.main

# 开发运行(方式二：使用启动脚本，自动检测虚拟环境)
run.bat [参数...]

# 打包
python -m PyInstaller build/markdownedit.spec --noconfirm
# 产物:dist/markdownedit/markdownedit.exe (78MB) + _internal/ (合计 ~1.5GB)
```

打包目录体积大主要因为 argostranslate 间接依赖(stanza / spacy / onnxruntime / bitsandbytes)，后续若要瘦身可在 spec `excludes` 列表中剔除 — 当前不影响功能。

---

## 7. 验证清单

- [x] 启动后默认进入翻译对照视图
- [x] 编辑英文 Markdown，150ms 内右栏出现段落译文(首次会有 1–3s 模型加载延迟)
- [x] 悬停英文单词 → 弹出中文释义
- [x] `Ctrl+2` 切到渲染预览，右键 → "用 Chrome 打开并翻译" → Chrome 弹出翻译提示
- [x] 右键另存为 HTML / PDF / Word，文件保存正确
- [x] 拖放 .md 文件到窗口 → 自动在新标签页打开
- [x] 多标签页切换 → 脏标记、关闭确认正常
- [x] 关闭网络后所有翻译/预览功能仍可用
- [x] 关闭窗口时，后台翻译线程能正确退出