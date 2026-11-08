# GomokuVision V0.3.8 — Compact WPF and multi-speed benchmark selection

The main WPF panel now shows video, engine, ROI, display and batch controls; calibration, templates and advanced options are moved into a collapsible panel. Select any combination of **1×, 2×, 4×**, then run 12, 24 or 36 native-engine benchmark cases and export CSV files grouped by playback speed.

**Playback speed is metadata for replay selection, NOT a compute-acceleration factor.** Each selected speed repeats the 12 engine/ROI/display combinations. New WPF UI and MATLAB native validation are pending on Windows.

# V0.3.7 — 12-case native-engine benchmark and CSV export

WPF adds **Run all 12 cases and export CSV**: three engines × two ROI modes × two overlay modes, processing the selected video independently for each case. Results: `benchmark-results.csv`, `benchmark-summary.csv`. MATLAB confirmed bounding boxes are thickened to 3px to remain visible after downscaling. Native Windows validation is still pending.

# GomokuVision Advanced V0.3.6 — Two ROI strategies and green recognition boxes

This release adds two **independent** mode selectors. The ROI strategy (`separated` or `shared`) controls whether color-specific contrast gates are used before NCC template matching, or whether both templates are tested within a common candidate ROI. The display mode (`recognition` or `recognition_prediction`) controls confirmed-move green rectangles and optional green/cyan heuristic suggestion circles. Both settings are forwarded to the Python, C# and MATLAB engines.

The 2025 legacy MATLAB `ROI_Sharing` and `ROI_black_and_white_separation` source files have nearly identical executable logic. This release implements genuinely distinct filtering paths; do not interpret old timings as a controlled comparison. The green-box demo videos are **ground-truth annotations of self-authored synthetic footage**, never evidence of a fresh model inference.

Two synchronized, independently playable **961-frame / 60-FPS (2×)** MP4s are included: `demo/full_game/full_game_recognition_green_961_2x.mp4` and `demo/full_game/full_game_recognition_prediction_green_961_2x.mp4`. The WPF player continues using the unannotated 30-FPS full-game source and renders overlays only when its calibration and recorded move timeline correspond to the selected video.

**Validation here:** 64/64 Python regression tests, both ROI modes on the 9-move synthetic short clip, and both modes on the 961-frame 41-move synthetic full game; final winner Black and move sequences identical. The new C#/WPF build and MATLAB native runtime are **NOT verified in this environment**; test on Windows using `Run-Legacy-Modes-Windows.bat`, adding `-IncludeMatlab` when licensed MATLAB is installed. Original third-party video is never distributed.

---

# GomokuVision Advanced V0.3.5 — Windows preview file-lock fix

This release supersedes V0.3.4. It fixes preview publication races observed on Windows: Python raised `PermissionError [WinError 5]` replacing `last_frame.png`, and native MATLAB failed on `movefile` while the image was in use.

All three engines now publish **immutable per-frame PNGs** in a run-unique `preview_frames/` directory, with the progress JSON referencing the completed file. WPF opens images and progress JSON with `FileShare.ReadWrite | FileShare.Delete`. The stable `last_frame.png` is written once upon completion for offline result viewing. Python JSON updates retry transient sharing violations; MATLAB JSON publishing retries and live progress failures are non-fatal.

**Verified here:** 61/61 Python/source tests PASS; full 961-frame synthetic video / 161 analyzed frames / 41 recognized moves; all 41 moves agree with the synthetic oracle; 70 immutable live preview snapshots generated. **Not verified here:** native MATLAB execution, V0.3.5 Windows C# WPF compilation and live GUI acceptance.

For Windows: unzip into a **new directory**, run `scripts/Verify-WPF-Build-Windows.bat` followed by `Launch-Desktop-Windows.bat`, and test Python/MATLAB/C# with separate new output folders using the self-authored 961-frame demo. Confirm the move list updates during analysis and no preview file lock errors occur. This ZIP contains no original third-party footage.

---

# GomokuVision Advanced V0.3.4 — live three-engine updates, MATLAB fix, final-frame sync

This release supersedes V0.3.3. **Fixes:** move-by-move GUI updates during C#/Python/MATLAB recognition, MATLAB `table` name collision with `Row`, cheaper MATLAB black-stone photometric prefilter, recognition-confirmation versus visual-event timeline compensation, and the 961-frame / 60fps side-by-side 2x movie now showing the winning line on **both** sides through frame 961. The original synthetic 961-frame detection input remains unmodified. New Windows scripts verify MATLAB independently, provided a licensed MATLAB is installed.

**Verified here:** Python unit/source tests, native Python recognition 41/41 against a self-authored synthetic oracle, MP4 decoding and final-frame visualization. **Not yet verified here:** V0.3.4 C# WPF build and runtime on Windows or native MATLAB execution, because these runtimes are unavailable. This is not a verified claim of real-footage accuracy or GPU performance.

See [the Traditional Chinese acceptance guide](docs/V034_WINDOWS_ACCEPTANCE_zh_TW.md).

---

## Historical V0.3.3 documentation (superseded)

# GomokuVision Advanced V0.3.3 — synchronized full-game video and three engines

New in V0.3.3: a self-rendered **961-frame, 41-move** Gomoku demonstration, a shared WPF playback clock (video and board update at the same source frame), default **2x playback**, and an independent MATLAB recognition engine selectable alongside Python/OpenCV and C#/OpenCvSharp.

**Videos**: `demo/full_game/full_game_961.mp4` is 720×720, 961 frames at 30 FPS (32.03 s, played at 2× in WPF). `demo/full_game/full_game_synced_961_2x.mp4` contains BOTH the video and live board, 961 frames at 60 FPS (~16.02 s) for direct viewing. Both are synthetic; no third-party source video is redistributed. `results/full_game_demo/moves.csv` is a **preauthored oracle timeline, NOT recognition output**.

**Playback**: Both WPF play buttons drive the same monotonic timeline when an exact video/moves pair is loaded. Seeking either the frame slider or a move updates both panels. A hash check protects against pairing a different video with historical moves. The standalone 60 FPS synced movie is already 2×, and the UI switches its player speed to 1× when selected.

**MATLAB**: Select `MATLAB / Image Processing Toolbox` in WPF. Requires licensed MATLAB (R2021b+ recommended) and Image Processing Toolbox; point `GOMOKUVISION_MATLAB_EXE` to `matlab.exe` if necessary. Native `matlab/modern/gomoku_batch.m` uses VideoReader, normxcorr2 and VideoWriter to emit the common CSV/JSON outputs; it does **not** invoke the Python or C# recognizer. Test explicitly with `Run-MATLAB-Gate-Windows.bat`. Legacy original scripts remain under `matlab/legacy/`.

**Evidence**: Python 52 tests PASS, and full synthetic video Python recognition matches all 41 color/position pairs, with a 6-frame detection confirmation delay. Both MP4 container/frame counts were checked. **MATLAB runtime and V0.3.3 Windows WPF build/playback are NOT verified in this environment.** Previous V0.2.6 Windows dual-engine results cannot establish three-engine acceptance for V0.3.3. See `docs/V033_WINDOWS_ACCEPTANCE_zh_TW.md`.

No GitHub repository was published by this step. This source candidate needs Windows/MATLAB runtime acceptance and permission review for legacy source files.

---

# GomokuVision Advanced V0.3.2 — Local Original Video Import

The bundled `demo/demo.mp4` is synthetic (9 moves), **not** the 961-frame original. In Windows WPF select **Import original project folder (local only)** and choose a privately extracted folder with `input.mp4`, `checkerboard_points.csv`, `black.png` and `white.png`. The program verifies SHA-256 of both the user-provided video and the saved 41-move CSV before linking the video timeline to the historical move replay. This import **never re-runs recognition**. Reanalysis remains an explicit separate Analyze action. No third-party source footage is shipped or uploaded.

The unchanged Python recognition engine was re-tested here against the user-provided original input: 961 source frames, 161 sampled/analyzed, 41 moves, Black winner, all 41 matching the original project CSV. This is historical-output agreement, not independent annotated accuracy. **New WPF import and synchronization are pending Windows runtime verification.** See `docs/V032_ORIGINAL_VIDEO_ACCEPTANCE_zh_TW.md`.

---

# GomokuVision Advanced V0.3.1 — WPF Footer / DPI Layout Fix

This is a layout-only follow-up based on the user's V0.3.0 Windows screenshot (2026-11-08). The old 64-DIP footer could compress or clip its buttons at various DPI settings. V0.3.1 places status text on a separate footer row, gives the three action buttons at least 42 DIPs, and puts the main three-panel content inside horizontal/vertical scrollable viewport while keeping the footer fixed. The move slider now takes available width instead of a fixed width. Initial window position and size are bounded to the Windows work area to avoid the taskbar.

**Validation:** 39/39 local Python and source-contract tests PASS, including 6 new static layout tests; XAML XML structure PASS. **Windows build, real WPF DPI layout, and interaction remain pending**; no Windows SDK is available in this environment. The original image recognition core and cached 41-move results are unchanged. The historical third-party video was not reprocessed. To test layout, run `scripts/Verify-WPF-Build-Windows.bat`, then `Launch-Desktop-Windows.bat`. Refer to `docs/V031_WPF_LAYOUT_ACCEPTANCE_zh_TW.md`. The optional quick-engine gate only uses a short synthetic demo video.

---

# GomokuVision Advanced V0.3.0 — WPF Video / Move Timeline

This is the **single current release candidate** (2026-11-08), based on the Windows-tested V0.2.6 synthetic dual-engine gate. It adds an interactive move slider, previous/next/play controls, a dynamically rendered board at any selected move, on-demand OpenCvSharp video seeking, and a manual four-corner 15×15 calibration preview with Undo.

**Critical safety rule:** A video is synchronized with a move log only if the result JSON `input` absolute path matches the loaded video file. The bundled `demo/demo.mp4` is a synthetic demonstration and must not be represented as the original historical 41-move footage. The 961-frame third-party video is not distributed or reprocessed.

**Validation:** Local Python 33/33 PASS; synthetic short video 9/9 moves and Black win PASS; XML/source-event checks PASS. V0.3 WPF compilation, runtime and interaction have **not** been tested on Windows in this environment. The user-provided V0.2.6 Windows evidence confirms 11/11 synthetic gate stages PASS on the older version only. MATLAB historical sources are preserved but not included in equivalent three-engine automated tests.

Run `scripts/Verify-WPF-Build-Windows.bat`, then `Launch-Desktop-Windows.bat`. For synthetic cross-engine evidence run `Quick-Engine-Gate-Windows.bat`. The new gate additionally writes descriptive, non-comparable timing JSON/CSV. See `docs/V030_GUI_ACCEPTANCE_zh_TW.md`.

---

# V0.2.6 — C# tactical self-test oracle correction (2026-11-08)

The user-provided V0.2.5 Windows Quick Gate log confirms Python dependencies, 22/22 Python tests, .NET 10 SDK, and C# Release CLI compilation passed. The next gate failed with `Winning move suggestion failed`. The C# self-test placed four black stones at D8, E8, F8, G8, but incorrectly expected D8 or I8 to win. The true immediate winning candidates are **C8 or H8**. The updated self-test validates those coordinates, the 10,000,000 tactical score, and a real resulting five-in-a-row. Three Python source/fixture cross-checks guard against repeating the wrong test oracle. Detection engines, MATLAB legacy source and historic 41-move results are unchanged. No historic footage is reprocessed. **Windows C# self-test, synthetic cross-engine parity and WPF build still require a fresh Windows run**; success must not be claimed from Python source checks alone.

From an extracted V0.2.6 directory, run `Quick-Engine-Gate-Windows.bat` and inspect `%LOCALAPPDATA%\GomokuVision\Gates\quick-gate-latest.json`. A full pass requires `QUICK_ENGINE_GATE_PASS`. A completed WPF GUI usage acceptance is separate from build success.

# V0.2.5 Windows PowerShell 5.1 quick-gate fix

The V0.2.4 Windows WPF UI launched successfully, but the synthetic quick gate stopped at the Python dependency preflight because Windows PowerShell 5.1 altered the quotes in an inline `python -c` expression. This does **not** establish that OpenCV or NumPy are missing. The preflight now executes `python/tools/check_dependencies.py` as a file. The program prints `DEPENDENCY_CHECK_PASS` or a precise import failure and install command. Historical 41-move data and the recognition engines are unchanged; the original 961-frame footage is NOT reprocessed. Windows cross-engine Gate still requires a real Windows run.

## V0.2.5 Dual-engine synthetic quick gate

The V0.2.3 WPF window was visibly launched on the user's Windows computer. The new V0.2.4 adds a WPF button and `Quick-Engine-Gate-Windows.bat` to test Python and C# independently on the **owned short synthetic demo** with a known nine-move oracle, cross-engine parity and a Windows WPF Release build. It never reprocesses the original 961-frame footage, and does not alter the 41 saved historical moves. See `%LOCALAPPDATA%\GomokuVision\Gates\quick-gate-latest.json` and dated logs for results. Requires .NET 10 SDK, Python with OpenCV/NumPy/pytest; dependencies are checked, not automatically installed. New V0.2.4 WPF build/runtime is **not yet verified on Windows**; this package contains source-level and Linux Python checks only. MATLAB legacy code remains separate from the gate.

## V0.2.3 CS1001 source fix (Windows .NET 10.0.403)

Fixed two `CS1001` parser errors at `csharp/GomokuVision/VisionDetector.cs:196` from invalid C# literals `[-1.,-1.]` to explicit `new double[] { -1.0, -1.0 }`. Added a regression source guard. Run `scripts/Verify-WPF-Build-Windows.bat` without reprocessing video, then `scripts/Launch-Desktop-Windows.bat` if the build passes. Windows WPF build/GUI acceptance remains pending.

# NU1701 compatibility fix — V0.2.3

The .NET 10 CLI previously referenced the `OpenCvSharp4.Windows` meta-package,
which transitively imported WPF extensions and raised `NU1701` when targeting `net10.0`.
The CLI now references `OpenCvSharp4` and `OpenCvSharp4.runtime.win` directly
(identical pinned package version `4.13.0.20260627`). The desktop project stays `net10.0-windows`.
Run `scripts/Verify-WPF-Build-Windows.bat` to restore and build **without processing any video**.
Windows compile/run have not been validated in this environment.

# GomokuVision Advanced V0.2.2 — MATLAB / Python / C# / WPF

15×15 Gomoku recognition from video with board calibration, NCC template matching, scan scheduling, move history, win detection, tactical move suggestions and a bilingual (Traditional Chinese / English) Windows WPF interface.

**Only this V0.2.2 source package is intended for review and potential GitHub publication.** The included demo video and templates are programmatically generated, not extracted from third-party footage.

## Engines

- `matlab/legacy`: archived original course project; unchanged, requires MATLAB and the relevant toolboxes. Not covered by new regression tests.
- `python/gomoku`: independent Python + OpenCV CLI; video recognition and outputs; automated tests verified in this environment.
- `csharp/GomokuVision`: independent .NET 10 / OpenCvSharp CLI with parity-oriented logic; **Windows build and end-to-end acceptance pending**.
- `csharp/GomokuVision.Desktop`: real Windows-only WPF source with engine selection (C# or installed Python), four-corner click calibration, live annotated-frame preview, cancellation, move table, board and top-5 suggestions. **WPF build and manual GUI acceptance pending**.

New tactic rules prioritize an immediate winning move over a forced single-step block, and a forced block over general positional heuristics. This is **not** AI model training, Gemini, Minimax or a proven optimal Gomoku AI.

## Quick start (Windows)

Install .NET 10 SDK and Python 3.10+ with pip. From the extracted repository folder:

```powershell
.\scripts\Run-All-Local-Windows.bat
.\scripts\Launch-Desktop-Windows.bat
```

If only Python is available:

```powershell
.\scripts\Run-All-Local-Windows.bat -SkipDotnet
```

The main video CLI commands and output file descriptions are in the [Traditional Chinese README](README.md). The scripts generate or use the self-authored synthetic demo in `demo/` and compare move sequences across engines when .NET is installed.

## Calibration and coordinate conventions

In the WPF UI, click the OUTERMOST grid intersections in **top-left → top-right → bottom-left → bottom-right** order. This is manual corner selection with bilinear interpolation, **not** automatic calibration. The legacy calibration CSV uses letter=row and number=column while visible move notation is letter=column and number=row.

## Validation and limitations

Python tests, synthetic video integration, and replay on the author's historical input were performed locally. The real replay reproduced **41 of 41 positions and color order compared against the old output CSV after whitespace normalization**, not a separately annotated ground truth. Dataset-level accuracy and cross-machine speed improvements are NOT established. WPF / C# require on-Windows build and GUI acceptance.

The demo and original 2025 sources are separate; historical third-party footage, captured templates, and the identifiable school report are excluded. No open-source license is imposed automatically; ensure original authorship and license rights before publishing.

See [Windows acceptance](docs/WINDOWS_ACCEPTANCE_zh_TW.md), [release audit](docs/PUBLISH_CHECKLIST_zh_TW.md), and [validation evidence](docs/VALIDATION_SUMMARY.json).

## V0.2.2 startup recovery and cached results

Use `scripts/Launch-Desktop-Windows.bat` for verbose WPF build/start diagnostics and logs in `%LOCALAPPDATA%\GomokuVision\Logs\`. If WPF cannot start, it reports failure and opens the offline **read-only** viewer; this is not a WPF success. For instant replay without reprocessing the original video or installing .NET/Python, double-click `scripts/Show-Verified-Results-Windows.bat`, or open `docs/VerifiedResults.html`. The 41-move historical result is bundled in `results/verified_historical` without copyrighted footage. Windows/WPF was not executed in this Linux testing environment.
