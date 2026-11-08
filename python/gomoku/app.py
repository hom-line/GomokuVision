"""CLI video pipeline. Skipped input frames are NOT written to the output.
Output fps is input fps divided by sample_every, preserving approximate duration.
"""
from __future__ import annotations
import argparse
import csv
import json
import uuid
from pathlib import Path
from time import perf_counter, sleep
import cv2
import numpy as np
from .core import Board, SIZE
from .vision import Calibration, Detector


def draw_overlay(frame, board: Board, calibration: Calibration, *, frame_number: int,
                 overlay_mode: str = "recognition_prediction"):
    image = frame.copy()
    for m in board.moves:
        x, y = np.rint(calibration.points[m.row,m.col]).astype(int)
        color = (35,235,60)  # verified green rectangle for a CONFIRMED move, both colors
        cv2.rectangle(image, (x-21,y-21), (x+21,y+21), color, 2)
        cv2.putText(image, m.position, (x+6,y-23), cv2.FONT_HERSHEY_SIMPLEX, .48, color, 1, cv2.LINE_AA)
    winner = board.winner()
    if winner:
        _, points = winner
        first = np.rint(calibration.points[points[0]]).astype(int)
        last = np.rint(calibration.points[points[-1]]).astype(int)
        cv2.line(image, tuple(first), tuple(last), (0,0,255), 4)
    if overlay_mode == "recognition_prediction" and board.moves and not winner:
        for player, color in ((1,(0,230,0)), (2,(255,255,0))):
            for candidate in board.suggestions(player, 3):
                x, y = np.rint(calibration.points[candidate.row,candidate.col]).astype(int)
                cv2.circle(image, (x,y), 9, color, 2)
    count_black = sum(m.color == 1 for m in board.moves)
    count_white = len(board.moves)-count_black
    cv2.rectangle(image, (0,0), (min(image.shape[1],400),56), (25,25,25), -1)
    cv2.putText(image, f'Frame: {frame_number}   Black: {count_black}  White: {count_white}',
                (8,24), cv2.FONT_HERSHEY_SIMPLEX, .55, (255,255,255), 1, cv2.LINE_AA)
    cv2.putText(image, ('Winner: BLACK' if winner[0] == 1 else 'Winner: WHITE') if winner else ('Heuristic: green=black, cyan=white' if overlay_mode == 'recognition_prediction' else 'Green=confirmed move'),
                (8,47), cv2.FONT_HERSHEY_SIMPLEX, .47, (225,225,225), 1, cv2.LINE_AA)
    return image


def draw_board(board: Board):
    canvas = np.full((580,580,3), (174,202,221), dtype=np.uint8)
    for i in range(SIZE):
        pos = 38 + i*36
        cv2.line(canvas, (38,pos), (542,pos), (70,70,70), 1)
        cv2.line(canvas, (pos,38), (pos,542), (70,70,70), 1)
        cv2.putText(canvas, chr(65+i), (pos-7,25), cv2.FONT_HERSHEY_SIMPLEX, .5, (0,0,0), 1)
        cv2.putText(canvas, str(i+1), (8,pos+4), cv2.FONT_HERSHEY_SIMPLEX, .45, (0,0,0), 1)
    for m in board.moves:
        pos = (38+m.col*36,38+m.row*36)
        cv2.circle(canvas, pos, 14, (25,25,25) if m.color == 1 else (240,240,240), -1, cv2.LINE_AA)
        cv2.circle(canvas, pos, 14, (10,10,10), 1, cv2.LINE_AA)
    win = board.winner()
    if win:
        _, line = win
        cv2.line(canvas,(38+line[0][1]*36,38+line[0][0]*36),
                 (38+line[-1][1]*36,38+line[-1][0]*36),(0,0,255),3)
    return canvas


def write_outputs(folder, board: Board, metrics: dict):
    with open(folder/'moves.csv','w',newline='',encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Index','Frame','Color','Row','Col','Position'])
        for i,m in enumerate(board.moves,1):
            writer.writerow([i,m.frame,'Black' if m.color == 1 else 'White',m.row+1,m.col+1,m.position])
    blacks = [m.position for m in board.moves if m.color == 1]
    whites = [m.position for m in board.moves if m.color == 2]
    with open(folder/'moves_legacy.csv','w',newline='',encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Round','Black','White'])
        for i in range(max(len(blacks),len(whites))):
            writer.writerow([i+1,blacks[i] if i<len(blacks) else '', whites[i] if i<len(whites) else ''])
    winner = board.winner()
    metrics['winner'] = 'Black' if winner and winner[0] == 1 else 'White' if winner else None
    metrics['moves'] = len(board.moves)
    metrics['black_moves'] = len(blacks)
    metrics['white_moves'] = len(whites)
    metrics['black_suggestions'] = [dict(position=s.position,score=round(s.score,2)) for s in board.suggestions(1)]
    metrics['white_suggestions'] = [dict(position=s.position,score=round(s.score,2)) for s in board.suggestions(2)]
    (folder/'summary.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False),encoding='utf-8')
    cv2.imwrite(str(folder/'board_final.png'),draw_board(board))


def run(args) -> dict:
    for f in (args.input,args.calibration,args.black_template,args.white_template):
        if not Path(f).is_file():
            raise FileNotFoundError(f)
    folder = Path(args.output_dir)
    folder.mkdir(parents=True,exist_ok=True)
    points = Calibration.from_legacy_csv(args.calibration)
    detector = Detector(points,args.black_template,args.white_template,
                        scale=args.scale,black_threshold=args.black_threshold,
                        white_threshold=args.white_threshold,confirmations=args.confirmations,
                        roi_mode=getattr(args, "roi_mode", "separated"))
    cap = cv2.VideoCapture(str(args.input))
    if not cap.isOpened():
        raise RuntimeError('Cannot open video')
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or not np.isfinite(fps):
        fps = 30.
    writer = None
    board = Board()
    num_read = num_analyzed = num_written = 0
    canceled = False
    progress_file = getattr(args, 'progress_file', None)
    cancel_file = getattr(args, 'cancel_file', None)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    t0 = perf_counter()
    recognition_seconds = 0.0
    last_visual = None
    last_reported_moves = -1
    # Snapshot names are immutable. Windows WPF can safely decode an older file
    # while the producer publishes a different one. Never replace last_frame.png
    # on every progress event: an open image blocks os.replace on Windows.
    preview_dir = folder / 'preview_frames' / uuid.uuid4().hex
    latest_preview = folder / 'last_frame.png'
    if progress_file is not None:
        preview_dir.mkdir(parents=True, exist_ok=False)

    def publish_preview(visual, frame_index):
        nonlocal latest_preview
        image_path = preview_dir / f'frame_{frame_index:06d}.png'
        if not cv2.imwrite(str(image_path), visual):
            raise IOError(f'Cannot write preview image: {image_path}')
        latest_preview = image_path
        report_progress(image_path)

    def report_progress(preview_path):
        if progress_file is None:
            return
        dest = Path(progress_file)
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = {'frame': num_read, 'total_frames': total_frames,
                'analyzed_frames': num_analyzed, 'moves': len(board.moves),
                'preview_path': str(preview_path),
                'move_records': [
                    {'frame': m.frame, 'color': m.color,
                     'row': m.row + 1, 'col': m.col + 1}
                    for m in board.moves] }
        temp = dest.with_name(dest.name + '.tmp')
        temp.write_text(json.dumps(data), encoding='utf-8')
        # A polling client or antivirus may briefly hold the JSON on Windows.
        # Retry a bounded number of times, without losing the analysis state.
        for attempt in range(8):
            try:
                temp.replace(dest)
                break
            except PermissionError:
                if attempt == 7:
                    raise
                sleep(0.03 * (attempt + 1))
    try:
        while True:
            if cancel_file is not None and Path(cancel_file).exists():
                canceled = True
                break
            ok, frame = cap.read()
            if not ok:
                break
            num_read += 1
            if args.max_frames and num_read > args.max_frames:
                num_read -= 1
                break
            if (num_read - 1) % args.sample_every != 0:
                continue
            num_analyzed += 1
            # Scan using PROCESSED frames, independent of the sampling frame number.
            full = (num_analyzed-1) % args.full_scan_every == 0
            if not board.winner():
                recognition_t0 = perf_counter()
                try:
                    newly_found = detector.detect(frame,board,full_scan=full,local_radius=args.local_radius)
                    for r,c,color in newly_found:
                        if board.cells[r][c] == 0:
                            board.place(num_read,color,r,c)
                finally:
                    recognition_seconds += perf_counter() - recognition_t0
            visual = draw_overlay(frame,board,points,frame_number=num_read,
                                  overlay_mode=getattr(args, "overlay_mode", "recognition_prediction"))
            if writer is None:
                h,w = visual.shape[:2]
                writer = cv2.VideoWriter(str(folder/'output.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),
                                         fps/args.sample_every,(w,h))
                if not writer.isOpened():
                    raise RuntimeError('Video writer failed: check codec availability')
            writer.write(visual)
            num_written += 1
            last_visual = visual
            if (num_analyzed == 1 or num_analyzed % 5 == 0 or
                    len(board.moves) != last_reported_moves or
                    (total_frames > 0 and num_read >= total_frames)):
                if progress_file is not None:
                    publish_preview(visual, num_read)
                last_reported_moves = len(board.moves)
            if args.preview:
                cv2.imshow('Gomoku Vision / ESC to exit', visual)
                if cv2.waitKey(1) == 27:
                    break
            if num_analyzed % 25 == 0:
                print(f'Analyzed {num_analyzed} frames; moves={len(board.moves)}',flush=True)
        if num_written and last_visual is not None:
            # The stable last_frame.png is for offline results only. The live GUI
            # uses latest_preview (immutable), so this single final write is not
            # involved in any producer/consumer rename race.
            final_path = folder / 'last_frame.png'
            if not cv2.imwrite(str(final_path), last_visual):
                raise IOError(f'Cannot write final preview: {final_path}')
            if progress_file is None:
                latest_preview = final_path
        report_progress(latest_preview)
    finally:
        cap.release()
        if writer is not None:
            writer.release()
        if args.preview:
            cv2.destroyAllWindows()
    metrics = {
        'engine':'python-opencv','input':str(args.input),'sampling_every':args.sample_every,
        'confirmations':args.confirmations,
        'roi_mode':getattr(args, 'roi_mode', 'separated'),
        'overlay_mode':getattr(args, 'overlay_mode', 'recognition_prediction'),
        'confirmation_delay_frames':args.sample_every*(args.confirmations-1),
        'full_scan_every_processed_frames':args.full_scan_every,'scale':args.scale,
        'input_fps':round(fps,5),'output_fps':round(fps/args.sample_every,5),
        'frames_read':num_read,'frames_analyzed':num_analyzed,'frames_written':num_written,
        'canceled':canceled,
        'wall_seconds':round(perf_counter()-t0,3),
        'recognition_seconds':round(recognition_seconds,4),**detector.diagnostics,
        'accuracy_note':'No accuracy claimed without independently labeled ground truth.'}
    write_outputs(folder,board,metrics)
    print(f'Done: {len(board.moves)} moves, {num_analyzed} analyzed frames -> {folder}')
    return metrics


def parse_args(argv=None):
    p=argparse.ArgumentParser(description='Gomoku recognition on an existing video with calibrated board points.')
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--calibration',required=True,type=Path)
    p.add_argument('--black-template',required=True,type=Path)
    p.add_argument('--white-template',required=True,type=Path)
    p.add_argument('--output-dir',type=Path,default=Path('results/python'))
    p.add_argument('--sample-every',type=int,default=6)
    p.add_argument('--full-scan-every',type=int,default=4)
    p.add_argument('--local-radius',type=int,default=6)
    p.add_argument('--confirmations',type=int,default=2)
    p.add_argument('--scale',type=float,default=.5)
    p.add_argument('--black-threshold',type=float,default=.65)
    p.add_argument('--white-threshold',type=float,default=.75)
    p.add_argument('--max-frames',type=int,default=0,help='0 means full video')
    p.add_argument('--preview',action='store_true')
    p.add_argument('--roi-mode',choices=['separated','shared'],default='separated',
                   help='Separate black/white contrast gates or one shared candidate ROI')
    p.add_argument('--overlay-mode',choices=['recognition','recognition_prediction'],
                   default='recognition_prediction',help='Confirmed green boxes, with optional predicted circles')
    p.add_argument('--progress-file',type=Path,help='Optional JSON progress state for WPF')
    p.add_argument('--cancel-file',type=Path,help='Stop gracefully when this file is created')
    args=p.parse_args(argv)
    if args.sample_every < 1 or args.full_scan_every < 1 or args.local_radius < 0:
        p.error('sample-every/full-scan-every must be >= 1; local-radius >= 0')
    return args


def main():
    run(parse_args())

if __name__ == '__main__':
    main()
