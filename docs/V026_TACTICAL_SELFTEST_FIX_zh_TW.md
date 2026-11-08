# GomokuVision V0.2.6｜C# 戰術自測修正與 Windows 驗收

## 先前 Windows 實測事實

- V0.2.5 Quick Gate：Python 依賴檢查 PASS；22/22 Python pytest PASS；.NET SDK 10.0.403 PASS；C# Release CLI 編譯 PASS（0 error）；C# 戰術／校準自測 FAIL。
- 實際終止訊息：`ERROR: Winning move suggestion failed`。由於 gate 立即停止，**該次沒有測試短合成影片的 Python/C# 對照，也沒有執行 WPF Build**。
- 來源：使用者 `quick-gate-20261108-171254.log` 及 JSON。該記錄只測合成素材，沒有重跑歷史 961 幀影片。

## 根因與修正

C# 自測建立棋盤：D8、E8、F8、G8 四顆黑子。C8 / H8 才是合法且立即獲勝的落點。原自測要求 `D8 or I8`：D8 已佔用，I8 非立即獲勝。正確的 C# 評分演算法不應因錯誤測試預期而被判失敗。

V0.2.6：改檢查 `C8 or H8`、10000000 戰術分數，並將推薦落點實際放回棋盤，再檢查勝者確實為黑棋。新增 Python 來源／棋局規則防回歸測試；不是聲稱已在 Linux 執行 C#。

## 你的 Windows 使用方法（不需重跑舊影片）

1. 解壓縮 V0.2.6 **完整 ZIP 到新資料夾**，不要與 V0.2.5 的 `obj`、`bin` 混用。
2. 確保 .NET 10 SDK 及 Python 依賴已有安裝；你之前的 Windows 日誌已確認。
3. 雙擊專案根目錄的 `Quick-Engine-Gate-Windows.bat`。此 Gate 只處理自製短影片 `demo/demo.mp4`，不會重新跑 961 影格原始影片。
4. 需看到 C# 自測步驟 `GATE_PASS: C# tactical/calibration self-tests`，且最後 `QUICK_ENGINE_GATE_PASS`、`WPF_BUILD_PASS` 才能認定所有自動測試通過。
5. 失敗時，查看 `%LOCALAPPDATA%\GomokuVision\Gates\quick-gate-latest.json`，或同目錄 `quick-gate-*.log`。`FAILED_STEP` 指向第一個失敗階段，後續未執行的步驟不得視為通過。

## 局限

這套快速 Gate 的成功只證明已知短合成棋局、戰術自測、跨引擎結果與 WPF Release 編譯。WPF 實際 UI 操作與真實影片辨識準確率仍需其他驗收。MATLAB 歷史版本目前未納入這個 Gate。
