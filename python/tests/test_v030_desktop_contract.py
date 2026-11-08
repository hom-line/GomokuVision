"""Structural contract for V0.3 WPF additions; not a Windows GUI runtime test."""
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
DESKTOP = ROOT / "csharp" / "GomokuVision.Desktop"
XAML = DESKTOP / "MainWindow.xaml"
CODE = DESKTOP / "MainWindow.xaml.cs"


def test_xaml_is_valid_and_new_handlers_exist():
    root = ET.parse(XAML).getroot()
    cs = CODE.read_text(encoding='utf-8')
    expected = {
        'MoveSlider_ValueChanged', 'MovesGrid_SelectionChanged',
        'PreviousMove_Click', 'NextMove_Click', 'MovePlay_Click',
        'LoadVideoPreview_Click', 'VideoPlay_Click', 'FrameSlider_ValueChanged',
    }
    values = []
    for element in root.iter():
        values.extend(v for k, v in element.attrib.items() if k in
                      {'Click', 'ValueChanged', 'SelectionChanged'})
    assert expected <= set(values)
    for name in expected:
        assert re.search(r'\b' + re.escape(name) + r'\s*\(', cs)


def test_replay_board_renders_moves_not_static_final_picture():
    renderer = (DESKTOP / 'ReplayBoardRenderer.cs').read_text(encoding='utf-8')
    assert 'board.Place(' in renderer
    assert 'board.Winner()' in renderer
    assert 'TryParsePosition' in renderer
    assert 'DrawEllipse' in renderer
    assert 'count = Math.Clamp(count, 0, moves.Count)' in renderer


def test_no_historical_video_confusion():
    code = CODE.read_text(encoding='utf-8')
    assert 'Path.IsPathFullyQualified(source)' in code
    assert 'string.Equals(_frameReader.Path,_resultsVideoPath,StringComparison.OrdinalIgnoreCase)' in code
    assert 'if (_videoMatchesMoves && _moveRows.Count>0)' in code
    assert 'if (seekMatchingVideo && _videoMatchesMoves' in code
    assert '_resultsVideoPath=null;' in code
    assert (ROOT/'results/verified_historical/moves.csv').exists()
    assert not (ROOT/'results/verified_historical/historical_input.mp4').exists()


def test_frame_reader_is_on_demand_and_serialized():
    reader = (DESKTOP/'VideoFrameReader.cs').read_text(encoding='utf-8')
    code = CODE.read_text(encoding='utf-8')
    assert 'lock (_gate)' in reader
    assert 'PosFrames' in reader
    assert 'await Task.Run(() => reader.ReadPng(frame))' in code
    assert 'frame!=_requestedFrame' in code
    assert 'if (!failed && _frameReader is not null' in code


def test_calibration_can_undo_and_preview_15_by_15():
    cal = (DESKTOP/'CalibrationWindow.xaml.cs').read_text(encoding='utf-8')
    root = ET.parse(DESKTOP/'CalibrationWindow.xaml').getroot()
    assert 'Undo_Click' in cal
    assert 'Interpolate(double u,double v)' in cal
    assert 'k<15' in cal
    assert any(e.attrib.get('Click') == 'Undo_Click' for e in root.iter())


def test_quick_gate_still_synthetic_only():
    script = (ROOT/'scripts/Quick-Engine-Gate-Windows.ps1').read_text(encoding='utf-8-sig')
    assert 'V0.3.3 QUICK ENGINE GATE' in script
    assert 'historical_video_reprocessed=$false' in script
    assert "'demo/demo.mp4'" in script
    assert 'summarize_engine_performance.py' in script


def test_descriptive_performance_report(tmp_path):
    from importlib.util import spec_from_file_location, module_from_spec
    script = ROOT/'python/tools/summarize_engine_performance.py'
    spec = spec_from_file_location('gv_perf', script)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    py=tmp_path/'py';cs=tmp_path/'cs';py.mkdir();cs.mkdir()
    (py/'summary.json').write_text(json.dumps({'wall_seconds':1.4,'frames_analyzed':29,'moves':9,'winner':'Black'}))
    (cs/'summary.json').write_text(json.dumps({'wall_seconds':0.9,'frames_analyzed':29,'moves':9,'winner':'Black'}))
    path=tmp_path/'out/report.json'
    module.report(py,cs,path)
    value=json.loads(path.read_text(encoding='utf-8'))
    assert value['historical_video_reprocessed'] is False
    assert value['engines'][0]['engine']=='python-opencv'
    assert (path.parent/'engine-comparison.csv').exists()


def test_wpf_controls_not_read_inside_background_frame_open():
    text=CODE.read_text(encoding='utf-8')
    assert 'string selectedPath=VideoPath.Text;' in text
    assert 'await Task.Run(() => new VideoFrameReader(selectedPath))' in text
    assert 'new VideoFrameReader(VideoPath.Text)' not in text
