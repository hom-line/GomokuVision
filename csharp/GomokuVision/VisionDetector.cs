using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using OpenCvSharp;

namespace GomokuVision;

/// <summary>
/// Warning: legacy checkerboard_points.csv labels encode row A..O and column 1..15.
/// This is the opposite of externally displayed move positions. Keep mapping here.
/// </summary>
public sealed class Calibration
{
    public (double X, double Y)[,] Points { get; } = new (double, double)[Board.Size, Board.Size];

    public static Calibration Load(string filename)
    {
        var cal = new Calibration();
        var lines = File.ReadAllLines(filename);
        if (lines.Length < 2 || lines[0].TrimStart('\uFEFF').Trim() != "Label,x,y")
            throw new FormatException("Expected calibration CSV header: Label,x,y");
        var used = new bool[Board.Size, Board.Size];
        for (int i = 1; i < lines.Length; i++)
        {
            if (string.IsNullOrWhiteSpace(lines[i])) continue;
            var parts = lines[i].Split(',');
            if (parts.Length != 3) throw new FormatException($"Bad line {i+1}");
            var label = parts[0].Trim().ToUpperInvariant();
            if (label.Length < 2) throw new FormatException($"Bad label: {label}");
            int row = label[0] - 'A';
            int col = int.Parse(label[1..], CultureInfo.InvariantCulture) - 1;
            if (row < 0 || row >= Board.Size || col < 0 || col >= Board.Size || used[row,col])
                throw new FormatException($"Invalid or duplicate calibration label: {label}");
            cal.Points[row,col] = (
                double.Parse(parts[1], CultureInfo.InvariantCulture),
                double.Parse(parts[2], CultureInfo.InvariantCulture));
            used[row,col] = true;
        }
        for (int r = 0; r < Board.Size; r++)
        for (int c = 0; c < Board.Size; c++)
            if (!used[r,c]) throw new FormatException($"Missing legacy calibration cell {r},{c}");
        return cal;
    }

    /// <summary>Four manually marked OUTERMOST grid intersections, ordered TL,TR,BL,BR.</summary>
    public static Calibration FromCorners((double X,double Y) tl, (double X,double Y) tr,
                                          (double X,double Y) bl, (double X,double Y) br)
    {
        var cal = new Calibration();
        for (int r=0;r<Board.Size;r++)
        for (int c=0;c<Board.Size;c++)
        {
            double u = (double)c/(Board.Size-1), v = (double)r/(Board.Size-1);
            cal.Points[r,c] = (
                (1-u)*(1-v)*tl.X + u*(1-v)*tr.X + (1-u)*v*bl.X + u*v*br.X,
                (1-u)*(1-v)*tl.Y + u*(1-v)*tr.Y + (1-u)*v*bl.Y + u*v*br.Y);
        }
        return cal;
    }

    public void SaveLegacyCsv(string filename)
    {
        using var writer = new StreamWriter(filename,false,new System.Text.UTF8Encoding(false));
        writer.WriteLine("Label,x,y");
        for (int c=0;c<Board.Size;c++)
        for (int r=0;r<Board.Size;r++)
            writer.WriteLine($"{(char)('A'+r)}{c+1},{Points[r,c].X.ToString("F6",CultureInfo.InvariantCulture)},{Points[r,c].Y.ToString("F6",CultureInfo.InvariantCulture)}");
    }

    public Point ImagePoint(int r, int c, double scale = 1)
    {
        var (x,y) = Points[r,c];
        return new Point((int)Math.Round(x*scale, MidpointRounding.ToEven),
                         (int)Math.Round(y*scale, MidpointRounding.ToEven));
    }

    public double CellSpacing(int r, int c, bool horizontal)
    {
        var now = Points[r,c];
        double best = double.PositiveInfinity;
        foreach (int direction in new[] { -1, 1 })
        {
            int nr = horizontal ? r : r + direction;
            int nc = horizontal ? c + direction : c;
            if (nr < 0 || nr >= Board.Size || nc < 0 || nc >= Board.Size) continue;
            var other = Points[nr,nc];
            double d = horizontal ? Math.Abs(other.X-now.X) : Math.Abs(other.Y-now.Y);
            best = Math.Min(best,d);
        }
        return double.IsFinite(best) ? Math.Max(1,best) : 10;
    }
}

public sealed class Detector : IDisposable
{
    private readonly Calibration _calibration;
    private readonly Mat[] _templates;
    private readonly double[] _thresholds;
    private readonly int[,,] _counts = new int[Board.Size,Board.Size,2];
    private readonly double _scale;
    private readonly int _confirmations;
    private readonly string _roiMode;
    public int ScannedCells { get; private set; }
    public int MatchAttempts { get; private set; }
    public int FullScans { get; private set; }
    public int LocalScans { get; private set; }

    public Detector(Calibration calibration, string blackFile, string whiteFile,
                    double scale, double blackThreshold, double whiteThreshold, int confirmations,
                    string roiMode = "separated")
    {
        if (scale <= 0 || scale > 1 || confirmations < 1)
            throw new ArgumentException("Scale must be in (0,1], confirmations >= 1");
        if (roiMode is not ("separated" or "shared"))
            throw new ArgumentException("Unknown ROI mode",nameof(roiMode));
        _roiMode = roiMode;
        _calibration = calibration;
        _scale = scale;
        _confirmations = confirmations;
        _thresholds = [blackThreshold,whiteThreshold];
        _templates = new Mat[2];
        foreach (var (file,idx) in new[] { (blackFile,0), (whiteFile,1) })
        {
            using var original = Cv2.ImRead(file,ImreadModes.Grayscale);
            if (original.Empty()) throw new FileNotFoundException("Cannot read template",file);
            var resized = new Mat();
            if (scale < 1) Cv2.Resize(original,resized,new Size(),scale,scale,InterpolationFlags.Area);
            else original.CopyTo(resized);
            if (resized.Width < 3 || resized.Height < 3)
                throw new ArgumentException("Template too small at selected scale");
            _templates[idx] = resized;
        }
    }

    public List<(int Row,int Col,int Color)> Detect(Mat frame, Board board, bool fullScan, int localRadius)
    {
        using var gray = new Mat();
        Cv2.CvtColor(frame,gray,ColorConversionCodes.BGR2GRAY);
        using var small = new Mat();
        if (_scale < 1) Cv2.Resize(gray,small,new Size(),_scale,_scale,InterpolationFlags.Area);
        else gray.CopyTo(small);
        if (fullScan || board.Moves.Count == 0) FullScans++;
        else LocalScans++;
        var locations = new List<(int Row,int Col)>();
        var recent = new List<(int Row,int Col)>();
        for (int color = 1; color <= 2; color++)
        {
            for (int i = board.Moves.Count-1; i >= 0; i--)
                if (board.Moves[i].Color == color)
                {
                    recent.Add((board.Moves[i].Row,board.Moves[i].Col));
                    break;
                }
        }
        if (recent.Count == 0) recent.Add((7,7));
        for (int r = 0; r < Board.Size; r++)
        for (int c = 0; c < Board.Size; c++)
        {
            if (fullScan || board.Moves.Count == 0)
                locations.Add((r,c));
            else
                foreach (var (rr,cc) in recent)
                    if (Math.Abs(r-rr)<=localRadius && Math.Abs(c-cc)<=localRadius)
                    {
                        locations.Add((r,c));
                        break;
                    }
        }
        var found = new List<(int Row,int Col,int Color)>();
        int maxSize = Math.Max(Math.Max(_templates[0].Width,_templates[0].Height),
                               Math.Max(_templates[1].Width,_templates[1].Height));
        foreach (var (r,c) in locations)
        {
            if (board.Cells[r,c]!=0) continue;
            ScannedCells++;
            var pt = _calibration.ImagePoint(r,c,_scale);
            int x=pt.X, y=pt.Y;
            if (x<0 || x>=small.Width || y<0 || y>=small.Height)
            {
                Reset(r,c);
                continue;
            }
            var centerRect = new Rect(Math.Max(0,x-1), Math.Max(0,y-1),
                                      Math.Min(small.Width,x+2)-Math.Max(0,x-1),
                                      Math.Min(small.Height,y+2)-Math.Max(0,y-1));
            using var center = new Mat(small,centerRect);
            double centerMean = Cv2.Mean(center).Val0;
            int radius = Math.Max(4,(int)Math.Round(maxSize*.7));
            var backgroundRect = new Rect(Math.Max(0,x-radius),Math.Max(0,y-radius),
                                          Math.Min(small.Width,x+radius+1)-Math.Max(0,x-radius),
                                          Math.Min(small.Height,y+radius+1)-Math.Max(0,y-radius));
            double background = Median(small,backgroundRect);
            bool blackAllowed = centerMean < background-20 || centerMean < 80;
            bool whiteAllowed = centerMean > background+20 || centerMean > 205;
            if (!blackAllowed && !whiteAllowed)
            {
                Reset(r,c);
                continue;
            }
            double[] scores = new double[] { -1.0, -1.0 };
            for (int i=0; i<2; i++)
            {
                if (_roiMode=="separated" && i==0 && !blackAllowed) continue;
                if (_roiMode=="separated" && i==1 && !whiteAllowed) continue;
                Mat templ = _templates[i];
                int padding = Math.Max(templ.Width,templ.Height);
                var rect = new Rect(Math.Max(0,x-padding),Math.Max(0,y-padding),
                                    Math.Min(small.Width,x+padding+1)-Math.Max(0,x-padding),
                                    Math.Min(small.Height,y+padding+1)-Math.Max(0,y-padding));
                if (rect.Width<templ.Width || rect.Height<templ.Height) continue;
                using var patch = new Mat(small,rect);
                using var response = new Mat();
                MatchAttempts++;
                Cv2.MatchTemplate(patch,templ,response,TemplateMatchModes.CCoeffNormed);
                Cv2.MinMaxLoc(response,out _,out double score,out _,out var maxLoc);
                double matchX = rect.X+maxLoc.X+templ.Width/2.0;
                double matchY = rect.Y+maxLoc.Y+templ.Height/2.0;
                double maxDx = Math.Max(2,_calibration.CellSpacing(r,c,true)*_scale*.4);
                double maxDy = Math.Max(2,_calibration.CellSpacing(r,c,false)*_scale*.4);
                if (Math.Abs(matchX-x)<=maxDx && Math.Abs(matchY-y)<=maxDy)
                    scores[i] = score;
            }
            int chosen = -1;
            if (scores[0]>=_thresholds[0]) chosen=0;
            if (scores[1]>=_thresholds[1] &&
                (chosen<0 || scores[1]-_thresholds[1]>scores[0]-_thresholds[0]))
                chosen=1;
            for (int i=0;i<2;i++)
                _counts[r,c,i] = chosen==i ? _counts[r,c,i]+1 : 0;
            if (chosen>=0 && _counts[r,c,chosen]>=_confirmations)
            {
                found.Add((r,c,chosen+1));
                Reset(r,c);
            }
        }
        return found;
    }

    private static double Median(Mat mat,Rect rect)
    {
        int len = rect.Width*rect.Height;
        byte[] values = new byte[len];
        int k=0;
        for (int row=rect.Top; row<rect.Bottom; row++)
        for (int col=rect.Left; col<rect.Right; col++)
            values[k++]=mat.At<byte>(row,col);
        Array.Sort(values);
        return values[len/2];
    }

    private void Reset(int r,int c) { _counts[r,c,0]=0;_counts[r,c,1]=0; }

    public void Dispose()
    {
        foreach (var mat in _templates) mat?.Dispose();
    }
}
