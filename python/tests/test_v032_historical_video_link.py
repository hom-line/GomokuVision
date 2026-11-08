"""Source safeguards for private historical video import, NOT a Windows GUI runtime test."""
from pathlib import Path
from xml.etree import ElementTree as ET
import re, hashlib

ROOT=Path(__file__).resolve().parents[2]
DESKTOP=ROOT/'csharp/GomokuVision.Desktop'
XAML=DESKTOP/'MainWindow.xaml'
CODE=DESKTOP/'MainWindow.xaml.cs'


def test_import_button_is_wired_to_real_handler():
    window=ET.parse(XAML).getroot()
    buttons=[e for e in window.iter() if e.attrib.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name')=='ImportOriginalButton']
    assert len(buttons)==1
    assert buttons[0].attrib['Click']=='ImportOriginal_Click'
    code=CODE.read_text(encoding='utf-8')
    assert re.search(r'void\s+ImportOriginal_Click\s*\(',code)


def test_import_uses_four_private_original_inputs_not_demo_assets():
    code=CODE.read_text(encoding='utf-8')
    for name in ('input.mp4','checkerboard_points.csv','black.png','white.png'):
        assert f'Path.Combine(folder, "{name}")' in code
    assert 'VideoPath.Text = video;' in code
    assert 'BlackPath.Text = black;' in code and 'WhitePath.Text = white;' in code
    assert 'LoadResults(historical);' in code
    assert 'LoadVideoPreview_Click(sender, e);' in code
    # Import / playback only must not invoke recognition.
    start=code.index('private void ImportOriginal_Click')
    stop=code.index('private void PickVideo_Click',start)
    section = '\n'.join(line for line in code[start:stop].splitlines() if not line.lstrip().startswith('//'))
    assert 'Analyze_Click(' not in section
    assert 'Program.Run(' not in code[start:stop]


def test_historical_sync_requires_content_hash_on_video_and_moves():
    code=CODE.read_text(encoding='utf-8')
    assert 'SHA256.HashData(stream)' in code
    assert 'KnownHistoricalVideoSha256' in code
    assert 'KnownHistoricalMovesSha256' in code
    assert 'FileSha256(moves)==KnownHistoricalMovesSha256' in code
    assert 'fingerprint=await Task.Run(() => FileSha256(selectedPath));' in code
    assert 'fingerprint==KnownHistoricalVideoSha256' in code
    assert '_resultsVideoPath=(matchesVerifiedHistorical || matchesBundledFullDemo)' in code
    assert 'string.Equals(_frameReader.Path,_resultsVideoPath,StringComparison.OrdinalIgnoreCase)' in code
    assert 'if (_videoMatchesMoves && _moveRows.Count>0)' in code
    assert 'FrameSlider.Value=reader.FrameCount-1;' in code  # terminal video frame, no premature cutoff


def test_demo_gate_still_uses_only_synthetic_video():
    script=(ROOT/'scripts/Quick-Engine-Gate-Windows.ps1').read_text(encoding='utf-8-sig')
    assert "'demo/demo.mp4'" in script
    assert 'historical_video_reprocessed=$false' in script
    assert not (ROOT/'demo/input.mp4').exists()
    assert not (ROOT/'input.mp4').exists()


def test_historical_reference_data_unchanged():
    moves=ROOT/'results/verified_historical/moves.csv'
    assert hashlib.sha256(moves.read_bytes()).hexdigest()=='e61a6da9a5808c7b22e7aa80a3eb9b1c20fd2ac89b187c7d2b822be934c6c5f0'
    data=ROOT/'results/verified_historical/summary.json'
    assert 'historical_input.mp4 (not distributed' in data.read_text(encoding='utf-8')
