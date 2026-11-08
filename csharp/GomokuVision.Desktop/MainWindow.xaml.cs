using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using Microsoft.Win32;

namespace GomokuVision.Desktop;

public partial class MainWindow : Window
{
    private CancellationTokenSource? _cts;
    private bool _running;
    private string _lastOutput = "";
    private string? _pythonCancelFile;
    private bool _pythonRunning;
    private bool _matlabRunning;
    private bool _gateRunning;
    private bool _benchmarkRunning;
    private string? _benchmarkCancelFlag;
    private readonly ObservableCollection<MoveRow> _moveRows = new();
    // V0.3 viewer state. Timeline uses saved moves, not recognition or historical video reprocessing.
    private readonly DispatcherTimer _moveTimer = new() { Interval = TimeSpan.FromMilliseconds(780) };
    private readonly DispatcherTimer _videoTimer = new() { Interval = TimeSpan.FromMilliseconds(40) };
    // A single monotonic playback clock drives BOTH image frame and board move state.
    private readonly Stopwatch _playbackClock = new();
    private int _playbackStartFrame;
    private bool _clockSeeking;
    private bool _fullDemoReferenceActive;
    private VideoFrameReader? _frameReader;
    private GomokuVision.Calibration? _overlayCalibration;
    private string _overlayCalibrationPath = "";
    private bool _selectionUpdating;
    private bool _videoMatchesMoves;
    private bool _decodeBusy;
    private int _requestedFrame;
    private int _renderedFrame = -1;
    private int _selectedStep;
    private string? _resultsVideoPath;
    // For historical replay, linking requires BOTH the original video digest and
    // the bundled 41-move CSV digest. No original video is bundled or uploaded.
    private bool _historicalReferenceActive;
    private bool _originalDataSelected;
    private const string KnownHistoricalVideoSha256 =
        "6d5bf68284bd7af7ac16ab3b24125c367ff84f4d1fff83223eff93cc32b96e39";
    private const string KnownHistoricalMovesSha256 =
        "e61a6da9a5808c7b22e7aa80a3eb9b1c20fd2ac89b187c7d2b822be934c6c5f0";
    private const string BundledFullGameVideoSha256 =
        "0518c8f5e0627e396ca1e4d5a9e0ff687008f8c90efe0b9ac91875c29c594641";
    // The 60 FPS video is already encoded at 2x; set the player to 1x for that file.
    private const string BundledSyncedTwoXVideoSha256 =
        "dcaf2f52e04c7cf6958fc9f693a4dd6695787d4c1170076064206bf2f771c84b";
    private static string FileSha256(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
    }
    // English is the first-run default (LanguageBox SelectedIndex=1); Traditional Chinese remains selectable.
    private bool English => LanguageBox.SelectedIndex == 1;
    private string Tr(string zh, string en) => English ? en : zh;

    public MainWindow()
    {
        InitializeComponent();
        // The initial 1390×875 layout must not start off-screen on small displays or DPI-scaled Windows.
        Loaded += (_, _) =>
        {
            var workArea = SystemParameters.WorkArea;
            Width = Math.Min(Width, Math.Max(MinWidth, workArea.Width - 20));
            Height = Math.Min(Height, Math.Max(MinHeight, workArea.Height - 20));
            // Re-clamp the initial centered position after resizing; keep the footer above the taskbar.
            Left = Math.Max(workArea.Left, Math.Min(Left, workArea.Right - Width));
            Top = Math.Max(workArea.Top, Math.Min(Top, workArea.Bottom - Height));
        };
        MovesGrid.ItemsSource = _moveRows;
        _moveTimer.Tick += (_, _) =>
        {
            if (_selectedStep >= _moveRows.Count) { StopMovePlayback(); return; }
            SetMoveStep(_selectedStep + 1, seekMatchingVideo: true);
        };
        _videoTimer.Tick += (_, _) =>
        {
            if (_frameReader is null) { StopVideoPlayback(); return; }
            int next = GomokuVision.PlaybackTimeline.FrameAt(
                _playbackStartFrame, _playbackClock.Elapsed.TotalSeconds,
                _frameReader.Fps, PlaybackSpeed(), _frameReader.FrameCount);
            _clockSeeking = true;
            try { FrameSlider.Value = next; }
            finally { _clockSeeking = false; }
            if (next >= _frameReader.FrameCount - 1)
            {
                RequestPreviewFrame(_frameReader.FrameCount-1); // Explicit terminal-frame decode.
                StopVideoPlayback();
            }
        };
        Closing += HandleClosing;
        string? root = FindProjectRoot();
        if (root is not null)
        {
            // The default is now a FULL 961-frame self-authored 41-move game.
            VideoPath.Text = Path.Combine(root,"demo","full_game","full_game_961.mp4");
            CalibrationPath.Text = Path.Combine(root,"demo","full_game","checkerboard_points.csv");
            BlackPath.Text = Path.Combine(root,"demo","full_game","black.png");
            WhitePath.Text = Path.Combine(root,"demo","full_game","white.png");
        }
        OutputPath.Text = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                                       "GomokuVision", "run-"+DateTime.Now.ToString("yyyyMMdd-HHmmss"));
        ApplyLanguage();
        // Start with the verified synthetic 41-move timeline; NOT third-party footage.
        if (root is not null)
        {
            string cached=Path.Combine(root,"results","full_game_demo");
            if (File.Exists(Path.Combine(cached,"summary.json")) &&
                File.Exists(Path.Combine(cached,"moves.csv")))
            {
                try
                {
                    _lastOutput=cached;
                    LoadResults(cached);
                    StatusText.Text=Tr("已載入 961 幀合成影片的 41 手棋譜（預設 2 倍速）",
                                       "Loaded 41-move synthetic game (961 frames, default 2x)");
                    PreviewCaption.Text=Tr("自行繪製的合成棋盤，非原始第三方影片",
                                           "Self-authored synthetic board, not original footage");
                }
                catch (Exception ex)
                {
                    StatusText.Text=Tr("無法開啟保存結果：","Could not load cached results: ")+ex.Message;
                }
            }
        }
        // The first preview is loaded only after WPF controls finish initialization.
        Loaded += (_, _) =>
        {
            if (_fullDemoReferenceActive && File.Exists(VideoPath.Text))
                LoadVideoPreview_Click(this, new RoutedEventArgs());
        };
    }

    private static string? FindProjectRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        for (int i=0;dir is not null && i<9;i++,dir=dir.Parent)
            if (File.Exists(Path.Combine(dir.FullName,"demo","demo.mp4")))
                return dir.FullName;
        return null;
    }

    private void HandleClosing(object? sender, CancelEventArgs e)
    {
        StopMovePlayback();
        StopVideoPlayback();
        if (_benchmarkRunning && !string.IsNullOrEmpty(_benchmarkCancelFlag))
        {
            e.Cancel=true;
            File.WriteAllText(_benchmarkCancelFlag,"cancel");
            StatusText.Text=Tr("正在取消完整比較；完成目前組合後可關閉…","Canceling full benchmark after current case…");
            return;
        }
        if (_running)
        {
            e.Cancel=true;
            if ((_pythonRunning || _matlabRunning) && _pythonCancelFile is not null)
                File.WriteAllText(_pythonCancelFile,"cancel");
            else _cts?.Cancel();
            StatusText.Text=Tr("正在取消分析，完成收尾後可關閉視窗…",
                               "Canceling and finalizing outputs before exit…");
        }
        else CloseVideoReader();
    }

    private static BitmapImage LoadPng(string path)
    {
        using var stream = new FileStream(path,FileMode.Open,FileAccess.Read,
            FileShare.ReadWrite | FileShare.Delete);
        var result=new BitmapImage();
        result.BeginInit();
        result.CacheOption=BitmapCacheOption.OnLoad;
        result.StreamSource=stream;
        result.EndInit();
        result.Freeze();
        return result;
    }

    private void ImportOriginal_Click(object sender, RoutedEventArgs e)
    {
        if (_running || _gateRunning || _benchmarkRunning) return;
        var dialog = new OpenFolderDialog
        {
            Title = Tr("選擇解壓後的原始期末專題資料夾（僅本機使用）",
                       "Choose the extracted historical project folder (local only)")
        };
        if (dialog.ShowDialog(this) != true) return;
        string folder = dialog.FolderName;
        string video = Path.Combine(folder, "input.mp4");
        string calibration = Path.Combine(folder, "checkerboard_points.csv");
        string black = Path.Combine(folder, "black.png");
        string white = Path.Combine(folder, "white.png");
        var missing = new[] { video, calibration, black, white }
            .Where(path => !File.Exists(path)).Select(Path.GetFileName).ToArray();
        if (missing.Length != 0)
        {
            ShowError(Tr("原始資料不完整，缺少：", "Missing original input files: ") +
                      string.Join(", ", missing));
            return;
        }
        CloseVideoReader();
        VideoPath.Text = video;
        _originalDataSelected = true;
        InputSourceNote.Text = Tr("已選擇本機原始影片（不會上傳），準備顯示 41 手歷史棋譜。",
                                  "Local original footage selected (not uploaded); loading 41 saved moves.");
        CalibrationPath.Text = calibration;
        BlackPath.Text = black;
        WhitePath.Text = white;
        // Reopen the bundled 41-move evidence: the preceding results may have
        // belonged to the synthetic demo. Never pair unlike board histories.
        var root = FindProjectRoot();
        if (root is not null)
        {
            var historical = Path.Combine(root, "results", "verified_historical");
            if (File.Exists(Path.Combine(historical, "moves.csv")) &&
                File.Exists(Path.Combine(historical, "summary.json")))
            {
                LoadResults(historical);
                _lastOutput = historical;
            }
        }
        StatusText.Text = Tr("已選取原始影片與其校準／模板，將檢查影片識別碼後配對歷史棋譜。",
                             "Selected original inputs. Checking video digest for historical pairing.");
        // Preview / SHA verification only: NEVER call Analyze_Click here.
        LoadVideoPreview_Click(sender, e);
    }

    private void PickVideo_Click(object sender,RoutedEventArgs e)
    {
        var previous=VideoPath.Text;
        PickFile(VideoPath,"Video|*.mp4;*.avi;*.mkv;*.mov|All files|*.*");
        if (!string.Equals(previous,VideoPath.Text,StringComparison.OrdinalIgnoreCase))
            CloseVideoReader(); // Never show frames from a different selected source.
    }
    private void PickCalibration_Click(object sender,RoutedEventArgs e) => PickFile(CalibrationPath,"CSV|*.csv|All files|*.*");
    private void PickBlack_Click(object sender,RoutedEventArgs e) => PickFile(BlackPath,"Images|*.png;*.jpg;*.bmp|All files|*.*");
    private void PickWhite_Click(object sender,RoutedEventArgs e) => PickFile(WhitePath,"Images|*.png;*.jpg;*.bmp|All files|*.*");
    private void PickFile(System.Windows.Controls.TextBox field,string filter)
    {
        var dialog=new OpenFileDialog {Filter=filter, CheckFileExists=true};
        if (dialog.ShowDialog(this)==true) field.Text=dialog.FileName;
    }

    private void PickOutput_Click(object sender,RoutedEventArgs e)
    {
        var dialog=new OpenFolderDialog {Title=Tr("選擇結果資料夾","Select output folder")};
        if (dialog.ShowDialog(this)==true) OutputPath.Text=dialog.FolderName;
    }

    private void Calibrate_Click(object sender,RoutedEventArgs e)
    {
        if (!File.Exists(VideoPath.Text))
        {
            ShowError(Tr("請先選擇有效的影片檔。","Select a valid video first.")); return;
        }
        try
        {
            var dialog=new CalibrationWindow(VideoPath.Text,English) {Owner=this};
            if (dialog.ShowDialog()==true && dialog.ResultPath is not null)
            {
                CalibrationPath.Text=dialog.ResultPath;
                StatusText.Text=Tr("已產生 225 點校準 CSV。","225-point calibration CSV created.");
            }
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private GomokuVision.Options BuildOptions()
    {
        string[] paths=[VideoPath.Text,CalibrationPath.Text,BlackPath.Text,WhitePath.Text];
        foreach (var path in paths)
            if (!File.Exists(path)) throw new FileNotFoundException(Tr("缺少檔案：","Missing file: ")+path);
        int ParseInt(string text,string name,int minimum)
        {
            if (!int.TryParse(text,NumberStyles.Integer,CultureInfo.InvariantCulture,out int n) || n<minimum)
                throw new ArgumentException($"{name}: integer >= {minimum} required");
            return n;
        }
        double ParseDouble(string text,string name,double min,double max)
        {
            if (!double.TryParse(text,NumberStyles.Float,CultureInfo.InvariantCulture,out double n) ||
                !double.IsFinite(n) || n<=min || n>max)
                throw new ArgumentException($"{name}: {min} < value <= {max} required (use period decimal)");
            return n;
        }
        string folder=OutputPath.Text.Trim();
        if (string.IsNullOrWhiteSpace(folder)) throw new ArgumentException("Output folder required");
        return new GomokuVision.Options(paths[0],paths[1],paths[2],paths[3],folder,
           ParseInt(EveryValue.Text,"sample-every",1),ParseInt(FullValue.Text,"full-scan-every",1),6,
           ParseInt(ConfirmValue.Text,"confirmations",1),
           ParseDouble(ScaleValue.Text,"scale",0,1),
           ParseDouble(BlackThresholdValue.Text,"black-threshold",-1,1),
           ParseDouble(WhiteThresholdValue.Text,"white-threshold",-1,1),
           0,false,false)
        {
            RoiMode = RoiModeBox.SelectedIndex==1 ? "shared" : "separated",
            OverlayMode = DisplayModeBox.SelectedIndex==0 ? "recognition" : "recognition_prediction"
        };
    }

    private async void Analyze_Click(object sender,RoutedEventArgs e)
    {
        GomokuVision.Options opts;
        try { opts=BuildOptions(); }
        catch (Exception ex) { ShowError(ex.Message); return; }
        Directory.CreateDirectory(opts.OutputDir);
        _lastOutput=opts.OutputDir;
        _cts=new CancellationTokenSource();
        _running=true;
        _pythonRunning=EngineBox.SelectedIndex==1;
        _matlabRunning=EngineBox.SelectedIndex==2;
        _pythonCancelFile=(_pythonRunning || _matlabRunning) ? Path.Combine(opts.OutputDir,".cancel-request") : null;
        if (_pythonCancelFile is not null && File.Exists(_pythonCancelFile)) File.Delete(_pythonCancelFile);
        RunButton.IsEnabled=false;
        QuickGateButton.IsEnabled=false;
        AllResultsButton.IsEnabled=false;
        LoadVideoButton.IsEnabled=false;
        CancelButton.IsEnabled=true;
        CalibrateButton.IsEnabled=false;
        Progress.IsIndeterminate=true;
        StopMovePlayback();
        StopVideoPlayback();
        ResetTimeline();
        PreviewImage.Source=null;
        BoardImage.Source=null;
        StatusText.Text=Tr("正在分析影片…","Analyzing video…");
        SummaryText.Text=Tr("正在處理","Processing");
        try
        {
            var token=_cts.Token;
            if (_pythonRunning) await RunPythonAsync(opts);
            else if (_matlabRunning) await RunMatlabAsync(opts);
            else await Task.Run(() => GomokuVision.Program.Run(opts,OnProgress,token));
            LoadResults(opts.OutputDir);
            // The final frame is the actual source-video end, NOT the last confirmed
            // detection frame (which can lag by one sample, e.g., F955 vs F949).
            if (_frameReader is not null && _videoMatchesMoves)
                FrameSlider.Value=_frameReader.FrameCount-1;
            else if (File.Exists(opts.Input))
                LoadVideoPreview_Click(this,new RoutedEventArgs());
            bool canceled=false;
            var summary=Path.Combine(opts.OutputDir,"summary.json");
            if (File.Exists(summary))
            {
                using var json=JsonDocument.Parse(File.ReadAllText(summary));
                canceled=json.RootElement.TryGetProperty("canceled",out var canceledElement) && canceledElement.GetBoolean();
            }
            StatusText.Text=canceled ? Tr("已取消，保留部分結果","Canceled; partial outputs retained") :
                                      Tr("辨識完成","Analysis complete");
            Progress.Value=canceled ? Progress.Value : 100;
        }
        catch (Exception ex)
        {
            StatusText.Text=Tr("分析失敗","Analysis failed");
            ShowError(ex.Message);
        }
        finally
        {
            _running=false;
            _pythonRunning=false;
            _matlabRunning=false;
            _pythonCancelFile=null;
            _cts.Dispose();
            _cts=null;
            RunButton.IsEnabled=true;
            QuickGateButton.IsEnabled=true;
            AllResultsButton.IsEnabled=true;
            LoadVideoButton.IsEnabled=true;
            CancelButton.IsEnabled=false;
            CalibrateButton.IsEnabled=true;
            Progress.IsIndeterminate=false;
        }
    }

    // Full 3-engine * 2-ROI * 2-overlay benchmark with a durable CSV export.
    // Distinct run directory; never mutates original 41-move historical evidence.
    private async void AllResults_Click(object sender,RoutedEventArgs e)
    {
        if (_running || _gateRunning || _benchmarkRunning) return;
        string? root=FindProjectRoot();
        if (root is null) { ShowError("Cannot locate GomokuVision project root."); return; }
        GomokuVision.Options opts;
        try { opts=BuildOptions(); }
        catch(Exception ex) { ShowError(ex.Message); return; }
        var selectedSpeeds = new List<int>();
        if (BenchmarkSpeed1.IsChecked==true) selectedSpeeds.Add(1);
        if (BenchmarkSpeed2.IsChecked==true) selectedSpeeds.Add(2);
        if (BenchmarkSpeed4.IsChecked==true) selectedSpeeds.Add(4);
        if (selectedSpeeds.Count==0)
        {
            ShowError(Tr("請至少勾選一種播放倍率（1×、2× 或 4×）。",
                         "Select at least one playback speed (1x, 2x or 4x)."));
            return;
        }
        int expectedCases=12*selectedSpeeds.Count;
        string selectedSpeedText=string.Join(", ",selectedSpeeds.Select(x=>x.ToString(CultureInfo.InvariantCulture)+"×"));
        var confirmation=MessageBox.Show(this,
            Tr($"將執行 {expectedCases} 組（三引擎 × 兩種 ROI × 兩種顯示模式 × {selectedSpeeds.Count} 種播放倍率：{selectedSpeedText}）。\n每組都重新辨識選取影片；倍率不會加速辨識運算。\n完成後自動匯出 CSV，是否開始？",
               $"Run {expectedCases} cases (3 engines × 2 ROI × 2 overlays × {selectedSpeeds.Count} playback speeds: {selectedSpeedText}).\nEvery case reprocesses the video. Replay speed does not accelerate recognition.\nExport CSV after completion?"),
            Tr("完整效能比較","Full benchmark"),MessageBoxButton.YesNo,MessageBoxImage.Question);
        if (confirmation != MessageBoxResult.Yes) return;
        string dir=Path.Combine(opts.OutputDir,"benchmark-"+DateTime.Now.ToString("yyyyMMdd-HHmmss"));
        Directory.CreateDirectory(dir);
        string script=Path.Combine(root,"python","tools","run_full_benchmark.py");
        if (!File.Exists(script)) { ShowError("Missing benchmark runner: "+script); return; }
        _benchmarkCancelFlag=Path.Combine(dir,"cancel.flag");
        string progress=Path.Combine(dir,"status.json");
        _benchmarkRunning=true;
        AllResultsButton.IsEnabled=false;
        QuickGateButton.IsEnabled=false;
        RunButton.IsEnabled=false;
        CancelButton.IsEnabled=true;
        Progress.IsIndeterminate=false; Progress.Value=0;
        _lastOutput=dir;
        StatusText.Text=Tr($"正在執行 {expectedCases} 組測試…",$"Running {expectedCases} benchmark cases…");
        try
        {
            var psi=new ProcessStartInfo("python") {
                WorkingDirectory=root,RedirectStandardOutput=true,RedirectStandardError=true,
                UseShellExecute=false,CreateNoWindow=true
            };
            foreach (var arg in new [] {
                script,"--input",opts.Input,"--calibration",opts.Calibration,
                "--black-template",opts.BlackTemplate,"--white-template",opts.WhiteTemplate,
                "--output-dir",dir,"--sample-every",opts.SampleEvery.ToString(System.Globalization.CultureInfo.InvariantCulture),
                "--full-scan-every",opts.FullScanEvery.ToString(System.Globalization.CultureInfo.InvariantCulture),
                "--confirmations",opts.Confirmations.ToString(System.Globalization.CultureInfo.InvariantCulture),
                "--scale",opts.Scale.ToString(System.Globalization.CultureInfo.InvariantCulture),
                "--black-threshold",opts.BlackThreshold.ToString(System.Globalization.CultureInfo.InvariantCulture),
                "--white-threshold",opts.WhiteThreshold.ToString(System.Globalization.CultureInfo.InvariantCulture),
                "--status-file",progress,"--cancel-file",_benchmarkCancelFlag!
            }) psi.ArgumentList.Add(arg);
            psi.ArgumentList.Add("--playback-speeds");
            foreach (int speed in selectedSpeeds)
                psi.ArgumentList.Add(speed.ToString(CultureInfo.InvariantCulture));
            using var process=Process.Start(psi) ?? throw new IOException("Cannot launch benchmark runner");
            var stdOut=process.StandardOutput.ReadToEndAsync();
            var stdErr=process.StandardError.ReadToEndAsync();
            while (!process.HasExited)
            {
                await Task.Delay(400);
                if (File.Exists(progress))
                {
                    try
                    {
                        using var doc=JsonDocument.Parse(File.ReadAllText(progress));
                        var obj=doc.RootElement;
                        int completed=obj.GetProperty("completed").GetInt32();
                        int total=obj.GetProperty("total").GetInt32();
                        string current=obj.TryGetProperty("current",out var cur)?cur.GetString() ?? "":"";
                        Progress.Value=total>0?completed*100.0/total:0;
                        StatusText.Text=Tr($"完整比較 {completed}/{total}: {current}", $"Benchmark {completed}/{total}: {current}");
                    }
                    catch (IOException) {} catch (JsonException) {} catch (KeyNotFoundException) {}
                }
            }
            await process.WaitForExitAsync();
            string output=await stdOut,err=await stdErr;
            File.WriteAllText(Path.Combine(dir,"wpf-benchmark-console.log"),output+Environment.NewLine+err);
            string csv=Path.Combine(dir,"benchmark-results.csv");
            string summary=Path.Combine(dir,"benchmark-summary.csv");
            if (!File.Exists(csv)) throw new IOException("Benchmark CSV not written. "+err);
            Progress.Value=100;
            StatusText.Text=process.ExitCode==0 ?
                Tr($"全部 {expectedCases} 組完成，CSV 已匯出",$"All {expectedCases} cases passed; CSV exported") :
                Tr("測試完成但有失敗／未執行項目，詳見 CSV","Finished with failures/skips; check CSV");
            MessageBox.Show(this,
                StatusText.Text+Environment.NewLine+csv+Environment.NewLine+summary,
                Tr("完整比較結果","Benchmark results"),MessageBoxButton.OK,
                process.ExitCode==0?MessageBoxImage.Information:MessageBoxImage.Warning);
        }
        catch(Exception ex) { StatusText.Text=Tr("完整比較中斷","Benchmark interrupted"); ShowError(ex.Message); }
        finally
        {
            _benchmarkRunning=false; _benchmarkCancelFlag=null;
            AllResultsButton.IsEnabled=true; QuickGateButton.IsEnabled=true;
            RunButton.IsEnabled=true; CancelButton.IsEnabled=false;
        }
    }

    // Isolated synthetic smoke test: uses only demo/demo.mp4 and writes a separate log.
    // The saved 41-move historical results are not read or modified by this gate.
    private async void QuickGate_Click(object sender, RoutedEventArgs e)
    {
        if (_running || _gateRunning || _benchmarkRunning) return;
        string? root=FindProjectRoot();
        if (root is null)
        {
            ShowError(Tr("找不到專案根目錄及合成示範影片。",
                         "Cannot locate the project root and synthetic demonstration video."));
            return;
        }
        string script=Path.Combine(root,"scripts","Quick-Engine-Gate-Windows.ps1");
        if (!File.Exists(script)) { ShowError("Missing gate script: " + script); return; }
        _gateRunning=true;
        QuickGateButton.IsEnabled=false;
        AllResultsButton.IsEnabled=false;
        RunButton.IsEnabled=false;
        Progress.IsIndeterminate=true;
        StatusText.Text=Tr("正在驗收 Python / C#（僅合成影片）…",
                           "Testing Python / C# using synthetic video only…");
        try
        {
            var psi=new ProcessStartInfo("powershell.exe")
            {
                UseShellExecute=false, RedirectStandardOutput=true,
                RedirectStandardError=true, CreateNoWindow=true,
                WorkingDirectory=root
            };
            foreach (var arg in new[]{"-NoProfile","-ExecutionPolicy","Bypass","-File",script})
                psi.ArgumentList.Add(arg);
            using var process=Process.Start(psi) ?? throw new IOException("Cannot start PowerShell gate");
            var stdout=process.StandardOutput.ReadToEndAsync();
            var stderr=process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();
            string output=await stdout;
            string error=await stderr;
            string logs=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                                     "GomokuVision","Gates");
            if (process.ExitCode!=0)
            {
                var lastLines=(output+Environment.NewLine+error)
                    .Split(new[]{'\r','\n'},StringSplitOptions.RemoveEmptyEntries)
                    .TakeLast(10);
                throw new IOException(Tr("雙引擎測試未通過。", "Dual-engine gate did not pass.")
                    + Environment.NewLine + string.Join(Environment.NewLine,lastLines)
                    + Environment.NewLine + Tr("完整日誌：", "Full logs: ") + logs);
            }
            StatusText.Text=Tr("雙引擎合成影片測試通過（不代表原始影片辨識率）",
                               "Synthetic dual-engine gate passed (not historical accuracy)");
            MessageBox.Show(this,
                Tr("Python / C# 合成影片、棋譜比對及 WPF 編譯檢查通過。",
                   "Python/C# synthetic video, move parity and WPF build checks passed.")
                + Environment.NewLine + Tr("測試報告位於：", "Test report: ") + logs,
                Tr("快速驗收通過", "Quick gate passed"),MessageBoxButton.OK,MessageBoxImage.Information);
        }
        catch (Exception ex)
        {
            StatusText.Text=Tr("快速驗收失敗（已保存診斷報告）",
                               "Quick gate failed (diagnostics saved)");
            ShowError(ex.Message);
        }
        finally
        {
            _gateRunning=false;
            QuickGateButton.IsEnabled=true;
            AllResultsButton.IsEnabled=true;
            RunButton.IsEnabled=true;
            Progress.IsIndeterminate=false;
        }
    }

    private async Task RunPythonAsync(GomokuVision.Options opts)
    {
        var root=FindProjectRoot() ?? throw new DirectoryNotFoundException(
            "Python mode requires the source checkout with the python/gomoku folder.");
        string progress=Path.Combine(opts.OutputDir,".wpf-progress.json");
        if (File.Exists(progress)) File.Delete(progress);
        var psi=new ProcessStartInfo("python")
        {
            WorkingDirectory=Path.Combine(root,"python"),
            RedirectStandardOutput=true,
            RedirectStandardError=true,
            UseShellExecute=false,
            CreateNoWindow=true
        };
        psi.Environment["PYTHONPATH"]=Path.Combine(root,"python");
        foreach (var value in new[]{
            "-m","gomoku", "--input",opts.Input, "--calibration",opts.Calibration,
            "--black-template",opts.BlackTemplate,"--white-template",opts.WhiteTemplate,
            "--output-dir",opts.OutputDir,"--sample-every",opts.SampleEvery.ToString(CultureInfo.InvariantCulture),
            "--full-scan-every",opts.FullScanEvery.ToString(CultureInfo.InvariantCulture),
            "--confirmations",opts.Confirmations.ToString(CultureInfo.InvariantCulture),
            "--local-radius",opts.LocalRadius.ToString(CultureInfo.InvariantCulture),
            "--scale",opts.Scale.ToString(CultureInfo.InvariantCulture),
            "--black-threshold",opts.BlackThreshold.ToString(CultureInfo.InvariantCulture),
            "--white-threshold",opts.WhiteThreshold.ToString(CultureInfo.InvariantCulture),
            "--roi-mode",opts.RoiMode,"--overlay-mode",opts.OverlayMode,
            "--progress-file",progress,"--cancel-file",_pythonCancelFile!})
            psi.ArgumentList.Add(value);
        using var process=Process.Start(psi) ?? throw new IOException("Cannot start Python engine");
        Task<string> stdout=process.StandardOutput.ReadToEndAsync();
        Task<string> stderr=process.StandardError.ReadToEndAsync();
        while (!process.HasExited)
        {
            await Task.Delay(250);
            PollPythonProgress(progress);
        }
        await process.WaitForExitAsync();
        PollPythonProgress(progress);
        string err=await stderr;
        string output=await stdout;
        if (process.ExitCode!=0) throw new IOException($"Python exited {process.ExitCode}: {err} {output}");
    }

    // Third independent engine: MATLAB Desktop runs in its own process via -batch.
    // This NEVER silently forwards work to Python or the C# detector.
    private async Task RunMatlabAsync(GomokuVision.Options opts)
    {
        string root=FindProjectRoot() ?? throw new DirectoryNotFoundException("Project root not found");
        string matlabScript=Path.Combine(root,"matlab","modern","gomoku_batch.m");
        if (!File.Exists(matlabScript)) throw new FileNotFoundException("MATLAB engine missing",matlabScript);
        string executable=Environment.GetEnvironmentVariable("GOMOKUVISION_MATLAB_EXE") ?? "matlab";
        string progress=Path.Combine(opts.OutputDir,".wpf-progress.json");
        string configPath=Path.Combine(opts.OutputDir,"matlab-run-config.json");
        var config=new Dictionary<string,object?>
        {
            ["input"]=opts.Input, ["calibration"]=opts.Calibration,
            ["black_template"]=opts.BlackTemplate, ["white_template"]=opts.WhiteTemplate,
            ["output_dir"]=opts.OutputDir, ["sample_every"]=opts.SampleEvery,
            ["full_scan_every"]=opts.FullScanEvery, ["confirmations"]=opts.Confirmations,
            ["local_radius"]=opts.LocalRadius, ["scale"]=opts.Scale,
            ["black_threshold"]=opts.BlackThreshold, ["white_threshold"]=opts.WhiteThreshold,
            ["roi_mode"]=opts.RoiMode, ["overlay_mode"]=opts.OverlayMode,
            ["progress_file"]=progress, ["cancel_file"]=_pythonCancelFile
        };
        File.WriteAllText(configPath,JsonSerializer.Serialize(config));
        string EscapeMatlab(string value) => value.Replace("'","''");
        var psi=new ProcessStartInfo(executable)
        {
            WorkingDirectory=Path.Combine(root,"matlab","modern"),
            RedirectStandardOutput=true, RedirectStandardError=true,
            UseShellExecute=false,CreateNoWindow=true
        };
        psi.ArgumentList.Add("-batch");
        psi.ArgumentList.Add($"addpath('{EscapeMatlab(psi.WorkingDirectory)}'); gomoku_batch('{EscapeMatlab(configPath)}')");
        Process process;
        try { process=Process.Start(psi) ?? throw new IOException("MATLAB process not created"); }
        catch (Win32Exception ex)
        {
            throw new IOException("MATLAB executable not found. Install licensed MATLAB + Image Processing Toolbox " +
                "and set GOMOKUVISION_MATLAB_EXE to the full matlab.exe path.",ex);
        }
        using (process)
        {
            Task<string> stdout=process.StandardOutput.ReadToEndAsync();
            Task<string> stderr=process.StandardError.ReadToEndAsync();
            while (!process.HasExited)
            {
                await Task.Delay(300);
                PollPythonProgress(progress); // Shared JSON progress contract, not Python execution.
            }
            await process.WaitForExitAsync();
            PollPythonProgress(progress);
            string output=await stdout, err=await stderr;
            File.WriteAllText(Path.Combine(opts.OutputDir,"matlab-console.log"),output+Environment.NewLine+err);
            if (process.ExitCode!=0)
                throw new IOException($"MATLAB exited {process.ExitCode}: {err} {output}");
        }
    }

    private void PollPythonProgress(string progressPath)
    {
        if (!File.Exists(progressPath)) return;
        try
        {
            using var stream = new FileStream(progressPath,FileMode.Open,FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete);
            using var doc=JsonDocument.Parse(stream);
            var e=doc.RootElement;
            var snapshot=new List<GomokuVision.Move>();
            if (e.TryGetProperty("move_records",out var records) && records.ValueKind==JsonValueKind.Array)
            {
                foreach (var m in records.EnumerateArray())
                    snapshot.Add(new GomokuVision.Move(
                        m.GetProperty("frame").GetInt32(),m.GetProperty("color").GetInt32(),
                        m.GetProperty("row").GetInt32()-1,m.GetProperty("col").GetInt32()-1));
            }
            OnProgress(new GomokuVision.RunProgress(
                e.GetProperty("frame").GetInt32(),e.GetProperty("total_frames").GetInt32(),
                e.GetProperty("analyzed_frames").GetInt32(),e.GetProperty("moves").GetInt32(),
                e.GetProperty("preview_path").GetString() ?? "",snapshot));
        }
        catch (IOException) { /* Atomic rename between poll iterations; retry next time. */ }
        catch (JsonException) { /* Incomplete state is not treated as finished work. */ }
    }

    private void OnProgress(GomokuVision.RunProgress value)
    {
        Dispatcher.BeginInvoke(new Action(() =>
        {
            if (value.TotalFrames>0)
            {
                Progress.IsIndeterminate=false;
                Progress.Value=Math.Clamp(value.Frame*100.0/value.TotalFrames,0,100);
            }
            StatusText.Text=Tr($"已分析 {value.AnalyzedFrames} 幀 · 已辨識 {value.Moves} 手",
                               $"Analyzed {value.AnalyzedFrames} frames · {value.Moves} moves");
            // All three engines now publish the SAME confirmed-move contract.
            // Never wait until moves.csv/summary.json is finalized to show moves.
            if (_running && value.MoveSnapshot is not null)
                ApplyLiveMoves(value.MoveSnapshot);
            if (File.Exists(value.PreviewPath))
            {
                try { PreviewImage.Source=LoadPng(value.PreviewPath); }
                catch (IOException) { /* A new snapshot may be replacing the old one. */ }
            }
        }));
    }

    private void ApplyLiveMoves(IReadOnlyList<GomokuVision.Move> observed)
    {
        if (observed.Count<_moveRows.Count) return; // Reject stale/out-of-order progress.
        for (int i=_moveRows.Count;i<observed.Count;i++)
        {
            var m=observed[i];
            if (m.Row<0 || m.Row>=15 || m.Col<0 || m.Col>=15 ||
                m.Color is not (1 or 2) || m.Frame<1) return;
            _moveRows.Add(new MoveRow(i+1,m.Frame,m.Color==1?"Black":"White",m.Position));
        }
        if (observed.Count==0 || observed.Count==_selectedStep) return;
        MoveSlider.Maximum=Math.Max(1,_moveRows.Count);
        MoveSlider.IsEnabled=true;
        PreviousMoveButton.IsEnabled=true;
        NextMoveButton.IsEnabled=true;
        MovePlayButton.IsEnabled=false; // During analysis there is no finalized playback source.
        SetMoveStep(observed.Count,seekMatchingVideo:false);
        SummaryText.Text=Tr($"即時辨識：{observed.Count} 手（尚未完成）",
                            $"Live recognition: {observed.Count} moves (in progress)");
    }

    private void LoadResults(string folder)
    {
        StopMovePlayback();
        _moveRows.Clear();
        string moves=Path.Combine(folder,"moves.csv");
        if (File.Exists(moves))
        {
            foreach (string line in File.ReadLines(moves).Skip(1))
            {
                var parts=line.Split(',');
                if (parts.Length>=6 && int.TryParse(parts[0],out int index) && int.TryParse(parts[1],out int frame))
                    _moveRows.Add(new MoveRow(index,frame,parts[2],parts[5]));
            }
        }
        string report=Path.Combine(folder,"summary.json");
        string? rootDir=FindProjectRoot();
        _historicalReferenceActive=rootDir is not null && _moveRows.Count==41 &&
            string.Equals(Path.GetFullPath(folder),
                Path.GetFullPath(Path.Combine(rootDir,"results","verified_historical")),
                StringComparison.OrdinalIgnoreCase) &&
            FileSha256(moves)==KnownHistoricalMovesSha256;
        _fullDemoReferenceActive=rootDir is not null && _moveRows.Count==41 &&
            string.Equals(Path.GetFullPath(folder),
                Path.GetFullPath(Path.Combine(rootDir,"results","full_game_demo")),
                StringComparison.OrdinalIgnoreCase) &&
            FileSha256(moves)==KnownHistoricalMovesSha256;
        _resultsVideoPath=null;
        if (File.Exists(report))
        {
            using var doc=JsonDocument.Parse(File.ReadAllText(report));
            var data=doc.RootElement;
            string Suggestions(string key) => data.TryGetProperty(key,out var array) ?
                string.Join(" · ",array.EnumerateArray().Select(x=>x.GetProperty("position").GetString())) : "—";
            BlackSuggestion.Text=Tr("● 黑棋：","● Black: ")+Suggestions("black_suggestions");
            WhiteSuggestion.Text=Tr("○ 白棋：","○ White: ")+Suggestions("white_suggestions");
            string winner=data.TryGetProperty("winner",out var w) && w.ValueKind==JsonValueKind.String
                ? w.GetString()! : Tr("未分勝負","None");
            string movesCount=data.TryGetProperty("moves",out var mc) ? mc.ToString() : _moveRows.Count.ToString();
            string frames=data.TryGetProperty("frames_analyzed",out var fc) ? fc.ToString() : "—";
            SummaryText.Text=Tr($"總計 {movesCount} 手 · 已分析 {frames} 幀 · 勝方：{winner}",
                                $"Moves: {movesCount} · Analyzed: {frames} · Winner: {winner}");
            // Detection confirmation occurs after several sampled frames. Preserve the
            // actual detection Frame in the CSV, while separately compensating its
            // display timestamp. This is approximate for uncontrolled real footage.
            int visualDelay=data.TryGetProperty("confirmation_delay_frames",out var delayValue) &&
                delayValue.ValueKind==JsonValueKind.Number ? Math.Clamp(delayValue.GetInt32(),0,120) : 0;
            if (visualDelay>0)
            {
                for (int i=0;i<_moveRows.Count;i++)
                    _moveRows[i]=_moveRows[i] with
                    { VisualFrame=Math.Max(1,_moveRows[i].Frame-visualDelay) };
            }
            if (data.TryGetProperty("wall_seconds",out var elapsed) && elapsed.ValueKind==JsonValueKind.Number &&
                elapsed.TryGetDouble(out double seconds))
                SummaryText.Text += Tr($" · 引擎內部處理：{seconds:F2} 秒", $" · Engine pipeline: {seconds:F2}s");
            if (data.TryGetProperty("recognition_seconds",out var recognition) && recognition.ValueKind==JsonValueKind.Number &&
                recognition.TryGetDouble(out double recognitionSeconds))
                SummaryText.Text += Tr($" · 核心辨識：{recognitionSeconds:F2} 秒", $" · Recognition core: {recognitionSeconds:F2}s");
            if (data.TryGetProperty("input",out var input) && input.ValueKind==JsonValueKind.String)
            {
                string? source=input.GetString();
                // Historical summaries use a descriptive placeholder, not an actual video path.
                if (!string.IsNullOrWhiteSpace(source) && Path.IsPathFullyQualified(source))
                    _resultsVideoPath=Path.GetFullPath(source);
            }
        }
        else SummaryText.Text=Tr($"已載入 {_moveRows.Count} 手（無 summary.json）",
                                 $"Loaded {_moveRows.Count} moves (no summary.json)");
        MoveSlider.IsEnabled=_moveRows.Count>0;
        MoveSlider.Maximum=Math.Max(1,_moveRows.Count);
        PreviousMoveButton.IsEnabled=_moveRows.Count>0;
        NextMoveButton.IsEnabled=_moveRows.Count>0;
        MovePlayButton.IsEnabled=_moveRows.Count>0;
        SetMoveStep(_moveRows.Count,seekMatchingVideo:false);
        RefreshVideoLink();
        if (_frameReader is null)
        {
            string preview=Path.Combine(folder,"last_frame.png");
            if (File.Exists(preview)) PreviewImage.Source=LoadPng(preview);
        }
    }

    private void ResetTimeline()
    {
        _moveRows.Clear();
        _selectedStep=0;
        MoveSlider.Maximum=1;
        MoveSlider.Value=0;
        MoveSlider.IsEnabled=false;
        PreviousMoveButton.IsEnabled=false;
        NextMoveButton.IsEnabled=false;
        MovePlayButton.IsEnabled=false;
        CurrentMoveLabel.Text="0 / 0";
        _resultsVideoPath=null;
        _historicalReferenceActive=false;
        _fullDemoReferenceActive=false;
        _videoMatchesMoves=false;
    }

    // Recommendations are evaluated for the ACTUALLY SELECTED replay step.
    // Never present future-board suggestions while rewound to an earlier move.
    // Historical/synthetic recorded moves are replay data, not newly inferred detections.
    private void UpdatePredictionPanel()
    {
        if (DisplayModeBox.SelectedIndex==0)
        {
            RecommendationsTitle.Text=Tr("模式一：純辨識", "Mode 1: Recognition only");
            BlackSuggestion.Text=Tr("綠框＝已確認／已記錄的棋子", "Green boxes = confirmed/recorded stones");
            WhiteSuggestion.Text=Tr("本模式不顯示推薦落點。", "Predictions hidden in this mode.");
            return;
        }
        var board=new GomokuVision.Board();
        for (int i=0;i<Math.Min(_selectedStep,_moveRows.Count);i++)
        {
            var move=_moveRows[i];
            string pos=move.Position.Trim().ToUpperInvariant();
            if (pos.Length<2 || pos[0]<'A' || pos[0]>'O' ||
                !int.TryParse(pos.Substring(1),NumberStyles.None,CultureInfo.InvariantCulture,out int row) ||
                row<1 || row>15) continue;
            int color=move.Color.Equals("Black",StringComparison.OrdinalIgnoreCase) ? 1 : 2;
            int col=pos[0]-'A';
            if (board.Cells[row-1,col]==0) board.Place(move.Frame,color,row-1,col);
        }
        var winner=board.Winner();
        if (winner is not null)
        {
            RecommendationsTitle.Text=Tr("對局結束 · 不再預測", "Game finished · no next move");
            BlackSuggestion.Text=Tr("已形成五連線。","Five in a row detected.");
            WhiteSuggestion.Text="";
            return;
        }
        RecommendationsTitle.Text=Tr("模式二：推薦落點 Top 5", "Mode 2: Top-5 candidate moves");
        if (board.Moves.Count==0)
        {
            BlackSuggestion.Text=Tr("尚無落子。","No moves yet.");
            WhiteSuggestion.Text="";
            return;
        }
        BlackSuggestion.Text=Tr("● 黑棋：","● Black: ")+string.Join(" · ",board.Suggestions(1,5).Select(x=>x.Position));
        WhiteSuggestion.Text=Tr("○ 白棋：","○ White: ")+string.Join(" · ",board.Suggestions(2,5).Select(x=>x.Position));
    }

    private void SetMoveStep(int count,bool seekMatchingVideo)
    {
        count=Math.Clamp(count,0,_moveRows.Count);
        _selectedStep=count;
        _selectionUpdating=true;
        try
        {
            MoveSlider.Value=count;
            MovesGrid.SelectedIndex=count>0 ? count-1 : -1;
            if (count>0) MovesGrid.ScrollIntoView(_moveRows[count-1]);
        }
        finally { _selectionUpdating=false; }
        try
        {
            BoardImage.Source=ReplayBoardRenderer.Draw(_moveRows,count);
            UpdatePredictionPanel();
        }
        catch(Exception ex)
        {
            StopMovePlayback();
            ShowError(Tr("棋譜內容無法重播：","Cannot replay moves: ")+ex.Message);
            return;
        }
        if (count==0) CurrentMoveLabel.Text=$"0 / {_moveRows.Count}";
        else
        {
            var move=_moveRows[count-1];
            CurrentMoveLabel.Text=$"{count}/{_moveRows.Count} · {move.Color} {move.Position} · F{move.Frame}";
            if (seekMatchingVideo && _videoMatchesMoves && _frameReader is not null)
                FrameSlider.Value=Math.Clamp(move.TimelineFrame-1,0,_frameReader.FrameCount-1);
        }
    }

    private void MoveSlider_ValueChanged(object sender,RoutedPropertyChangedEventArgs<double> e)
    {
        if (!IsLoaded || _selectionUpdating) return;
        SetMoveStep((int)Math.Round(e.NewValue),seekMatchingVideo:true);
    }

    private void MovesGrid_SelectionChanged(object sender,System.Windows.Controls.SelectionChangedEventArgs e)
    {
        if (!IsLoaded || _running || _selectionUpdating || MovesGrid.SelectedIndex<0) return;
        SetMoveStep(MovesGrid.SelectedIndex+1,seekMatchingVideo:true);
    }

    private void PreviousMove_Click(object sender,RoutedEventArgs e)
    {
        StopMovePlayback();
        StopVideoPlayback();
        SetMoveStep(_selectedStep-1,seekMatchingVideo:true);
    }

    private void NextMove_Click(object sender,RoutedEventArgs e)
    {
        StopMovePlayback();
        StopVideoPlayback();
        SetMoveStep(_selectedStep+1,seekMatchingVideo:true);
    }

    private void MovePlay_Click(object sender,RoutedEventArgs e)
    {
        if (_running) return; // Do not play finalized timeline while detector mutates it.
        if (_videoMatchesMoves && _frameReader is not null)
        {
            VideoPlay_Click(sender,e); // ONE shared video+board clock; no competing timers.
            return;
        }
        if (_moveTimer.IsEnabled) { StopMovePlayback(); return; }
        if (_moveRows.Count==0) return;
        // Without the exact paired footage there is no frame-accurate video synchronization.
        if (_frameReader is not null)
        {
            StatusText.Text=Tr("影片與棋譜來源不同，請先載入配對的結果。",
                               "Video and moves are not paired; load matching results first.");
            return;
        }
        if (_selectedStep==_moveRows.Count) SetMoveStep(0,seekMatchingVideo:true);
        _moveTimer.Start();
        MovePlayButton.Content=Tr("暫停棋譜","Pause moves");
    }

    private void StopMovePlayback()
    {
        _moveTimer.Stop();
        MovePlayButton.Content=Tr("播放棋譜","Play moves");
    }

    private async void LoadVideoPreview_Click(object sender,RoutedEventArgs e)
    {
        StopVideoPlayback();
        if (!File.Exists(VideoPath.Text)) { ShowError(Tr("請先選擇影片。","Select a video first.")); return; }
        LoadVideoButton.IsEnabled=false;
        try
        {
            // Establish a fresh decoder; the previous reader is never used for new paths.
            string selectedPath=VideoPath.Text; // Read WPF control only on the UI thread.
            bool matchesVerifiedHistorical=false;
            bool matchesBundledFullDemo=false;
            // A pre-encoded 60fps double-speed video must be played at 1x.
            // A 30fps authored source plays at 2x. This holds for all engines,
            // even after the source is recognized again and reference flags reset.
            string fingerprint=await Task.Run(() => FileSha256(selectedPath));
            if (fingerprint==BundledSyncedTwoXVideoSha256)
                SpeedBox.SelectedIndex=0;
            else if (fingerprint==BundledFullGameVideoSha256)
                SpeedBox.SelectedIndex=1;
            matchesVerifiedHistorical=_historicalReferenceActive &&
                fingerprint==KnownHistoricalVideoSha256;
            matchesBundledFullDemo=_fullDemoReferenceActive &&
                (fingerprint==BundledFullGameVideoSha256 ||
                 fingerprint==BundledSyncedTwoXVideoSha256);
            var reader=await Task.Run(() => new VideoFrameReader(selectedPath));
            CloseVideoReader();
            _frameReader=reader;
            if (_historicalReferenceActive || _fullDemoReferenceActive)
                _resultsVideoPath=(matchesVerifiedHistorical || matchesBundledFullDemo)
                    ? Path.GetFullPath(selectedPath) : null;
            _renderedFrame=-1;
            _requestedFrame=0;
            FrameSlider.Maximum=Math.Max(1,reader.FrameCount-1);
            FrameSlider.Value=0;
            FrameSlider.IsEnabled=true;
            VideoPlayButton.IsEnabled=true;
            FrameLabel.Text=$"1/{reader.FrameCount} · 0.00s";
            RefreshVideoLink();
            if (_historicalReferenceActive || _fullDemoReferenceActive)
                VideoLinkNote.Text=(matchesVerifiedHistorical || matchesBundledFullDemo)
                    ? Tr("影片 SHA-256 配對成功：兩個播放按鈕共用時間軸，2 倍速同步棋盤／影片。",
                         "Video SHA-256 matched: both play buttons drive one timeline, 2x sync.")
                    : Tr("影片雜湊不符棋譜，禁止錯誤連動。",
                         "Video hash does not match the move sequence; sync disabled.");
            // If paired, keep the preview at the same move as the final board,
            // instead of displaying frame 1 beside a completed 41-stone board.
            if (_videoMatchesMoves && _fullDemoReferenceActive)
            {
                // New synthetic full game opens at the beginning, ready for 2x synchronized play.
                SetMoveStep(0, seekMatchingVideo:false);
                FrameSlider.Value=0;
            }
            else if (_videoMatchesMoves && _moveRows.Count > 0)
                FrameSlider.Value=reader.FrameCount-1;
            RequestPreviewFrame((int)FrameSlider.Value);
        }
        catch (Exception ex) { ShowError(ex.Message); }
        finally { LoadVideoButton.IsEnabled=true; }
    }

    private void RefreshVideoLink()
    {
        _videoMatchesMoves=_frameReader is not null && _resultsVideoPath is not null &&
            string.Equals(_frameReader.Path,_resultsVideoPath,StringComparison.OrdinalIgnoreCase);
        VideoLinkNote.Text=_videoMatchesMoves
            ? Tr("已驗證影片與棋譜相符；影片與棋盤共用時間軸。",
                 "Verified matching video and moves: one shared playback clock.")
            : Tr("影片與棋譜未配對；可分別預覽，但不會將示範影格冒充歷史影格。",
                 "Video and results are not linked. Frames are preview-only, not historical footage.");
    }

    private void FrameSlider_ValueChanged(object sender,RoutedPropertyChangedEventArgs<double> e)
    {
        if (!IsLoaded || _frameReader is null) return;
        if (!_clockSeeking && _videoTimer.IsEnabled) StopVideoPlayback();
        int frame=Math.Clamp((int)Math.Round(e.NewValue),0,_frameReader.FrameCount-1);
        FrameLabel.Text=$"{frame+1}/{_frameReader.FrameCount} · {(frame/_frameReader.Fps):F2}s";
        if (_videoMatchesMoves && _moveRows.Count>0)
        {
            int count=_moveRows.TakeWhile(m => m.TimelineFrame<=frame+1).Count();
            if (count!=_selectedStep) SetMoveStep(count,seekMatchingVideo:false);
        }
        RequestPreviewFrame(frame);
    }

    private void RequestPreviewFrame(int frame)
    {
        _requestedFrame=frame;
        if (!_decodeBusy) _=DecodePreviewLoopAsync();
    }

    private async Task DecodePreviewLoopAsync()
    {
        _decodeBusy=true;
        bool failed=false;
        try
        {
            while (_frameReader is not null)
            {
                var reader=_frameReader;
                int frame=_requestedFrame;
                byte[] png=await Task.Run(() => reader.ReadPng(frame));
                if (!ReferenceEquals(reader,_frameReader)) break;
                if (frame!=_requestedFrame) continue; // Drop stale frames from fast slider movement.
                using var memory=new MemoryStream(png);
                var image=new BitmapImage();
                image.BeginInit();
                image.StreamSource=memory;
                image.CacheOption=BitmapCacheOption.OnLoad;
                image.EndInit();
                image.Freeze();
                // Recreate historical recognition rectangles from the confirmed,
                // timestamped move list. This is an overlay, not fresh NCC evidence.
                // It uses calibrated source-frame coordinates, not arbitrary canvas pixels.
                if (_videoMatchesMoves && _moveRows.Count>0)
                {
                    try
                    {
                        var cal=PreviewCalibration();
                        int n=_moveRows.TakeWhile(m=>m.TimelineFrame<=frame+1).Count();
                        PreviewImage.Source=cal is null ? image : RecognitionOverlayRenderer.Draw(
                            image,_moveRows,n,cal,
                            DisplayModeBox.SelectedIndex==0 ? "recognition" : "recognition_prediction");
                    }
                    catch (Exception ex)
                    {
                        PreviewImage.Source=image;
                        StatusText.Text=Tr("綠框預覽無法繪製：","Overlay render failed: ")+ex.Message;
                    }
                }
                else PreviewImage.Source=image;
                _renderedFrame=frame;
                break;
            }
        }
        catch (ObjectDisposedException) { failed=true; /* Switching videos disposes the old capture. */ }
        catch (Exception ex)
        {
            failed=true;
            StatusText.Text=Tr("無法讀取預覽影格：","Preview decode failed: ")+ex.Message;
        }
        finally
        {
            _decodeBusy=false;
            if (!failed && _frameReader is not null && _requestedFrame!=_renderedFrame && _frameReader.FrameCount>0)
                _=DecodePreviewLoopAsync();
        }
    }

    private GomokuVision.Calibration? PreviewCalibration()
    {
        var file=CalibrationPath.Text;
        if (!File.Exists(file)) return null;
        string full=Path.GetFullPath(file);
        if (_overlayCalibration is null || !string.Equals(_overlayCalibrationPath,full,StringComparison.OrdinalIgnoreCase))
        {
            _overlayCalibration=GomokuVision.Calibration.Load(full);
            _overlayCalibrationPath=full;
        }
        return _overlayCalibration;
    }

    private void DisplayModeBox_SelectionChanged(object sender,
        System.Windows.Controls.SelectionChangedEventArgs e)
    {
        if (!IsLoaded) return;
        UpdatePredictionPanel();
        if (_frameReader is null || _running) return;
        // Annotation mode affects rendering, not recognition or stored moves.
        RequestPreviewFrame(Math.Clamp((int)FrameSlider.Value,0,_frameReader.FrameCount-1));
    }

    private double PlaybackSpeed() => SpeedBox.SelectedIndex switch
    {
        0 => 1.0,
        2 => 4.0,
        _ => 2.0
    };

    private void SpeedBox_SelectionChanged(object sender,System.Windows.Controls.SelectionChangedEventArgs e)
    {
        if (!IsLoaded || !_videoTimer.IsEnabled) return;
        // Rebase the same stopwatch at the currently visible frame on speed changes.
        _playbackStartFrame=(int)FrameSlider.Value;
        _playbackClock.Restart();
    }

    private void VideoPlay_Click(object sender,RoutedEventArgs e)
    {
        if (_running) return; // An unfinished live result must not start a second clock.
        if (_videoTimer.IsEnabled) { StopVideoPlayback(); return; }
        if (_frameReader is null) return;
        StopMovePlayback();
        if ((int)FrameSlider.Value >= _frameReader.FrameCount - 1)
            FrameSlider.Value=0;
        _playbackStartFrame=(int)FrameSlider.Value;
        _playbackClock.Restart();
        _videoTimer.Start();
        VideoPlayButton.Content=Tr("暫停影片","Pause video");
        if (_videoMatchesMoves)
            MovePlayButton.Content=Tr("暫停同步播放","Pause sync");
    }

    private void StopVideoPlayback()
    {
        _videoTimer.Stop();
        _playbackClock.Stop();
        VideoPlayButton.Content=Tr("播放影片","Play video");
        if (!_moveTimer.IsEnabled)
            MovePlayButton.Content=Tr("同步播放","Sync play");
    }

    private void CloseVideoReader()
    {
        StopVideoPlayback();
        FrameSlider.IsEnabled=false;
        VideoPlayButton.IsEnabled=false;
        _frameReader?.Dispose();
        _frameReader=null;
        PreviewImage.Source=null;
        FrameLabel.Text=Tr("未載入影片","No video loaded");
        _videoMatchesMoves=false;
        _renderedFrame=-1;
        RefreshVideoLink();
    }

    private void Cancel_Click(object sender,RoutedEventArgs e)
    {
        if (_benchmarkRunning && !string.IsNullOrEmpty(_benchmarkCancelFlag))
        {
            File.WriteAllText(_benchmarkCancelFlag,"cancel");
            CancelButton.IsEnabled=false;
            StatusText.Text=Tr("將在目前測試結束後取消剩餘測試…","Canceling after current case…");
            return;
        }
        if ((_pythonRunning || _matlabRunning) && _pythonCancelFile is not null)
            File.WriteAllText(_pythonCancelFile,"cancel");
        else _cts?.Cancel();
        CancelButton.IsEnabled=false;
        StatusText.Text=Tr("正在安全取消…","Canceling safely…");
    }

    private void LoadCached_Click(object sender,RoutedEventArgs e)
    {
        var dialog=new OpenFolderDialog {Title=Tr("選擇已保存分析結果的資料夾","Choose an existing results folder")};
        string? root=FindProjectRoot();
        if (root is not null)
        {
            var cached=Path.Combine(root,"results","verified_historical");
            if (Directory.Exists(cached)) dialog.InitialDirectory=cached;
        }
        if (dialog.ShowDialog(this)!=true) return;
        string folder=dialog.FolderName;
        if (!File.Exists(Path.Combine(folder,"summary.json")) ||
            !File.Exists(Path.Combine(folder,"moves.csv")))
        {
            ShowError(Tr("選取的資料夾沒有 summary.json 與 moves.csv。",
                         "The selected folder must contain summary.json and moves.csv."));
            return;
        }
        try
        {
            LoadResults(folder);
            _lastOutput=folder;
            StatusText.Text=Tr("已載入先前結果，不需重新辨識。",
                               "Previous results loaded without rerunning the detector.");
        }
        catch(Exception ex) {ShowError(ex.Message);}
    }

    private void OpenResults_Click(object sender,RoutedEventArgs e)
    {
        string folder=Directory.Exists(_lastOutput) ? _lastOutput : OutputPath.Text;
        if (!Directory.Exists(folder)) { ShowError(Tr("找不到結果資料夾。","Output folder does not exist.")); return; }
        System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(folder){UseShellExecute=true});
    }

    private void ShowError(string message) => MessageBox.Show(this,message,Tr("錯誤","Error"),MessageBoxButton.OK,MessageBoxImage.Error);

    private void LanguageBox_SelectionChanged(object sender,System.Windows.Controls.SelectionChangedEventArgs e)
    {
        if (IsLoaded) ApplyLanguage();
    }

    private void ApplyLanguage()
    {
        Title=Tr("五子棋辨識與預測 · 進階版","Gomoku Vision · Advanced");
        Heading.Text=Tr("五子棋影像辨識與預測","Gomoku Vision & Prediction");
        Subtitle.Text=Tr("MATLAB · Python · C#  |  Windows 原生 C# 分析介面",
                         "MATLAB · Python · C#  |  Native C# desktop analyzer");
        LanguageLabel.Text=Tr("介面語言","UI Language");
        ImportOriginalButton.ToolTip=Tr("僅匯入本機資料夾，不上傳私人影片。",
                                        "Import from a local folder only; private footage is never uploaded.");
        QuickGateButton.ToolTip=Tr("僅測試自製合成影片，不重新分析原始影片。",
                                   "Tests self-authored synthetic footage only; does not process historical footage.");
        AllResultsButton.ToolTip=Tr("每勾選一種倍率重跑 12 組辨識；倍率不會使演算法加速。",
                                    "12 independent analysis cases per selected speed; playback speed does not accelerate recognition.");
        SpeedBox.ToolTip=Tr("影片與棋盤共用的播放速度", "Shared video / board playback speed");
        InputTitle.Text=Tr("開始辨識","Recognition");
        BenchmarkExpander.Header=Tr("批次比較 · CSV 匯出","Batch benchmark · CSV export");
        AdvancedExpander.Header=Tr("更多設定 · 校準 / 模板 / 輸出","More settings · Calibration / templates / output");
        BenchmarkSpeedLabel.Text=Tr("選擇播放倍率（可複選）","Playback speeds (select multiple)");
        VideoLabel.Text=Tr("影片檔","Video file");
        CalibrationLabel.Text=Tr("棋盤校準 CSV（225 點）","Board calibration CSV (225 points)");
        BlackLabel.Text=Tr("黑棋模板 PNG","Black-stone template PNG");
        WhiteLabel.Text=Tr("白棋模板 PNG","White-stone template PNG");
        OutputLabel.Text=Tr("結果輸出資料夾","Output directory");
        EngineLabel.Text=Tr("辨識引擎","Recognition engine");
        RoiModeLabel.Text=Tr("ROI 搜尋模式（下次辨識時生效）","ROI strategy (next analysis run)");
        DisplayModeLabel.Text=Tr("原版顯示模式（可即時切換）","Legacy display mode (switch anytime)");
        ((System.Windows.Controls.ComboBoxItem)RoiModeBox.Items[0]).Content=Tr("黑白分離 ROI（各自預篩）","Separate black/white ROI gates");
        ((System.Windows.Controls.ComboBoxItem)RoiModeBox.Items[1]).Content=Tr("共用 ROI（共同候選區）","Shared candidate ROI");
        ((System.Windows.Controls.ComboBoxItem)DisplayModeBox.Items[0]).Content=Tr("模式一：純辨識（綠框）","Mode 1: Recognition (green boxes)");
        ((System.Windows.Controls.ComboBoxItem)DisplayModeBox.Items[1]).Content=Tr("模式二：辨識＋預測（綠框／建議圈）","Mode 2: Recognition + prediction");
        GreenBoxNote.Text=Tr("綠框＝已確認棋子；建議圈是策略推薦，不代表已落子。",
                              "Green boxes = confirmed moves; circles = suggested, not detected stones.");
        SettingsTitle.Text=Tr("辨識設定","Recognition settings");
        EveryLabel.Text=Tr("取樣間隔（幀）","Sample every N frames");
        FullLabel.Text=Tr("全盤掃描週期","Full scan every N analyses");
        ConfirmLabel.Text=Tr("確認次數","Confirmations");
        ScaleLabel.Text=Tr("影像比例","Image scale");
        BlackThresholdLabel.Text=Tr("黑棋 NCC 門檻","Black NCC threshold");
        WhiteThresholdLabel.Text=Tr("白棋 NCC 門檻","White NCC threshold");
        LimitLabel.Text=Tr("需固定鏡頭與校準點；棋步為啟發式建議，並非神經網路模型。",
                           "Fixed camera and calibration required; moves use heuristics, not a trained AI model.");
        PreviewTitle.Text=Tr("影片分析與影格預覽","Analysis and frame preview");
        LoadVideoButton.Content=Tr("載入影片預覽","Load video preview");
        RefreshVideoLink();
        PreviewCaption.Text=Tr("合成影片與棋盤同步預覽","Synchronized video and board preview");
        MoveTitle.Text=Tr("落子紀錄（點選定位）","Move history (select to navigate)");
        BoardTitle.Text=Tr("棋盤逐手重播","Move-by-move board");
        PreviousMoveButton.Content=Tr("上一手","Previous");
        NextMoveButton.Content=Tr("下一手","Next");
        RecommendationsTitle.Text=Tr("推薦落點 Top 5","Top-5 candidate moves");
        CalibrateButton.Content=Tr("從影片手動點選四角校準","Calibrate by clicking four corners");
        foreach (var b in new[]{VideoPick,CalibrationPick,BlackPick,WhitePick,OutputPick})
            b.Content=Tr("選擇","Browse");
        ImportOriginalButton.Content=Tr("匯入原始專題資料夾（本機私人影片）",
                                         "Import original project folder (local only)");
        InputSourceNote.Text=_originalDataSelected
            ? Tr("已選擇本機原始影片（不會上傳），準備顯示 41 手歷史棋譜。",
                 "Local original footage selected (not uploaded); loading 41 saved moves.")
            : Tr("預設是 961 幀、41 手自製合成影片；按兩個播放鍵都會同步棋盤。",
                 "Default: self-authored 961-frame, 41-move demo; both play buttons synchronize.");
        LoadCachedButton.Content=Tr("開啟已保存的結果（免重跑）","Open saved results (no rerun)");
        QuickGateButton.Content=Tr("Python／C# 快速驗收（MATLAB 另測）","Python/C# gate (MATLAB separate)");
        AllResultsButton.Content=Tr("執行所選測試 · 匯出 CSV","Run selected cases · Export CSV");
        BenchmarkNote.Text=Tr("每選一種倍率都會重新辨識 12 組，最多 36 組。1×/2×/4× 不會加速運算；MATLAB 需授權。",
                              "12 recognition runs per selected playback speed (up to 36). Speed does not accelerate computation; MATLAB requires a license.");
        OpenResultsButton.Content=Tr("開啟結果資料夾","Open output folder");
        CancelButton.Content=Tr("取消分析","Cancel");
        RunButton.Content=Tr("開始辨識與預測","Analyze & Predict");
        if (_moveRows.Count>0) UpdatePredictionPanel();
        if (!_running && !_gateRunning) StatusText.Text=Tr("準備就緒","Ready");
    }
}

public sealed record MoveRow(int Index,int Frame,string Color,string Position,int VisualFrame=0)
{
    // The exported CSV Frame is the recognition confirmation frame. VisualFrame
    // approximates the stone's initial visible frame after confirmation latency.
    public int TimelineFrame => VisualFrame>0 ? VisualFrame : Frame;
}
