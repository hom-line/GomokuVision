"""Run native 3-engine / 2-ROI / 2-overlay benchmarks for selected playback speeds.

Creates unique output paths and CSV even when MATLAB is missing or any test fails.
Each selected speed runs 12 independent analyses. Playback speed is a labeled playback
contract, NOT an engine compute accelerator; it never changes source FPS or detection args.
"""
import argparse,csv,hashlib,json,os,shutil,subprocess,sys,time,traceback
from datetime import datetime, timezone
from pathlib import Path
import cv2

ROOT=Path(__file__).resolve().parents[2]
ENGINES=('csharp','python','matlab')
ROIS=('separated','shared')
VIEWS=('recognition','recognition_prediction')
COLUMNS=['case','engine','roi_mode','overlay_mode','status','exit_code','elapsed_wall_seconds',
         'engine_wall_seconds','recognition_seconds','external_overhead_seconds','pipeline_other_seconds','playback_speed','expected_playback_seconds','playback_model_verified','frames_read','frames_analyzed','moves','black_moves','white_moves',
         'winner','match_attempts','input_sha256','oracle_verified','error','result_dir','log_file']

def atomic_json(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(tmp,p)

def write_csv(path,fields,records):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(records)

def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()

def expected_oracle_matches(moves_csv,expected_csv,report):
    with open(moves_csv,encoding='utf-8-sig',newline='') as f: got=list(csv.DictReader(f))
    with open(expected_csv,encoding='utf-8-sig',newline='') as f: truth=list(csv.DictReader(f))
    return (len(got)==len(truth)==41 and
            all((a['Color'],a['Position'])==(b['Color'],b['Position']) for a,b in zip(got,truth)) and
            report.get('winner')=='Black' and report.get('frames_read')==961)

def parse(argv=None):
    p=argparse.ArgumentParser()
    for name in ['input','calibration','black-template','white-template','output-dir','status-file','cancel-file']:
        p.add_argument('--'+name,required=name not in ('status-file','cancel-file'),type=Path)
    for name,default in [('sample-every',6),('full-scan-every',4),('confirmations',2)]:
        p.add_argument('--'+name,type=int,default=default)
    for name,default in [('scale',.5),('black-threshold',.65),('white-threshold',.75)]:
        p.add_argument('--'+name,type=float,default=default)
    p.add_argument('--engines',nargs='+',choices=ENGINES,default=list(ENGINES))
    p.add_argument('--playback-speeds',nargs='+',type=int,choices=(1,2,4),default=[1],
                   help='Replay speeds to include. Each speed repeats the 3x2x2 compute matrix; playback speed is NOT passed to detectors.')
    p.add_argument('--max-seconds-per-case',type=int,default=900)
    return p.parse_args(argv)

def run(args):
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    video=args.input.resolve()
    for p in (video,args.calibration,args.black_template,args.white_template):
        if not p.is_file(): raise FileNotFoundError(p)
    started=datetime.now(timezone.utc).isoformat()
    hash_value=digest(video)
    demo=(ROOT/'demo/full_game/full_game_961.mp4')
    synthetic_oracle=(ROOT/'results/full_game_demo/moves.csv')
    demo_hash=digest(demo) if demo.exists() else None
    oracle=hash_value==demo_hash and synthetic_oracle.exists() and args.sample_every==6 and args.confirmations==2
    speeds=list(dict.fromkeys(args.playback_speeds))
    cases=[(speed,e,r,v) for speed in speeds for e in args.engines for r in ROIS for v in VIEWS]
    # Read metadata only; the source video is not transcoded or rewritten.
    capture=cv2.VideoCapture(str(video))
    fps=float(capture.get(cv2.CAP_PROP_FPS)) if capture.isOpened() else 0.0
    frame_count=int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) if capture.isOpened() else 0
    capture.release()
    if not (fps>0 and frame_count>0): raise RuntimeError('Could not read source FPS/frame count')
    records=[];status_file=args.status_file or out/'status.json'
    def status(current=''):
        atomic_json(status_file,{'started_utc':started,'completed':len(records),'total':len(cases),
           'current':current,'selected_playback_speeds':speeds,'finished':len(records)==len(cases),
           'pass':sum(r['status']=='PASS' for r in records),'failed':sum(r['status']=='FAIL' for r in records),
           'skipped':sum(r['status'] in ('SKIP','CANCELLED') for r in records)})
    def export():
        write_csv(out/'benchmark-results.csv',COLUMNS,records)
        groups=[]
        for speed in speeds:
            for engine in args.engines:
                for roi in ROIS:
                    relevant=[r for r in records if r['engine']==engine and r['roi_mode']==roi
                              and r['playback_speed']==speed]
                    passed=[r for r in relevant if r['status']=='PASS']
                    times=[float(r['elapsed_wall_seconds']) for r in passed]
                    internals=[float(r['engine_wall_seconds']) for r in passed if r['engine_wall_seconds']!='']
                    cores=[float(r['recognition_seconds']) for r in passed if r['recognition_seconds']!='']
                    overheads=[float(r['external_overhead_seconds']) for r in passed if r['external_overhead_seconds']!='']
                    groups.append({'playback_speed':speed,'engine':engine,'roi_mode':roi,
                        'cases_expected':len(VIEWS),'cases_completed':len(relevant),
                        'pass':len(passed),'fail':sum(r['status']=='FAIL' for r in relevant),
                        'skipped':sum(r['status']!='PASS' and r['status']!='FAIL' for r in relevant),
                        'mean_recognition_seconds':round(sum(cores)/len(cores),4) if cores else '',
                        'mean_engine_wall_seconds':round(sum(internals)/len(internals),4) if internals else '',
                        'mean_elapsed_seconds':round(sum(times)/len(times),3) if times else '',
                        'mean_external_overhead_seconds':round(sum(overheads)/len(overheads),4) if overheads else '',
                        'min_elapsed_seconds':round(min(times),3) if times else '',
                        'max_elapsed_seconds':round(max(times),3) if times else '',
                        'note':'Recognition=time within detector+move updates; engine=time inside application incl video I/O/overlays; elapsed=launcher wall clock incl startup. Speed is playback metadata.'})
        write_csv(out/'benchmark-summary.csv',list(groups[0].keys()),groups)
    status('preparing')
    # Pre-build C# CLI exactly once; its restore/build time is excluded from per-case measurements.
    dotnet=shutil.which('dotnet');dll=ROOT/'csharp/GomokuVision/bin/Release/net10.0/GomokuVision.dll'
    build_err=None
    if 'csharp' in args.engines:
        if not dotnet:build_err='dotnet SDK not found'
        else:
            b=subprocess.run([dotnet,'build',str(ROOT/'csharp/GomokuVision/GomokuVision.csproj'),'-c','Release','--nologo'],
              cwd=str(ROOT),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,errors='replace',timeout=240)
            (out/'csharp-build.log').write_text(b.stdout or '',encoding='utf-8')
            if b.returncode!=0 or not dll.is_file():build_err='C# build failed; see csharp-build.log'
    matlab=os.environ.get('GOMOKUVISION_MATLAB_EXE') or shutil.which('matlab')
    if matlab and not Path(matlab).exists() and not shutil.which(matlab):matlab=None
    all_errors=0
    for i,(speed,engine,roi,view) in enumerate(cases,1):
        name=f'{engine}-{roi}-{view}-x{speed}'
        status(name)
        run_dir=out/f'x{speed}'/name;run_dir.mkdir(parents=True,exist_ok=True)
        log=run_dir/'console.log'
        record={'case':i,'engine':engine,'roi_mode':roi,'overlay_mode':view,'status':'SKIP',
                'exit_code':'','elapsed_wall_seconds':'','engine_wall_seconds':'',
                'recognition_seconds':'','external_overhead_seconds':'','pipeline_other_seconds':'',
                'playback_speed':speed,'expected_playback_seconds':round(frame_count/fps/speed,3),
                'playback_model_verified': 'PASS' if int(min(frame_count-1,(frame_count/fps/speed)*fps*speed))==frame_count-1 else 'FAIL',
                'frames_read':'','frames_analyzed':'','moves':'','black_moves':'',
                'white_moves':'','winner':'','match_attempts':'','input_sha256':hash_value,
                'oracle_verified':'NOT_APPLICABLE','error':'','result_dir':str(run_dir),
                'log_file':str(log)}
        if args.cancel_file and args.cancel_file.exists():
            record['status']='CANCELLED';record['error']='User canceled before case began'
        elif engine=='matlab' and not matlab:
            record['error']='MATLAB missing; set GOMOKUVISION_MATLAB_EXE'
        elif engine=='csharp' and build_err:
            record['status']='FAIL';record['error']=build_err
        else:
            cmd=[]
            if engine=='matlab':
                conf=run_dir/'matlab-run-config.json'
                conf.write_text(json.dumps({'input':str(video),'calibration':str(args.calibration.resolve()),
                    'black_template':str(args.black_template.resolve()),'white_template':str(args.white_template.resolve()),
                    'output_dir':str(run_dir),'sample_every':args.sample_every,
                    'full_scan_every':args.full_scan_every,'confirmations':args.confirmations,
                    'scale':args.scale,'black_threshold':args.black_threshold,'white_threshold':args.white_threshold,
                    'roi_mode':roi,'overlay_mode':view},ensure_ascii=False),encoding='utf-8')
                escape=lambda s:s.replace("'","''")
                expr=f"addpath('{escape(str(ROOT/'matlab/modern'))}'); gomoku_batch('{escape(str(conf))}')"
                cmd=[str(matlab),'-batch',expr]
            else:
                cmd=([sys.executable,'-m','gomoku'] if engine=='python' else [dotnet,str(dll)])
                cmd+=['--input',str(video),'--calibration',str(args.calibration.resolve()),
                    '--black-template',str(args.black_template.resolve()),'--white-template',str(args.white_template.resolve()),
                    '--output-dir',str(run_dir),'--sample-every',str(args.sample_every),
                    '--full-scan-every',str(args.full_scan_every),'--confirmations',str(args.confirmations),
                    '--scale',str(args.scale),'--black-threshold',str(args.black_threshold),
                    '--white-threshold',str(args.white_threshold),'--roi-mode',roi,'--overlay-mode',view]
            env=os.environ.copy()
            if engine=='python':env['PYTHONPATH']=str(ROOT/'python')+os.pathsep+env.get('PYTHONPATH','')
            t0=time.perf_counter()
            try:
                with log.open('w',encoding='utf-8',errors='replace') as f:
                    cp=subprocess.run(cmd,cwd=str(ROOT),env=env,stdout=f,stderr=subprocess.STDOUT,
                                      timeout=args.max_seconds_per_case,check=False)
                record['elapsed_wall_seconds']=round(time.perf_counter()-t0,3)
                record['exit_code']=cp.returncode
                summary_path=run_dir/'summary.json'
                if cp.returncode!=0:
                    record['status']='FAIL';record['error']='Exit '+str(cp.returncode)+'; see console.log'
                elif not summary_path.is_file() or not (run_dir/'moves.csv').exists():
                    record['status']='FAIL';record['error']='Missing summary.json or moves.csv'
                else:
                    summary=json.loads(summary_path.read_text(encoding='utf-8-sig'))
                    for key in ('frames_read','frames_analyzed','moves','black_moves','white_moves','winner','match_attempts'):
                        record[key]=summary.get(key,'')
                    record['engine_wall_seconds']=summary.get('wall_seconds','')
                    record['recognition_seconds']=summary.get('recognition_seconds','')
                    # Three DIFFERENT clocks: pure detection, in-process pipeline, and launcher wall time.
                    # Never present MATLAB's -batch startup as detector execution.
                    try:
                        inside=float(record['engine_wall_seconds'])
                        record['external_overhead_seconds']=round(max(0.0,float(record['elapsed_wall_seconds'])-inside),4)
                        if record['recognition_seconds'] != '':
                            record['pipeline_other_seconds']=round(max(0.0,inside-float(record['recognition_seconds'])),4)
                    except (ValueError,TypeError):
                        pass
                    record['status']='PASS'
                    if oracle:
                        verified=expected_oracle_matches(run_dir/'moves.csv',synthetic_oracle,summary)
                        record['oracle_verified']='PASS' if verified else 'FAIL'
                        if not verified:
                            record['status']='FAIL';record['error']='Synthetic 41-move oracle mismatch'
            except subprocess.TimeoutExpired:
                record['status']='FAIL';record['error']='Timed out after '+str(args.max_seconds_per_case)+' seconds'
                record['elapsed_wall_seconds']=round(time.perf_counter()-t0,3)
            except Exception as ex:
                record['status']='FAIL';record['error']=repr(ex)
                record['elapsed_wall_seconds']=round(time.perf_counter()-t0,3)
        records.append(record)
        export();status(name)
        print(f"[{i}/{len(cases)}] {name}: {record['status']} {record['elapsed_wall_seconds']}s {record['error']}",flush=True)
        if record['status']=='FAIL': all_errors+=1
    status('complete')
    (out/'benchmark-meta.json').write_text(json.dumps({'input':str(video),'input_sha256':hash_value,
        'generated_utc':datetime.now(timezone.utc).isoformat(), 'synthetic_oracle_applicable':oracle,
        'playback_speed_affects_compute_time':False,'selected_playback_speeds':speeds,
        'timing_methodology':{'recognition_seconds':'Sum of each detect/confirm call and move placement; excludes video decode, rendering, encoding, app startup',
                              'engine_wall_seconds':'Engine-owned in-process timer around video processing; includes I/O and overlay',
                              'elapsed_wall_seconds':'External benchmark wall clock for each child process, includes interpreter / MATLAB startup',
                              'external_overhead_seconds':'elapsed_wall_seconds minus engine_wall_seconds; includes process startup, initialization, shutdown and final output, not startup alone',
                              'playback_speed':'Replay label only, not a computational speed setting'},
        'source_fps':fps,'source_frames':frame_count,
        'playback_validation':'Mathematical replay endpoint model only; NOT a WPF GUI playback runtime test',
        'cases':len(cases),
        'pass':sum(r['status']=='PASS' for r in records),
        'note':'Each selected playback speed repeats the 12 independent computational cases. Speed is metadata, NOT an engine acceleration setting; real GUI playback needs separate manual acceptance. Synthetic oracle is not real-world accuracy.'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('BENCHMARK_RESULTS_CSV:',out/'benchmark-results.csv',flush=True)
    print('BENCHMARK_SUMMARY_CSV:',out/'benchmark-summary.csv',flush=True)
    return 0 if len(records)==len(cases) and all(r['status']=='PASS' for r in records) else 1

if __name__=='__main__':
    a=parse()
    try:sys.exit(run(a))
    except Exception:
        traceback.print_exc();sys.exit(2)
