# GomokuVision V0.3.8｜精簡 GUI 與 1×／2×／4× 複選測試

## 介面修改

- 左側主區：影片、三種引擎、兩種 ROI、兩種顯示模式、倍率複選與一鍵 CSV 匯出。
- 「更多設定 · 校準／模板／輸出」預設收合，保留四角校準、黑白模板、儲存路徑、辨識進階參數、歷史資料載入及快速驗收功能，**沒有刪除底層核心功能**。
- 右側棋盤、綠框、推薦候選、同步影片播放與逐手重播保留不變。
- 繁中／English 均提供新的面板名稱與警示。

## 一鍵多倍率測試

在 GUI 左側「批次比較 · CSV 匯出」可獨立勾選 `1×`、`2×`、`4×`，按「執行所選測試 · 匯出 CSV」。

| 勾選倍率 | 引擎 × ROI × 顯示模式 | 總運算組數 |
|---|---:|---:|
| 任選一種 | 3 × 2 × 2 | 12 |
| 任選兩種 | 3 × 2 × 2 × 2 | 24 |
| 三種全選 | 3 × 2 × 2 × 3 | 36 |

全部取消勾選時會出現提示，不會啟動測試。每組使用獨立輸出資料夾，以免覆蓋歷史 41 手棋譜；按「取消」會在目前組合結束後把尚未執行的項目記為 `CANCELLED`。

### 關於播放速度

**1×／2×／4× 是 WPF 影片重播倍率，不是辨識演算法的倍速模式。** 這次選擇多種倍率會為每一倍率**重新執行同樣的 12 組辨識演算**，用於重複量測與依倍率分組整理；不會把演算法加速到 2 或 4 倍，也沒有驗證 WPF 的實際 FPS。CSV `playback_speed` 表示標籤，`expected_playback_seconds` 是理論重播長度，`playback_model_verified` 僅檢查數學端點模型，不能當作 GUI 實機播放通過。

理論上 961 幀、30 FPS 影片的播放時間：1× 約 32.03 秒、2× 約 16.02 秒、4× 約 8.01 秒；辨識計算耗時應獨立解讀。

### 輸出

- `benchmark-results.csv`：每個案例一列，包括 `playback_speed`、`elapsed_wall_seconds`、`engine_wall_seconds`、棋步、影格、匹配次數、正解與失敗原因。
- `benchmark-summary.csv`：按「倍率 × 引擎 × ROI」分組，每組彙整兩種顯示模式的 PASS／FAIL／SKIP 與耗時。
- `benchmark-meta.json`：原始影片 SHA-256、選取倍率、來源 FPS、總影格與測試範圍。
- `status.json`：執行進度與每組結果；還有各案例 `console.log`。

只測 Python 或操作命令列時可執行根目錄 `scripts/Run-Selected-Speeds-Windows.bat`，未指定參數預設 1×，或從 CMD 輸入：

```bat
scripts/Run-Selected-Speeds-Windows.bat 1 2 4
```

也可以直接呼叫 `python/tools/run_full_benchmark.py --playback-speeds 1 4`，其它必要參數參考根目錄批次檔。

## Windows WPF 驗收清單

1. 解壓至新的 V0.3.8 資料夾，不覆蓋 V0.3.7；先跑 `scripts\Verify-WPF-Build-Windows.bat`，再開啟 `Launch-Desktop-Windows.bat`。
2. 左側確認可直接操作引擎／ROI／顯示模式，進階設定預設收合並可展開。
3. 先勾 `1×`，確認提示 12 組；再勾 `1× + 4×`，確認提示 24 組；全勾確認 36 組。
4. 測試完成後檢查 CSV 的 `playback_speed` 分組、輸出路徑與 PASS/FAIL。
5. 另外手動使用影片播放器的 1×、2×、4× 驗收影片、棋盤、落子紀錄的同步；這是 GUI 實機驗收，不能由批次 CSV 取代。

## 本次已測與待測

- Python / XAML 靜態來源與回歸：70/70 PASS。
- Python 自製 961 幀完整棋局：3 種倍率分別執行各四種組合，合計 12/12 PASS，全部 41/41 手，黑棋獲勝；各倍率獨立執行，不代表 WPF 中的一鍵 36 組已實機驗證。
- 新版 C#／WPF 編譯、GUI 多倍率選項及 MATLAB 原生 36 組：需要 Windows 實機再驗收。
- 合成棋譜正確不代表一般真實攝影影片的辨識準確率。
