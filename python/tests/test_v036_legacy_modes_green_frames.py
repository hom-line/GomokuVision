"""Validate two real ROI strategies, legacy presentation modes and green boxes.

C# / MATLAB GUI logic has source-contract checks until Windows+MATLAB gates run.
"""
from pathlib import Path
import json
import cv2
import numpy as np
from gomoku.app import parse_args, draw_overlay, run
from gomoku.core import Board
from gomoku.vision import Calibration, Detector

ROOT=Path(__file__).resolve().parents[2]


def test_green_confirmed_boxes_and_prediction_modes():
    cal=Calibration.from_legacy_csv(ROOT/'demo/checkerboard_points.csv')
    board=Board()
    board.place(25,1,7,7)
    frame=np.full((720,720,3),155,dtype=np.uint8)
    plain=draw_overlay(frame,board,cal,frame_number=25,overlay_mode='recognition')
    predicted=draw_overlay(frame,board,cal,frame_number=25,overlay_mode='recognition_prediction')
    x,y=np.rint(cal.points[7,7]).astype(int)
    # A green confirmed rectangle is shown in BOTH modes (BGR pixel order).
    assert 225 <= plain[y-21,x-21,1] <= 255
    assert 225 <= predicted[y-21,x-21,1] <= 255
    # Predictive circles add pixels; basic recognition stays uncluttered.
    assert np.count_nonzero(np.any(plain!=predicted,axis=2)) > 10
    # Neither display path changes the underlying one-move board.
    assert len(board.moves)==1


def test_separate_and_shared_roi_produce_grounded_full_demo_moves(tmp_path):
    demo=ROOT/'demo'
    outcomes={}
    for mode in ('separated','shared'):
        args=parse_args([
            '--input',str(demo/'demo.mp4'),
            '--calibration',str(demo/'checkerboard_points.csv'),
            '--black-template',str(demo/'black.png'),
            '--white-template',str(demo/'white.png'),
            '--output-dir',str(tmp_path/mode),
            '--roi-mode',mode,'--overlay-mode','recognition',
        ])
        metrics=run(args)
        assert metrics['roi_mode']==mode
        assert metrics['overlay_mode']=='recognition'
        assert metrics['winner']=='Black'
        assert metrics['moves']==9
        outcomes[mode]=(tmp_path/mode/'moves.csv').read_text('utf-8')
        assert (tmp_path/mode/'last_frame.png').is_file()
    assert outcomes['shared']==outcomes['separated']


def test_cross_engine_mode_settings_are_wired_not_cosmetic():
    root=ROOT
    wpf=(root/'csharp/GomokuVision.Desktop/MainWindow.xaml.cs').read_text('utf-8')
    xaml=(root/'csharp/GomokuVision.Desktop/MainWindow.xaml').read_text('utf-8')
    core=(root/'csharp/GomokuVision/VisionDetector.cs').read_text('utf-8')
    cli=(root/'csharp/GomokuVision/Program.cs').read_text('utf-8')
    matlab=(root/'matlab/modern/gomoku_batch.m').read_text('utf-8')
    renderer=(root/'csharp/GomokuVision.Desktop/RecognitionOverlayRenderer.cs').read_text('utf-8')
    assert 'RoiModeBox' in xaml and 'DisplayModeBox' in xaml
    assert '"--roi-mode",opts.RoiMode' in wpf
    assert '"--overlay-mode",opts.OverlayMode' in wpf
    assert '["roi_mode"]=opts.RoiMode' in wpf
    assert 'RecognitionOverlayRenderer.Draw' in wpf
    assert 'opts.RoiMode' in cli and '_roiMode=="separated"' in core
    assert "strcmp(opts.roi_mode,'separated')" in matlab
    assert 'paintRecognition(frame,board,pts,opts.overlay_mode)' in matlab
    assert 'Stroke' not in renderer or 'confirmedPen' in renderer
    assert 'TimelineFrame<=frame+1' in wpf
    assert 'UpdatePredictionPanel()' in wpf
    assert '對局結束 · 不再預測' in wpf
