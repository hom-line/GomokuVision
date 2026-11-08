"""Video frame calibration and NCC detection.

Legacy CSV uses A1..O1, A2..O2 layout: first token letter is *row*,
number is *column*. This is opposite to the published move notation.
Never parse the legacy label as a normal game move position.
"""
from __future__ import annotations
import csv
from dataclasses import dataclass
from pathlib import Path
import cv2
import numpy as np
from .core import SIZE


@dataclass
class Calibration:
    points: np.ndarray  # [row, col, xy], float64

    @classmethod
    def from_legacy_csv(cls, path: str | Path) -> 'Calibration':
        points = np.full((SIZE, SIZE, 2), np.nan, dtype=np.float64)
        with open(path, newline='', encoding='utf-8-sig') as f:
            for entry in csv.DictReader(f):
                label = entry['Label'].strip().upper()
                if not label or label[0] not in 'ABCDEFGHIJKLMNO':
                    raise ValueError(f'Bad legacy calibration label: {label}')
                row, col = ord(label[0]) - 65, int(label[1:]) - 1
                if not (0 <= col < SIZE):
                    raise ValueError(f'Bad calibration column: {label}')
                if np.isfinite(points[row, col]).all():
                    raise ValueError(f'Duplicate calibration label: {label}')
                points[row, col] = float(entry['x']), float(entry['y'])
        if not np.isfinite(points).all():
            raise ValueError('Calibration must contain every one of 225 cells')
        return cls(points)

    @staticmethod
    def create_from_corners(tl, tr, bl, br) -> 'Calibration':
        """Bilinear calibration, not automatic board/corner recognition."""
        pts = np.empty((SIZE, SIZE, 2), dtype=np.float64)
        tl, tr, bl, br = map(lambda x: np.asarray(x, dtype=np.float64), (tl, tr, bl, br))
        for r in range(SIZE):
            for c in range(SIZE):
                u, v = c / (SIZE - 1), r / (SIZE - 1)
                pts[r, c] = (1-u)*(1-v)*tl + u*(1-v)*tr + (1-u)*v*bl + u*v*br
        return Calibration(pts)

    def write_legacy_csv(self, path: str | Path) -> None:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Label', 'x', 'y'])
            for c in range(SIZE):
                for r in range(SIZE):
                    writer.writerow([f'{chr(65+r)}{c+1}', f'{self.points[r,c,0]:.6f}', f'{self.points[r,c,1]:.6f}'])


class Detector:
    def __init__(self, calibration: Calibration, black_template: str, white_template: str,
                 *, scale: float = .2, black_threshold: float = .65,
                 white_threshold: float = .8, confirmations: int = 2,
                 roi_mode: str = "separated"):
        if not 0 < scale <= 1 or confirmations < 1:
            raise ValueError('Scale must be in (0,1]; confirmations >= 1')
        if roi_mode not in ("shared", "separated"):
            raise ValueError("roi_mode must be shared or separated")
        self.roi_mode = roi_mode
        self.calibration = calibration
        self.scale = scale
        self.thresholds = (black_threshold, white_threshold)
        self.confirmations = confirmations
        self.templates = []
        for file in (black_template, white_template):
            template = cv2.imread(str(file), cv2.IMREAD_GRAYSCALE)
            if template is None:
                raise FileNotFoundError(f'Cannot load template: {file}')
            if scale < 1:
                template = cv2.resize(template, None, fx=scale, fy=scale,
                                      interpolation=cv2.INTER_AREA)
            if min(template.shape) < 3 or float(template.std()) < .1:
                raise ValueError(f'Non-textured or too-small template: {file}')
            self.templates.append(template)
        self.counts = np.zeros((SIZE, SIZE, 2), dtype=np.int32)
        self.diagnostics = {'scanned_cells': 0, 'match_attempts': 0, 'full_scans': 0, 'local_scans': 0}

    def detect(self, frame: np.ndarray, board, *, full_scan: bool, local_radius: int = 6):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = (cv2.resize(gray, None, fx=self.scale, fy=self.scale, interpolation=cv2.INTER_AREA)
                 if self.scale < 1 else gray)
        if full_scan or not board.moves:
            locations = [(r, c) for r in range(SIZE) for c in range(SIZE)]
            self.diagnostics['full_scans'] += 1
        else:
            # Include neighborhoods of last black and last white moves, not only a guessed next move.
            recent = []
            for color in (1, 2):
                last = next((m for m in reversed(board.moves) if m.color == color), None)
                if last:
                    recent.append((last.row, last.col))
            if not recent:
                recent = [(7, 7)]
            locations = [(r, c) for r in range(SIZE) for c in range(SIZE)
                         if any(abs(r - rr) <= local_radius and abs(c - cc) <= local_radius
                                for rr, cc in recent)]
            self.diagnostics['local_scans'] += 1
        found = []
        for r, c in locations:
            if board.cells[r][c]:
                continue
            self.diagnostics['scanned_cells'] += 1
            x, y = np.rint(self.calibration.points[r, c] * self.scale).astype(int)
            if not (0 <= x < small.shape[1] and 0 <= y < small.shape[0]):
                self.counts[r, c] = 0
                continue
            # A circular stone must differ from its surrounding wooden board.
            # This reduces false matches at the crossed black grid lines.
            max_size = max(max(t.shape) for t in self.templates)
            radius = max(4, int(round(max_size * .7)))
            yy1, yy2 = max(0, y-radius), min(small.shape[0], y+radius+1)
            xx1, xx2 = max(0, x-radius), min(small.shape[1], x+radius+1)
            center = small[max(0,y-1):min(small.shape[0],y+2),
                           max(0,x-1):min(small.shape[1],x+2)]
            if not center.size:
                continue
            center_mean = float(center.mean())
            patch_back = small[yy1:yy2, xx1:xx2]
            background = float(np.median(patch_back))
            # Relative contrast works on wooden boards, while the absolute
            # fallback rescues dark pieces covering most of the local patch.
            # Absolute values are lighting-sensitive; see README limitations.
            black_allowed = center_mean < background - 20 or center_mean < 80
            white_allowed = center_mean > background + 20 or center_mean > 205
            if not (black_allowed or white_allowed):
                self.counts[r, c] = 0
                continue
            scores = [-1., -1.]
            for idx, templ in enumerate(self.templates):
                # separated: each color needs its own contrast gate.
                # shared: a common contrast-positive ROI is matched by both templates.
                if self.roi_mode == "separated":
                    if idx == 0 and not black_allowed:
                        continue
                    if idx == 1 and not white_allowed:
                        continue
                th, tw = templ.shape
                padding = max(th, tw)
                x1, y1 = max(0, x-padding), max(0, y-padding)
                x2, y2 = min(small.shape[1], x+padding+1), min(small.shape[0], y+padding+1)
                roi = small[y1:y2, x1:x2]
                if roi.shape[0] < th or roi.shape[1] < tw:
                    continue
                self.diagnostics['match_attempts'] += 1
                response = cv2.matchTemplate(roi, templ, cv2.TM_CCOEFF_NORMED)
                _, max_score, _, (mx, my) = cv2.minMaxLoc(response)
                cx, cy = x1 + mx + tw/2, y1 + my + th/2
                # A nearby stone must not be allocated to the empty intersection.
                # 0.4 cell spacing is a conservative upper bound on correction.
                dcol = _min_neighbor_spacing(self.calibration.points, r, c, 'col') * self.scale
                drow = _min_neighbor_spacing(self.calibration.points, r, c, 'row') * self.scale
                max_dx, max_dy = max(2, dcol*.4), max(2, drow*.4)
                if abs(cx-x) <= max_dx and abs(cy-y) <= max_dy:
                    scores[idx] = max_score
            candidates = [i for i in range(2) if scores[i] >= self.thresholds[i]]
            chosen = max(candidates, key=lambda i: scores[i] - self.thresholds[i]) if candidates else None
            for i in range(2):
                self.counts[r, c, i] = self.counts[r, c, i]+1 if chosen == i else 0
            if chosen is not None and self.counts[r, c, chosen] >= self.confirmations:
                found.append((r, c, chosen+1))
                self.counts[r, c] = 0
        return found


def _min_neighbor_spacing(points: np.ndarray, r: int, c: int, axis: str) -> float:
    current = points[r, c]
    neighbors = []
    if axis == 'col':
        for cc in (c-1,c+1):
            if 0 <= cc < SIZE:
                neighbors.append(abs(float(points[r,cc,0] - current[0])))
    else:
        for rr in (r-1,r+1):
            if 0 <= rr < SIZE:
                neighbors.append(abs(float(points[rr,c,1] - current[1])))
    return max(1, min(neighbors) if neighbors else 10.)
