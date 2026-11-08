# GomokuVision V0.3.4 — Windows 原生三引擎同步／MATLAB 修復驗收

## 目標與判定界線

本版修正 V0.3.3 使用者實測的四項缺陷：MATLAB `table` 欄名 `Row` 衝突、辨識時棋盤與棋步清單未即時更新、辨識確認幀與原始出現幀混用、同步影片最後一幀左側缺少勝利標註；同時優化 MATLAB 的空棋格預篩以降低不必要的 `normxcorr2` 呼叫。

請注意：此套件在非 Windows／非 MATLAB 的環境完成來源與 Python 測試，**並未**在此環境執行 WPF 編譯、Windows GUI 或 MATLAB 原生辨識。不能把 Python PASS 當成三引擎 PASS。

## 本機檢查（只解壓最新 V0.3.4）

1. 在**新的**資料夾解壓縮 ZIP，避免舊 `bin/obj` 與新版混用。
2. 執行 `scripts\Verify-WPF-Build-Windows.bat`，確認 `WPF_BUILD_PASS`；若失敗請保留 `%LOCALAPPDATA%\GomokuVision\Logs\wpf-build-*.log`。
3. 執行 `Launch-Desktop-Windows.bat`，可立即觀看自製 961 幀合成棋局。選 2×，按「播放影片」或「同步播放」應帶動同一時間軸。兩者不是獨立播放器。
4. 在**未重新辨識**的情況下檢查：F1/F24 是空棋盤；F25 為第 1 手 H8；F949 為第 41 手 L8、黑棋勝利；F961 仍保留完整 41 手與勝利連線。前後拖曳影片影格滑桿，棋盤及清單必須同步回復或前進。
5. 另外可直接用任意影片播放器開啟 `demo\full_game\full_game_synced_961_2x.mp4`。這是已編碼的 60 FPS、961 幀、16.02 秒 2× 影片，左／右兩側從 F949 到最後 F961 均應顯示最後一手及勝利連線；**在 WPF 選擇這支 60 FPS 影片時，播放器選 1×**，避免再倍速。

## 辨識期間逐手紀錄驗收（每種引擎獨立測）

1. 左側選擇 `C# / OpenCvSharp`，輸入維持 `demo\full_game\full_game_961.mp4`，校準及黑白模板同樣保持此資料夾；結果輸出選擇新資料夾。
2. 按「開始辨識與預測」。**在程序尚未完成時**，右側棋盤與中間棋譜記錄應逐手增加，不能到最後才一次產生 41 手。輸入影片使用固定 961 幀、每 6 幀取樣與連續 2 次確認。
3. 結束後驗證顯示 41 手、黑棋勝利，使用「播放影片」或「同步播放」，應使用來源影片 F1 至 F961 共用時鐘，最後完整棋局保留，不應停止在最後一次辨識確認影格。
4. Python 引擎同樣檢查以上各項。已確認之 Python 41 手結果與合成正解符合，但 **C# 的此版 Windows GUI 動態效果仍需本機實測**。
5. MATLAB 第三引擎同樣檢查：前幾幀啟動／MATLAB 初始化可能比 Python、C# 慢；實際分析後仍應逐手加入，並在完成時產生 `moves.csv`、`summary.json`、`board_final.png`，不應再出現 `Duplicate dimension and variable name: Row`。MATLAB 速度必須實際量測，不預先宣稱比其他引擎快。

**影格定義：** `moves.csv` 的 `Frame` 一律保存真正「辨識確認影格」（合成示範通常比實際出現晚 6 幀）；播放介面透過 `confirmation_delay_frames` 對顯示時刻做近似補償。未知場景的出現幀不保證精確，不能把這個補償視為演算法的人工標註正解。使用自製正解 `results\full_game_demo\moves.csv` 重播時，Frame 即是準確的來源出現幀。

## 一鍵驗收入口

- `Quick-Engine-Gate-Windows.bat`：原有 Python／C# **短 9 手**測試及 WPF Release 編譯。
- `Run-Three-Engine-QuickGate-Windows.bat`：Python + C# + 真正的 MATLAB 短 9 手驗收。需要本機具有 MATLAB 授權與 Image Processing Toolbox；未安裝應回報缺少而不是 PASS。
- `Run-MATLAB-961-Gate-Windows.bat`：以自製 961 幀完整棋局直接啟動 MATLAB，與 41 手正解比較，記錄完整 MATLAB 原生耗時與日誌。此項會重新做**合成影片**辨識，可能比 Python 慢，不會碰原始第三方影片。

已保存的歷史 41 手資料與原始私人影片不在這些 gate 中重新計算。要測真正第三方影片，需在有合法權利的本機環境另外選取檔案。

## 失敗時保留的證據

- `run-...\matlab-console.log`、`.wpf-progress.json`、`summary.json`、`moves.csv`；MATLAB 視窗若報錯請貼上完整堆疊。
- `%LOCALAPPDATA%\GomokuVision\Gates\quick-gate-*.json` 和 `.log`。
- 啟動／編譯日誌：`%LOCALAPPDATA%\GomokuVision\Logs\`。
- 請不要把原始第三方影片、學號、MATLAB 授權檔放上公開 GitHub。
