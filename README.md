# GomokuVision

**Gomoku Board Recognition & Move Prediction / 五子棋棋盤辨識與棋步預測**

**MATLAB · Python / OpenCV · C# / OpenCvSharp · Windows WPF · Web Replay**

> ⭐ **Like this project? Give it a Star! / 如果這個專案對你有幫助，歡迎給予 Star 支持技術分享。**

[**Download / 下載**](https://github.com/hom-line/GomokuVision/releases/tag/GomokuVision) · [**Quick Start / 快速開始**](#-quick-start--快速開始) · [**Web Replay / 網頁重播**](#-web-replay--網頁棋譜重播) · [**Benchmarks / 測試結果**](#-verified-benchmarks--實測結果) · [**License / 授權**](#-license--授權)

![Synthetic Gomoku board with highlighted stones / 自製五子棋棋盤與綠色標記](docs/V036_Green_Box_Final_Frame.png)

## 📖 About / 專案簡介

GomokuVision started as a **2025 university final course assignment**, *Design and Implementation of a Real-Time Gomoku Board Recognition and Prediction System*. In **November 2026**, the original MATLAB-based concept was modernized into a three-language computer vision project with a Windows desktop interface, synchronized replay, heuristic move prediction and automated benchmarks.

GomokuVision 起源於 **2025 年大學課程期末作業**「即時五子棋棋盤辨識與預測系統之設計與實現」。於 **2026 年 11 月**，以原 MATLAB 專題概念為基礎，升級為三語言電腦視覺專案，加入 Windows 桌面介面、影音棋盤同步、落點預測與自動化效能比較。

**Purpose / 專案定位：** Education · Technical Sharing · Reproducible Engineering / 教育學習、開源技術交流與可重現的工程實驗。

## ✨ Features / 主要功能

| Feature / 功能 | Implementation / 實作說明 |
| --- | --- |
| **Three recognition engines / 三語言辨識** | MATLAB + Image Processing Toolbox、Python/OpenCV、C#/OpenCvSharp；三套獨立實作 |
| **Windows desktop / Windows 桌面版** | WPF + .NET 10；English by default / 預設英文，可切換繁體中文 |
| **Recognition modes / 辨識模式** | Shared ROI or separate black/white ROI / 共用 ROI、黑白分離 ROI |
| **Visualization / 視覺化** | Confirmed-stone green boxes + optional heuristic move suggestions / 綠框辨識、可選棋步建議 |
| **Synchronized playback / 同步重播** | Video, 15×15 board and move timeline / 影片、15×15 棋盤與棋步同步；1× / 2× / 4× |
| **Web Replay / 網頁展示** | Static replay, move history and benchmark chart / 靜態棋譜重播、棋步紀錄與效能圖表 |
| **Automated benchmarks / 自動化比較** | 3 engines × 2 ROI × 2 overlays × 1–3 speed labels / 12、24 或 36 組測試；CSV + JSON |
| **Self-generated demo / 自製示範影片** | 961 frames, 30 FPS, 41 moves / 961 幀、30 FPS、完整 41 手棋譜 |

> **Important / 注意：** The browser replay displays a known synthetic reference game; it **does not execute MATLAB, Python or C# recognition in the browser**. The Windows WPF app runs the recognition engines. / 網頁版是**已知合成棋局的同步展示**，並不會在瀏覽器中執行三套辨識引擎；正式辨識由 Windows WPF 應用程式執行。

## 📥 Download / 下載專案

**[GomokuVision — GitHub Release](https://github.com/hom-line/GomokuVision/releases/tag/GomokuVision)**

- [**GomokuVision_v0.3.9_Source.zip**](https://github.com/hom-line/GomokuVision/releases/download/GomokuVision/GomokuVision_v0.3.9_Source.zip) — Full source package / 完整原始碼與自製展示素材。
- [**SHA256_GomokuVision_v0.3.9.txt**](https://github.com/hom-line/GomokuVision/releases/download/GomokuVision/SHA256_GomokuVision_v0.3.9.txt) — Download integrity check / 下載完整性校驗。

The repository is named **GomokuVision**; `v0.3.9` identifies the initial source-release version. This is a **source-code distribution**, not a prebuilt standalone Windows EXE.

專案名稱維持 **GomokuVision**；`v0.3.9` 僅是首次發布版號。本次提供的是**原始碼版本**，不是免安裝的 Windows EXE。

## 🚀 Quick Start / 快速開始

**Requirements / 環境需求：** Windows x64, .NET 10 SDK, Python 3.10+ (Python engine). MATLAB + Image Processing Toolbox is **optional and separately licensed**. / Windows x64、.NET 10 SDK、Python 3.10 以上；MATLAB 引擎須自行安裝合法授權的 MATLAB 與 Image Processing Toolbox。

**1. Clone or download / 複製儲存庫或下載 ZIP**

~~~powershell
git clone https://github.com/hom-line/GomokuVision.git
cd GomokuVision
python -m pip install -r python/requirements.txt
~~~

**2. Restore the sample video / 還原自製示範影片**

~~~powershell
python python/tools/restore_demo_videos.py --verify
~~~

Four self-generated MP4 files are stored as lossless `.mp4.xz` archives. The restore tool checks SHA-256 and reconstructs the exact demo video files. / 四支自製 MP4 以無損 `.mp4.xz` 封存，可經 SHA-256 驗證後還原為原始影片。

**3. Build and launch WPF / 建置並啟動 Windows 桌面版**

~~~powershell
.\scripts\Verify-WPF-Build-Windows.bat
.\Launch-Desktop-Windows.bat
~~~

**4. Run a benchmark / 執行批次比較**

~~~powershell
.\scripts\Run-Selected-Speeds-Windows.bat 1 2 4
~~~

Choose the recognition engine, ROI strategy and display mode in WPF, or run 1×/2×/4× benchmark groups and export CSV/JSON. 在 WPF 選擇引擎、ROI 與顯示模式；亦可勾選不同倍率的測試組合，匯出 CSV／JSON。

## 🌐 Web Replay / 網頁棋譜重播

Open [`index.html`](index.html) directly in a browser, or host the repository using GitHub Pages **after Pages is enabled**. / 可直接使用瀏覽器開啟 [`index.html`](index.html)；若啟用 GitHub Pages，也能作為公開展示頁。

- Synchronized MP4 + board + 41-move timeline / 影片、棋盤、41 手紀錄同步
- Previous / Next / Seek / 上一步、下一步與進度拖曳
- 1× / 2× / 4× replay / 多倍率重播
- Green reference markers and benchmark comparison / 綠色參考框與三引擎效能比較

The web-friendly H.264 `demo/full_game/full_game_961_web.mp4` follows the same 961-frame timeline. It is a visualization, **not real-time recognition inference**. / 網頁展示影片沿用同一個 961 幀時間軸，但不代表在網頁內重新執行即時辨識。

## 🧪 Verified Benchmarks / 實測結果

**Windows acceptance / Windows 驗收：2026-11-08 — 36/36 PASS (0 failed, 0 skipped).**

Each test uses the **same self-generated 961-frame video**, processes 161 sampled frames and matches all **41 reference moves**, with Black winning. The 36 settings are **3 engines × 2 ROI modes × 2 overlay modes × 3 playback labels**.

36 組設定皆使用**同一支自行生成的 961 幀影片**，分析 161 個取樣影格，符合 **41/41 手參考棋譜**、黑棋獲勝。測試矩陣為三引擎 × 兩種 ROI × 兩種顯示模式 × 三種播放倍率標籤。

| Engine / 引擎 | Recognition core / 核心辨識 | In-process pipeline / 引擎內處理 | Full process / 完整程序 |
| --- | ---: | ---: | ---: |
| **C# / OpenCvSharp** | **1.010 s** | **1.821 s** | **1.929 s** |
| **Python / OpenCV** | 1.377 s | 2.830 s | 2.988 s |
| **MATLAB** | 1.363 s | 8.909 s | 21.889 s |

**Fair timing / 公平計時：** Detection-core time excludes video decoding/encoding, overlays and startup; full-process time includes external overhead such as MATLAB initialization. These values average **one run per configuration**, not repeated independent trials. / 核心辨識時間不含影片讀寫、畫框及啟動成本；完整程序時間包含 MATLAB 初始化等額外開銷。每個設定只有一次測試，尚不是多輪獨立統計實驗。

**Limitations / 限制：** Playback speeds **do not accelerate detector computation**, and passing a single synthetic game **does not establish real-world recognition accuracy**. / 1×／2×／4× **不會加速辨識運算**；單一合成棋局全數通過，**不代表真實場景辨識準確率為 100%**。

[36-case CSV / 36 組明細](docs/benchmarks/windows_v039_36_case_results_2026-11-08.csv) · [Engine summary / 引擎平均](docs/benchmarks/windows_v039_engine_summary.csv) · [Evidence / 驗證說明](docs/benchmarks/WINDOWS_V039_36_CASE_EVIDENCE.md) · [Timing methodology / 計時方法](docs/benchmarks/TIMING_METHODS.md)

## 🧩 Project Structure / 專案結構

~~~text
GomokuVision/
├── csharp/              C# engine & Windows WPF / C# 引擎與桌面介面
├── python/              OpenCV engine, tests & tools / Python 引擎與測試
├── matlab/modern/       MATLAB engine / 現代版 MATLAB 引擎
├── demo/full_game/      Synthetic video & reference / 自製影片與棋譜
├── web/ + index.html    Browser replay / 網頁棋譜展示
├── data/ + results/     Demo data and results / 示範資料與結果
├── scripts/             Windows launch & test tools / 啟動與批次測試
├── docs/benchmarks/     Verified results / 實測方法及證據
├── docs/releases/       Release documentation / 發布文件
└── .github/workflows/   GitHub Actions CI / 自動化檢查
~~~

### Development & CI / 開發與持續整合

~~~powershell
python -m pip install -r python/requirements-dev.txt
$env:PYTHONPATH = "python"
python -m pytest -q python/tests
~~~

GitHub Actions checks Python and Windows functionality; see [CI runs](https://github.com/hom-line/GomokuVision/actions) for the latest results. GitHub Actions 執行 Python 與 Windows 自動化測試，最新狀態請以 [Actions 頁面](https://github.com/hom-line/GomokuVision/actions) 為準。

## 🗺️ History & Roadmap / 專案歷程與規劃

| Period / 時間 | Milestone / 內容 |
| --- | --- |
| **2025** | University final course assignment in MATLAB / MATLAB 大學課程期末作業 |
| **November 2026 / 2026 年 11 月** | Three-language modernization, WPF, Web Replay, 36-case evidence / 三語言重構、桌面及網頁展示、36 組測試 |
| **Next / 下一步** | GitHub Pages browser acceptance, standalone Windows build / GitHub Pages 驗收與獨立 Windows 發布版 |
| **Future / 未來** | Real-camera dataset, auto calibration, occlusion recovery, tactical search / 真實攝影資料、自動校準、遮擋恢復與策略搜尋 |

## ⚖️ License / 授權與聲明

The author's modern MATLAB/Python/C# source and self-generated demo assets are published under the [MIT License](LICENSE). MATLAB and its toolboxes are proprietary and require separate licenses; other dependencies retain their upstream terms ([Third-party Notices](THIRD_PARTY_NOTICES.md)). The historical 2025 MATLAB coursework files and original third-party footage are **not included**.

現代版 MATLAB／Python／C# 原始碼與自製合成素材採用 [MIT License](LICENSE) 開源。MATLAB 及其工具箱仍屬專有軟體，須另行取得授權；第三方依賴遵循各自條款（詳見[第三方授權聲明](THIRD_PARTY_NOTICES.md)）。**2025 年歷史課程 MATLAB 原始檔與原始第三方影片並未納入公開版本**。

---

**Maintainer / 維護者：** [hom-line](https://github.com/hom-line) · **Origin / 專題起點：** 2025 final course assignment / 2025 年期末作業 · **Modernized / 升級：** November 2026 / 2026 年 11 月
