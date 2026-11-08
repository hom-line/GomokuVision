import csv
from pathlib import Path
from gomoku.core import Board
from gomoku.vision import Calibration


def test_winner_horizontal():
    board=Board()
    for col in range(5): board.place(col+1,1,7,col+3)
    win=board.winner()
    assert win is not None and win[0] == 1 and len(win[1]) == 5


def test_winner_diagonal_and_no_false_positive():
    b=Board()
    for i in range(4):b.place(i+1,2,i,4+i)
    assert b.winner() is None
    b.place(5,2,4,8)
    assert b.winner()[0] == 2


def test_win_move_recommendation_first():
    b=Board()
    for i in range(4):b.place(i+1,1,7,4+i)
    assert b.suggestions(1,1)[0].position in {'D8','I8'}


def test_legacy_transpose(tmp_path):
    cal=Calibration.create_from_corners((10,20),(150,20),(10,160),(150,160))
    p=tmp_path/'pts.csv';cal.write_legacy_csv(p)
    read=Calibration.from_legacy_csv(p)
    assert tuple(read.points[7,8]) == (90.,90.)
    with p.open() as f:
        rows={r['Label']:(float(r['x']),float(r['y'])) for r in csv.DictReader(f)}
    assert rows['H9'] == (90.,90.)  # row H, numeric legacy col 9


def test_occupied_and_tie_order():
    b=Board();b.place(1,1,7,7)
    assert all(s.position!='H8' for s in b.suggestions(2))
