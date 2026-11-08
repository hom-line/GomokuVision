"""Synthesize descriptive benchmark metadata from short synthetic test results only.

Not an accuracy test and not a controlled cross-language hardware benchmark.
"""
import csv
import json
from pathlib import Path
import sys


def report(py_dir: Path, cs_dir: Path, target: Path):
    rows=[]
    for label, folder in [('python-opencv', py_dir), ('csharp-opencvsharp', cs_dir)]:
        summary=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
        rows.append({'engine':label,
            'wall_seconds':round(float(summary['wall_seconds']),4),
            'frames_analyzed':int(summary['frames_analyzed']),
            'moves':int(summary['moves']),
            'winner':summary['winner']})
    if any(x['moves']!=9 or x['winner']!='Black' for x in rows):
        raise ValueError('Synthetic expected results are not met; no benchmark report produced')
    payload={
        'scenario':'self-authored synthetic video, 9 moves',
        'scope':'Descriptive timing on the test machine; excludes independent ground-truth accuracy',
        'note':'Runtime includes implementation overhead, codec and filesystem differences; not an isolated algorithm speed comparison.',
        'historical_video_reprocessed':False,
        'engines':rows,
    }
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (target.parent/'engine-comparison.csv').open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    print('SYNTHETIC_PERFORMANCE_REPORT_PASS:',target)


if __name__=='__main__':
    report(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
