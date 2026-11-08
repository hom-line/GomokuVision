# GomokuVision

> ⭐ If this educational project helps you, consider giving it a **Star**. Technical feedback, reproducible bug reports and contributions are welcome.

**Gomoku Board Recognition & Move Prediction — MATLAB · Python/OpenCV · C#/OpenCvSharp**

GomokuVision began as a **2025 university final course assignment** titled *Design and Implementation of a Real-Time Gomoku Board Recognition and Prediction System* (「即時五子棋棋盤辨識與預測系統之設計與實現」). In **November 2026**, the original MATLAB project was modernized into independent three-language implementations, a Windows WPF graphical interface, synchronized replay, visual move recognition, move prediction and reproducible benchmarks.

This project is intended for **educational use, technical exchange and transparent engineering experiments**. It is not a claim of commercial readiness or general recognition accuracy on real-world footage.

[繁體中文 / Traditional Chinese](#繁體中文--traditional-chinese) · [Publication status](PUBLICATION_STATUS.md)

## Features

| Component | Implementation |
| --- | --- |
| Recognition engines | MATLAB / Image Processing Toolbox, Python / OpenCV, C# / OpenCvSharp |
| Desktop | Windows WPF (.NET 10), English-first with Traditional Chinese |
| Browser | **Static synchronized replay**, not browser execution of three recognition engines |
| ROI strategies | Shared ROI or separate black/white ROI |
| Visualization | Confirmed-stone green boxes, optional heuristic move prediction |
| Playback | Synchronized video, board and move list at 1× / 2× / 4× |
| Benchmarks | 12 / 24 / 36 combinations with CSV and JSON exports |
| Demo | Self-created 961-frame, 41-move synthetic Gomoku video |

## Verified Windows results — November 8, 2026

**36 / 36 PASS**, with no failures or skips. The evaluation covers three engines, two ROI strategies, two display modes and three playback-speed labels. Each configuration uses the **same 961-frame synthetic input** and matches the 41-move reference game, with Black winning.

| Engine | Recognition core | In-process pipeline | Full process |
| --- | ---: | ---: | ---: |
| C# / OpenCvSharp | 1.010 s | 1.821 s | 1.929 s |
| Python / OpenCV | 1.377 s | 2.831 s | 2.988 s |
| MATLAB | 1.363 s | 8.909 s | 21.889 s |

These are averages of **one run per configuration**, not repeated independent benchmark trials. Core recognition excludes video I/O, overlays and process startup; full-process measurements include additional overhead such as MATLAB initialization. The 1×/2×/4× settings are **playback labels, not computational accelerators**. Synthetic accuracy does not establish real-world generalization.

## Publication and source status

The **repository overview, MIT License and third-party notices are online**. The complete modern MATLAB, Python and C# sources, WPF, browser replay and demo files are prepared but **not uploaded to this repository yet**. The first GitHub Release also remains pending; do not confuse license publication with completed code publication.

The author has confirmed ownership of the modern project source and original synthetic assets and has approved the [MIT License](LICENSE). The modern source distribution is prepared for upload. Dependencies retain their own license terms ([third-party notices](THIRD_PARTY_NOTICES.md)). The historical 2025 MATLAB course source and original third-party footage are excluded.

The repository and README title stay **GomokuVision**. The planned initial release tag is `v0.3.9`.

## Project history

- **2025** — University final course assignment, initially implemented in MATLAB.
- **November 2026** — Three-language modernization, Windows desktop UI, browser replay work and synthetic benchmark automation.
- **Next** — Finalize licensing, publish approved source, verify GitHub Actions and publish a reproducible source Release.

**Maintainer:** [hom-line](https://github.com/hom-line)

---

## 繁體中文 / Traditional Chinese

**五子棋棋盤辨識與落點預測 — MATLAB · Python · C#**

> ⭐ 如果本專案對你有幫助，歡迎給予 Star，支持技術分享與後續維護。

GomokuVision 最初為 **2025 年大學課程期末作業**，題目為「即時五子棋棋盤辨識與預測系統之設計與實現」，初版主要以 MATLAB 開發。

**2026 年 11 月**，在原始概念基礎上，擴充 MATLAB、Python/OpenCV、C#/OpenCvSharp 三套實作，加入 Windows WPF 圖形介面、影片與棋盤同步重播、落子綠框、落點預測，以及三語言效能測試與 CSV 匯出。本專案以**技術交流、教育學習與可重現工程實驗**為目的。

[目前發布狀態](PUBLICATION_STATUS.md)

## 主要功能

- MATLAB、Python、C# 三套辨識引擎。
- Windows WPF（預設英文，支援繁體中文）。
- 已知合成棋譜的 Web Replay 展示；**不是網頁直接執行三套辨識引擎**。
- 黑白分離／共用 ROI、純辨識／辨識加預測、綠框標示。
- 961 幀自行生成的完整 41 手棋局，同步 1×／2×／4× 重播。
- 自動化 12／24／36 組測試，以及 CSV／JSON 報告。

## 2026-11-08 Windows 驗證

**36/36 PASS，失敗 0、跳過 0。** 測試採同一支 961 幀合成棋局；全部組合皆符合 41 手參考棋譜、黑棋獲勝。播放倍率僅是重播標籤，不是辨識運算加速。

| 引擎 | 純辨識核心平均 | 引擎內處理平均 | 完整程序平均 |
| --- | ---: | ---: | ---: |
| C# | 1.010 秒 | 1.821 秒 | 1.929 秒 |
| Python | 1.377 秒 | 2.831 秒 | 2.988 秒 |
| MATLAB | 1.363 秒 | 8.909 秒 | 21.889 秒 |

不同計時範圍不可混用；單一合成影片測試通過不代表所有真實影像都能正確辨識。

## 專案公開狀態

**專案介紹與 MIT License 已公開。完整現代版原始碼、展示影片、Web Replay 與正式 Release 尚待上傳；MIT 授權適用於作者自有作品，不包含第三方依賴或專有 MATLAB 執行環境。**

2025 年歷史 MATLAB 原始檔及第三方原始影片不包含在首次公開包內。專案標題僅使用 **GomokuVision**，規劃首次 Release Tag 為 `v0.3.9`。

**維護者：** [hom-line](https://github.com/hom-line)
