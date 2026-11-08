> **V0.2.6 Windows Gate 狀態：待實機複驗。** V0.2.5 日誌已證明 Python 22/22、C# Release 編譯通過；C# 戰術自測當時因錯誤的預期棋步（D8/I8）失敗。V0.2.6 修正預期 C8/H8 並加入勝負判定防回歸；尚不能視為 Windows 全面 PASS。

# V0.2.6 雙引擎快速驗收（不重新分析原始影片）

- 已有證據：V0.2.3 與 V0.2.4 已由使用者 Windows 截圖確認 WPF 主視窗開啟並載入歷史棋譜；V0.2.4 快速驗收卡在 Python 依賴檢查，已於 V0.2.5 修正 PowerShell 引號傳遞。
- 待驗證：V0.2.4 新增的快速驗收按鈕、Windows Release 編譯、Python/C# 合成影片運算與互相比對。
- 執行方式：主視窗按「雙引擎快速驗收（合成影片）」；或直接執行根目錄 `Quick-Engine-Gate-Windows.bat`。
- 合成測試輸出、日誌：`%LOCALAPPDATA%\GomokuVision\Gates`；尋找 `quick-gate-latest.json`。
- 只使用 `demo/demo.mp4`，不會重新跑歷史 961 幀影片，不會修改 `results/verified_historical`。
- 顯示 `QUICK_ENGINE_GATE_PASS` 且報告 `outcome: PASS` 才代表**本階段合成雙引擎與編譯 Gate** 通過；WPF 真實辨識、GUI 的取消／校準／語言切換仍須人工作業確認。

# Windows V0.2 GUI / C# / Python 驗收計畫

此表是**待執行的驗收門檻**，不是已確認 PASS 的記錄。工作環境沒有 .NET SDK 或 Windows WPF runtime，不得把檔案產生成功等同 GUI 驗收。

## A. 自動化

- A01：Windows 10/11 x64，.NET 10 SDK `dotnet --version` 正常。
- A02：執行 `scripts\Run-All-Local-Windows.bat`，Python pytest 全通過。
- A03：CLI Release build 零錯誤；`--self-test` 通過勝負、立即勝、防守與四角插值。
- A04：Python / C# 處理同一個自製合成 `demo.mp4`，輸出 `output.mp4`、`moves.csv`、`summary.json`、`board_final.png`。
- A05：`compare_runs.py` 回報雙引擎棋譜及勝負一致。
- A06：WPF Release build 成功，沒有 .NET assembly / native DLL 載入失敗。

## B. Windows WPF 人工驗收

- B01：雙擊啟動 `.\scripts\Launch-Desktop-Windows.bat`，介面顯示三欄布局，無 XAML 例外。
- B02：切換「繁體中文／English」，欄位/按鈕文案更新；輸入的路徑未遺失。
- B03：選擇影片、校準 CSV、模板與結果資料夾，輸入錯誤路徑時提示，不會標示完成。
- B04：四角校準可依順序點選，點擊影像以外區域不計數，重設可清除點，儲存輸出 225 點 CSV。
- B05：C# 引擎啟動，顯示狀態、進度、棋步、棋盤與雙方推薦落點。
- B06：Python 引擎啟動，顯示狀態、進度、棋步、棋盤與雙方推薦落點；Python 未安裝時明確報錯。
- B07：處理中按取消，完成收尾，`summary.json` 的 `canceled=true`，UI 不錯誤標示正常完成。
- B08：完成後點「開啟結果資料夾」開啟正確結果路徑；輸出影片可播放。
- B09：再次分析或使用不同影片，前次視覺結果能重設，不把舊結果當作新結果。
- B10：關閉視窗時若仍在分析，先取消、收尾，避免留下半寫入的結果。

## C. 穩定性與真實影片

- C01：以有使用權的真實影片測試，使用人工標註棋譜，計算棋子 Precision、Recall 及落子位置正確率。
- C02：至少 3 種不同光照／角度，以及手部遮擋情境；列出失敗案例。
- C03：同硬體、同影片、同參數重複至少 5 次，分開紀錄 MATLAB/Python/C# 的端到端時間、取樣分析幀數、平均分析耗時。
- C04：確認第三方影片與報告原始個資完全未進入 GitHub 版本。

**發布門檻**：A 與 B 必須實際執行且 PASS 才可標示 `WINDOWS_DESKTOP_VERIFIED`。即使全部通過，C 的跨場景準確率仍不可自行宣稱 100%。
