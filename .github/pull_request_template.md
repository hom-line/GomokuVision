# Summary / 修改摘要

<!-- Describe what changed and why. / 說明修改內容與原因。 -->

## Scope / 影響範圍

- [ ] MATLAB recognition / MATLAB 辨識
- [ ] Python / OpenCV recognition / Python 辨識
- [ ] C# / OpenCvSharp recognition / C# 辨識
- [ ] Windows WPF desktop / Windows 桌面介面
- [ ] Web Replay / 網頁棋譜展示
- [ ] Benchmark / performance measurement / 測試與計時
- [ ] Documentation / CI / 文件與自動化

## Validation / 驗證紀錄

<!-- Provide commands and real results; do not mark checks complete without running them. / 請附實際執行的指令與結果。 -->

- [ ] Python regression tests have passed (or explain why not). / Python 回歸測試通過或說明未測原因
- [ ] Windows WPF build checked if desktop code changed. / 桌面程式改動已驗證 Windows 編譯
- [ ] Synthetic game recognition parity checked if algorithms changed. / 辨識演算法變更已確認棋譜一致性
- [ ] Frame timeline / ROI / coordinate impacts documented if applicable. / 說明時間軸、ROI 或座標影響
- [ ] Three timing scopes remain clearly separated if performance metrics changed. / 保留核心、引擎內及完整程序三種計時定義

## Safety and provenance / 素材來源與權利

- [ ] New source and assets can be distributed under this project's MIT License. / 確認新增內容具備 MIT 授權權利
- [ ] No private files, secrets, historical unreviewed MATLAB source or third-party source footage are included. / 未包含私人資料、憑證、歷史未審核程式或第三方原始影片
- [ ] Third-party dependencies and notices updated if needed. / 必要時更新第三方授權聲明

## Additional notes / 補充說明

<!-- Screenshots, linked issues, limitations and next steps. / 可放截圖、相關 Issues、限制與後續項目。 -->

> A 36/36 PASS result on one synthetic game is not proof of real-camera accuracy. Playback speed labels do not accelerate recognition. / 單一合成棋局 36/36 PASS 不代表真實攝影辨識準確率；播放倍率不加速運算。
