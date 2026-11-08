# V0.3.5 Windows GUI / MATLAB / Python 驗收表

## 目的

只驗證 V0.3.4 已定位的兩項檔案鎖錯誤及三引擎即時顯示：
- Python `last_frame.tmp.png -> last_frame.png`：`WinError 5 PermissionError`。
- MATLAB `movefile(tmpPreview,lastPreview,'f')`：檔案正在由另一程式使用。

## 操作

1. 以**新資料夾**解壓 V0.3.5，不覆蓋先前版本。
2. 在 Windows 10 / .NET 10 SDK 執行 `scripts/Verify-WPF-Build-Windows.bat`，先確認 `WPF_BUILD_PASS`。
3. 執行 `Launch-Desktop-Windows.bat`，保持預設的自製完整棋局 `demo/full_game/full_game_961.mp4`，並使用對應 `checkerboard_points.csv`、`black.png`、`white.png`。
4. Python / OpenCV：選取空資料夾 A 並開始辨識。檢查在 **前 41 手辨識期間**有持續增加落子，而不是結束時才一次出現；結束 `41 手 / 161 分析幀 / Black`，`preview_frames/<ID>/frame_*.png` 多個檔案，最後包含 F961。
5. MATLAB：選取空資料夾 B，再執行辨識。確認不再出現 `movefile` 檔案鎖錯誤；應持續回報進度。Matlab 原生 41 手結果**須實際確認**，不以 Python 的 41/41 代替。
6. C#：選取空資料夾 C，重跑合成影片，確認先前已通過的路徑未退步，進度、GUI 棋盤與輸出皆正常。
7. 如任何引擎中途失敗，請保存 Windows 錯誤畫面、結果資料夾 `summary.json`（若有）、`.wpf-progress.json`、MATLAB 的 `matlab-console.log`（若有）。

## 通過標準

- WPF `WPF_BUILD_PASS`。
- Python／MATLAB／C# **各自**完整結束且有 `moves.csv`、`summary.json`、`last_frame.png`。
- 三引擎在辨識過程中棋步與棋盤**增量更新**，沒有檔案鎖例外。
- 三個 `moves.csv` 與自製合成棋譜正解皆為 41 手、棋色座標一致、勝者 Black。影格確認時間可有取樣延遲，應另行檢查。
- 播放時間軸可定位至 F961，左右 2× 同步影片仍顯示最後勝利線。

本版未在這個 Linux 環境實測 MATLAB 或 WPF Windows GUI，請勿以來源合約測試冒充該項 PASS。
