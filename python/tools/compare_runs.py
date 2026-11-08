"""Compare two language ports by move sequence and result fields.

This is a parity check against a reference, NOT independently labeled accuracy.
"""
import argparse
import csv
import json
from pathlib import Path


def load(folder):
    with (folder/'moves.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    with (folder/'summary.json').open(encoding='utf-8-sig') as f:
        summary=json.load(f)
    return [(x['Color'],x['Position']) for x in rows],summary


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('first',type=Path)
    parser.add_argument('second',type=Path)
    args=parser.parse_args()
    a,ma=load(args.first)
    b,mb=load(args.second)
    if a==b and ma['winner']==mb['winner']:
        print(f'PARITY PASS: {len(a)} move positions and colors, winner={ma["winner"]}')
        print('Frame timestamps and execution times may differ across decoders/platforms.')
        return
    print(f'PARITY FAIL: first={len(a)} second={len(b)}; winners {ma["winner"]}/{mb["winner"]}')
    for i in range(max(len(a),len(b))):
        aa=a[i] if i<len(a) else '<missing>'
        bb=b[i] if i<len(b) else '<missing>'
        if aa!=bb:print(f'  move {i+1}: first={aa}, second={bb}')
    raise SystemExit(1)

if __name__=='__main__':main()
