using System;
using System.Collections.Generic;
using System.IO;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Shapes;
using Microsoft.Win32;

namespace GomokuVision.Desktop;

public partial class CalibrationWindow : Window
{
    private readonly bool _english;
    private readonly List<(double X,double Y)> _points=new();
    public string? ResultPath {get; private set;}

    public CalibrationWindow(string videoPath,bool english)
    {
        InitializeComponent();
        _english=english;
        Title=english ? "Calibrate board" : "棋盤四角校準";
        Instructions.Text=english ?
            "Click four OUTER grid intersections: top-left → top-right → bottom-left → bottom-right" :
            "依序點選最外圍四個交叉點：左上 → 右上 → 左下 → 右下";
        Note.Text=english ? "Use the outermost 15×15 intersections, NOT the wooden board edges." :
                             "四個點必須是 15×15 棋盤最外圈交叉點，不是木板邊角。";
        ResetButton.Content=english ? "Reset" : "重設";
        UndoButton.Content=english ? "Undo point" : "撤銷上一點";
        SaveButton.Content=english ? "Save CSV" : "儲存 CSV";
        using var capture=new OpenCvSharp.VideoCapture(videoPath);
        using var frame=new OpenCvSharp.Mat();
        if (!capture.IsOpened() || !capture.Read(frame) || frame.Empty())
            throw new IOException("Cannot read the first frame of video");
        OpenCvSharp.Cv2.ImEncode(".png",frame,out byte[] bytes);
        using var memory=new MemoryStream(bytes);
        var source=new BitmapImage();
        source.BeginInit();
        source.StreamSource=memory;
        source.CacheOption=BitmapCacheOption.OnLoad;
        source.EndInit();
        source.Freeze();
        FrameImage.Source=source;
        RenderStatus();
        CanvasArea.SizeChanged+=(_,_)=>RedrawMarkers();
    }

    private (double displayX,double displayY,double pixelX,double pixelY)? MapClick(System.Windows.Point mouse)
    {
        if (FrameImage.Source is not BitmapSource image || CanvasArea.ActualWidth<=0 || CanvasArea.ActualHeight<=0)
            return null;
        double fit=Math.Min(CanvasArea.ActualWidth/image.PixelWidth,CanvasArea.ActualHeight/image.PixelHeight);
        double w=image.PixelWidth*fit,h=image.PixelHeight*fit;
        double left=(CanvasArea.ActualWidth-w)/2,top=(CanvasArea.ActualHeight-h)/2;
        if (mouse.X<left || mouse.X>left+w || mouse.Y<top || mouse.Y>top+h) return null;
        return (mouse.X,mouse.Y,(mouse.X-left)/fit,(mouse.Y-top)/fit);
    }

    private void FrameImage_MouseLeftButtonDown(object sender,MouseButtonEventArgs e)
    {
        if (_points.Count>=4) return;
        var pt=MapClick(e.GetPosition(CanvasArea));
        if (pt is null) return;
        _points.Add((pt.Value.pixelX,pt.Value.pixelY));
        RenderStatus();
        RedrawMarkers();
    }

    private void RenderStatus()
    {
        string[] names=_english ? ["top-left","top-right","bottom-left","bottom-right"] :
                                   ["左上","右上","左下","右下"];
        ProgressLabel.Text=_points.Count==4 ? (_english?"4/4 — ready to save":"4/4 — 可以儲存") :
            $"{_points.Count}/4 — {(_english?"Next":"下一點")}: {names[_points.Count]}";
        SaveButton.IsEnabled=_points.Count==4;
        UndoButton.IsEnabled=_points.Count>0;
    }

    private void RedrawMarkers()
    {
        Markers.Children.Clear();
        if (FrameImage.Source is not BitmapSource bitmap || CanvasArea.ActualWidth<=0 || CanvasArea.ActualHeight<=0)
            return;
        double fit=Math.Min(CanvasArea.ActualWidth/bitmap.PixelWidth,CanvasArea.ActualHeight/bitmap.PixelHeight);
        double ox=(CanvasArea.ActualWidth-bitmap.PixelWidth*fit)/2;
        double oy=(CanvasArea.ActualHeight-bitmap.PixelHeight*fit)/2;
        if (_points.Count == 4)
        {
            // Preview the bilinear 15x15 intersection calibration BEFORE saving.
            var tl=_points[0]; var tr=_points[1]; var bl=_points[2]; var br=_points[3];
            (double X,double Y) Interpolate(double u,double v) =>
                (tl.X*(1-u)*(1-v)+tr.X*u*(1-v)+bl.X*(1-u)*v+br.X*u*v,
                 tl.Y*(1-u)*(1-v)+tr.Y*u*(1-v)+bl.Y*(1-u)*v+br.Y*u*v);
            var gridPen=new SolidColorBrush(Color.FromArgb(120, 42, 176, 232));
            for (int k=0;k<15;k++)
            {
                foreach (bool horizontal in new[]{true,false})
                {
                    var a=horizontal ? Interpolate(0,k/14.0) : Interpolate(k/14.0,0);
                    var b=horizontal ? Interpolate(1,k/14.0) : Interpolate(k/14.0,1);
                    var line=new Line{ X1=ox+a.X*fit,Y1=oy+a.Y*fit,
                        X2=ox+b.X*fit,Y2=oy+b.Y*fit,Stroke=gridPen,StrokeThickness=1.2 };
                    Markers.Children.Add(line);
                }
            }
        }
        for (int i=0;i<_points.Count;i++)
        {
            var (x,y)=_points[i];
            var circle=new Ellipse{Width=16,Height=16,Fill=Brushes.DeepSkyBlue,Stroke=Brushes.White,StrokeThickness=2};
            System.Windows.Controls.Canvas.SetLeft(circle,ox+x*fit-8);
            System.Windows.Controls.Canvas.SetTop(circle,oy+y*fit-8);
            Markers.Children.Add(circle);
        }
    }

    private void Undo_Click(object sender,RoutedEventArgs e)
    {
        if (_points.Count==0) return;
        _points.RemoveAt(_points.Count-1);
        RenderStatus();
        RedrawMarkers();
    }

    private void Reset_Click(object sender,RoutedEventArgs e)
    {
        _points.Clear();RenderStatus();RedrawMarkers();
    }

    private void Save_Click(object sender,RoutedEventArgs e)
    {
        if (_points.Count!=4) return;
        var dialog=new SaveFileDialog {Filter="CSV|*.csv",DefaultExt=".csv",FileName="checkerboard_points.csv"};
        if (dialog.ShowDialog(this)!=true) return;
        var cal=GomokuVision.Calibration.FromCorners(_points[0],_points[1],_points[2],_points[3]);
        cal.SaveLegacyCsv(dialog.FileName);
        ResultPath=dialog.FileName;
        DialogResult=true;
    }
}
