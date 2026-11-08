"""Self-authored synthetic test data. No third-party video included."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from gomoku.vision import Calibration
from gomoku.core import SIZE


def make(out: Path):
    out.mkdir(parents=True,exist_ok=True)
    width,height = 840,840
    cal=Calibration.create_from_corners((70,70),(770,70),(70,770),(770,770))
    cal.write_legacy_csv(out/'checkerboard_points.csv')
    base=np.full((height,width,3),(166,195,220),dtype=np.uint8)
    for i in range(SIZE):
        x,y=round(cal.points[0,i,0]),round(cal.points[i,0,1])
        cv2.line(base,(x,70),(x,770),(71,88,103),2)
        cv2.line(base,(70,y),(770,y),(71,88,103),2)
    # Templates from the SAME synthetic rendering algorithm, centered on a grid crossing.
    def stone(base_frame,row,col,color):
        x,y=np.rint(cal.points[row,col]).astype(int)
        bgr=(29,29,29) if color == 1 else (235,235,235)
        cv2.circle(base_frame,(x,y),16,bgr,-1,cv2.LINE_8)
        cv2.circle(base_frame,(x,y),16,(35,35,35),1,cv2.LINE_8)
    for filename,color in [('black.png',1),('white.png',2)]:
        b=base.copy();stone(b,7,7,color)
        cv2.imwrite(str(out/filename),b[7*50+70-23:7*50+70+24,7*50+70-23:7*50+70+24])
    # 9 moves, alternating legal turn order, black wins with horizontal five.
    sequence=[(7,4,1),(8,4,2),(7,5,1),(8,5,2),(7,6,1),
              (8,6,2),(7,7,1),(8,7,2),(7,8,1)]
    writer=cv2.VideoWriter(str(out/'demo.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),12,(width,height))
    if not writer.isOpened():
        raise RuntimeError('Cannot create synthetic test video')
    current=base.copy()
    # hold each move for 6 frames; 2 frames confirmation with sample-every=2
    for r,c,color in sequence:
        stone(current,r,c,color)
        for _ in range(6):writer.write(current)
    for _ in range(4):writer.write(current)
    writer.release()
    print(f'Synthetic demo generated in {out}')


if __name__=='__main__':
    make(Path(sys.argv[1] if len(sys.argv)>1 else 'demo'))
