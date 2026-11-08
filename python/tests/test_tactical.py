"""Additional tactical and reproducibility regression cases."""
import pytest
from gomoku.core import Board
from gomoku.vision import Calibration


def test_immediate_win_over_center():
    board=Board()
    for c in (3,4,5,6):board.place(c,1,7,c)
    best=board.suggestions(1,1)[0]
    assert best.position in {'C8','H8'}
    assert best.score==10_000_000


def test_opponent_four_must_be_blocked():
    board=Board()
    for r in (3,4,5,6):board.place(r,2,r,7)
    best=board.suggestions(1,1)[0]
    assert best.position in {'H3','H8'}
    assert best.score==5_000_000


def test_own_win_outweighs_opp_block():
    board=Board()
    for c in (3,4,5,6):board.place(c,1,7,c)
    for r in (3,4,5,6):board.place(9+r,2,r,11)
    best=board.suggestions(1,1)[0]
    assert best.score==10_000_000


def test_diagonal_win_priority():
    board=Board()
    for i in range(4):board.place(i+1,2,3+i,5+i)
    assert board.suggestions(2,1)[0].score==10_000_000


def test_deterministic_empty_board():
    a,b=Board(),Board()
    assert a.suggestions(1)==b.suggestions(1)
    assert a.suggestions(1,1)[0].position=='H8'


def test_corner_calibration_roundtrip(tmp_path):
    corners=((20,30),(690,25),(30,700),(700,705))
    cal=Calibration.create_from_corners(*corners)
    path=tmp_path/'cal.csv'
    cal.write_legacy_csv(path)
    loaded=Calibration.from_legacy_csv(path)
    assert abs(loaded.points[0,0,0]-20)<1e-5
    assert abs(loaded.points[14,14,1]-705)<1e-5
    assert abs(loaded.points[7,7,1]-365)<1e-5


def test_duplicate_coordinate_rejected():
    b=Board();b.place(1,1,7,7)
    with pytest.raises(ValueError): b.place(2,2,7,7)
