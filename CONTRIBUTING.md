# Contributing / 參與貢獻

GomokuVision is an MIT-licensed educational computer vision project. Contributions to the modern MATLAB, Python and C# recognition engines, Windows WPF application, Web Replay, tests and documentation are welcome.

GomokuVision 是採用 MIT License 的教育與技術分享專案，歡迎參與三語言辨識、WPF、Web Replay、測試與文件改進。

## Before submitting / 提交前

1. Describe the change and the affected engine, ROI strategy, and overlay mode. / 說明修改內容及受影響的引擎和模式。
2. Supply a self-generated synthetic fixture and a reproducible regression test where applicable. / 使用可公開的自製資料，提供可重現測試。
3. State any effects on board coordinates, frame synchronization and benchmark timing definitions. / 說明座標、時間同步、計時口徑的變動。
4. Verify the Python suite and, for Windows-specific changes, the WPF build. / 確認 Python 回歸測試及必要的 WPF 編譯。
5. Contribute only material you have the rights to share under the repository's [MIT License](LICENSE). Respect all [third-party license terms](THIRD_PARTY_NOTICES.md). / 確認授權權利並遵守第三方依賴條款。

```powershell
python -m pip install -r python/requirements-dev.txt
$env:PYTHONPATH = "python"
python -m pytest -q python/tests
```

Do not upload the unreviewed 2025 historical MATLAB coursework, original third-party videos, personal files, credentials, or licensed MATLAB binaries. Synthetic 36/36 PASS is not a general real-world accuracy estimate.

請勿上傳 2025 年歷史課程原始檔、第三方影片、個資、憑證或 MATLAB 專有執行檔。合成測試 36/36 PASS 不代表真實環境辨識準確率。
