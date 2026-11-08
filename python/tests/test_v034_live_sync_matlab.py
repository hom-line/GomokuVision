"""V0.3.4 evidence-oriented tests (not Windows WPF nor licensed MATLAB acceptance)."""
from pathlib import Path
import cv2
import csv
import hashlib
import json
from gomoku.app import run, parse_args
ROOT = Path(__file__).resolve().parents[2]


def _red_count(frame, rect):
    x1,y1,x2,y2=rect
    patch=frame[y1:y2,x1:x2]
    b,g,r=cv2.split(patch)
    return int(((r>175)&(g<120)&(b<120)).sum())


def test_synced_movie_contains_terminal_frame_and_both_winning_lines():
    cap=cv2.VideoCapture(str(ROOT/'demo/full_game/full_game_synced_961_2x.mp4'))
    assert cap.isOpened()
    assert cap.get(cv2.CAP_PROP_FRAME_COUNT)==961
    assert cap.get(cv2.CAP_PROP_FPS)==60
    captures=[]
    for index in (947,948,960):
        cap.set(cv2.CAP_PROP_POS_FRAMES,index)
        ok,frame=cap.read()
        assert ok, index
        captures.append(frame)
    cap.release()
    before,after,terminal=captures
    # Left is genuine synthetic source + winner annotation; right is board simulation.
    left=(12,12,672,672); right=(688,75,1218,605)
    assert _red_count(before,left)<10
    assert _red_count(after,left)>100
    assert _red_count(terminal,left)>100
    assert _red_count(terminal,right)>100
    assert _red_count(before,right)<10


def test_live_python_progress_contains_every_confirmed_move(tmp_path):
    demo=ROOT/'demo'
    progress=tmp_path/'progress.json'
    args=parse_args(['--input',str(demo/'demo.mp4'),
                     '--calibration',str(demo/'checkerboard_points.csv'),
                     '--black-template',str(demo/'black.png'),
                     '--white-template',str(demo/'white.png'),
                     '--output-dir',str(tmp_path/'out'),
                     '--progress-file',str(progress)])
    out=run(args)
    assert out['moves']==9 and out['winner']=='Black'
    assert out['confirmation_delay_frames']==6
    state=json.loads(progress.read_text(encoding='utf-8'))
    assert state['moves']==9 and len(state['move_records'])==9
    assert state['move_records'][0]['color']==1
    assert state['move_records'][-1]['color']==1
    with (tmp_path/'out/moves.csv').open() as f:
        rows=list(csv.DictReader(f))
    assert [m['frame'] for m in state['move_records']]==[int(r['Frame']) for r in rows]


def test_csharp_and_wpf_use_live_snapshot_not_wait_for_completed_csv():
    core=(ROOT/'csharp/GomokuVision/Program.cs').read_text(encoding='utf-8')
    gui=(ROOT/'csharp/GomokuVision.Desktop/MainWindow.xaml.cs').read_text(encoding='utf-8')
    assert 'board.Moves.ToArray()' in core
    assert 'IReadOnlyList<Move>? MoveSnapshot' in core
    assert 'ApplyLiveMoves(value.MoveSnapshot)' in gui
    assert 'e.TryGetProperty("move_records"' in gui
    assert 'MoveSlider.Maximum=Math.Max(1,_moveRows.Count)' in gui
    assert 'move.TimelineFrame-1' in gui
    assert 'm.TimelineFrame<=frame+1' in gui
    assert 'RequestPreviewFrame(_frameReader.FrameCount-1)' in gui


def test_matlab_export_row_conflict_fixed_and_matlab_progress_is_incremental():
    m=(ROOT/'matlab/modern/gomoku_batch.m').read_text(encoding='utf-8')
    assert "'VariableNames'," in m
    assert "'DimensionNames',{'MoveRecords','Variables'}" in m
    assert 'lastProgressMoves' in m
    assert "'move_records',records" in m
    assert 'writeProgress(opts,numRead,video,numAnalyzed,moveCount,lastPreview,moves(1:moveCount,:))' in m
    assert 'imwrite(annotated,lastPreview)' in m
    assert 'previewDir=tempname(previewRoot)' in m
    assert "movefile(tmpPreview,lastPreview,'f')" not in m
    selftest=(ROOT/'matlab/modern/gomoku_selftest.m').read_text(encoding='utf-8')
    assert "'DimensionNames',{'MoveRecords','Variables'}" in selftest


def test_dual_video_hash_keeps_original_source_unchanged():
    demo=ROOT/'demo/full_game'
    manifest=json.loads((demo/'manifest.json').read_text(encoding='utf-8'))
    for name,key in [('full_game_961.mp4','video_sha256'),
                     ('full_game_synced_961_2x.mp4','side_by_side_2x_sha256')]:
        assert hashlib.sha256((demo/name).read_bytes()).hexdigest()==manifest[key]
    assert manifest['video_sha256']=='0518c8f5e0627e396ca1e4d5a9e0ff687008f8c90efe0b9ac91875c29c594641'
