using System;
using System.IO;
using OpenCvSharp;

namespace GomokuVision.Desktop;

/// <summary>
/// On-demand frame decoding, independent from recognition. All OpenCV access is serialized.
/// WPF calls ReadPng on a background task so moving the timeline does not freeze the UI.
/// </summary>
internal sealed class VideoFrameReader : IDisposable
{
    private readonly object _gate = new();
    private readonly VideoCapture _capture;
    private bool _disposed;
    public string Path { get; }
    public int FrameCount { get; }
    public double Fps { get; }

    public VideoFrameReader(string path)
    {
        Path = System.IO.Path.GetFullPath(path);
        if (!File.Exists(Path)) throw new FileNotFoundException("Video not found", Path);
        _capture = new VideoCapture(Path);
        if (!_capture.IsOpened()) { _capture.Dispose(); throw new IOException("Could not open video: " + Path); }
        FrameCount = Math.Max(0, (int)Math.Round(_capture.Get(VideoCaptureProperties.FrameCount)));
        var fps = _capture.Get(VideoCaptureProperties.Fps);
        Fps = double.IsFinite(fps) && fps > 0 ? fps : 12.0;
        if (FrameCount <= 0) { _capture.Dispose(); throw new IOException("Video frame count not available"); }
    }

    public byte[] ReadPng(int index)
    {
        lock (_gate)
        {
            if (_disposed) throw new ObjectDisposedException(nameof(VideoFrameReader));
            index = Math.Clamp(index, 0, FrameCount - 1);
            _capture.Set(VideoCaptureProperties.PosFrames, index);
            using var frame = new Mat();
            if (!_capture.Read(frame) || frame.Empty()) throw new IOException($"Could not decode frame {index + 1}");
            Cv2.ImEncode(".png", frame, out byte[] png);
            return png;
        }
    }

    public void Dispose()
    {
        lock (_gate)
        {
            if (_disposed) return;
            _disposed = true;
            _capture.Dispose();
        }
    }
}
