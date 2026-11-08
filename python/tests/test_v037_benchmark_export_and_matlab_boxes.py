"""V0.3.7 contract tests; MATLAB native execution remains Windows-dependent."""
from pathlib import Path
from unittest.mock import patch
import importlib.util
import csv
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]

def load_runner():
    loc=ROOT/'python/tools/run_full_benchmark.py'
    spec=importlib.util.spec_from_file_location('gomoku_full_benchmark',loc)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def test_matlab_missing_has_four_explicit_skips_and_writes_csv(tmp_path):
    b=load_runner()
    args=b.parse(['--input',str(ROOT/'demo/demo.mp4'),
        '--calibration',str(ROOT/'demo/checkerboard_points.csv'),
        '--black-template',str(ROOT/'demo/black.png'),
        '--white-template',str(ROOT/'demo/white.png'),
        '--output-dir',str(tmp_path),'--engines','matlab'])
    with patch.object(b.shutil,'which',return_value=None), patch.object(b.os.environ,'get',return_value=None):
        ret=b.run(args)
    assert ret==1
    with open(tmp_path/'benchmark-results.csv',encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==4
    assert all(r['status']=='SKIP' and 'MATLAB' in r['error'] for r in rows)
    assert (tmp_path/'benchmark-summary.csv').exists()
    assert (tmp_path/'status.json').exists()

def test_wpf_button_and_three_pixel_matlab_boxes():
    wpf=ROOT/'csharp/GomokuVision.Desktop'
    tree=ET.parse(wpf/'MainWindow.xaml')
    btns=[n for n in tree.iter() if n.attrib.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name')=='AllResultsButton']
    assert len(btns)==1 and btns[0].get('Click')=='AllResults_Click'
    src=(wpf/'MainWindow.xaml.cs').read_text('utf-8')
    assert 'private async void AllResults_Click' in src
    assert '"--status-file",progress' in src
    assert '"--cancel-file",_benchmarkCancelFlag' in src
    m=(ROOT/'matlab/modern/gomoku_batch.m').read_text('utf-8')
    assert 'uint8([35,255,45]),3' in m
    assert 'out(y1:y1+th-1,x1:x2,ch)' in m
