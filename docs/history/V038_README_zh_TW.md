# GomokuVision V0.3.8 — 精簡介面與倍率複選批次測試

新版 WPF 主介面只保留影片、引擎、ROI、顯示模式及批次測試，較少使用的校準、模板、進階參數都可從「更多設定」展開。批次測試可勾選 **1×／2×／4×** 任意組合，執行 12／24／36 組後輸出 CSV；請參閱 `docs/V038_COMPACT_UI_MULTI_SPEED_ACCEPTANCE_zh_TW.md`。

**重要：** 倍率是播放速度標籤而非辨識運算加速。每選一種倍率會重跑一輪 12 組，並分別記錄耗時。Windows 最新版 WPF／MATLAB 的實機驗收仍待確認。

# V0.3.7 更新：完整基準與 CSV 匯出

WPF 左側新增 **「一鍵測試全部 12 組並匯出 CSV」** 按鈕（MATLAB／Python／C# × 黑白分離／共用 ROI × 純辨識／辨識＋預測）。

會重新分析目前選取的影片，每組各自執行，結束後自動產出 `benchmark-results.csv`、`benchmark-summary.csv`。完整說明參閱 `docs/V037_FULL_BENCHMARK_GUIDE_zh_TW.md`。MATLAB 的一像素綠框已加粗為三像素；新版原生 Windows 驗收待確認。

# GomokuVision Advanced V0.3.6 — 原始雙 ROI 模式、綠框與辨識／預測切換

**本版接續 V0.3.5，保留三引擎即時棋步及 Windows 鎖檔修正。** 新增兩個*獨立*的選擇器：

| 設定 | 選項 | 真正影響 | 預設 |
|---|---|---|---|
| ROI 搜尋策略 | **黑白分離**／**共用 ROI** | 分離模式各自使用黑、白棋的亮度預篩；共用模式只要通過任一棋色候選預篩，就對兩種模板執行 NCC，仍使用各自閾值 | 黑白分離 |
| 顯示模式 | **純辨識**／**辨識＋預測** | 綠色方框顯示已確認或已記錄的棋子；預測模式另外顯示綠色（黑棋）及青色（白棋）的候選落點圈 | 辨識＋預測 |

**注意歷史來源：** 原始 MATLAB `ROI_Sharing.m` 與 `ROI_black_and_white_separation.m` 幾乎只有註解差異，因此不能把歷史報告的兩組耗時直接當成不同演算法的有效對照；V0.3.6 才在 Python、C#、MATLAB 現代核心建立可比較的獨立預篩邏輯。原版另有辨識加啟發式預測的程式，並非 Gemini API。綠框標記*已經進入棋譜*的棋子，不是逐格 NCC 分數熱圖。候選圈只是策略推薦，不能當作已落子。

## 直接觀看 961 幀、2 倍速同步的兩種模式

影片都是**自行繪製的合成對局／已知參考棋譜**，不是原始第三方攝影影片，也**不是重新推論的模型結果**。左側綠框和右側棋盤根據相同影格依序更新，第 949 幀最後落子，第 961 幀完整保留。

- `demo/full_game/full_game_recognition_green_961_2x.mp4` — **純辨識綠框**，961 幀、60 FPS（約 16 秒）。
- `demo/full_game/full_game_recognition_prediction_green_961_2x.mp4` — **綠框＋預測圈**，同樣 961 幀／60 FPS。
- `demo/full_game/full_game_961.mp4` — 未標記的原始合成影片，30 FPS；**WPF 使用此檔，配合模式選項動態渲染綠框**。按 2× 會同步播放約 16 秒。

WPF 已載入已保存的結果且影片與棋譜配對時，兩個「顯示模式」可即時切換而不重新辨識；「ROI 搜尋策略」則在**下一次真正開始辨識時**生效，會傳到 Python、C# 或 MATLAB。WPF 的影格定位依已保存棋譜、來源影片校準點位重新疊上綠框；執行中的進度預覽由各引擎把實際確認落子畫入快照。未配對影片不會冒用另一份棋譜的綠框。

## 本版實際驗證與界線

- Python 來源、演算法及檔案鎖回歸 **64/64 PASS**。
- 合成短影片的「ROI 共用」和「黑白分離」均辨識 **9/9 手、黑棋勝利**。
- Python 對兩種 ROI 策略各跑一次完整 **961 幀／161 分析幀／41 手**，兩組棋色與落子位置均與合成正解一致。分離模式嘗試 NCC 25,458 次；共用模式 50,916 次。速度因執行環境與候選數不同，不當成普遍快慢結論。
- 兩支同步綠框 MP4 已完成 961 幀／60 FPS 封裝與影格解碼確認；綠框依合成正解時間軸添加，不能稱作「偵測準確率」。
- **未在本環境進行最新版 C#／WPF Windows 編譯或 MATLAB 授權執行。** 前版 C#／Python Windows 961 幀 41 手證據不能無條件沿用來宣稱 V0.3.6 的新模式也通過。

## Windows 一鍵驗收

1. 解壓 ZIP 到**新資料夾**（不要覆蓋 V0.3.5 `bin/obj`），執行 `scripts/Verify-WPF-Build-Windows.bat`，再執行 `Launch-Desktop-Windows.bat`。
2. 左側先選「黑白分離 ROI」，上方模式選「純辨識（綠框）」，影片預覽選擇 `demo/full_game/full_game_961.mp4`。拖動影片時間軸從 F1、F25 到 F949／F961，確認綠框和棋盤棋子數一致，勝利線在最後呈現。
3. 切換「辨識＋預測」：中途未完局應出現額外綠／青候選圈，棋譜、實際辨識結果不得因畫面切換而變動。
4. 用 `Run-Legacy-Modes-Windows.bat` 一鍵比較 Python／C# 兩種 ROI × 兩種展示模式的短合成影片及正解，每組均需通過。若電腦已安裝授權 MATLAB，選擇 `Run-Legacy-Modes-Windows.bat -IncludeMatlab` 才額外測 MATLAB 原生兩模式。
5. 選擇三個引擎各自建立**新的結果資料夾**再分析。驗收 961 幀、逐手落子、綠框、畫面切換與取消操作。本機工具不會自動將第三方原始影片上傳。

若編譯或 MATLAB 失敗，請提供 Windows 錯誤日誌。**只有實際通過的引擎與模式才標記 PASS**；不應以 WPF GUI 開啟成功推論所有辨識都通過。新模式操作驗收清單：`docs/V036_LEGACY_MODES_ACCEPTANCE_zh_TW.md`。

---

# GomokuVision Advanced V0.3.5 — Windows 預覽檔案競爭修復

**此版取代 V0.3.4。** 針對使用者 Windows 實測：Python 在 `temp_image.replace(last_frame.png)` 遇到 `WinError 5`；MATLAB 在 `movefile(tmpPreview,lastPreview,'f')` 因檔案正在使用而中斷。C# 在 V0.3.4 已能完成 41 手，本版僅同步加固其預覽流程，不更動辨識演算法與棋步策略。

## 根本問題與修正

前版三個引擎都可能以**相同的 `last_frame.png` 路徑反覆覆蓋預覽**。Windows 上 WPF／防毒程式／圖片處理元件正在開啟該路徑時，替換或改名可能被拒絕。新版的三引擎改為：

1. 每次辨識工作使用獨立的 `preview_frames/<工作識別碼>/` 目錄。
2. 每次進度事件完成編碼後才發布 `frame_000001.png`、`frame_000007.png` 等**不再修改的圖片路徑**。
3. WPF 只讀取 JSON 指向的已完成圖片；圖片讀取使用允許共用讀寫及刪除的 FileStream。
4. `last_frame.png` 僅在辨識結束後寫入一次，供離線結果讀取；不是即時更新管道。
5. Python 進度 JSON 在短暫檔案鎖下有限次重試；MATLAB 的 JSON 發布亦有重試，並避免因個別進度快照失敗就放棄整局辨識。

**這不是換掉辨識器，也不宣稱改變準確率。** 舊版合成完整棋局與原始專題歷史棋譜仍保留。影片播放／棋譜同步與速率控制行為維持既有設計。

## 本次已驗證

- Python / 來源回歸 **61/61 PASS**，新增 Windows 鎖檔模擬、JSON 短暫鎖定重試，以及 CLI 離線模式輸出檢查。
- Python 完整 **961 來源幀／161 分析幀／41 手**合成對局辨識，與合成棋譜正解 **41/41** 棋色及座標一致，勝方 Black。
- GUI 進度模式產生 70 張**不重複命名**的預覽快照，最後 JSON 指向 `frame_000961.png`，`last_frame.png` 也於結束後存在。
- 新版 **Windows C#／WPF 編譯、MATLAB 真實執行、三引擎 GUI 即時顯示：尚待 Windows 使用者驗收**。這些不是從 Python 測試推論出來的。

## Windows 驗收（不需要原始第三方影片）

1. 將本版 ZIP **解壓至新的 `GomokuVision_Advanced_V0.3.5` 資料夾**，不要覆蓋舊版 `bin/obj`。
2. 執行 `scripts\Verify-WPF-Build-Windows.bat`，成功應顯示 `WPF_BUILD_PASS`。
3. 執行 `Launch-Desktop-Windows.bat`，預設使用 `demo/full_game/full_game_961.mp4`（自製 961 幀合成棋局）。
4. 依序選擇 Python、MATLAB、C#，各自使用**不同的空白結果資料夾**，按「開始辨識與預測」。確認落子清單逐手增加、右側棋盤即時增加、流程不中斷，最後 41 手、黑棋勝利。
5. MATLAB 如仍失敗，保存 `matlab-console.log`；Python 若失敗，保存錯誤訊息及執行目錄下的 `.wpf-progress.json`。只有三者實機都完成後才能稱為三引擎 GUI PASS。
6. 不需重新處理原始第三方影片。完整合成影片則應在三引擎各執行一次，才能完成這次的 Windows 實機驗收。

可先檢查進度圖片目錄 `結果資料夾/preview_frames/` 是否每次產生新 `frame_XXXXXX.png`，而不是對同一個 `last_frame.png` 反覆搬移。

**提醒：** `output.mp4` 是抽樣辨識輸出，不等於完整 961 幀原始播放影片；完整播放應使用 `demo/full_game/full_game_961.mp4`，左右同步 2 倍速影片是 `demo/full_game/full_game_synced_961_2x.mp4`。已記錄之棋子辨識影格可能比影片實際落子影格晚 6 幀。

---

# GomokuVision Advanced V0.3.4 — 三引擎即時棋步更新、MATLAB 修復、最後影格同步

**此版取代 V0.3.3。** 直接下載本版 ZIP 使用，勿與 V0.3.3 的 `bin/obj` 或舊同步 MP4 混用。V0.3.3 的歷史說明保留在下文供參考。

**本版重要修正：**
- C#／Python／MATLAB 在辨識過程中逐步輸出已確認落子快照，WPF 在執行時即時新增棋譜、更新右側棋盤與預覽；不再等結束才一次顯示全部 41 手。
- MATLAB 原生 `table` 使用獨立維度名稱 `MoveRecords`，解決 `Duplicate dimension and variable name: Row`；MATLAB 的 `gomoku_selftest.m` 新增回歸案例。
- MATLAB 使用較大半徑的黑棋亮度預篩以避免把空的棋盤交叉線誤當黑棋候選而大量重複呼叫 NCC；白棋仍採原先較敏感的門檻。預期降低空格模板匹配次數，但**本環境沒有 MATLAB，沒有宣稱實測提速百分比**。
- 分離棋子實際出現時刻與辨識確認時刻：`moves.csv` 保留原始確認影格；`summary.json` 新增 `confirmation_delay_frames`，WPF 做有條件的近似顯示補償，不修改原始紀錄。
- **961 幀／60 FPS 雙畫面 2 倍速 MP4 已重新編碼**：F949～F961 左右兩側都含完整第 41 手與勝利連線。WPF 播到最後 F961，不提前停在演算法確認影格。
- 另外增加 `Run-Three-Engine-QuickGate-Windows.bat` 與 `Run-MATLAB-961-Gate-Windows.bat`，可在具備 MATLAB 授權的 Windows 上做三引擎短測及 MATLAB 全局驗收。

**本環境已實測：** Python 57 項原測試＋新增 V0.3.4 測試（完整數量及最新結果請見 `docs/V034_VALIDATION.json`）；Python 完整 961 幀辨識 41/41 並比對自製正解。**尚未驗收：** 最新 V0.3.4 的 Windows C#／WPF 實際編譯、即時 GUI 行為及 MATLAB 原生執行。上版 V0.2.6 11/11 Windows gate PASS 不等於新版 PASS。

- 最新 Windows 驗收：[docs/V034_WINDOWS_ACCEPTANCE_zh_TW.md](docs/V034_WINDOWS_ACCEPTANCE_zh_TW.md)
- **完整 2 倍速同步影片：** `demo/full_game/full_game_synced_961_2x.mp4`；普通分析影片：`demo/full_game/full_game_961.mp4`。
- 唯一官方測試素材為自行繪製棋盤影片，無第三方原始影片內容；`results/full_game_demo/moves.csv` 是**合成棋局正解**，不是人工標註的真實辨識率。

---

## V0.3.3 歷史版說明（已由本版修正取代）

# GomokuVision Advanced V0.3.3 — 三引擎、961 幀完整對局、同步倍速播放

**這是由 V0.3.2 擴充的完整來源交付候選版。** 本次新增全新自行繪製的 961 幀／41 手五子棋影片，WPF 預設 2× 倍速、棋盤與影片共用時間軸，並將 MATLAB 獨立辨識核心接入現有 Python／C# WPF GUI。**沒有包含原始第三方對局影片。**

## 直接查看兩側同步影片（無需安裝開發環境）

- `demo/full_game/full_game_synced_961_2x.mp4`：**961 幀、60 FPS、約 16.02 秒**；左側自製對局影片、右側模擬棋盤在同一影格更新。已實際解碼第 1／25／493／949／961 幀確認。
- `demo/full_game/full_game_961.mp4`：720×720、**961 幀、30 FPS、約 32.03 秒**，供 Windows WPF 逐影格控制。WPF **預設 2×**，約 16 秒播完。
- `results/full_game_demo/moves.csv`：內含 41 手、棋色、交叉點及來源影格編號。這是影片的**合成劇本／正解資料（oracle）**，不能冒充辨識演算法輸出。
- `demo/full_game/manifest.json`：檔案雜湊、影格數與授權範圍。

預設打開桌面程式時載入 41 手合成棋局，播放前畫面為空棋盤、從第 1 幀起始。**按「播放影片」或「同步播放／播放棋譜」都是啟動同一個播放時鐘**；影片時間軸按影格帶動棋盤及棋譜，點選上一手／下一手或拖曳棋步滑桿也會尋找對應影片影格。提供 1×、2×、4× 選擇；在 WPF 選擇已經編為 60 FPS 的雙畫面影片時，播放器自動改成 1×，避免再加速一次。

**配對防護：** 只有影片 SHA-256 與保存棋譜相符、或新分析結果 `summary.json` 指向同一來源檔時，才連動兩者。用戶原始私人影片另有自己的 41 手歷史資料配對，不會誤連到自製影片。無配對影片時不能假裝動作同步。

## Windows 執行（.NET 10 SDK、Python 3.10+）

先執行 `Launch-Desktop-Windows.bat`。如果需要純編譯檢查：`scripts/Verify-WPF-Build-Windows.bat`。首次編譯會還原 NuGet 套件。預設無需重新辨識影片即可觀看 41 手同步重播。

要重新做電腦視覺辨識，先選「C# / OpenCvSharp」或「Python / OpenCV」再按「開始辨識與預測」，並使用獨立的輸出資料夾。**完整 961 幀是自製測試資料**，前一版的 `demo/demo.mp4`（短 9 手影片）仍留作快速回歸，不是原始第三方影片。

## MATLAB 已接入 WPF（第三個獨立辨識引擎）

左側「辨識引擎」新增 **MATLAB / Image Processing Toolbox**。WPF 會建立 `matlab-run-config.json`，以 `matlab -batch` 啟動 `matlab/modern/gomoku_batch.m`，由 MATLAB 的 `VideoReader`、`normxcorr2`、`VideoWriter` 執行**獨立影像分析**；**並不是讓 MATLAB 呼叫 Python 或 C# 來冒充第三引擎**。會寫出相容的 `moves.csv`、`moves_legacy.csv`、`summary.json`、`last_frame.png` 和 `output.mp4`，進度可由 GUI 讀取，取消時透過檔案提出安全停止要求。

需要 **已授權的 MATLAB（建議 R2021b 或更新）＋Image Processing Toolbox**。若 `matlab` 尚未在 PATH，先設定使用者環境變數 `GOMOKUVISION_MATLAB_EXE` 為本機 `matlab.exe` 的完整路徑；請勿將 MATLAB 本體、授權檔或私有素材放入 GitHub。WPF 的 MATLAB 自動測試可用 `Run-MATLAB-Gate-Windows.bat`（會跑原生 MATLAB 核心測試與短 9 手合成影片，並用 Python 作為**獨立的棋譜正解檢查器**）。

> **重要驗收界線：** 本回合執行環境沒有 MATLAB，也沒有 Windows .NET SDK；所以 MATLAB 實際辨識及 V0.3.3 WPF 編譯／同步播放仍需 Windows 實機驗收。現有 Windows V0.2.6 雙引擎 11/11 PASS 屬於前版證據，不能直接當成新版的三引擎 PASS。舊 2025 年 MATLAB 腳本仍保留在 `matlab/legacy/`，但不應直接視為已統一測試規格。

## 本次已執行測試

- **Python 來源與契約測試：52/52 PASS**。
- 完整合成影片實際執行 Python／OpenCV 辨識：來源 **961 幀、分析 161 幀、41/41 棋色與落點一致、黑棋勝利**。當 `confirmations=2`、`sample_every=6`，確認影格**全部延後 6 幀**，因此將「影像出現幀」與「演算法確認幀」分開記錄。
- 影片容器實測：普通影片 961 幀／30 FPS；同步雙畫面影片 961 幀／60 FPS；並已檢視兩側在多個影格的對應內容。
- MATLAB 新核心是程式碼及結構檢查，**未做授權 MATLAB 實際辨識測試**；C#／WPF 新功能同樣待 Windows 編譯及 GUI 動態驗收。

請參考：[Windows 完整驗收指引](docs/V033_WINDOWS_ACCEPTANCE_zh_TW.md)、[測試證據 JSON](docs/V033_VALIDATION.json)、[同步影格預覽](docs/V033_Synchronized_Frames_Preview.png)。

## GitHub 公開注意

本套件包含自行合成的棋盤影片、模擬檔、程式碼和 41 手保存棋譜，不含原始第三方影片、原始棋子截圖及個資原始報告。`results/full_game_demo` 是**合成劇本**；`results/verified_historical` 只是原專題輸出的棋譜回歸參考，不是人工標註的真實準確率。舊 MATLAB 程式仍應確認是否擁有公開權利，不能假設所有第三方素材皆可開源。

正式 GitHub 發布前，應完成 Windows 版 WPF 同步操作與 MATLAB 自測驗收。尚未自動上傳 GitHub。

---

# GomokuVision Advanced V0.3.2 — 本機原始影片匯入與 41 手棋譜同步

**此版本是公開程式碼候選套件，不包含原始第三方影片。** V0.3.1 預設 `demo/demo.mp4` 是 9 手合成影片，因此原始專題需要額外匯入本機私人資料，不應將 demo 當成原始影片。

在 Windows WPF 左側頂端點「**匯入原始專題資料夾（本機私人影片）**」，選擇含有 `input.mp4`、`checkerboard_points.csv`、`black.png`、`white.png` 的**原始期末專題解壓資料夾**。此操作不會重新辨識，只載入私人影片的影格並顯示保存的 41 手；只有影片及 41 手資料 SHA-256 都符合已知原始輸入時，才允許棋步與影格同步。若想重新評估原始影片，請明確選擇 Python 或 C# 引擎並按「開始辨識與預測」，且使用不同結果輸出資料夾。

**開發環境直接驗證**：以 V0.3.1（V0.3.2 同一 Python 辨識核心）分析你最初提供的原始 `input.mp4`，得 961 幀、取樣分析 161 幀、41 手、黑棋獲勝，棋步位置／棋色順序與原始專題 CSV 全部一致。原始影片與影格不包含在本 ZIP，這是歷史 CSV 的回歸一致性，不代表獨立人工標註的 100% 正確率。新增 Windows WPF 匯入按鈕／影片同步**仍待你的 Windows GUI 驗收**。

[操作與驗收說明](docs/V032_ORIGINAL_VIDEO_ACCEPTANCE_zh_TW.md) ｜ [本次 Python 原始影片測試摘要](docs/V032_LOCAL_HISTORICAL_RECHECK.json)

---

# GomokuVision Advanced V0.3.1 — WPF 底部遮擋與縮放版面修正

> **以使用者 2026-11-08 的 V0.3.0 Windows WPF 畫面為修正依據。** 本版只修正 WPF 版面配置與視窗適應性；三語言辨識核心、預先保存的 41 手棋譜及合成測試素材均未改動。沒有重新處理歷史 961 幀原始影片。

## 本次修正

- **底部操作列**：由固定 64 單位高改為內容自動決定高度；狀態文字與操作控制分成兩列，按鈕高度至少 42，避免繁體中文文字被壓住。
- **螢幕尺寸與 DPI**：啟動時以 Windows 工作區（不含工作列）調整大小與起始位置；中間三欄區塊支援水平和垂直捲動，底部操作列維持可見。
- **棋譜控制**：「上一手／播放棋譜／下一手」維持原事件處理，棋步滑桿使用剩餘寬度而非固定 150，避免小視窗溢出。
- **狀態訊息**：長文字採單列省略號顯示，滑鼠移入可查看完整內容；進度條獨立保留。
- **測試**：非 Windows 開發環境 Python **39/39 PASS**（含 6 項新版 WPF 版面／事件合約測試），XAML XML 解析通過，封裝完整性驗證通過。**V0.3.1 尚未在 Windows 實機編譯及視覺驗收。**

## 在 Windows 只驗證介面（不重跑影片）

1. 解壓縮至全新資料夾 `GomokuVision_Advanced_V0.3.1`。
2. 執行 `scripts\Verify-WPF-Build-Windows.bat`，確認 `WPF_BUILD_PASS`。
3. 執行 `Launch-Desktop-Windows.bat`。確認底部三個按鈕文字完整且不超出視窗邊界。
4. 縮小視窗，並在 Windows **125%／150% 縮放**下觀察：中間內容可捲動、底部操作列始終可見，且不被工作列遮住。
5. 使用已載入的歷史 41 手結果按上一手、下一手、棋譜滑桿；**無須**重新跑歷史影像。

完整檢查表：[V0.3.1 版面驗收](docs/V031_WPF_LAYOUT_ACCEPTANCE_zh_TW.md)。要跑短合成影片的雙引擎回歸可另用 `Quick-Engine-Gate-Windows.bat`，不需要這次介面修正的首輪驗收執行。

**目前狀態：** `LAYOUT_FIX_SOURCE_TESTED / WINDOWS_GUI_PENDING`。你提供的 V0.3.0 截圖確認前版 WPF 已能開啟，但不代表本版的畫面已實測成功。本 ZIP 尚未上傳到 GitHub。

---

# GomokuVision Advanced V0.3.0 — Windows 影片預覽與棋步同步

> **唯一交付的新版本**（2026-11-08）：保留 V0.2.6 已在 Windows 通過的雙引擎合成驗收，新增可操作 WPF 棋譜重播、影片影格時間軸、來源配對防護與校準網格預覽。

## V0.3.0 新功能與實際狀態

| 功能 | 說明 | 驗證狀態 |
|---|---|---|
| 逐手棋譜重播 | 上一步／下一步、棋步滑桿、選取清單、自動播放；每一步從 CSV 重新繪製當下棋盤 | Python 合約／來源測試已通過；Windows GUI 待操作驗收 |
| 影片影格預覽 | 使用 OpenCvSharp 依需定位影格、播放暫停、影格／秒數顯示，解碼在背景執行 | 來源合約檢查通過；Windows 播放待驗收 |
| 正確影片配對 | `summary.json` 的絕對來源路徑與目前載入影片一致才允許棋步與影格同步；歷史 41 手與 demo.mp4 **不會假裝配對** | 自動來源防護測試通過 |
| 校準可視化 | 四角完成後預覽 15×15 網格；可撤銷最後一點後重選 | XAML／來源測試通過；Windows 操作待驗收 |
| 效能紀錄 | 快速驗收產生 `engine-comparison.json` / `.csv`，記錄兩引擎在**短合成影片**的描述性處理時間 | Python 報告產生測試通過；完整 Windows Gate 待複驗 |
| 雙引擎辨識與戰術核心 | V0.2.6 已在使用者 Windows 10 通過 11/11 Gate、Python 25/25、雙引擎 9/9 棋步一致 | **歷史版本的 Windows 證據**，不是 V0.3 本身 GUI PASS |

**本次開發環境驗證：** Python **33/33 PASS**，短合成影片 **9/9 手、黑棋勝利 PASS**，歷史 41 手重播資料合法性核對通過；WPF XAML XML 結構與 UI 事件合約通過。**尚未在 Windows 上編譯或啟動 V0.3 的新增 GUI**，因此新版狀態仍是 `WINDOWS_GUI_ACCEPTANCE_PENDING`。歷史 961 幀影片沒有重跑。

### 建議先做的 Windows 驗收（不重跑原始影片）

1. 將本 ZIP 解壓縮至新的 `GomokuVision_Advanced_V0.3.0` 目錄。
2. 執行 `scripts\Verify-WPF-Build-Windows.bat`；通過 `WPF_BUILD_PASS` 後再執行 `Launch-Desktop-Windows.bat`。
3. 預設載入歷史 41 手 CSV；直接使用「上一手」「下一手」「播放棋譜」或棋步滑桿，觀察右側棋盤動態重繪，不需要歷史影片。
4. 若要試影片預覽，保持 `demo/demo.mp4`，點「載入影片預覽」；拖曳影格時間軸。畫面應明確標記「影片未與歷史棋譜配對」。
5. 想測真正的影格／棋步同步，可用自製 demo 影片跑一次**新的短合成影片分析**，使 `summary.json` 的 input 路徑確實與 demo 相同，再選取棋步。
6. 執行 `Quick-Engine-Gate-Windows.bat` 複驗 Python／C# 引擎、9 手結果與 WPF 編譯；新版會額外產生描述性雙引擎效能 JSON/CSV。

完整圖形操作驗收步驟：[V0.3 Windows 驗收清單](docs/V030_GUI_ACCEPTANCE_zh_TW.md)。

**授權與成果界線：** 沒有附第三方歷史影片、人物個資或原課堂報告。41/41 是與舊程式 CSV 一致，非獨立人工標註的 100% 準確率。MATLAB 原始碼仍在 `matlab/legacy/` 作為歷史基線，未納入自動跨語言引擎測試。尚未自動建立或上傳 GitHub 儲存庫。

---

# GomokuVision Advanced V0.2.6 · MATLAB / Python / C# / Windows WPF

> 15×15 五子棋影片辨識、棋譜追蹤、立即勝負威脅評分、棋盤標註及互動式 Windows GUI。三語言開發；介面提供繁體中文／English 切換。

**合成測試結果預覽**（非原始第三方影片）

![合成棋局的最終棋盤](docs/demo_board.png)

**公開範圍**：此 ZIP 是 V0.2.6 進階版來源封裝，不含可能屬於第三方的原始影片、棋子截圖模板、課堂報告原件及個人資料。示範影片與模板為程式自行合成。

## V0.2.6：修正 C# 自測預期座標錯誤（2026-11-08）

Windows 10 + .NET SDK 10.0.403 實機回報：V0.2.5 Quick Engine Gate 已通過 Python 套件檢查、**22/22 Python 測試**與 C# Release CLI 編譯（0 errors），但在 `C# tactical/calibration self-tests` 收到 `ERROR: Winning move suggestion failed`，因此後續影片雙引擎比對及 WPF Build **尚未執行**。

**根因**：`Program.cs` 建立的是 D8、E8、F8、G8 四連線。立即獲勝落點是 **C8 / H8**；舊版自測錯誤地預期 `D8 / I8`。D8 已被占用，而 I8 並不能立即五連線。這是 **測試預期答案錯誤**，不是依照此證據就能判定辨識演算法有問題。

本版修正：

- 更新 C# 自測預期為 `C8 / H8`，且檢查建議分數 **10,000,000**。
- 實際將所推薦的那一手放入棋盤，斷言五連線勝利，而不僅比較落點字串。
- 新增 Python 交叉語言測試案例，驗證 C# 自測棋局與 Python 共用規則相符（此為 **source guard，不是 C# 實測**）。
- 既有 Python/C# 辨識演算法、NCC 門檻、合成影片、歷史 41 手棋譜與 MATLAB 原版**完全不變**。不重跑原始 961 幀影片。
- Windows 上需重新執行 `Quick-Engine-Gate-Windows.bat`。**直到 Windows 回報 `QUICK_ENGINE_GATE_PASS`，不得宣稱跨引擎測試完成。**

本機非 Windows 環境可執行 Python 測試與來源檢查；.NET CLI 與 WPF 執行結果必須依 Windows 實測日誌確認。

## V0.2.5：修復 Windows PowerShell 5.1 的 Python 依賴檢查錯誤（2026-11-08）

Windows 10 實機回報：V0.2.4 WPF 主視窗已能開啟，但快速驗收在第一個 Python 依賴步驟出現 `SyntaxError: unexpected EOF while parsing`；原因是 PowerShell 5.1 傳遞 `python -c` 內嵌雙引號時破壞 Python 程式內容，**不是已確認缺少 NumPy／OpenCV**。

- 新增 `python/tools/check_dependencies.py`，用檔案方式檢查 `cv2`、`numpy`、`pytest`，避免命令列引號在 Windows 5.1 被移除。
- 快速驗收改為呼叫檔案，成功輸出 `DEPENDENCY_CHECK_PASS`；確實缺套件則顯示 `DEPENDENCY_CHECK_FAIL` 以及安裝建議。
- 增加來源防回歸與本機檢查測試；保留合成影片九手已知正解與跨引擎棋譜對照。
- 只處理依賴檢查／驗收腳本，**沒有修改影像辨識演算法或 41 手歷史結果**；不重新分析原始 961 幀影片。
- **Windows 實機 Gate 仍待驗收**。V0.2.4 的 WPF 已能開啟，不代表 C#／Python 快速驗收完成。

操作：解壓縮 V0.2.5 至全新資料夾，雙擊根目錄 `Quick-Engine-Gate-Windows.bat`；或從 WPF 內按「雙引擎快速驗收（合成影片）」。日誌與結果保存在 `%LOCALAPPDATA%\GomokuVision\Gates`。只有 `QUICK_ENGINE_GATE_PASS` 才算完整快速驗收通過。

## V0.2.4：雙引擎快速驗收（前一階段）

使用者已在 Windows 10 + .NET 10 SDK 10.0.403 上成功開啟 **V0.2.3 WPF 主視窗**，這確立 GUI 啟動能力，不等同 C#／Python 實際影片分析驗收。V0.2.4 新增 WPF 左側「**雙引擎快速驗收（合成影片）**」按鈕與根目錄 `Quick-Engine-Gate-Windows.bat`。

這項快速驗收僅使用自製 `demo/demo.mp4`：Python 依賴、pytest、C# CLI Release、自測、兩引擎的短合成影片辨識、各引擎對照 9 手已知正解、棋譜／勝者一致性，以及 WPF Release 編譯。**完全不重跑你之前 961 影格／41 手的第三方影片，也不會修改已存的 41 手結果**。

按下按鈕後，結果會保存在 `%LOCALAPPDATA%\GomokuVision\Gates\quick-gate-*.log` 與 `quick-gate-latest.json`，包含每項 PASS／FAIL、耗時與出錯位置；失敗不會假裝成功。需要 Windows 10/11、.NET 10 SDK、Python 3.10+，以及 `opencv-python`、`numpy`、`pytest`（尚未安裝時：`python -m pip install -r python\requirements-dev.txt`）。

可不開啟 WPF，直接在專案根目錄雙擊：

```powershell
.\Quick-Engine-Gate-Windows.bat
```

測試成功會印出 `QUICK_ENGINE_GATE_PASS`。這只代表合成測試、雙引擎一致性及 WPF **編譯**成功；WPF GUI 內各按鈕、手動校準、取消、真實影片準確率仍需另外驗收。MATLAB 仍屬歷史基線，沒有計入雙引擎測試。

上一版 V0.2.3 已由使用者 Windows 截圖確認實際開啟 WPF；**這一份新的 V0.2.4 尚未在 Windows 實機編譯／啟動**，不能僅憑這裡的 Python 靜態檢查宣稱完成全部驗收。

## V0.2.3：修復 Windows 回報的 CS1001 編譯錯誤

在 .NET 10 SDK 10.0.403 的 Windows 真實建置日誌中，`VisionDetector.cs` 第 196 行因 `[-1.,-1.]` 出現兩筆 `CS1001`。本版修正為 `new double[] { -1.0, -1.0 }`，並新增來源檢查測試。**這是原始碼問題，不需要重裝 .NET，也不必重新分析歷史影片。**

在全新解壓縮的 V0.2.3 資料夾雙擊 `scripts\Verify-WPF-Build-Windows.bat`。若輸出 `WPF_BUILD_PASS`，再雙擊 `scripts\Launch-Desktop-Windows.bat`。若遇到其他 CSxxxx 或 XAML 錯誤，請提供最新日誌；本版不宣稱 Windows WPF 已完成實測。

## V0.2.2 NuGet 相容性修復與免重跑結果檢視

若舊版 `Launch-Desktop-Windows.bat` 雙擊沒反應，請改用本版 `scripts/Launch-Desktop-Windows.bat`。它會顯示 .NET SDK／WPF 建置錯誤、留下 `%LOCALAPPDATA%\GomokuVision\Logs\launch-*.log`，若 WPF 無法啟動則明確標示失敗，不會直接讓視窗無聲關閉。詳見 [Windows 啟動疑難排解](docs/WINDOWS_STARTUP_TROUBLESHOOTING_zh_TW.md)。

**不需再跑數據：** `scripts/Show-Verified-Results-Windows.bat` 會直接開啟 [離線棋譜重播頁](docs/VerifiedResults.html)，不依賴 .NET 或 Python。套件已內附 `results/verified_historical`（41 手歷史棋譜、最終棋盤與統計），不包含第三方影片或原始影格。WPF 啟動成功後也會自動載入同一份快取結果。

既有 V0.2.2 已執行 Python 14/14 測試與完整原始影片辨識，41/41 手與舊 CSV 一致（非獨立標註準確率），耗時 7.44 秒；**Windows WPF 啟動與 C# 編譯仍未實機驗證**。


## V0.2.2：修復 Windows 回報的 NU1701（不需要重算原始影片）

已確認原本 `csharp/GomokuVision/GomokuVision.csproj` 的 `OpenCvSharp4.Windows` 對 `net10.0` 核心專案引入不必要的 `OpenCvSharp4.WpfExtensions`，在使用者的 .NET SDK 10.0.403 上顯示 `error NU1701`。本版只修改依賴拆分與測試／文件，不修改辨識門檻、41 手棋譜或 MATLAB 歷史原碼。

- **舊版：** `OpenCvSharp4.Windows 4.13.0.20260627`（含 WPF 擴充相依）
- **新版：** `OpenCvSharp4 4.13.0.20260627` + `OpenCvSharp4.runtime.win 4.13.0.20260627`
- C# 引擎仍是 `net10.0`；Desktop 仍是 `net10.0-windows`／`UseWPF=true`。WPF 的影像顯示使用內建 `BitmapImage`，不需要 OpenCvSharp WpfExtensions。
- **只測編譯，不重跑任何影片：** `scripts\Verify-WPF-Build-Windows.bat`。成功時顯示 `WPF_BUILD_PASS`。
- **正式啟動：** `scripts\Launch-Desktop-Windows.bat`，成功才算 WPF 已開啟；若有新錯誤，查看 `%LOCALAPPDATA%\GomokuVision\Logs`。

本次修正已完成相依結構靜態驗證與 Python 回歸；目前工作環境沒有 Windows／.NET SDK，**沒有宣稱 Windows C# 或 WPF 已經編譯通過**。

## 核心功能

| 模組 | MATLAB 歷史原版 | Python / OpenCV | C# / OpenCvSharp + WPF |
|---|---|---|---|
| 15×15 棋盤、黑白棋辨識 | 原版 | ✅ | ✅ CLI + WPF 可選 |
| 舊 CSV 225 點座標相容 | 原版 | ✅ | ✅ |
| 取樣頻率／全盤掃描分離 | 舊版有已知問題 | ✅ | ✅ |
| NCC 模板匹配與時間確認 | 原版 | ✅ | ✅ |
| 五連線判定／棋譜 CSV | ✅ | ✅ | ✅ |
| Top-5 啟發式建議 | 歷史實作 | ✅ 進階戰術優先 | ✅ 同一套評分規則 |
| 四角手動校準（不是自動找角） | 未隨原包提供 | ✅ 命令列 | ✅ 影片點選 GUI |
| Windows 圖形介面 | MATLAB figure | CLI，選用 OpenCV 預覽 | ✅ WPF 源碼，待 Windows GUI 驗收 |
| 中英雙語介面 | 無 | CLI 英文 | ✅ 繁中／英文 |
| 分析中影格預覽／取消 | 原版 | ✅ WPF Python 模式 | ✅ WPF C# 模式 |
| 自動化驗收 | 無 | ✅ Linux 本機已測 | ⚠️ 需 Windows/.NET 10 驗證 |

### 技術定位（不要誤標 AI）

本系統使用 **NCC 模板比對 + ROI 掃描 + 棋局啟發式評分**，不是神經網路、Gemini API、YOLO、Minimax 或正式電腦棋力引擎。新增加「自己下一手可直接獲勝」及「對方下一手可直接獲勝則優先防守」的**單步戰術優先規則**；沒有多回合博弈樹搜尋，無法保證推薦為最佳步。

## 專案樹

```text
GomokuVision_Advanced_V0.2.6/
├── csharp/
│   ├── GomokuVision/               .NET 10 獨立 CLI 與 OpenCvSharp 引擎
│   └── GomokuVision.Desktop/       Windows WPF 雙引擎、中英文 GUI、四角校準
├── python/
│   ├── gomoku/                     獨立 Python 影像辨識與棋步分析
│   ├── tests/                      核心、戰術、校準、影片回歸及取消
│   └── tools/                      合成影片、四角 CSV 產生、雙語言比對
├── matlab/legacy/                 2025 MATLAB 原程式（保留歷史，不宣稱已修正）
├── demo/                          自行合成棋盤影片、模板與校準點
├── data/                          舊 CSV 的幾何及棋譜示例
├── results/verified_historical/   已分析的 41 手結果（不含原影片與影格）
├── scripts/                       Windows 啟動、離線結果瀏覽與一鍵測試
├── docs/                          離線結果頁、驗收、授權、技術差異
└── .github/workflows/ci.yml       Linux Python、Windows .NET + WPF + 兩引擎回歸
```

## 安裝需求

- Windows 10/11 x64；桌面版僅支援 Windows。
- **.NET SDK 10**（第一次 `dotnet restore/build` 需能存取 NuGet）；C# 引擎使用套件 `OpenCvSharp4 4.13.0.20260627` 與 `OpenCvSharp4.runtime.win 4.13.0.20260627`。
- **Python 3.10+**，建議 Python 3.12，搭配 `pip`。Python 引擎與 Linux 測試需 `opencv-python`, `numpy`, `pytest`。
- MATLAB 歷史程式需單獨安裝 MATLAB 及相應工具箱；Python / C# 不需 MATLAB Runtime。

### 直接開啟 Windows WPF

將 ZIP 解壓至可讀寫位置，在根目錄執行：

```powershell
.\scripts\Launch-Desktop-Windows.bat
```

或使用命令：

```powershell
dotnet run -c Release --project .\csharp\GomokuVision.Desktop\GomokuVision.Desktop.csproj
```

桌面介面步驟：

1. 選擇一段固定鏡頭的棋局影片。
2. 選擇 225 點校準 CSV；若沒有，可按「從影片手動點選四角校準」，依左上→右上→左下→右下順序點選**最外圈四個網格交叉點**，儲存新 CSV。
3. 選擇合法且來源明確的黑棋／白棋 PNG 模板。
4. 選擇 **C# / OpenCvSharp** 或 **Python / OpenCV**；後者需要 Python 已加入 PATH 且以原始碼資料夾啟動。
5. 設定取樣、全盤掃描及 NCC 門檻，按「開始辨識與預測」。
6. 觀察分析進度、最近影格、棋譜表、最終棋盤及兩方 Top-5 推薦；可使用「取消分析」安全收尾並保留部分輸出。

桌面版是**新撰寫的實際 WPF 原始碼**，但目前交付環境沒有 Windows/.NET SDK，**尚未經 Windows 真實建置及人工 GUI 驗收**。Windows 上若出現編譯或執行問題，請依 `docs/WINDOWS_ACCEPTANCE_zh_TW.md` 留下錯誤輸出；不得宣稱已 GUI PASS。

### Windows 一鍵自動化測試

```powershell
.\scripts\Run-All-Local-Windows.bat
```

它會檢查 Python 測試、合成影片端到端、.NET CLI 自測、C# 影片處理、兩種引擎棋譜比對、WPF Release 建置。只有全部通過才會顯示 `ALL_LOCAL_AUTOMATED_GATES_PASS`。

如果尚未安裝 .NET：

```powershell
.\scripts\Run-All-Local-Windows.bat -SkipDotnet
```

此時只代表 `PYTHON_ONLY_PASS`，絕不代表 C# / WPF 已通過。

### 只執行 Python

```powershell
python -m pip install -r .\python\requirements-dev.txt
$env:PYTHONPATH = ".\python"
python -m pytest -q .\python\tests
python -m gomoku --input .\demo\demo.mp4 `
  --calibration .\demo\checkerboard_points.csv `
  --black-template .\demo\black.png --white-template .\demo\white.png `
  --output-dir .\results\python --sample-every 2 --full-scan-every 3 --scale 0.5 --white-threshold 0.75
```

### 只執行 C#

```powershell
dotnet run --project .\csharp\GomokuVision\GomokuVision.csproj -- --self-test

dotnet run --project .\csharp\GomokuVision\GomokuVision.csproj -- `
  --input .\demo\demo.mp4 `
  --calibration .\demo\checkerboard_points.csv `
  --black-template .\demo\black.png --white-template .\demo\white.png `
  --output-dir .\results\csharp --sample-every 2 --full-scan-every 3 --scale 0.5 --white-threshold 0.75
```

## 輸出規格

| 檔案 | 說明 |
|---|---|
| `output.mp4` | 已抽樣的畫面與棋子／預測標記；FPS 依跳幀比例調整 |
| `moves.csv` | Index,Frame,Color,Row,Col,Position |
| `moves_legacy.csv` | Round,Black,White（相容舊 MATLAB） |
| `summary.json` | frames_read / frames_analyzed / diagnostics / canceled / winner / move suggestions |
| `board_final.png` | 最終 15×15 棋盤 |
| `last_frame.png` | 用於 WPF 的最近處理影格 |

棋步顯示格式為**欄 A–O + 列 1–15**，例如 `H8`。舊 `checkerboard_points.csv` 則是**字母表示 row、數字表示 col**，兩者已做相容轉換，**不可直接按棋步位置解析校準座標**。

### 實驗與限制

- 原有 2025 影片為 961 個來源幀；Python 新版採 `sample-every=6`，分析 161 幀，輸出的**41 手落子（位置與黑白順序）與歷史 CSV 在去除空白後完全一致**。這是**相對於舊專題輸出的回歸一致性**，不是獨立人工標註的 100% 準確率。
- 自行生成合成影片與 Python 單元／整合測試已在此工作環境通過；C# CLI 與 WPF 尚須 Windows 建置與影片端到端、雙引擎一致性、人機互動測試。
- 棋盤自動偵測、鏡頭晃動穩定化、遮擋補償、深度學習辨識及 Minimax **不在此版**。
- 四角校準是人為標記 + 雙線性內插。透視嚴重失真時，需要更高精度相機校正，不能保證效果。
- 多步同時出現或落子時間接近取樣間隔時，辨識時序未必準確；沒有強制輪流落子校驗。

## 公開 GitHub 之前

保留 `matlab/legacy` 需先確認原創歸屬、課堂素材與任何共同作者權利。此包刻意**沒有任意指定 MIT 授權**；請由權利人決定 LICENSE。**不要將原始第三方 YouTube 影片、影片中擷取的模板、含學號姓名的 PDF、私人資料或 API 金鑰加入 repository。**

詳見：[英文說明](README_EN.md) · [Windows GUI 驗收](docs/WINDOWS_ACCEPTANCE_zh_TW.md) · [發布清單](docs/PUBLISH_CHECKLIST_zh_TW.md) · [驗證紀錄](docs/VALIDATION_SUMMARY.json)
