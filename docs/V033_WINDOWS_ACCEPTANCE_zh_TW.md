# GomokuVision V0.3.3 — Windows／MATLAB 驗收指引

## A. 先看完整同步影片（不須 WPF 或 MATLAB）

直接開啟 `demo/full_game/full_game_synced_961_2x.mp4`：961 幀、60 FPS、約 16.02 秒。左側影像與右側模擬棋盤應在 Frame 25 第 1 手、Frame 43 第 2 手、Frame 949 第 41 手同步更新，黑棋獲勝。

## B. WPF 共用時間軸（需要 .NET 10 SDK）

1. 解壓縮到**全新資料夾**，避免混用 V0.3.2 的 bin/obj；執行 `scripts/Verify-WPF-Build-Windows.bat`。預期 `WPF_BUILD_PASS`。
2. 執行 `Launch-Desktop-Windows.bat`；預設應顯示 **961 幀合成影片**和 41 手棋譜，影片時間軸顯示 1/961，棋盤空白。兩者都不是原始第三方影像。
3. 按「播放影片」或「同步播放」任一按鈕；另一個按鈕應同時切換成暫停狀態，棋盤與影片一起前進。預設 **2×**，約 16 秒完成。另一個按鈕可停止同一時間軸。
4. 在 Frame 24 時棋盤為 0 手；Frame 25 時應為 1 手 H8；Frame 43 時為 2 手；Frame 949 時為 41 手，出現勝利連線。
5. 暫停後拖動**影片**影格滑桿，右側棋盤應對應改變；點棋譜列表或上一手／下一手，影片應跳到該手影格；移至最後一手並重新按播放應從起點重新播放。
6. 速度選單 1×、2×、4× 有效，變更播放速度時不應跳回第一手。若改選 `full_game_synced_961_2x.mp4`，應驗證 SHA 後切為 1×（該影片已是 60 FPS 的 2 倍速成品）。
7. 選擇其他無關影片時不應把它的時間軸與目前 41 手誤配對。

## C. 三個獨立辨識引擎

Python/C#：用 `Quick-Engine-Gate-Windows.bat`，本腳本只跑原有 9 手短合成影片，最後應出現 `QUICK_ENGINE_GATE_PASS` 和 `WPF_BUILD_PASS`。**這仍然只是 Python/C#**，不是 MATLAB PASS。

MATLAB：需要 MATLAB 授權及 Image Processing Toolbox。若 `matlab.exe` 不在 PATH，在 PowerShell 先設 `$env:GOMOKUVISION_MATLAB_EXE = '實際安裝位置\bin\matlab.exe'`，再執行 `Run-MATLAB-Gate-Windows.bat`。應出現 `MATLAB_SELFTEST_PASS`、`MATLAB_ENGINE_COMPLETE`、`SYNTHETIC_ORACLE_PASS`、最後 `MATLAB_GATE_PASS`。若未安裝則回報 `MATLAB_GATE_NOT_INSTALLED`，不能標為成功。GUI 選 MATLAB 後按「開始辨識與預測」，同樣須產生 CSV、JSON、PNG、MP4。

注意：MATLAB 是獨立 NCC 辨識，實際效能和棋譜是否 9/9 需由已安裝 MATLAB 的 Windows 實機測試確認，不能因為 Python 成功就當作 MATLAB 成功。

## D. 維護與證據

若失敗：WPF 的 `wpf-build-*.log` 在 `%LOCALAPPDATA%\GomokuVision\Logs`，Python/C# `quick-gate-*.log` 在 `%LOCALAPPDATA%\GomokuVision\Gates`，MATLAB `matlab-gate.log` 在本次 MATLAB 測試輸出目錄。**不需要重新跑原始私人 961 幀影片**。

歷史 41 手原始程式輸出的 CSV 仍是回歸參考，不能宣稱真實影片 100% 辨識準確率。使用者專題中的第三方影片或模板不會隨此 ZIP 散布。
