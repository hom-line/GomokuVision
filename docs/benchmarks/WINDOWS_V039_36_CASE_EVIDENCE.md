# GomokuVision — v0.3.9 Windows verification, November 8, 2026

**36/36 PASS**, 0 failures, 0 skipped. The maintainer ran 3 language engines (MATLAB / Python / C#), 2 ROI strategies, 2 overlay modes and 3 playback labels (1×/2×/4×). Each case reported 961 source frames, 161 analyzed frames, 41 matched moves and Black as winner. All matched the **self-generated synthetic oracle**.

| Engine | Mean detection/commit only | Mean in-process pipeline | Mean end-to-end process |
|---|---:|---:|---:|
| C# / OpenCvSharp | 1.010s | 1.821s | 1.929s |
| Python / OpenCV | 1.377s | 2.830s | 2.988s |
| MATLAB | 1.363s | 8.909s | 21.889s |

[Raw per-case CSV](windows_v039_36_case_results_2026-11-08.csv) · [Engine summary CSV](windows_v039_engine_summary.csv) · [Timing methodology](TIMING_METHODS.md).

**Experimental limitations**

- This is the same 961-frame self-generated game across cases, not 36 independent videos or general real-world accuracy measurement.
- 1× / 2× / 4× are playback selections and repeated-benchmark *labels*, not a multiplier for detector computation speed.
- Recognition timing measures detection and move placement, excluding video decode, overlays, encoding and runtime launch. The pipeline and full-process columns measure different scopes and must not be conflated.
- MATLAB starts a fresh licensed process for each case in this test. The difference between process/pipeline timings is *external overhead*, including launch and shutdown; do not assign all overhead to startup alone.
- The three implementations have different accounting for NCC attempts; direct engine efficiency claims require matching units and workloads.
- Playback endpoint checks in the benchmark are mathematical, not a WPF or browser interactive acceptance test.
- Windows runtime evidence is reported by the maintainer; independently rerun using `Run-Selected-Speeds-Windows.bat` on a licensed test machine.
