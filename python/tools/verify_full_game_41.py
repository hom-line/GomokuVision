"""Compare a native engine's complete synthetic 961-frame run to its independent oracle.

Only colors/positions/winner are treated as exact recognition targets. Detected
confirmation frame may lag visible source event by one sampled interval.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('results',type=Path)
    a=ap.parse_args()
    oracle=rows(ROOT/'results/full_game_demo/moves.csv')
    got=rows(a.results/'moves.csv')
    report=json.loads((a.results/'summary.json').read_text(encoding='utf-8-sig'))
    if len(got)!=41 or len(oracle)!=41:
        raise AssertionError(f'FULL_GAME_41_FAIL: expected 41 moves, got {len(got)}')
    for i,(expected,observed) in enumerate(zip(oracle,got),1):
        if (expected['Color'],expected['Position']) != (observed['Color'],observed['Position']):
            raise AssertionError(f'FULL_GAME_41_FAIL: move {i}: {observed} != {expected}')
    if report.get('winner')!='Black' or report.get('moves')!=41:
        raise AssertionError('FULL_GAME_41_FAIL: winner/move count mismatch')
    if report.get('frames_read')!=961:
        raise AssertionError(f'FULL_GAME_41_FAIL: source was not fully read ({report.get("frames_read")})')
    if report.get('frames_analyzed')!=161:
        raise AssertionError(f'FULL_GAME_41_FAIL: expected 161 samples ({report.get("frames_analyzed")})')
    if not (a.results/'last_frame.png').is_file():
        raise AssertionError('FULL_GAME_41_FAIL: missing terminal preview')
    print(f'FULL_GAME_41_PASS: {report.get("engine")} 41/41 moves, Black winner, 961 read / 161 sampled')

if __name__=='__main__': main()
