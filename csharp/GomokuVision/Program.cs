using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading;
using OpenCvSharp;

namespace GomokuVision;

public static class Program
{
    public static int Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        try
        {
            var opts = Options.Parse(args);
            if (opts.SelfTest)
            {
                SelfTest();
                return 0;
            }
            Run(opts);
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"ERROR: {ex.Message}");
            Console.Error.WriteLine("See README.md for usage and prerequisites.");
            return 1;
        }
    }

    private static void SelfTest()
    {
        var board = new Board();
        for (int col=0; col<4; col++) board.Place(col+1,1,7,col+3);
        if (board.Winner()!=null) throw new Exception("Premature winner");
        // D8, E8, F8, G8 are already black. Only C8 or H8 can win in one move.
        // D8 is occupied; I8 is two cells away from the four-in-a-row.
        var winning = board.Suggestions(1,1)[0];
        if (winning.Position is not ("C8" or "H8") || winning.Score != 10_000_000)
            throw new Exception($"Winning move suggestion failed: {winning.Position} score={winning.Score}; expected C8/H8 score=10000000");
        board.Place(5,1,winning.Row,winning.Col);
        if (board.Winner()?.Color!=1) throw new Exception("Suggested winning move did not actually win");
        var white = new Board();
        for (int i=0; i<5; i++) white.Place(i+1,2,i,4+i);
        if (white.Winner()?.Color!=2) throw new Exception("Diagonal win failed");
        var blocked = new Board();
        for (int i=3;i<7;i++) blocked.Place(i,2,i,7);
        if (blocked.Suggestions(1,1)[0].Score!=5_000_000)
            throw new Exception("Immediate opponent threat not blocked");
        var own = new Board();
        for (int i=3;i<7;i++) own.Place(i,1,7,i);
        if (own.Suggestions(1,1)[0].Score!=10_000_000)
            throw new Exception("Immediate own win not prioritized");
        var cal=Calibration.FromCorners((20,30),(690,25),(30,700),(700,705));
        if (Math.Abs(cal.Points[7,7].Y-365)>1e-6)
            throw new Exception("Calibration bilinear interpolation failed");
        var sampleFrames=new int[]{25,43,61,79,949};
        if (PlaybackTimeline.MoveCountAtFrame(sampleFrames,23)!=0 ||
            PlaybackTimeline.MoveCountAtFrame(sampleFrames,24)!=1 ||
            PlaybackTimeline.MoveCountAtFrame(sampleFrames,948)!=5 ||
            PlaybackTimeline.FrameAt(0,0.5,30,2,961)!=30 ||
            PlaybackTimeline.FrameAt(948,1.0,30,2,961)!=960)
            throw new Exception("Synchronized playback timeline self-test failed");
        Console.WriteLine("C# core/tactical/calibration self-tests PASS");
    }

    /// <summary>WPF invokes the same engine directly, no Python process or MATLAB runtime.</summary>
    public static void Run(Options opts, Action<RunProgress>? progress = null,
                           CancellationToken cancellationToken = default)
    {
        foreach (string path in new[] { opts.Input,opts.Calibration,opts.BlackTemplate,opts.WhiteTemplate })
            if (!File.Exists(path)) throw new FileNotFoundException("Missing input file",path);
        Directory.CreateDirectory(opts.OutputDir);
        var calibration = Calibration.Load(opts.Calibration);
        using var detector = new Detector(calibration,opts.BlackTemplate,opts.WhiteTemplate,
                                          opts.Scale,opts.BlackThreshold,opts.WhiteThreshold,opts.Confirmations,opts.RoiMode);
        using var capture = new VideoCapture(opts.Input);
        if (!capture.IsOpened()) throw new IOException("VideoCapture could not open video");
        double fps = capture.Fps;
        if (fps<=0 || double.IsNaN(fps)) fps=30;
        using var writer = new VideoWriter();
        using var frame = new Mat();
        using var finalPreview = new Mat();
        var board = new Board();
        int framesRead=0, framesAnalyzed=0, framesWritten=0;
        int framesTotal=(int)Math.Clamp(capture.FrameCount,0,int.MaxValue);
        bool canceled=false;
        int lastProgressMoves=-1;
        string previewFile=Path.Combine(opts.OutputDir,"last_frame.png");
        string previewFolder=Path.Combine(opts.OutputDir,"preview_frames",Guid.NewGuid().ToString("N"));
        if (progress is not null) Directory.CreateDirectory(previewFolder);
        string latestPreview=previewFile;
        var watch = Stopwatch.StartNew();
        double recognitionSeconds = 0;
        while (capture.Read(frame) && !frame.Empty())
        {
            if (cancellationToken.IsCancellationRequested) { canceled=true; break; }
            framesRead++;
            if (opts.MaxFrames>0 && framesRead>opts.MaxFrames)
            {
                framesRead--;
                break;
            }
            if ((framesRead-1)%opts.SampleEvery!=0) continue;
            framesAnalyzed++;
            bool fullScan = (framesAnalyzed-1)%opts.FullScanEvery==0;
            if (board.Winner() is null)
            {
                var recognitionClock = Stopwatch.StartNew();
                try
                {
                    foreach (var (row,col,color) in detector.Detect(frame,board,fullScan,opts.LocalRadius))
                        if (board.Cells[row,col]==0) board.Place(framesRead,color,row,col);
                }
                finally
                {
                    recognitionClock.Stop();
                    recognitionSeconds += recognitionClock.Elapsed.TotalSeconds;
                }
            }
            using var annotated = Overlay(frame,board,calibration,framesRead,opts.OverlayMode);
            if (!writer.IsOpened())
            {
                if (!writer.Open(Path.Combine(opts.OutputDir,"output.mp4"),
                                 FourCC.FromString("mp4v"),fps/opts.SampleEvery,
                                 new Size(annotated.Width,annotated.Height)))
                    throw new IOException("VideoWriter could not open output codec mp4v");
            }
            writer.Write(annotated);
            annotated.CopyTo(finalPreview);
            framesWritten++;
            if (framesAnalyzed==1 || framesAnalyzed%5==0 ||
                board.Moves.Count!=lastProgressMoves ||
                (framesTotal>0 && framesRead>=framesTotal))
            {
                if (progress is not null)
                {
                    // Immutable snapshots: no overwrite of WPF's open bitmap.
                    latestPreview=Path.Combine(previewFolder,$"frame_{framesRead:D6}.png");
                    if (!Cv2.ImWrite(latestPreview,annotated))
                        throw new IOException("Cannot write preview: " + latestPreview);
                    progress(new RunProgress(framesRead,framesTotal,framesAnalyzed,
                                             board.Moves.Count,latestPreview,board.Moves.ToArray()));
                }
                lastProgressMoves=board.Moves.Count;
            }
            if (opts.Preview)
            {
                Cv2.ImShow("Gomoku Vision / ESC to exit",annotated);
                if (Cv2.WaitKey(1)==27) break;
            }
            if (framesAnalyzed%25==0)
                Console.WriteLine($"Analyzed {framesAnalyzed} frames; moves={board.Moves.Count}");
            if (opts.MaxFrames==0 && capture.FrameCount>0 && framesRead>=capture.FrameCount)
                break;
        }
        writer.Release();
        if (opts.Preview) Cv2.DestroyAllWindows();
        // Retain the latest COMPLETED frame, not an earlier ten-frame snapshot.
        if (!finalPreview.Empty())
        {
            // A stable image is only written once after recognition finishes.
            if (!Cv2.ImWrite(previewFile,finalPreview))
                throw new IOException("Cannot write final preview: " + previewFile);
        }
        progress?.Invoke(new RunProgress(framesRead,framesTotal,framesAnalyzed,
                                         board.Moves.Count,latestPreview,board.Moves.ToArray()));
        watch.Stop();
        WriteOutputs(opts.OutputDir,board,new Dictionary<string,object?>
        {
            ["engine"]="csharp-opencvsharp", ["input"]=opts.Input,
            ["sampling_every"]=opts.SampleEvery,
            ["confirmations"]=opts.Confirmations,
            ["roi_mode"]=opts.RoiMode,["overlay_mode"]=opts.OverlayMode,
            ["confirmation_delay_frames"]=opts.SampleEvery*(opts.Confirmations-1),
            ["full_scan_every_processed_frames"]=opts.FullScanEvery,
            ["scale"]=opts.Scale,["input_fps"]=Math.Round(fps,5),
            ["output_fps"]=Math.Round(fps/opts.SampleEvery,5),
            ["frames_read"]=framesRead,["frames_analyzed"]=framesAnalyzed,
            ["frames_written"]=framesWritten,["canceled"]=canceled,
            ["wall_seconds"]=Math.Round(watch.Elapsed.TotalSeconds,3),
            ["recognition_seconds"]=Math.Round(recognitionSeconds,4),
            ["scanned_cells"]=detector.ScannedCells,["match_attempts"]=detector.MatchAttempts,
            ["full_scans"]=detector.FullScans,["local_scans"]=detector.LocalScans,
            ["accuracy_note"]="No accuracy claimed without independently labeled ground truth."
        });
        using var boardImage=DrawBoard(board);
        Cv2.ImWrite(Path.Combine(opts.OutputDir,"board_final.png"),boardImage);
        Console.WriteLine($"{(canceled ? "Canceled" : "Done")}: {board.Moves.Count} moves, {framesAnalyzed} frames -> {opts.OutputDir}");
    }

    private static Mat Overlay(Mat source,Board board,Calibration cal,int frameIndex,string overlayMode)
    {
        Mat image=source.Clone();
        foreach (Move move in board.Moves)
        {
            var pt=cal.ImagePoint(move.Row,move.Col);
            var color=new Scalar(35,235,60); // confirmed green bounding box; BOTH colors
            Cv2.Rectangle(image,new Rect(pt.X-21,pt.Y-21,42,42),color,2);
            Cv2.PutText(image,move.Position,new Point(pt.X+6,pt.Y-23),
                        HersheyFonts.HersheySimplex,.48,color,1,LineTypes.AntiAlias);
        }
        var winner=board.Winner();
        if (winner is not null)
        {
            var first=winner.Value.Line[0];
            var last=winner.Value.Line[^1];
            Cv2.Line(image,cal.ImagePoint(first.Row,first.Col),cal.ImagePoint(last.Row,last.Col),
                     new Scalar(0,0,255),4);
        }
        else if (overlayMode=="recognition_prediction" && board.Moves.Count>0)
        {
            foreach (var (player,color) in new[] {(1,new Scalar(0,230,0)),(2,new Scalar(255,255,0))})
            foreach (var candidate in board.Suggestions(player,3))
                Cv2.Circle(image,cal.ImagePoint(candidate.Row,candidate.Col),9,color,2);
        }
        int blacks=board.Moves.Count(m=>m.Color==1), whites=board.Moves.Count-blacks;
        Cv2.Rectangle(image,new Rect(0,0,Math.Min(image.Width,400),56),new Scalar(25,25,25),-1);
        Cv2.PutText(image,$"Frame: {frameIndex}   Black: {blacks}  White: {whites}",
                    new Point(8,24),HersheyFonts.HersheySimplex,.55,Scalar.White,1,LineTypes.AntiAlias);
        string status=winner?.Color==1 ? "Winner: BLACK" : winner?.Color==2 ? "Winner: WHITE"
            : overlayMode=="recognition_prediction" ? "Heuristic: green=black, cyan=white" : "Green=confirmed move";
        Cv2.PutText(image,status,new Point(8,47),HersheyFonts.HersheySimplex,.47,
                    new Scalar(225,225,225),1,LineTypes.AntiAlias);
        return image;
    }

    private static Mat DrawBoard(Board board)
    {
        var canvas = new Mat(580,580,MatType.CV_8UC3,new Scalar(174,202,221));
        for (int i=0; i<Board.Size; i++)
        {
            int pos=38+i*36;
            Cv2.Line(canvas,new Point(38,pos),new Point(542,pos),new Scalar(70,70,70));
            Cv2.Line(canvas,new Point(pos,38),new Point(pos,542),new Scalar(70,70,70));
            Cv2.PutText(canvas,$"{(char)('A'+i)}",new Point(pos-7,25),HersheyFonts.HersheySimplex,.5,Scalar.Black);
            Cv2.PutText(canvas,$"{i+1}",new Point(8,pos+4),HersheyFonts.HersheySimplex,.45,Scalar.Black);
        }
        foreach(var move in board.Moves)
        {
            var p = new Point(38+move.Col*36,38+move.Row*36);
            Cv2.Circle(canvas,p,14,move.Color==1 ? new Scalar(25,25,25) : new Scalar(240,240,240),-1,LineTypes.AntiAlias);
            Cv2.Circle(canvas,p,14,new Scalar(10,10,10),1,LineTypes.AntiAlias);
        }
        var win=board.Winner();
        if (win is not null)
        {
            var first=win.Value.Line[0]; var last=win.Value.Line[^1];
            Cv2.Line(canvas,new Point(38+first.Col*36,38+first.Row*36),
                     new Point(38+last.Col*36,38+last.Row*36),new Scalar(0,0,255),3);
        }
        return canvas;
    }

    private static void WriteOutputs(string folder,Board board,Dictionary<string,object?> summary)
    {
        var lines=new List<string>{"Index,Frame,Color,Row,Col,Position"};
        for (int i=0;i<board.Moves.Count;i++)
        {
            var m=board.Moves[i];
            lines.Add($"{i+1},{m.Frame},{(m.Color==1?"Black":"White")},{m.Row+1},{m.Col+1},{m.Position}");
        }
        File.WriteAllLines(Path.Combine(folder,"moves.csv"),lines,new UTF8Encoding(false));
        var blacks=board.Moves.Where(m=>m.Color==1).Select(m=>m.Position).ToList();
        var whites=board.Moves.Where(m=>m.Color==2).Select(m=>m.Position).ToList();
        lines=["Round,Black,White"];
        for (int i=0;i<Math.Max(blacks.Count,whites.Count);i++)
            lines.Add($"{i+1},{(i<blacks.Count?blacks[i]:"")},{(i<whites.Count?whites[i]:"")}");
        File.WriteAllLines(Path.Combine(folder,"moves_legacy.csv"),lines,new UTF8Encoding(false));
        summary["winner"]=board.Winner()?.Color==1 ? "Black" : board.Winner()?.Color==2 ? "White" : null;
        summary["moves"]=board.Moves.Count;
        summary["black_moves"]=blacks.Count;
        summary["white_moves"]=whites.Count;
        summary["black_suggestions"]=board.Suggestions(1).Select(s=>new {position=s.Position,score=Math.Round(s.Score,2)}).ToList();
        summary["white_suggestions"]=board.Suggestions(2).Select(s=>new {position=s.Position,score=Math.Round(s.Score,2)}).ToList();
        File.WriteAllText(Path.Combine(folder,"summary.json"),
                          JsonSerializer.Serialize(summary,new JsonSerializerOptions{WriteIndented=true}),new UTF8Encoding(false));
    }
}

// MoveSnapshot carries only completed/confirmed moves; the UI must never infer
// partial moves from preview images or report a future frame as recognized.
public sealed record RunProgress(int Frame,int TotalFrames,int AnalyzedFrames,int Moves,
                                 string PreviewPath,IReadOnlyList<Move>? MoveSnapshot=null);

public sealed record Options(
    string Input,string Calibration,string BlackTemplate,string WhiteTemplate,string OutputDir,
    int SampleEvery,int FullScanEvery,int LocalRadius,int Confirmations,double Scale,
    double BlackThreshold,double WhiteThreshold,int MaxFrames,bool Preview,bool SelfTest)
{
    public string RoiMode { get; init; } = "separated";
    public string OverlayMode { get; init; } = "recognition_prediction";
    public static Options Parse(string[] args)
    {
        if (args.Length==1 && args[0]=="--self-test")
            return new Options("","","","","",6,4,6,2,.5,.65,.75,0,false,true);
        if (args.Length==0 || args.Contains("--help"))
            throw new ArgumentException("Usage: --input video.mp4 --calibration pts.csv --black-template black.png --white-template white.png [--output-dir results] [--sample-every 6] [--full-scan-every 4] [--confirmations 2] [--scale .5] [--white-threshold .75] [--preview]");
        var data=new Dictionary<string,string>(StringComparer.Ordinal);
        bool preview=false;
        for (int i=0;i<args.Length;i++)
        {
            if (args[i]=="--preview") { preview=true;continue; }
            if (!args[i].StartsWith("--",StringComparison.Ordinal) || i+1>=args.Length || args[i+1].StartsWith("--",StringComparison.Ordinal))
                throw new ArgumentException($"Invalid option: {args[i]}");
            data[args[i++]]=args[i];
        }
        string Required(string key) => data.TryGetValue(key,out var v) ? v : throw new ArgumentException($"Missing {key}");
        string Get(string key,string value) => data.TryGetValue(key,out var v) ? v : value;
        int Integer(string key,int value) => int.Parse(Get(key,value.ToString(CultureInfo.InvariantCulture)),CultureInfo.InvariantCulture);
        double Real(string key,double value) => double.Parse(Get(key,value.ToString(CultureInfo.InvariantCulture)),CultureInfo.InvariantCulture);
        var opts=new Options(Required("--input"),Required("--calibration"),Required("--black-template"),
                             Required("--white-template"),Get("--output-dir","results/csharp"),
                             Integer("--sample-every",6),Integer("--full-scan-every",4),
                             Integer("--local-radius",6),Integer("--confirmations",2),
                             Real("--scale",.5),Real("--black-threshold",.65),
                             Real("--white-threshold",.75),Integer("--max-frames",0),preview,false)
        { RoiMode=Get("--roi-mode","separated"), OverlayMode=Get("--overlay-mode","recognition_prediction") };
        if (opts.SampleEvery<1 || opts.FullScanEvery<1 || opts.LocalRadius<0 || opts.Confirmations<1 || opts.Scale<=0 || opts.Scale>1 ||
            opts.RoiMode is not ("shared" or "separated") ||
            opts.OverlayMode is not ("recognition" or "recognition_prediction"))
            throw new ArgumentException("Invalid numeric option values");
        return opts;
    }
}
