"""Public distribution static contracts; licensed-asset and GUI runtime review remain manual."""
from pathlib import Path
import csv
import json
import re

ROOT=Path(__file__).resolve().parents[2]

def test_web_replay_has_one_video_board_timeline_and_no_third_party_js():
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    js=(ROOT/'web/app.js').read_text(encoding='utf-8')
    assert '<video id="video"' in html
    assert 'id="board"' in html and 'id="move-list"' in html
    assert 'id="speed"' in html and 'id="timeline"' in html
    assert 'demo/full_game/full_game_961_web.mp4' in html
    assert 'https://' not in html and '<script src="http' not in html
    assert 'video.currentTime' in js and 'moveCount(frame)' in js
    assert 'video.playbackRate=2' in js
    assert "['timeupdate','seeked','loadedmetadata','ended']" in js
    assert (ROOT/'web/style.css').is_file()

def test_reference_has_41_moves_and_last_move_at_frame_949():
    raw=(ROOT/'web/data.js').read_text(encoding='utf-8')
    moves=json.loads(raw.split('window.GOMOKU_DEMO_MOVES = ',1)[1].removesuffix(';\n'))
    assert len(moves)==41
    assert moves[-1]['frame']==949 and moves[-1]['color']=='Black'
    assert [m['index'] for m in moves]==list(range(1,42))
    assert all(1 <= m['frame'] <= 961 for m in moves)

def test_latest_windows_csv_has_complete_36_and_no_local_paths():
    f=ROOT/'docs/benchmarks/windows_v039_36_case_results_2026-11-08.csv'
    with f.open(encoding='utf-8',newline='') as h:
        data=list(csv.DictReader(h))
    assert len(data)==36
    assert all(x['status']=='PASS' and x['oracle_verified']=='PASS' for x in data)
    assert {'1','2','4'}=={x['playback_speed'] for x in data}
    assert {'csharp','python','matlab'}=={x['engine'] for x in data}
    assert all(x['moves']=='41' and x['frames_read']=='961' for x in data)
    assert not {'result_dir','log_file'}.intersection(data[0])
    assert 'C:\\Users\\' not in f.read_text(encoding='utf-8')

def test_public_package_does_not_include_2025_unreviewed_matlab_sources():
    assert not (ROOT/'matlab/legacy').exists()
    assert (ROOT/'matlab/modern/gomoku_batch.m').is_file()
    assert (ROOT/'README.md').read_text(encoding='utf-8').startswith('# GomokuVision')
    assert (ROOT/'PUBLICATION_GATE.md').is_file()
    assert (ROOT/'LICENSE').read_text(encoding='utf-8').startswith('MIT License')
