# Windows 36-case synthetic benchmark — 2026-11-08

**Observed evidence:** A user-executed Windows run completed all 36 cases (3 engines × 2 ROI modes × 2 overlays × 3 playback speed labels), all `PASS` with zero failed/skipped. Each case reported 961 source frames, 161 analyzed frames, 41 matched moves (21 black, 20 white), Black winner, and a synthetic oracle `PASS`. The selected speed labels were 1×, 2× and 4×.

| Engine | Cases | Mean pipeline time | Mean total process time | Mean external overhead* |
|---|---:|---:|---:|---:|
| C# / OpenCvSharp | 12 | 1.874 s | 1.985 s | 0.111 s |
| Python / OpenCV | 12 | 2.920 s | 3.087 s | 0.167 s |
| MATLAB | 12 | 8.767 s | 21.406 s | 12.639 s |

*External overhead includes startup, setup, shutdown and non-timed output; it is not a direct measurement of startup alone.

Data: [per-case CSV](windows_36_case_results_2026-11-08.csv), [summary CSV](windows_36_case_engine_summary.csv).

**Timing methodology change introduced in V0.3.9:** The 36-case Windows data above come from **V0.3.8** and have no independently recorded recognition-core timer. The 8.767-second MATLAB figure is the *pipeline time*, **not** an estimate of NCC-only computation. Do not invent retroactive core timing numbers. V0.3.9 writes three distinct metrics for fresh runs: `recognition_seconds` (detection and move commit), `engine_wall_seconds` (pipeline incl. video I/O/overlay), `elapsed_wall_seconds` (child process wall time incl. runtime launch). It also publishes `external_overhead_seconds` and `pipeline_other_seconds`. The non-core overhead includes more than just interpreter startup. 

**Interpretation limits:** Playback speed is metadata, not an engine-acceleration control. The 36 cases are NOT 36 independent videos: they repeat 12 configurations three times under different playback labels. The demo is self-authored synthetic footage, not real camera footage. The benchmark's playback check is a **mathematical endpoint model**, not proof that WPF video playback at each speed has passed interactive runtime acceptance. These timings include system, decoder and process effects; MATLAB's external overhead is substantial and should be isolated in future warm-process runs. No cross-scene accuracy or generality should be inferred.

The CSV intentionally omits local folder paths and console logs from the Windows test machine. No historical third-party footage is redistributed.
