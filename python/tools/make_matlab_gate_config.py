"""Make JSON config for MATLAB native engine to test the *short* self-owned demo.
MATLAB is invoked separately: this script does not perform MATLAB recognition.
"""
import json,sys
from pathlib import Path
if len(sys.argv) not in (2,3,4):
    raise SystemExit('Usage: make_matlab_gate_config.py OUTPUT-DIR [shared|separated] [recognition|recognition_prediction]')
roi_mode = sys.argv[2] if len(sys.argv)>2 else 'separated'
overlay_mode = sys.argv[3] if len(sys.argv)>3 else 'recognition_prediction'
if roi_mode not in ('separated','shared') or overlay_mode not in ('recognition','recognition_prediction'):
    raise SystemExit('Unsupported mode')
root=Path(__file__).resolve().parents[2]
out=Path(sys.argv[1]).resolve()
out.mkdir(parents=True,exist_ok=True)
config={'input':str(root/'demo/demo.mp4'),
'calibration':str(root/'demo/checkerboard_points.csv'),
'black_template':str(root/'demo/black.png'),
'white_template':str(root/'demo/white.png'),
'output_dir':str(out),'sample_every':2,'full_scan_every':3,'confirmations':2,
'local_radius':6,'scale':.5,'black_threshold':.65,'white_threshold':.75,
'progress_file':str(out/'.wpf-progress.json'),'cancel_file':str(out/'.cancel-request'),
'roi_mode':roi_mode,'overlay_mode':overlay_mode}
p=out/'matlab-gate-config.json'
p.write_text(json.dumps(config,indent=2),encoding='utf-8')
print(p)
