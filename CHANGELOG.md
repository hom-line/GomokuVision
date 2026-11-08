### V0.3.9 benchmark timing correction

- Instrumented `recognition_seconds` across MATLAB, Python and C# using per-detection timers with matched scope.
- `benchmark-results.csv` retains end-to-end and in-process time and adds core recognition, launcher overhead and non-recognition pipeline costs.
- `benchmark-summary.csv` now includes separate means for recognition/core, in-process pipeline and launcher overhead.
- Windows GUI result summary distinguishes recognition time from pipeline time instead of labeling either as a generic runtime.
- Historical V0.3.8 observations remain intact; no nonexistent core metrics were backfilled. New Windows native measurements are required to validate core timings.

## V0.3.9 — English-first desktop and GitHub publication candidate (2026-11-08)

- Default WPF `LanguageBox` selection is now English while Traditional Chinese remains available.
- Added English localization for first-run tooltips, preserving existing bilingual controls.
- Replaced the overlong root historical README with a focused English project landing page and a Traditional Chinese companion. Historical README content is preserved under `docs/history/`.
- Added anonymized 36/36 native Windows synthetic benchmark evidence from the user-provided V0.3.8 results (1×/2×/4× playback labels); accurately separates compute time from playback speed.
- Added publishing/licensing readiness guide, contributing and security notes. No LICENSE is asserted until original authorship/rights are confirmed.
- **No recognition, ROI, move prediction or timeline algorithm changes.** Windows v0.3.9 startup language still needs a fresh GUI smoke test.

## V0.3.8 — 精簡 GUI 與可複選倍率的自動化測試

- 左側主要操作區精簡為影片、引擎、ROI、顯示模式及批次測試；校準、黑白模板、輸出、進階參數與舊驗收收進可展開面板，不刪除功能。
- 一鍵測試可複選 1×、2×、4×，一次執行 12／24／36 組（3 引擎 × 2 ROI × 2 顯示模式 × 勾選倍率）。
- CSV 新增 `playback_speed`、理論播放秒數、播放端點數學模型欄；摘要依倍率分組。明確註明倍率不是運算加速。
- 不同倍率的每組辨識使用獨立目錄；原始 41 手歷史資料不被覆寫。
- Python／來源測試 70/70 PASS；Python 完整 961 幀三倍率、各四組合分別驗證，共 12/12 PASS。C#／WPF 與 MATLAB 新介面需要 Windows 驗收。

## V0.3.7 — 三引擎 12 組完整基準與 MATLAB 綠框視覺修復

- WPF 一鍵執行 3 引擎 × 2 ROI × 2 顯示模式，共 12 組，每組獨立輸出。
- 自動匯出明細／摘要 CSV，記錄耗時、棋步、匹配次數、失敗與未執行項目。
- MATLAB 已確認棋子的綠框從一像素調為三像素，預測框兩像素，改善縮小預覽時的消失問題。
- MATLAB summary.json 補足 ROI／顯示模式與 NCC 匹配嘗試次數。
- V0.3.6 核心與合成棋局資料保留；Windows C#／WPF 與 MATLAB 新增功能尚待實機驗收。

## V0.3.6 — 2026-11-08 (legacy ROI strategies + green box overlays)

- Implemented **separated black/white ROI** and **shared candidate ROI** as distinct per-color NCC gating behaviors in all three new engines. Default separated keeps V0.3.5 behavior.
- Added two WPF display modes: green confirmed-move rectangles only; or green rectangles plus heuristic green/cyan prediction markers. WPF overlay uses calibrated source pixel coordinates and the existing synchronized move timeline.
- Exported recognition video and previews now draw green rectangles on **confirmed detections**; MATLAB uses pure image assignment instead of adding a new toolbox requirement. Full synthetic demo films render green boxes from the **reference oracle**, clearly marked as such.
- Included two new 961-frame, 60-FPS side-by-side 2× synthetic demo videos; final frame and win line are retained.
- Included `Run-Legacy-Modes-Windows.bat` with Python/C# 2×2 synthetic oracle and parity checks, optionally native MATLAB with `-IncludeMatlab`.
- Python tests 64/64 PASS; 961-frame full-game 41/41 in both ROI strategies. **New C#/WPF and MATLAB runtime verification pending**.

---

## V0.3.5 (2026-11-08) — immutable preview snapshots / WinError 5 / MATLAB movefile fix

- Fix preview filename sharing race for Python, MATLAB and C#; WPF readers now permit deletion sharing.
- Python progress JSON: bounded retry for transient Windows file sharing failure.
- MATLAB progress: unique PNG per publish, `writeJson` retries, best-effort progress without aborting recognition.
- Added regression tests that emulate denied replacement of `last_frame.png` and intermittent progress JSON lock.
- Python 61/61 PASS and full 961-frame synthetic video 41/41 move parity. C#/WPF Windows build and licensed MATLAB run are NOT executed here.

## V0.3.4 — playback/live recognition/MATLAB fixes (2026-11-08)

- WPF now consumes Python and MATLAB atomic `move_records` JSON and C# immutable `MoveSnapshot` progress callbacks. The live board, move list and status advance on each confirmed move, not only after output CSV creation.
- Fix the MATLAB `table` error when the CSV column is named `Row` by assigning `DimensionNames={'MoveRecords','Variables'}`; add MATLAB smoke coverage for this regression.
- Improve MATLAB dark-stone candidate gating (broader disk instead of a dark cross center) and move overlay image grid allocation out of the loop. MATLAB performance is *not* benchmarked in the current environment.
- Keep recognition-confirmation frame indices in engine CSVs but add an explicit approximate visual-timeline delay for the viewer; oracle timelines are not modified.
- Re-encode the 961-frame 60fps left/right demonstration with the same final Black victory line on both sides, retaining 961 frames and 16.02-second baked 2x duration.
- WPF finalizes at source frame 961, rather than jumping to last confirmation at F955; a pre-baked 60fps movie auto-sets viewer speed to 1x even when reanalyzed.
- Optional three-engine quick Windows gate and full 961-frame *MATLAB-only* independent oracle gate.
- Verification: consult docs/V034_VALIDATION.json. Windows C# and licensed MATLAB runtime acceptance remain pending.

# V0.3.3 — 2026-11-08 (Synced 961-frame full game + MATLAB engine)

- Self-generated complete Gomoku: 961 frames, 30 FPS source, 41 moves, black win; side-by-side 60 FPS/2× MP4 renders both board states on the same frame.
- WPF defaults to full synthetic video and 41-move oracle, with verified hash pairing. Single monotonic clock drives both play buttons, sliders and board state; 1×/2×/4× controls added.
- MATLAB native `-batch` engine and optional 9-move MATLAB gate; separate legacy MATLAB code retained.
- Python full synthetic recognition: 41/41 known moves, 161 analyzed frames, 6-frame detection confirmation lag; 52 Python/source tests PASS.
- Known limits: Windows WPF V0.3.3 build and MATLAB native runtime not verified in this environment; original third-party movie excluded.

---

# V0.3.2 — Local original footage import + authenticated historical replay (2026-11-08)

- WPF original-folder import selects the private source video, its original 225-point calibration, and original black/white templates together; no raw footage is distributed.
- Original-source SHA-256 + historical 41-move CSV SHA-256 verification gates move/frame synchronization; mismatch means independent preview only.
- Import resets any previously shown 9-move demo results and reloads the saved 41-move historical results, without invoking the recognition engine.
- Legacy default demo and Quick Engine Gate remain synthetic; their 9-move oracle stays unchanged.
- V0.3.1 Python recognition core was re-run on user-provided historical footage: 961 frames, 161 analyzed, 41/41 equal to legacy output, Black wins. Not independent ground-truth accuracy.
- WPF Windows .NET build and interactive import/synchronization of V0.3.2 are not tested in this environment; requires actual Windows GUI acceptance.

---

# V0.3.1 — WPF footer clipping, compact-window/DPI layout hotfix (2026-11-08)

- Replaced the fixed 64-DIP bottom row with auto-sized footer containing separate status and controls rows.
- Gave footer buttons explicit 42-DIP minimum heights and reserved progress bar space; long status strings have ellipsis and tooltip.
- Main 3-column area scrolls independently, preserving a visible footer on compact and high-DPI displays.
- Changed the move slider to responsive star-column allocation, preserving its handlers and features.
- Fit initial window size/position within the Windows work area so the bottom controls do not start behind the taskbar.
- Local validation: Python/source tests 39/39 PASS, XAML XML parse and event contract PASS; no Windows WPF compile/runtime verification in this environment.
- Only layout/source/test/docs changed. No historical 961-frame video processing; no core recognition algorithm change.

---

# V0.3.0 — Video timeline and move replay (2026-11-08)

- Added on-demand OpenCvSharp video frame preview and seek/play controls, decoding on background tasks.
- Added move-by-move board redraw from cached move CSV, previous/next/scrub/autoplay and row-selection navigation.
- Synchronization is enabled only for exact `summary.json` video path matches; synthetic demo frames are never represented as historical footage.
- Added Undo and 15×15 grid overlay in four-corner calibration.
- Added descriptive synthetic Python/C# timing JSON/CSV to the existing Windows quick gate.
- Local validation: 32 Python tests PASS, synthetic 9-move / Black-winner oracle PASS, historical 41-move board state verified.
- V0.2.6 user Windows quick gate was 11/11 PASS. V0.3 Windows WPF build and GUI interaction remain unverified at packaging time.
- No historical video reprocessing; no third-party footage or private student report.

---

## V0.2.6 — C# tactical self-test golden answer hotfix (2026-11-08)

- Windows V0.2.5 Quick Gate evidence: Python dependencies PASS, Python pytest 22/22 PASS, .NET 10 SDK PASS, C# Release CLI build PASS (zero compile errors); `--self-test` failed at `Winning move suggestion failed` before synthetic video parity and WPF build.
- Fixed incorrectly specified self-test expected winning squares from `D8 / I8` to `C8 / H8` on the D8–G8 four-black-stone position. D8 was occupied; I8 was not an immediate winner.
- Strengthened C# self-test: assert top recommendation has tactical score 10,000,000; place it; assert five connected stones actually win.
- Added 3 source/fixture regression tests to Python, without mislabeling them as executed C#/.NET tests.
- Updated Windows gate version to 0.2.6. No changes to actual recognition scoring, templates, historical 41 move cache, MATLAB legacy, or video processing. No historical video reprocessing.
- Windows runtime result remains PENDING until a real Quick Gate run reaches `QUICK_ENGINE_GATE_PASS` and reports synthetic Python/C# oracle + WPF build.

## V0.2.5 — Windows PowerShell 5.1 quick-gate dependency quoting fix (2026-11-08)

- Windows screenshot confirmed V0.2.4 WPF opened, but synthetic quick gate failed at the FIRST Python dependency step with `SyntaxError: unexpected EOF while parsing`.
- Avoid `python -c` with nested quotes in Windows PowerShell 5.1: add `python/tools/check_dependencies.py` and invoke as a file. A successful import reports `DEPENDENCY_CHECK_PASS`; missing dependencies now report an install hint.
- Add a targeted regression test for argument-safe dependency checking and preserve the known nine-move synthetic oracle.
- No change to recognition code, historical 41-move cache, MATLAB sources, or demo video; **961-frame historical footage is not rerun**.
- Verified locally with Python tests and manifest validation. Windows .NET/C# cross-engine Gate remains unverified here; do not claim `QUICK_ENGINE_GATE_PASS` without the Windows run.

## V0.2.4 — Dual-engine synthetic quick gate and WPF experience (2026-11-08)

- Added a WPF button to run **Python + C# synthetic-only quick verification**, with standard output, error reporting, dated PowerShell logs and structured JSON in `%LOCALAPPDATA%\GomokuVision\Gates`.
- Verifies Python dependencies/tests, C# build/core tests, Python/C# recognition on owned `demo/demo.mp4`, independent nine-move synthetic oracle, move/color/winner parity, and WPF Release compilation. **Never reruns original 961-frame historical footage**.
- Added `Quick-Engine-Gate-Windows.bat` and `scripts/Quick-Engine-Gate-Windows.ps1`. No automatic `pip install`; prerequisite errors are explicit. Historical saved 41-move replay remains unchanged.
- Added path tooltips to address truncated Windows file paths; widened left input panel; connected localized button and status text.
- Added source/wiring guard tests and switched Windows GitHub CI to use the quick gate. The historical MATLAB files are unchanged and still require a separate MATLAB environment for tests.
- Evidence: V0.2.3 Windows WPF GUI was displayed in user screenshot, but the **new V0.2.4 build, C# runtime smoke tests and WPF button need Windows verification**; Linux Python tests and synthetic checks are performed here.

## V0.2.3 — CS1001 compiler syntax hotfix (2026-11-08)

- Fixed `csharp/GomokuVision/VisionDetector.cs:196` invalid C# floating-point forms `[-1.,-1.]` by explicitly initializing a double array with `-1.0` literals.
- This addresses the **two CS1001 errors reported on Windows .NET SDK 10.0.403**, once the V0.2.2 NuGet dependency issue was fixed.
- Added Python source guard tests and a Windows build preflight to detect recurrence of this exact malformed source line.
- Updated version/package, without changing detector thresholds, chess move data, original MATLAB sources, cached Python result, or video-processing behavior.
- **No video reprocessing is required for WPF build/launch checks.**
- Acceptance: Python and source tests checked locally; actual Windows .NET 10 WPF build, launch and C# engine still require Windows verification, not falsely claimed as passed.

## V0.2.2 — NU1701 / OpenCvSharp dependency fix (2026-11-08)

- Corrected .NET 10 CLI dependencies from `OpenCvSharp4.Windows` to `OpenCvSharp4` + `OpenCvSharp4.runtime.win`, both `4.13.0.20260627`.
- Prevent WPF extension package from entering the non-WPF `net10.0` core's transitive restore graph.
- Added Windows restore/build-only check with persistent log; this does not analyze any video.
- Updated Traditional Chinese and English instructions and manifest. All previously verified output records are preserved.
- Acceptance: Python tests and synthetic sample pass locally. Windows C# / WPF compile/run **not locally executed**.

## V0.2.1 - Desktop launch diagnostics / cached results (2026-11-08)

- Windows BAT and PowerShell launcher with persistent errors/logging and rapid-exit detection.
- WPF global exception log, startup cached-results view, and load-saved-results button.
- Offline HTML viewer for historical 41-move replay without .NET, Python, original footage, or rerunning video.
- Original video retested on Python: 14/14 unit tests; 41/41 replay CSV matches; 961 read / 161 analyzed; 7.437s in current Linux environment.
- C# WPF Windows compilation/execution remains not validated here.

# Changelog

## V0.2 — Advanced multi-language source candidate (2026-11-08)

- Kept all three historical MATLAB `.m` files unchanged under `matlab/legacy`.
- Python/C# core: immediate winning move > opponent immediate-win blocking > positional ranking; deterministic center opening; unmodified win detection and record format.
- Added independent C# WPF desktop source (Traditional Chinese/English UI), C#/Python engine selector, interactive four-corner calibration, input/template selectors, output folder, latest annotated-frame preview, move table, final board, top-5 suggestions and cancellation.
- Python engine: progress JSON and cancellation-file handshake; keep partial results on a graceful stop.
- C# engine: progress callbacks, cancellation token, rolling preview snapshot, final frame snapshot and partial-result report.
- Windows CI/build/test scripts, 14 Python pytest cases, C# tactical and calibration self-test gates, synthetic video and two-engine parity checks.
- Documented known limits, actual test state, rights audit and source-only GitHub publication guidance.

**Acceptance:** Python tests and replay passed locally. .NET 10 C# and Windows WPF compilation, runtime and GUI remain unverified in this environment.
