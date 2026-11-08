from pathlib import Path
import csv
import sys
from types import SimpleNamespace
from gomoku.app import run


def test_synthetic_end_to_end(tmp_path):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
    from make_demo import make
    demo=tmp_path/'demo'
    make(demo)
    out=tmp_path/'results'
    args=SimpleNamespace(input=demo/'demo.mp4', calibration=demo/'checkerboard_points.csv',
       black_template=demo/'black.png',white_template=demo/'white.png',
       output_dir=out,sample_every=2,full_scan_every=3,local_radius=6,
       confirmations=2,scale=.5,black_threshold=.65,white_threshold=.75,
       max_frames=0,preview=False)
    summary=run(args)
    assert summary['moves']==9 and summary['winner']=='Black'
    assert summary['frames_written'] == summary['frames_analyzed'] == 29
    with (out/'moves.csv').open() as f:
        rows=list(csv.DictReader(f))
    assert [row['Position'] for row in rows]==['E8','E9','F8','F9','G8','G9','H8','H9','I8']
    assert (out/'output.mp4').stat().st_size>2000
    assert (out/'board_final.png').stat().st_size>500


def test_progress_snapshot_and_graceful_cancellation(tmp_path):
    import json
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
    from make_demo import make
    demo=tmp_path/'demo';make(demo)
    out=tmp_path/'results'
    progress=tmp_path/'progress.json'
    canceled=tmp_path/'cancel.now'
    # Preexisting cancellation is a deterministic way to exercise a safe
    # empty-output stop without threading/timing races.
    canceled.write_text('cancel',encoding='utf-8')
    args=SimpleNamespace(input=demo/'demo.mp4',calibration=demo/'checkerboard_points.csv',
        black_template=demo/'black.png',white_template=demo/'white.png',
        output_dir=out,sample_every=2,full_scan_every=3,local_radius=6,
        confirmations=2,scale=.5,black_threshold=.65,white_threshold=.75,
        max_frames=0,preview=False,progress_file=progress,cancel_file=canceled)
    summary=run(args)
    assert summary['canceled'] is True and summary['frames_analyzed']==0
    assert (out/'summary.json').exists() and progress.exists()
    assert json.loads(progress.read_text())['analyzed_frames']==0
