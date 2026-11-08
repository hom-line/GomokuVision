"""Regression checks for V0.3.1: visibility at compact resolutions and DPI scaling.

These are XAML/source contracts, not a substitute for an actual Windows WPF render.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
import re

ROOT = Path(__file__).resolve().parents[2]
XAML = ROOT / 'csharp' / 'GomokuVision.Desktop' / 'MainWindow.xaml'
CODE = ROOT / 'csharp' / 'GomokuVision.Desktop' / 'MainWindow.xaml.cs'
NS = '{http://schemas.microsoft.com/winfx/2006/xaml/presentation}'
X = '{http://schemas.microsoft.com/winfx/2006/xaml}'


def _get(name):
    root = ET.parse(XAML).getroot()
    found = [e for e in root.iter() if e.attrib.get(X+'Name') == name]
    assert len(found) == 1, f'{name} missing or duplicated'
    return found[0]


def test_footer_uses_auto_height_separate_status_row():
    root = ET.parse(XAML).getroot()
    grid = next(e for e in root if e.tag == NS+'Grid')
    rows = grid.find(NS+'Grid.RowDefinitions')
    assert rows is not None
    assert [x.attrib['Height'] for x in rows] == ['70','*','Auto']
    status = _get('StatusText')
    progress = _get('Progress')
    assert status.attrib['Grid.Row'] == '0'
    assert any(child.tag == NS+'Grid' and child.attrib.get('Grid.Row') == '1' and any(grand.attrib.get(X+'Name') == 'Progress' for grand in child) for child in root.iter())
    assert status.attrib['TextTrimming'] == 'CharacterEllipsis'
    assert 'ToolTip' in status.attrib


def test_footer_buttons_have_unclipped_height_and_stable_order():
    controls = [(_get(name), index) for index,name in enumerate(
        ['OpenResultsButton','CancelButton','RunButton'], start=1)]
    for element,index in controls:
        assert int(element.attrib['MinHeight']) >= 40
        assert int(element.attrib['Grid.Column']) == index
        assert element.attrib['VerticalAlignment'] == 'Center'
        assert int(element.attrib['Padding'].split(',')[1]) >= 9
    footer = _get('RunButton')
    assert footer.attrib['Click'] == 'Analyze_Click'


def test_main_content_scrolls_independently_of_footer():
    viewport = _get('MainContentViewport')
    assert viewport.attrib['Grid.Row'] == '1'
    assert viewport.attrib['VerticalScrollBarVisibility'] == 'Auto'
    assert viewport.attrib['HorizontalScrollBarVisibility'] == 'Auto'
    content = viewport.find(NS+'Grid')
    assert content is not None
    assert int(content.attrib['MinWidth']) >= 1000
    assert int(content.attrib['MinHeight']) >= 540
    assert 'ViewportHeight, ElementName=MainContentViewport' in content.attrib['Height']
    assert 'ViewportWidth, ElementName=MainContentViewport' in content.attrib['Width']


def test_no_fixed_width_replay_slider_and_all_handlers_preserved():
    slider = _get('MoveSlider')
    assert 'Width' not in slider.attrib
    assert slider.attrib['Grid.Column'] == '3'
    assert slider.attrib['ValueChanged'] == 'MoveSlider_ValueChanged'
    for name in ('PreviousMoveButton','NextMoveButton','MovePlayButton'):
        assert _get(name).attrib['MinHeight'] == '34'
    assert _get('FrameSlider').attrib['ValueChanged'] == 'FrameSlider_ValueChanged'


def test_work_area_clamp_and_no_recognition_reexecution():
    code = CODE.read_text(encoding='utf-8')
    assert 'SystemParameters.WorkArea' in code
    assert 'workArea.Bottom - Height' in code
    assert 'workArea.Right - Width' in code
    assert 'LoadResults(cached);' in code
    assert 'string.Equals(_frameReader.Path,_resultsVideoPath,StringComparison.OrdinalIgnoreCase)' in code


def test_wpf_references_expected_event_handlers():
    root = ET.parse(XAML).getroot()
    cs = CODE.read_text(encoding='utf-8')
    events = {'Click','SelectionChanged','ValueChanged'}
    for element in root.iter():
        for key,val in element.attrib.items():
            if key in events:
                assert re.search(r'\b' + re.escape(val) + r'\s*\(', cs), val
