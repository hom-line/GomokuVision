"""Regression for Windows WinError 5 on overwriting a displayed PNG.

Tests Python for real; asserts shared C# / MATLAB / WPF source contracts.
Windows and MATLAB native runtime are independently verified by the user.
"""
import csv
import json
from pathlib import Path
from gomoku.app import parse_args, run

ROOT = Path(__file__).resolve().parents[2]


def _demo_args(tmp_path, progress_file):
    demo = ROOT / 'demo'
    return parse_args([
        '--input', str(demo / 'demo.mp4'),
        '--calibration', str(demo / 'checkerboard_points.csv'),
        '--black-template', str(demo / 'black.png'),
        '--white-template', str(demo / 'white.png'),
        '--output-dir', str(tmp_path / 'outputs'),
    ] + (['--progress-file', str(progress_file)] if progress_file is not None else []))


def test_live_preview_never_replaces_last_frame_and_retries_json_contention(tmp_path, monkeypatch):
    progress = tmp_path / 'progress.json'
    original_replace = Path.replace
    state = {'json_failures': 0}

    def simulate_windows_file_lock(source, destination):
        name = Path(destination).name
        if name == 'last_frame.png':
            raise PermissionError('WinError 5: last_frame.png is being displayed')
        if name == 'progress.json' and state['json_failures'] < 2:
            state['json_failures'] += 1
            raise PermissionError('WinError 5: progress reader briefly held the file')
        return original_replace(source, destination)

    monkeypatch.setattr(Path, 'replace', simulate_windows_file_lock)
    stats = run(_demo_args(tmp_path, progress))
    assert stats['moves'] == 9
    assert stats['winner'] == 'Black'
    assert state['json_failures'] == 2
    snapshots = sorted((tmp_path / 'outputs' / 'preview_frames').rglob('frame_*.png'))
    assert len(snapshots) >= 3
    assert len({p.name for p in snapshots}) == len(snapshots)
    assert (tmp_path / 'outputs' / 'last_frame.png').is_file()
    latest = json.loads(progress.read_text(encoding='utf-8'))
    assert latest['moves'] == 9
    assert len(latest['move_records']) == 9
    assert Path(latest['preview_path']).is_file()
    assert Path(latest['preview_path']).parent == snapshots[-1].parent
    with (tmp_path / 'outputs' / 'moves.csv').open(newline='') as f:
        assert len(list(csv.DictReader(f))) == 9


def test_without_gui_progress_still_writes_stable_final_thumbnail(tmp_path):
    stats = run(_demo_args(tmp_path, None))
    assert stats['moves'] == 9
    assert (tmp_path / 'outputs' / 'last_frame.png').is_file()
    assert not (tmp_path / 'outputs' / 'preview_frames').exists()


def test_matlab_is_immutable_png_publisher_with_bounded_json_retry():
    text = (ROOT/'matlab/modern/gomoku_batch.m').read_text(encoding='utf-8')
    assert 'previewDir=tempname(previewRoot)' in text
    assert "imwrite(annotated,lastPreview)" in text
    assert "movefile(tmpPreview,lastPreview,'f')" not in text
    assert "for attempt=1:8" in text
    assert "'preview_path',preview" in text
    assert "writeProgress(opts,numRead,video,numAnalyzed,moveCount,lastPreview,moves(1:moveCount,:))" in text


def test_csharp_uses_immutable_snapshots_and_wpf_readers_allow_delete_sharing():
    core = (ROOT/'csharp/GomokuVision/Program.cs').read_text(encoding='utf-8')
    ui = (ROOT/'csharp/GomokuVision.Desktop/MainWindow.xaml.cs').read_text(encoding='utf-8')
    assert 'Guid.NewGuid().ToString("N")' in core
    assert 'latestPreview=Path.Combine(previewFolder,' in core
    assert 'File.Move(tempFile,previewFile,true)' not in core
    assert 'FileShare.ReadWrite | FileShare.Delete' in ui
    assert 'JsonDocument.Parse(stream)' in ui
    assert 'ApplyLiveMoves(value.MoveSnapshot)' in ui
