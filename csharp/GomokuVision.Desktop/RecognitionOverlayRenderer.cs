using System;
using System.Collections.Generic;
using System.Globalization;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace GomokuVision.Desktop;

/// <summary>
/// Render calibrated, timestamp-bound green boxes on raw source frames.
/// Only moves confirmed by a saved or live detector are outlined.
/// Never paints predictions as confirmed detections.
/// </summary>
internal static class RecognitionOverlayRenderer
{
    public static BitmapSource Draw(BitmapSource frame,IReadOnlyList<MoveRow> moves,
        int count,GomokuVision.Calibration cal,string mode)
    {
        count=Math.Clamp(count,0,moves.Count);
        int w=frame.PixelWidth, h=frame.PixelHeight;
        var board=new GomokuVision.Board();
        var visual=new DrawingVisual();
        using (var ctx=visual.RenderOpen())
        {
            ctx.DrawImage(frame,new Rect(0,0,w,h));
            var confirmedPen=new Pen(new SolidColorBrush(Color.FromRgb(49,230,63)),2.7);
            var lastPen=new Pen(Brushes.DeepSkyBlue,2);
            for (int i=0;i<count;i++)
            {
                MoveRow item=moves[i];
                if (!TryMove(item,out int r,out int c,out int color)) continue;
                if (board.Cells[r,c]!=0) continue;
                board.Place(item.Frame,color,r,c);
                var point=cal.Points[r,c];
                double x=point.X,y=point.Y;
                if (x<0 || y<0 || x>=w || y>=h) continue;
                double box=Math.Clamp(Math.Min(cal.CellSpacing(r,c,true),cal.CellSpacing(r,c,false))*.62,12,48);
                ctx.DrawRoundedRectangle(null,confirmedPen,new Rect(x-box/2,y-box/2,box,box),2,2);
                if (i==count-1)
                    ctx.DrawEllipse(null,lastPen,new Point(x,y),box*.64,box*.64);
            }
            var winner=board.Winner();
            if (winner is not null)
            {
                var line=winner.Value.Line;
                var a=cal.Points[line[0].Row,line[0].Col];
                var b=cal.Points[line[^1].Row,line[^1].Col];
                ctx.DrawLine(new Pen(Brushes.Red,3.8),new Point(a.X,a.Y),new Point(b.X,b.Y));
            }
            else if (mode=="recognition_prediction" && count>0)
            {
                // Green circles are black-side heuristic suggestions, cyan are white-side.
                foreach (int player in new[]{1,2})
                {
                    var pen=new Pen(player==1 ? Brushes.LimeGreen : Brushes.Cyan,2.2);
                    foreach(var item in board.Suggestions(player,3))
                    {
                        var p=cal.Points[item.Row,item.Col];
                        ctx.DrawEllipse(null,pen,new Point(p.X,p.Y),10,10);
                    }
                }
            }
        }
        var output=new RenderTargetBitmap(w,h,96,96,PixelFormats.Pbgra32);
        output.Render(visual);
        output.Freeze();
        return output;
    }
    private static bool TryMove(MoveRow m,out int r,out int c,out int color)
    {
        r=c=color=-1;
        var name=m.Position.Trim().ToUpperInvariant();
        if (name.Length<2 || name.Length>3 || name[0]<'A' || name[0]>'O') return false;
        if (!int.TryParse(name.AsSpan(1),NumberStyles.None,CultureInfo.InvariantCulture,out int row)
            || row<1 || row>15) return false;
        if (m.Color.Equals("Black",StringComparison.OrdinalIgnoreCase)) color=1;
        else if (m.Color.Equals("White",StringComparison.OrdinalIgnoreCase)) color=2;
        else return false;
        r=row-1;c=name[0]-'A';
        return true;
    }
}
