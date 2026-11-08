"""Validate synthetic-only gate wiring and preserve historical data boundary."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


def test_quick_gate_is_exclusively_synthetic_and_keeps_logs():
    script = (ROOT / "scripts" / "Quick-Engine-Gate-Windows.ps1").read_text(encoding="utf-8-sig")
    assert "demo/demo.mp4" in script
    assert "python/tools/compare_runs.py" in script
    assert "verify_synthetic_expected.py" in script
    assert "python/tools/check_dependencies.py" in script
    assert "'-c','import" not in script  # no fragile inline Python source
    assert "historical_video_reprocessed=$false" in script
    assert "QUICK_ENGINE_GATE_PASS" in script
    assert "quick-gate-latest.json" in script
    assert "-c','Release'" in script
    assert "results/verified_historical" not in script


def test_wpf_button_is_wired_and_input_paths_have_tooltips():
    xaml = ROOT / "csharp" / "GomokuVision.Desktop" / "MainWindow.xaml"
    tree = ET.parse(xaml)
    buttons = [el for el in tree.iter() if el.get("{http://schemas.microsoft.com/winfx/2006/xaml}Name") == "QuickGateButton"]
    assert len(buttons) == 1 and buttons[0].get("Click") == "QuickGate_Click"
    code = (xaml.parent / "MainWindow.xaml.cs").read_text(encoding="utf-8")
    assert "private async void QuickGate_Click" in code
    assert "if (_running || _gateRunning || _benchmarkRunning) return;" in code
    for name in ("VideoPath", "CalibrationPath", "BlackPath", "WhitePath", "OutputPath"):
        el = next(el for el in tree.iter() if el.get("{http://schemas.microsoft.com/winfx/2006/xaml}Name") == name)
        assert el.get("ToolTip") == "{Binding Text, RelativeSource={RelativeSource Self}}"


def test_historical_cache_does_not_require_original_video_in_release():
    folder = ROOT / "results" / "verified_historical"
    assert (folder / "moves.csv").is_file()
    assert (folder / "summary.json").is_file()
    assert not (folder / "input.mp4").exists()


def test_synthetic_known_moves_oracle(tmp_path):
    import sys
    sys.path.insert(0, str(ROOT / "python" / "tools"))
    from verify_synthetic_expected import check
    from make_demo import make
    from gomoku.app import run
    from types import SimpleNamespace
    demo=tmp_path / "demo"
    make(demo)
    folder=tmp_path / "out"
    args=SimpleNamespace(input=demo / "demo.mp4", calibration=demo / "checkerboard_points.csv",
        black_template=demo / "black.png",white_template=demo / "white.png",output_dir=folder,
        sample_every=2,full_scan_every=3,local_radius=6,confirmations=2,scale=0.5,
        black_threshold=0.65,white_threshold=0.75,max_frames=0,preview=False)
    run(args)
    check(folder)
    original=(folder / "moves.csv").read_text(encoding="utf-8")
    (folder / "moves.csv").write_text(original.replace("E8", "J8", 1), encoding="utf-8")
    try:
        check(folder)
    except AssertionError as error:
        assert "SYNTHETIC_ORACLE_FAIL" in str(error)
    else:
        raise AssertionError("Corrupted move should fail the synthetic oracle")


def test_python_dependency_preflight_does_not_use_inline_python():
    import subprocess
    import sys
    step = ROOT / "python" / "tools" / "check_dependencies.py"
    source = step.read_text(encoding="utf-8")
    assert "DEPENDENCY_CHECK_PASS" in source
    assert "DEPENDENCY_CHECK_FAIL" in source
    result = subprocess.run([sys.executable, str(step)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "DEPENDENCY_CHECK_PASS" in result.stdout


def test_quick_gate_is_safe_for_windows_powershell_51():
    script = (ROOT / "scripts" / "Quick-Engine-Gate-Windows.ps1").read_text(encoding="utf-8-sig")
    assert "@('python/tools/check_dependencies.py')" in script
    assert "print(\"Python engine dependencies OK\")" not in script
    assert "historical_video_reprocessed=$false" in script
