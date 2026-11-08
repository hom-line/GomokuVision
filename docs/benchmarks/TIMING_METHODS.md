# Timing methodology — three independent engines

This benchmark separates **different time scopes** instead of hiding MATLAB's launch cost.

| CSV / summary field | Scope | Contains |
|---|---|---|
| `recognition_seconds` | Accumulated core timer only | Repeated template matching/detection, confirmation and placement of new stones; excludes video reading, annotated rendering and video writing |
| `engine_wall_seconds` | In-process application timer | Whole video processing loop, overlays and encoded-video output; excludes initial interpreter / MATLAB startup and some setup |
| `elapsed_wall_seconds` | External orchestration timer | Time from starting the engine subprocess until process exit, including MATLAB `-batch` startup/shutdown |
| `pipeline_other_seconds` | Approx. engine minus core | Reading/decoding frames, drawing overlays, encoding frames, progress and final thumbnail within engine timer |
| `external_overhead_seconds` | Approx. external minus engine | Runtime startup + setup + final output + shutdown and other overhead; **not** identical to startup alone |

For a fair algorithmic comparison, show `recognition_seconds` beside `engine_wall_seconds`; for user-facing waiting time, also show `elapsed_wall_seconds`. Do not substitute one for another, and do not reduce or hide measured end-to-end MATLAB time. The core timer is a summed timer inside each recognition loop, using Python `perf_counter`, C# `Stopwatch`, and MATLAB `tic/toc`. It is not a precisely isolated microbenchmark: each engine still uses a different implementation and runtime, and ROI policies can alter workload.

**Original V0.3.8 Windows data:** 36/36 synthetic cases PASS; all recorded **pipeline** time and total child-process time. The archived CSV has no measured `recognition_seconds`, so no detection-only figures are claimed for that run. V0.3.9 on Windows requires a new benchmark to populate core values. Playback 1×/2×/4× affects replay timing, **not** recognition speed, even though selecting all three repeats analyses and adds samples. For publication, repeat at least 5 times in interleaved/randomized order and report median, range and hardware/OS versions. MATLAB licensing and MATLAB cold start must be disclosed.
