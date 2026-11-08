"""C# self-test oracle parity guard, run on all supported Python hosts.

This checks the *test fixture* against the language-neutral game rules.
It is a source-level guard, not a substitute for running `dotnet run -- --self-test`.
"""
from pathlib import Path
from gomoku.core import Board

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "csharp" / "GomokuVision" / "Program.cs"


def test_csharp_winning_move_oracle_agrees_with_board():
    board = Board()
    for col in range(3, 7):
        board.place(col - 2, 1, 7, col)
    best = board.suggestions(1, 1)[0]
    assert best.position in {"C8", "H8"}
    assert best.score == 10_000_000
    assert board.cells[7][3] == 1  # D8 already occupied
    assert board.cells[7][8] == 0  # I8 is empty but cannot win immediately
    board.place(5, 1, best.row, best.col)
    assert board.winner() is not None and board.winner()[0] == 1


def test_csharp_selftest_checks_a_real_win_and_correct_fixture():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'winning.Position is not ("C8" or "H8")' in source
    assert 'winning.Score != 10_000_000' in source
    assert 'board.Place(5,1,winning.Row,winning.Col)' in source
    assert 'board.Winner()?.Color!=1' in source
    assert 'Position is not ("D8" or "I8")' not in source


def test_csharp_blocking_fixture_follows_shared_rules():
    board = Board()
    for row in range(3, 7):
        board.place(row, 2, row, 7)
    best = board.suggestions(1, 1)[0]
    assert best.position in {"H3", "H8"}
    assert best.score == 5_000_000
    source = SOURCE.read_text(encoding="utf-8")
    assert 'Immediate opponent threat not blocked' in source
