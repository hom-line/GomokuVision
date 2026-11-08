using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;

namespace GomokuVision.Desktop;

public partial class App : Application
{
    private static void WriteCrashLog(string source, Exception ex)
    {
        try
        {
            string baseDir = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string folder = Path.Combine(baseDir, "GomokuVision", "Logs");
            Directory.CreateDirectory(folder);
            File.AppendAllText(Path.Combine(folder, "desktop-errors.log"),
                $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {source}{Environment.NewLine}{ex}{Environment.NewLine}{Environment.NewLine}",
                Encoding.UTF8);
        }
        catch { /* Logging must never hide the original error. */ }
    }

    protected override void OnStartup(StartupEventArgs e)
    {
        DispatcherUnhandledException += OnDispatcherUnhandledException;
        AppDomain.CurrentDomain.UnhandledException += (_, args) =>
        {
            if (args.ExceptionObject is Exception ex) WriteCrashLog("AppDomain", ex);
        };
        TaskScheduler.UnobservedTaskException += (_, args) =>
        {
            WriteCrashLog("TaskScheduler", args.Exception);
            args.SetObserved();
        };
        try { base.OnStartup(e); }
        catch (Exception ex)
        {
            WriteCrashLog("Startup", ex);
            MessageBox.Show("GomokuVision startup failed. See %LOCALAPPDATA%\\GomokuVision\\Logs\\desktop-errors.log\n\n" + ex.Message,
                            "GomokuVision Startup Error", MessageBoxButton.OK, MessageBoxImage.Error);
            Shutdown(1);
        }
    }

    private void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
    {
        WriteCrashLog("Dispatcher", e.Exception);
        MessageBox.Show("GomokuVision encountered an error. Check %LOCALAPPDATA%\\GomokuVision\\Logs\\desktop-errors.log\n\n" + e.Exception.Message,
                        "GomokuVision Error", MessageBoxButton.OK, MessageBoxImage.Error);
        e.Handled = true;
        Shutdown(1);
    }
}
