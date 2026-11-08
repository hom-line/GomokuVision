"""Recreate the fully SELF-RENDERED 41-move/961-frame demo from moves.csv.

No original footage, no third-party image source, and no model inference are used.
Note: video byte digests depend on codec versions. Regenerating the video may
produce a different SHA and require a fresh engine-result pairing in the WPF UI.

Run: PYTHONPATH=python python python/tools/make_full_game.py --output /tmp/new-demo
"""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
import cv2, numpy as np
from gomoku.app import draw_board
from gomoku.core import Board
from gomoku.vision import Calibration

ROOT=Path(__file__).resolve().parents[2]
FRAMES=961


def create(output:Path, source:Path, side_by_side=True, reuse_source=False) -> dict:
    output.mkdir(parents=True,exist_ok=True)
    with source.open(encoding='utf-8-sig',newline='') as f:
        moves=list(csv.DictReader(f))
    assert len(moves)==41
    final=Board()
    for m in moves:
        final.place(int(m['Frame']),1 if m['Color']=='Black' else 2,
                    int(m['Row'])-1,int(m['Col'])-1)
    assert final.winner()[0]==1
    cal=Calibration.create_from_corners((72,72),(648,72),(72,648),(648,648))
    cal.write_legacy_csv(output/'checkerboard_points.csv')
    canvas=np.full((720,720,3),(166,196,223),np.uint8)
    cv2.rectangle(canvas,(14,14),(705,705),(115,150,188),14)
    cv2.rectangle(canvas,(36,36),(683,683),(155,178,203),3)
    for k in range(15):
        x=int(round(cal.points[0,k,0])); y=int(round(cal.points[k,0,1]))
        cv2.line(canvas,(x,72),(x,648),(91,111,124),2,cv2.LINE_AA)
        cv2.line(canvas,(72,y),(648,y),(91,111,124),2,cv2.LINE_AA)
    for r,c in ((3,3),(3,11),(7,7),(11,3),(11,11)):
        cv2.circle(canvas,tuple(np.rint(cal.points[r,c]).astype(int)),4,(60,70,80),-1,cv2.LINE_AA)

    def stone(img,r,c,color):
        x,y=np.rint(cal.points[r,c]).astype(int)
        fill=(26,29,33) if color==1 else (242,241,238)
        cv2.circle(img,(x+1,y+2),15,(80,96,108),-1,cv2.LINE_AA)
        cv2.circle(img,(x,y),14,fill,-1,cv2.LINE_AA)
        cv2.circle(img,(x,y),14,(40,44,51),1,cv2.LINE_AA)
        cv2.circle(img,(x-4,y-4),3,(70,70,70) if color==1 else (255,255,255),-1,cv2.LINE_AA)

    for name,color in (('black.png',1),('white.png',2)):
        temp=canvas.copy();stone(temp,7,7,color)
        x,y=np.rint(cal.points[7,7]).astype(int)
        cv2.imwrite(str(output/name),temp[y-19:y+20,x-19:x+20])
    src=output/'full_game_961.mp4'
    if not reuse_source:
        writer=cv2.VideoWriter(str(src),cv2.VideoWriter_fourcc(*'mp4v'),30,(720,720))
        if not writer.isOpened(): raise RuntimeError('MP4 codec unavailable')
        current=canvas.copy(); step=0
        try:
            for frame in range(1,FRAMES+1):
                while step<len(moves) and int(moves[step]['Frame'])<=frame:
                    m=moves[step]
                    stone(current,int(m['Row'])-1,int(m['Col'])-1,
                          1 if m['Color']=='Black' else 2)
                    step+=1
                writer.write(current)
        finally: writer.release()
        assert step==41
    elif not src.exists():
        raise FileNotFoundError('Cannot reuse a missing authored source video')
    report={'frame_count':FRAMES,'fps':30,'duration_at_2x':round(FRAMES/60,3),
            'known_move_count':41,'source':'fully synthetic 15x15 game',
            'video_sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
    if side_by_side:
        side=output/'full_game_synced_961_2x.mp4'
        cap=cv2.VideoCapture(str(src))
        comparison=cv2.VideoWriter(str(side),cv2.VideoWriter_fourcc(*'mp4v'),60,(1230,690))
        if not comparison.isOpened(): raise RuntimeError('Synchronized MP4 codec unavailable')
        state=Board(); step=0
        board_img=cv2.resize(draw_board(state),(530,530),interpolation=cv2.INTER_AREA)
        try:
            for frame in range(1,FRAMES+1):
                good,image=cap.read()
                if not good: raise RuntimeError(f'Decode failure at frame {frame}')
                while step<len(moves) and int(moves[step]['Frame'])<=frame:
                    m=moves[step]
                    state.place(int(m['Frame']),1 if m['Color']=='Black' else 2,
                                int(m['Row'])-1,int(m['Col'])-1)
                    step+=1
                    board_img=cv2.resize(draw_board(state),(530,530),interpolation=cv2.INTER_AREA)
                # Visual presentation only: keep the source MP4 unchanged for
                # recognition. Show the SAME winner line on the LEFT and RIGHT.
                if step == len(moves):
                    _, winning_line=state.winner()
                    start=tuple(np.rint(cal.points[winning_line[0]]).astype(int))
                    end=tuple(np.rint(cal.points[winning_line[-1]]).astype(int))
                    cv2.line(image,start,end,(20,20,242),5,cv2.LINE_AA)
                both=np.full((690,1230,3),(247,244,240),dtype=np.uint8)
                both[12:672,12:672]=cv2.resize(image,(660,660),interpolation=cv2.INTER_AREA)
                both[75:605,688:1218]=board_img
                cv2.rectangle(both,(680,70),(1223,612),(200,208,220),2)
                cv2.putText(both,'SYNTHETIC VIDEO',(702,43),cv2.FONT_HERSHEY_SIMPLEX,.72,(55,65,80),2,cv2.LINE_AA)
                cv2.putText(both,f'{frame:03d} / 961',(1020,43),cv2.FONT_HERSHEY_SIMPLEX,.62,(55,65,80),2,cv2.LINE_AA)
                cv2.putText(both,'LIVE BOARD SIMULATION',(703,655),cv2.FONT_HERSHEY_SIMPLEX,.64,(65,70,85),2,cv2.LINE_AA)
                cv2.putText(both,f'MOVE {step:02d} / 41',(702,674),cv2.FONT_HERSHEY_SIMPLEX,.56,(55,65,80),1,cv2.LINE_AA)
                comparison.write(both)
        finally: cap.release();comparison.release()
        report['synchronized_video_sha256']=hashlib.sha256(side.read_bytes()).hexdigest()
        report['synchronized_video_fps']=60
    (output/'regeneration-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--no-synced-video',action='store_true')
    parser.add_argument('--reuse-source',action='store_true',
                        help='Regenerate only the side-by-side movie; keep existing 961-frame source bytes')
    options=parser.parse_args()
    print(json.dumps(create(options.output,ROOT/'results/full_game_demo/moves.csv',
                            side_by_side=not options.no_synced_video,
                            reuse_source=options.reuse_source),indent=2))
