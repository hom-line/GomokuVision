# GomokuVision

> ⭐ If this educational project helps you, consider giving it a **Star**. Technical feedback, reproducible bug reports and contributions are welcome.

**Gomoku Board Recognition & Move Prediction — MATLAB · Python/OpenCV · C#/OpenCvSharp**

GomokuVision began as a **2025 university final course assignment** titled *Design and Implementation of a Real-Time Gomoku Board Recognition and Prediction System* (「即時五子棋棋盤辨識與預測系統之設計與實現」). In **November 2026**, the original MATLAB project was modernized into independent three-language implementations, a Windows WPF graphical interface, synchronized replay, visual move recognition, move prediction and reproducible benchmarks.

This project is intended for **educational use, technical exchange and transparent engineering experiments**. It is not a claim of commercial readiness or general recognition accuracy on real-world footage.

[繁體中文說明](README_zh_TW.md) · [Publication status](PUBLICATION_STATUS.md)

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

The **repository overview is published first**. Complete modern MATLAB, Python and C# sources, WPF, browser replay, demo files and the first GitHub Release remain **pending publication review and upload**. This public repository is not yet a completed open-source software distribution.

Before uploading code, we will verify original-contributor redistribution rights, review third-party notices and select a suitable root license. The historical 2025 MATLAB source and third-party original footage are excluded until rights are established.

The repository and README title stay **GomokuVision**. The planned initial release tag is `v0.3.9`.

## Project history

- **2025** — University final course assignment, initially implemented in MATLAB.
- **November 2026** — Three-language modernization, Windows desktop UI, browser replay work and synthetic benchmark automation.
- **Next** — Finalize licensing, publish approved source, verify GitHub Actions and publish a reproducible source Release.

**Maintainer:** [hom-line](https://github.com/hom-line)
