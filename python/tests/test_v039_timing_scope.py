"""Timing scope regression tests: exact native MATLAB/C# outcomes still require Windows."""
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parents[2]


def test_all_three_engines_expose_detection_only_clock():
    py=(ROOT/'python/gomoku/app.py').read_text('utf-8')
    cs=(ROOT/'csharp/GomokuVision/Program.cs').read_text('utf-8')
    matlab=(ROOT/'matlab/modern/gomoku_batch.m').read_text('utf-8')
    assert 'recognition_seconds += perf_counter() - recognition_t0' in py
    assert "'recognition_seconds':round(recognition_seconds,4)" in py
    assert 'recognitionSeconds += recognitionClock.Elapsed.TotalSeconds' in cs
    assert '["recognition_seconds"]=Math.Round(recognitionSeconds,4)' in cs
    assert 'recognitionSeconds=recognitionSeconds+toc(recognitionClock)' in matlab
    assert "'recognition_seconds',round(recognitionSeconds,4)" in matlab


def test_benchmark_fields_and_no_retroactive_invention(tmp_path):
    import importlib.util
    spec=importlib.util.spec_from_file_location('v039_benchmark', ROOT/'python/tools/run_full_benchmark.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert {'recognition_seconds','engine_wall_seconds','elapsed_wall_seconds',
            'external_overhead_seconds','pipeline_other_seconds'}.issubset(set(module.COLUMNS))
    historical=(ROOT/'docs/benchmarks/windows_36_case_results_2026-11-08.csv')
    with historical.open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==36
    assert 'recognition_seconds' not in rows[0]
    assert 'TIMING_METHODS.md' in (ROOT/'README.md').read_text('utf-8')


def test_python_benchmark_writes_core_pipeline_and_end_to_end(tmp_path):
    import importlib.util
    spec=importlib.util.spec_from_file_location('v039_live',ROOT/'python/tools/run_full_benchmark.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    d=ROOT/'demo'
    args=module.parse(['--input',str(d/'demo.mp4'), '--calibration',str(d/'checkerboard_points.csv'),
        '--black-template',str(d/'black.png'), '--white-template',str(d/'white.png'),
        '--output-dir',str(tmp_path), '--engines','python','--playback-speeds','1'])
    assert module.run(args)==0
    with (tmp_path/'benchmark-results.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==4 and all(r['status']=='PASS' for r in rows)
    for r in rows:
        core=float(r['recognition_seconds'])
        inside=float(r['engine_wall_seconds'])
        alltime=float(r['elapsed_wall_seconds'])
        assert 0 < core <= inside + .003
        assert inside <= alltime + .003
        assert abs(float(r['pipeline_other_seconds'])-(inside-core)) < .004
        assert abs(float(r['external_overhead_seconds'])-(alltime-inside)) < .004
    with (tmp_path/'benchmark-summary.csv').open(encoding='utf-8-sig',newline='') as f:
        summaries=list(csv.DictReader(f))
    assert len(summaries)==2
    assert all(float(s['mean_recognition_seconds'])>0 for s in summaries)
    meta=json.loads((tmp_path/'benchmark-meta.json').read_text('utf-8'))
    assert meta['timing_methodology']['recognition_seconds'].startswith('Sum of')
