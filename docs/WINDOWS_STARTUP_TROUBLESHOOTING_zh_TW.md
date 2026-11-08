# Windows 啟動疑難排解（V0.2.3）

## 先確認狀態

`Launch-Desktop-Windows.bat` 會嘗試建置並啟動 **真正的 C# WPF**。成功時不會重新分析影片；GUI 將自動讀取套件內 `results/verified_historical/`，顯示歷史已驗證的 41 手棋譜。可以按「開啟已保存的結果（免重跑）」讀取其他輸出資料夾。

本版本新增 Windows PowerShell 診斷腳本，可記錄 .NET SDK 偵測、WPF 建置輸出及啟動狀態。若 WPF 啟動失敗，BAT **會停留顯示錯誤**，並開啟不依賴 .NET 的 `docs/VerifiedResults.html`（只讀結果頁），不會把 HTML 網頁誤稱為 WPF 已啟動。

## 不需要再次跑原始影片

若只要看已驗證的 41 手棋譜，直接雙擊 `scripts/Show-Verified-Results-Windows.bat`，或開啟 `docs/VerifiedResults.html`。該頁是純本機 HTML，完全離線，不需 .NET、Python 或網路。

## 想使用原生 WPF 介面

1. Windows 10／11 x64 上需要 **.NET 10 SDK x64**，而不只是 .NET 10 Runtime。第一次建置如套件未快取，需要能從 NuGet 取得 OpenCvSharp4 與 OpenCvSharp4.runtime.win 相依項。
2. 解壓縮整個 ZIP 到可寫入的資料夾，不要直接在壓縮檔預覽器中雙擊 BAT。路徑有空白或中文時腳本也應正常運作。
3. 雙擊 `scripts/Launch-Desktop-Windows.bat`。這只執行 WPF 建置與開啟，不會自動跑影片辨識。
4. 若建置失敗，視窗會顯示錯誤並等待按鍵；請打開 `%LOCALAPPDATA%\GomokuVision\Logs\launch-*.log` 檢查。
5. 若 WPF 啟動後立即崩潰，請查看 `%LOCALAPPDATA%\GomokuVision\Logs\desktop-errors.log`。
6. 已成功建置後，可用 `scripts/Launch-Desktop-Windows.bat -NoBuild` 略過重建，直接開啟現有 EXE。

## 常見情況

| 訊息 | 說明與處理 |
|---|---|
| Missing .NET 10 SDK / dotnet command | 未安裝 SDK 或 PATH 找不到。安裝 .NET 10 x64 SDK；純結果展示可直接使用 HTML。 |
| .NET 10 SDK was not found | 可能只安裝 Runtime，或 SDK 是較舊大版本。 |
| WPF build failed | 從 `launch-*.log` 查明 NuGet 套件下載、C# 編譯或 WPF XAML 錯誤。 |
| WPF exited within 4 seconds | 程式初始化就結束，查詢 `desktop-errors.log` 及 Windows 事件檢視器。 |
| Cannot load native OpenCV DLL | 確認 Windows x64 環境與 Visual C++ Redistributable 及套件相依是否正確。 |
| Python not found | 只影響 GUI 內的 Python 引擎；使用 C# 引擎或離線結果頁不需 Python。 |

## 已執行與尚未執行的測試

本回合在 Linux 測試環境實際執行：Python `pytest` 14/14、完整歷史影片分析及 41/41 舊 CSV 逐手一致。沒有 Windows/.NET SDK，因此 **C# 編譯、WPF 啟動、雙引擎執行結果一致性沒有實測通過**；不應把 Python 結果誤當作 C# 的測試資料。

## V0.2.2 修正 NU1701

若 Windows 顯示 `error NU1701`，且指出 `OpenCvSharp4.WpfExtensions 4.13.0.20260627` 與 `net10.0` 不相容，代表可能使用舊版的 C# 專案。

1. 解壓縮 **完整 V0.2.2 ZIP** 到新的資料夾（不要混用舊版 `obj/` 或 `bin/`）。
2. 檢查 `csharp\GomokuVision\GomokuVision.csproj` 是否已改為 `OpenCvSharp4` + `OpenCvSharp4.runtime.win`（不再引用 `OpenCvSharp4.Windows`）。
3. 雙擊 `scripts\Verify-WPF-Build-Windows.bat`，只做 NuGet 還原與 Release 編譯，不重新分析影片。
4. 如顯示 `WPF_BUILD_PASS`，再雙擊 `scripts\Launch-Desktop-Windows.bat`。
5. 若改報 CSxxxx / MCxxxx / 其他 NUxxxx，保存 `%LOCALAPPDATA%\GomokuVision\Logs\wpf-build-*.log`；下一步需按真正的編譯錯誤修正，不能把 HTML 視為 WPF 通過。

**不要**為掩蓋錯誤而設定 `NoWarn=NU1701` 或更改成 .NET Framework 4.x；那只會隱藏套件相容風險。

## V0.2.3：CS1001（VisionDetector.cs 第 196 行）

如果 V0.2.2 的 log 顯示 `error CS1001` at `(196,35)` and `(196,39)`，代表 `double[] scores = [-1.,-1.];` 在 C# 不合法；V0.2.3 已更正為 `double[] scores = new double[] { -1.0, -1.0 };`。不需要重跑任何影片，使用 `Verify-WPF-Build-Windows.bat` 即可重新檢查 WPF Release 編譯。若新錯誤出現，請提供新的 log，不能認定所有 WPF 問題已解決。
