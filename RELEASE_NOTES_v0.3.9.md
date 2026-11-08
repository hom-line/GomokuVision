# GomokuVision — Initial Technical Release

**2025 final course assignment → November 2026 modernization.**

First planned public technical sharing release of a three-language Gomoku video recognition system, with MATLAB, Python and C# independent engines, Windows WPF, and a static browser-based synchronized replay for the self-generated synthetic game.

Highlights: two ROI modes, recognition/heuristic suggestion overlays, 961-frame/41-move synthetic sample, 1×/2×/4× synchronized replay, 12–36 case CSV export and explicit three-scope benchmarking methodology.

**Windows evidence (2026-11-08):** 36/36 synthetic scenarios PASS; 41/41 moves with Black winner in each case. Full case data under `docs/benchmarks/`.

**Important limits:** The browser replay does *not* execute native recognition. Playback speed does not accelerate detector computations. Synthetic test pass rates are not real-world accuracy evidence. MATLAB requires separately licensed proprietary software. No original third-party video is bundled.

The source license and all rights notices must be completed before this Release is published. This document is draft release text, not a published GitHub Release.
