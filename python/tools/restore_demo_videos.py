"""Restore losslessly compressed self-rendered video assets after Git clone.

The four .mp4.xz files preserve byte-for-byte the V0.3.9 reference videos.
No external footage or network access is used. Requires Python 3 stdlib only.

    python python/tools/restore_demo_videos.py
    python python/tools/restore_demo_videos.py --verify
"""
from __future__ import annotations
import argparse
import hashlib
import lzma
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VIDEO = ROOT / 'demo' / 'full_game'
EXPECTED = {
    'full_game_961.mp4': '0518c8f5e0627e396ca1e4d5a9e0ff687008f8c90efe0b9ac91875c29c594641',
    'full_game_synced_961_2x.mp4': 'dcaf2f52e04c7cf6958fc9f693a4dd6695787d4c1170076064206bf2f771c84b',
    'full_game_recognition_green_961_2x.mp4': '57e44acdae41fc28a2ae8e89b0e10249b87ac9fcfb662fcbef53c79374bb1e07',
    'full_game_recognition_prediction_green_961_2x.mp4': '533cb23731dd36d32ea6276ba9967315633c89ed8a4456e2c41ecdd34fa2ced0',
}


def hash_file(path: Path) -> str:
    hasher=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def restore(name: str) -> None:
    path=VIDEO/name
    sha=EXPECTED[name]
    if path.is_file():
        current=hash_file(path)
        if current != sha:
            raise RuntimeError(f'Existing video SHA mismatch (will not overwrite): {path} ({current})')
        print(f'VERIFIED: {name} (already present)')
        return
    packed=path.with_suffix(path.suffix+'.xz')
    if not packed.is_file():
        raise FileNotFoundError(f'Missing source video archive: {packed}')
    tmp=None
    try:
        with tempfile.NamedTemporaryFile(dir=str(VIDEO),suffix='.tmp',delete=False) as dst:
            tmp=Path(dst.name)
            with lzma.open(packed,'rb') as source:
                for block in iter(lambda:source.read(1024*1024),b''):
                    dst.write(block)
        actual=hash_file(tmp)
        if actual != sha:
            raise RuntimeError(f'Unpacked video SHA mismatch: {name} {actual} != {sha}')
        os.replace(tmp,path)
        print(f'RESTORED_AND_VERIFIED: {name} ({path.stat().st_size} bytes)')
    finally:
        if tmp and tmp.exists():tmp.unlink()

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',choices=sorted(EXPECTED),help='Restore only one video')
    parser.add_argument('--verify',action='store_true',help='Explicit verification (always enabled)')
    args=parser.parse_args()
    for name in ([args.only] if args.only else EXPECTED):restore(name)
