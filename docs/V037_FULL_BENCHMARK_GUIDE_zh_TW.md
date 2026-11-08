# GomokuVision V0.3.7｜12 組全自動比較與 CSV 匯出

本版新增 GUI 內的「一鍵測試全部 12 組並匯出 CSV」。預設使用目前選取的影片與校準／黑白棋模板。請確認有 MATLAB 授權、Python OpenCV/NumPy 與 .NET 10 SDK。

## 測試矩陣

- C#、Python、MATLAB（各自執行原生辨識，不代理呼叫其他辨識引擎）
- 黑白分離 ROI／共用 ROI
- 純辨識／辨識＋預測

共 3 × 2 × 2 = 12 組，每組**只執行一次**；結果依序寫入獨立資料夾，不覆蓋歷史 41 手 CSV。

## 操作

1. 執行 `scripts\Verify-WPF-Build-Windows.bat`，通過後啟動 `Launch-Desktop-Windows.bat`。
2. 在左側選擇影片、225 點校準 CSV 與黑白棋模板。若只想比較自製 961 幀影片，保留預設值。
3. 按 **「一鍵測試全部 12 組並匯出 CSV」**，確認後依序運算。此功能**會重新辨識你選擇的影片 12 次**，並非重播保存結果。
4. GUI 在測試間顯示目前組合與完成數；按「取消分析」將於該組完成後停止後續組合。
5. 完成後到所選輸出資料夾的 `benchmark-日期時間` 子資料夾查看報告：
   - `benchmark-results.csv`：每組獨立耗時、引擎、兩種模式、41 手、匹配次數、勝方、錯誤、紀錄位置及合成影片正解檢查
   - `benchmark-summary.csv`：依引擎與 ROI 摘要，僅取已通過組合的單次耗時算術平均。
   - `benchmark-meta.json`：影片 SHA-256、日期及合成正解適用範圍。
   - 每組資料夾內 `summary.json`、`moves.csv`、`console.log`，及 `output.mp4`。

可在未開 GUI 時直接雙擊根目錄的 `Run-All-12-Benchmark-Windows.bat`，使用套件自製的 961 幀影片。

## 判定規則

- `PASS`：該程式正常結束，`summary.json` 和 `moves.csv` 存在；若輸入的影片 SHA-256 精確符合內附的自製完整棋局，還必須比對 41 手棋色／位置與黑棋勝方正解。
- `FAIL`：程式報錯、逾時、沒有產生輸出或不符合合成棋譜正解。
- `SKIP`：MATLAB 等環境不存在。這不是 PASS，也不能納入平均。
- `CANCELLED`：使用者要求停止，尚未開始的組合不再執行。

**注意**：播放速度 1×、2×、4× 不改變運算耗時。各引擎以單次的 `elapsed_wall_seconds`（含程式啟動與分析）比較；`engine_wall_seconds` 是引擎內部計時，兩者不混算。MATLAB 啟動成本會進入 `elapsed_wall_seconds`。C# 的 .NET 編譯預先完成，不計入每組耗時。

只有一輪的結果不能當成穩健的統計效能排名；正式報告建議每組至少重複 5 次，並提供中位數／四分位範圍。即使合成影片 41/41 正確，也不代表真實影像場景的普遍準確率。

## MATLAB 綠框

舊版 MATLAB 以一像素線繪製綠框，WPF 縮小預覽時可能看似缺框。本版將已確認棋子的框改成 3 像素、較高亮度，推薦框改成 2 像素；色框仍由**已確認棋步**生成，並未改動辨識分類邏輯。新版顯示仍需 Windows + MATLAB 實際驗收。
