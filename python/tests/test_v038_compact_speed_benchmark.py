"""V0.3.8 compact UI + selectable multi-speed benchmarks.

Native WPF runtime remains Windows-only; these tests validate source contracts and
exercise the runner on actual self-generated synthetic frames.
"""
from pathlib import Path
import csv
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/'python/tools/run_full_benchmark.py'


def load_runner():
    import importlib.util
    spec=importlib.util.spec_from_file_location('benchmark_v038',RUNNER)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def demo_args(out, *extra):
    demo=ROOT/'demo'
    return ['--input',str(demo/'demo.mp4'),
        '--calibration',str(demo/'checkerboard_points.csv'),
        '--black-template',str(demo/'black.png'),
        '--white-template',str(demo/'white.png'),
        '--output-dir',str(out),*extra]


def test_speed_parse_defaults_deduplicated_runtime(tmp_path):
    m=load_runner()
    args=m.parse(demo_args(tmp_path,'--engines','matlab',
        '--playback-speeds','1','4','1','2'))
    assert args.playback_speeds==[1,4,1,2]
    with patch.object(m.shutil,'which',return_value=None),patch.object(m.os.environ,'get',return_value=None):
        rc=m.run(args)
    assert rc==1  # No MATLAB installed is SKIP, never mislabeled PASS.
    with (tmp_path/'benchmark-results.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==12  # 3 unique speeds x 2 ROI x 2 displays
    assert {r['playback_speed'] for r in rows}=={'1','2','4'}
    assert all(r['status']=='SKIP' for r in rows)
    assert all(r['playback_model_verified']=='PASS' for r in rows)
    assert len({r['result_dir'] for r in rows})==12
    assert all(float(r['expected_playback_seconds'])>0 for r in rows)
    meta=json.loads((tmp_path/'benchmark-meta.json').read_text('utf-8'))
    assert meta['selected_playback_speeds']==[1,4,2]
    assert meta['cases']==12
    assert meta['playback_speed_affects_compute_time'] is False
    with (tmp_path/'benchmark-summary.csv').open(encoding='utf-8-sig',newline='') as f:
        summary=list(csv.DictReader(f))
    assert len(summary)==6 # three speeds × one engine × two ROIs
    assert all(int(r['cases_expected'])==2 for r in summary)


def test_one_or_two_speeds_correct_video_case_count(tmp_path):
    m=load_runner()
    args=m.parse(demo_args(tmp_path, '--engines','python','--playback-speeds','1','4'))
    assert m.run(args)==0
    with (tmp_path/'benchmark-results.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==8
    assert all(r['status']=='PASS' and int(r['moves'])==9 and r['winner']=='Black' for r in rows)
    assert all(r['oracle_verified']=='NOT_APPLICABLE' for r in rows) # short demo, not 41-move oracle
    assert all(r['playback_model_verified']=='PASS' for r in rows)
    assert {r['playback_speed'] for r in rows}=={'1','4'}
    first=float(next(r['expected_playback_seconds'] for r in rows if r['playback_speed']=='1'))
    fourth=float(next(r['expected_playback_seconds'] for r in rows if r['playback_speed']=='4'))
    assert abs(first/4-fourth)<.005


def test_ui_is_compact_with_multiple_checkbox_selection():
    wpf=ROOT/'csharp/GomokuVision.Desktop'
    tree=ET.parse(wpf/'MainWindow.xaml')
    nodes={}
    ns='{http://schemas.microsoft.com/winfx/2006/xaml}'
    for item in tree.iter():
        name=item.attrib.get(ns+'Name')
        if name:
            assert name not in nodes, 'duplicate XAML name: '+name
            nodes[name]=item
    assert nodes['AdvancedExpander'].attrib['IsExpanded']=='False'
    assert nodes['BenchmarkExpander'].attrib['IsExpanded']=='True'
    for speed in (1,2,4):
        node=nodes[f'BenchmarkSpeed{speed}']
        assert node.attrib['Content']==f'{speed}×'
    assert nodes['AllResultsButton'].attrib['Click']=='AllResults_Click'
    for name in ('CalibrationPath','BlackPath','WhitePath','OutputPath','QuickGateButton',
                 'EveryValue','ConfirmValue','FullValue'):
        assert name in nodes
    code=(wpf/'MainWindow.xaml.cs').read_text('utf-8')
    assert 'if (selectedSpeeds.Count==0)' in code
    assert 'expectedCases=12*selectedSpeeds.Count' in code
    assert 'psi.ArgumentList.Add("--playback-speeds")' in code
    assert 'BenchmarkSpeed4.IsChecked==true' in code


def test_runner_invalid_speed_rejected(tmp_path):
    m=load_runner()
    import pytest
    with pytest.raises(SystemExit):
        m.parse(demo_args(tmp_path,'--playback-speeds','3'))
