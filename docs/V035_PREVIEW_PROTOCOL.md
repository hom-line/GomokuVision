# V0.3.5 Preview Protocol

1. Live engine creates `preview_frames/<run-id>/frame_<frame-index>.png` and never modifies that image again.
2. Engine finishes PNG writing before publishing progress JSON (`frame`, `total_frames`, `analyzed_frames`, `moves`, `preview_path`, `move_records`).
3. WPF opens both progress JSON and PNG with `FileShare.ReadWrite | FileShare.Delete`, reads the entire PNG via `BitmapCacheOption.OnLoad`, and displays confirmed move snapshots immediately.
4. `last_frame.png` is an offline thumbnail, saved **once** after decoding ends; not a live communication channel.
5. A result's output folder should be unique per run. `preview_frames` are temporary diagnostic artifacts and may be deleted after the GUI closes and tests are archived.
6. A temporary sharing violation in progress JSON publishing is retried; the MATLAB progress path is best-effort and does not cancel the underlying analysis when one snapshot cannot be published.
