"""V0.3.3 runtime asset checks + static contracts.
Do NOT mislabel as Windows WPF or native MATLAB runtime acceptance.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
import csv
import hashlib
import json
import cv2
import pytest

ROOT=Path(__file__).resolve().parents[2]
DEMO=ROOT/'demo/full_game'
RESULT=ROOT/'results/full_game_demo'


def get_moves():
    with (RESULT/'moves.csv').open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def test_source_video_is_exactly_961_frames_and_30fps():
    cap=cv2.VideoCapture(str(DEMO/'full_game_961.mp4'))
    try:
        assert cap.isOpened()
        assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT))==961
        assert cap.get(cv2.CAP_PROP_FPS)==pytest.approx(30,abs=.01)
        for frame in (1,24,25,43,949,961):
            cap.set(cv2.CAP_PROP_POS_FRAMES,frame-1)
            good,image=cap.read()
            assert good and image is not None,frame
    finally:
        cap.release()


def test_synced_movie_has_same_961_frames_and_baked_two_times_speed():
    cap=cv2.VideoCapture(str(DEMO/'full_game_synced_961_2x.mp4'))
    try:
        assert cap.isOpened()
        assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT))==961
        assert cap.get(cv2.CAP_PROP_FPS)==pytest.approx(60,abs=.01)
    finally: cap.release()


def test_oracle_is_41_legal_moves_with_black_winner():
    from gomoku.core import Board
    rows=get_moves()
    assert len(rows)==41
    assert rows[0]['Frame']=='25'
    assert rows[-1]['Frame']=='949'
    game=Board()
    for i,item in enumerate(rows,1):
        assert item['Index']==str(i)
        assert int(item['Frame'])>=1
        color=1 if item['Color']=='Black' else 2
        assert color==(1 if i%2 else 2)
        game.place(int(item['Frame']),color,int(item['Row'])-1,int(item['Col'])-1)
    assert game.winner()[0]==1


def test_video_metadata_and_moves_are_hashed_and_explicitly_synthetic():
    meta=json.loads((DEMO/'manifest.json').read_text(encoding='utf-8'))
    assert meta['frame_count']==961 and meta['fps']==30
    assert meta['side_by_side_frame_count']==961 and meta['side_by_side_fps']==60
    for path,key in ((DEMO/'full_game_961.mp4','video_sha256'),
                     (DEMO/'full_game_synced_961_2x.mp4','side_by_side_2x_sha256')):
        assert hashlib.sha256(path.read_bytes()).hexdigest()==meta[key]
    assert hashlib.sha256((RESULT/'moves.csv').read_bytes()).hexdigest()==meta['moves_sha256']
    summary=json.loads((RESULT/'summary.json').read_text(encoding='utf-8'))
    assert summary['engine']=='synthetic-oracle'
    assert summary['original_video_redistributed'] is False
    assert 'NOT model inference' in summary['accuracy_note']


def test_wpf_two_buttons_use_same_monotonic_timeline():
    root=ET.parse(ROOT/'csharp/GomokuVision.Desktop/MainWindow.xaml').getroot()
    code=(ROOT/'csharp/GomokuVision.Desktop/MainWindow.xaml.cs').read_text(encoding='utf-8')
    controls={el.attrib.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name'):el
              for el in root.iter()}
    assert controls['SpeedBox'].attrib['SelectionChanged']=='SpeedBox_SelectionChanged'
    assert controls['MovePlayButton'].attrib['Click']=='MovePlay_Click'
    assert controls['VideoPlayButton'].attrib['Click']=='VideoPlay_Click'
    assert 'VideoPlay_Click(sender,e); // ONE shared video+board clock' in code
    assert 'PlaybackTimeline.FrameAt(' in code
    assert '_playbackClock.Elapsed.TotalSeconds' in code
    assert 'FrameSlider.Value = next' in code
    assert 'if (_videoMatchesMoves && _moveRows.Count>0)' in code
    assert 'SetMoveStep(count,seekMatchingVideo:false)' in code
    assert 'SpeedBox.SelectedIndex switch' in code
    assert 'FrameSlider.Value=Math.Clamp(move.TimelineFrame-1' in code
    assert 'BundledFullGameVideoSha256' in code


def test_third_matlab_engine_is_real_process_not_python_wrapper():
    root=ET.parse(ROOT/'csharp/GomokuVision.Desktop/MainWindow.xaml').getroot()
    controls={el.attrib.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name'):el
              for el in root.iter()}
    options=[e.attrib.get('Content') for e in controls['EngineBox']]
    assert len(options)==3 and 'MATLAB' in options[2]
    code=(ROOT/'csharp/GomokuVision.Desktop/MainWindow.xaml.cs').read_text(encoding='utf-8')
    assert '_matlabRunning=EngineBox.SelectedIndex==2;' in code
    assert 'else if (_matlabRunning) await RunMatlabAsync(opts);' in code
    assert 'psi.ArgumentList.Add("-batch");' in code
    assert 'GOMOKUVISION_MATLAB_EXE' in code
    m=(ROOT/'matlab/modern/gomoku_batch.m').read_text(encoding='utf-8')
    assert 'VideoReader(' in m and 'normxcorr2(' in m and 'VideoWriter(' in m
    assert 'writetable(result,' in m and "'summary.json'" in m
    assert 'python' not in m.lower().replace('no python','')
    assert (ROOT/'scripts/Run-MATLAB-Gate-Windows.ps1').is_file()


def test_video_and_board_share_frame_25_jump():
    rows=get_moves()
    frames=[int(x['Frame']) for x in rows]
    assert sum(f<=24 for f in frames)==0
    assert sum(f<=25 for f in frames)==1
    assert sum(f<=43 for f in frames)==2
    assert sum(f<=949 for f in frames)==41


def test_side_by_side_can_be_manually_selected_without_wrong_speed_pairing():
    code=(ROOT/'csharp/GomokuVision.Desktop/MainWindow.xaml.cs').read_text(encoding='utf-8')
    assert 'BundledSyncedTwoXVideoSha256' in code
    assert 'if (fingerprint==BundledSyncedTwoXVideoSha256)' in code
    assert 'SpeedBox.SelectedIndex=0;' in code
    assert 'else if (fingerprint==BundledFullGameVideoSha256)' in code
    assert 'SpeedBox.SelectedIndex=1;' in code
