"""Language-neutral game logic. Coordinates are always 0-based internally.

Board: 0 empty, 1 black, 2 white. Display position: column A..O + row 1..15.
The heuristic is intentionally shallow: this is NOT a minimax or a learned model.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

SIZE = 15
DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))


@dataclass(frozen=True)
class Move:
    frame: int
    color: int
    row: int
    col: int

    @property
    def position(self) -> str:
        return f'{chr(65 + self.col)}{self.row + 1}'


@dataclass(frozen=True)
class Suggestion:
    row: int
    col: int
    score: float

    @property
    def position(self) -> str:
        return f'{chr(65 + self.col)}{self.row + 1}'


class Board:
    def __init__(self) -> None:
        self.cells = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
        self.moves: list[Move] = []

    def place(self, frame: int, color: int, row: int, col: int) -> Move:
        if color not in (1, 2) or not (0 <= row < SIZE and 0 <= col < SIZE):
            raise ValueError('Invalid color or coordinate')
        if self.cells[row][col]:
            raise ValueError(f'Occupied square {chr(65 + col)}{row + 1}')
        self.cells[row][col] = color
        move = Move(frame, color, row, col)
        self.moves.append(move)
        return move

    def winner(self) -> Optional[tuple[int, list[tuple[int, int]]]]:
        for r in range(SIZE):
            for c in range(SIZE):
                color = self.cells[r][c]
                if not color:
                    continue
                for dr, dc in DIRECTIONS:
                    line = []
                    for k in range(5):
                        rr, cc = r + k * dr, c + k * dc
                        if not _inside(rr, cc) or self.cells[rr][cc] != color:
                            break
                        line.append((rr, cc))
                    if len(line) == 5:
                        return color, line
        return None

    def suggestions(self, player: int, top: int = 5) -> list[Suggestion]:
        if player not in (1, 2):
            raise ValueError('player must be 1 or 2')
        scored = []
        for r in range(SIZE):
            for c in range(SIZE):
                if self.cells[r][c] == 0:
                    scored.append(Suggestion(r, c, self._evaluate(r, c, player)))
        scored.sort(key=lambda x: (-x.score, x.row, x.col))
        return scored[:top]

    def _evaluate(self, r: int, c: int, player: int) -> float:
        opponent = 3 - player
        # Tactical safety gate: winning now > blocking a one-move loss >
        # positional heuristics. This is not multi-ply minimax.
        if self._wins_with(r, c, player):
            return 10_000_000.0
        if self._wins_with(r, c, opponent):
            return 5_000_000.0
        moves = len(self.moves)
        center_dist = abs(r - 7) + abs(c - 7)
        center = 50 * max(0, (3 - center_dist) / 3)
        nearby = sum(
            self.cells[rr][cc] == player
            for rr in range(max(0, r - 2), min(SIZE, r + 3))
            for cc in range(max(0, c - 2), min(SIZE, c + 3))
            if (rr, cc) != (r, c)
        )
        structure = 100 * nearby if nearby >= 2 else 0
        new_front = 80 if 8 <= moves < 30 and center_dist > 5 and nearby <= 1 else 0
        offense = 0
        defense = 0
        for dr, dc in DIRECTIONS:
            own_count, own_open = self._line_shape(r, c, player, dr, dc)
            opp_count, opp_open = self._line_shape(r, c, opponent, dr, dc)
            offense += _pattern_score(own_count, own_open)
            defense += _pattern_score(opp_count, opp_open) * .9
        if moves >= 30:
            return max(offense, defense * 1.2)
        if moves >= 10:
            return max(offense, defense * 1.1) + center + structure
        return offense * 1.2 + defense + center + structure + new_front

    def _wins_with(self, r: int, c: int, color: int) -> bool:
        if self.cells[r][c] != 0:
            return False
        for dr, dc in DIRECTIONS:
            total = 1
            for sign in (-1, 1):
                for k in range(1, 5):
                    rr, cc = r + sign*k*dr, c + sign*k*dc
                    if not _inside(rr, cc) or self.cells[rr][cc] != color:
                        break
                    total += 1
            if total >= 5:
                return True
        return False

    def _line_shape(self, r: int, c: int, color: int, dr: int, dc: int) -> tuple[int, int]:
        total = 1  # hypothetical placement at the candidate
        open_ends = 0
        for direction in (1, -1):
            run = 0
            while True:
                rr = r + direction * (run + 1) * dr
                cc = c + direction * (run + 1) * dc
                if not _inside(rr, cc) or self.cells[rr][cc] != color:
                    break
                run += 1
            total += run
            rr = r + direction * (run + 1) * dr
            cc = c + direction * (run + 1) * dc
            if _inside(rr, cc) and self.cells[rr][cc] == 0:
                open_ends += 1
        return total, open_ends


def _inside(r: int, c: int) -> bool:
    return 0 <= r < SIZE and 0 <= c < SIZE


def _pattern_score(count: int, ends: int) -> int:
    if count >= 5:
        return 1_000_000
    if count == 4:
        return 100_000 if ends else 5_000
    if count == 3:
        return 10_000 if ends == 2 else (5_000 if ends else 0)
    if count == 2:
        return 1_000 if ends == 2 else (500 if ends else 0)
    return 0
