"""Generate a 15x15 legacy compatible calibration from four MANUALLY chosen points.

This is a bilinear interpolation utility, not automatic corner detection.
"""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gomoku.vision import Calibration


def pair(s: str):
    try:
        x,y=map(float,s.split(','))
    except ValueError as e:
        raise argparse.ArgumentTypeError('Expected X,Y e.g. 75,80') from e
    return x,y


def main():
    p=argparse.ArgumentParser(description='Generate legacy checkerboard_points.csv from manually selected four corners.')
    for a in ('top-left','top-right','bottom-left','bottom-right'):
        p.add_argument('--'+a,type=pair,required=True)
    p.add_argument('--output',type=Path,default=Path('checkerboard_points.csv'))
    a=p.parse_args()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    Calibration.create_from_corners(a.top_left,a.top_right,a.bottom_left,a.bottom_right).write_legacy_csv(a.output)
    print(f'Wrote 225 board intersections: {a.output}')

if __name__=='__main__':main()
