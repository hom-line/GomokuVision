# GomokuVision — Publication status / 發布狀態

Updated / 更新：2026-11-09

| Item / 項目 | Verified status / 狀態 |
| --- | --- |
| Repository / 儲存庫 | Public; modern source and documentation available on `main` |
| README | One English–Traditional Chinese interleaved `README.md` / 單一中英混排 |
| Recognition engines / 辨識引擎 | Modern MATLAB, Python and C# sources published |
| Windows desktop | WPF source included; build using .NET 10 SDK / 附原始碼，需自行編譯 |
| Web Replay | Browser source included; interactive browser acceptance pending / 網頁實機驗收待完成 |
| Demo | Self-generated 961-frame / 41-move synthetic reference and verified video archives |
| Windows synthetic results | 36/36 PASS with 41/41 reference moves on **one** synthetic game |
| License | [MIT](../../LICENSE) for author's work; dependencies retain upstream licenses |
| Release | [GomokuVision](https://github.com/hom-line/GomokuVision/releases/tag/GomokuVision) is published with `GomokuVision_v0.3.9_Source.zip` and its SHA-256 file |
| GitHub Actions | Both Python and Windows jobs passed on 2026-11-08 at commit `92ae3230`; check [live CI](https://github.com/hom-line/GomokuVision/actions/workflows/ci.yml) for later maintenance commits |
| GitHub Pages | Not enabled; no verified hosted Web Replay URL |

**Release version / 版本：** v0.3.9. **Repository and existing release tag / 專案與既有標籤：** GomokuVision.

Changes on `main` after the release do **not** silently replace the already published source ZIP. The 2025 course MATLAB files and original third-party footage remain excluded. The three playback labels do not accelerate recognition, and one synthetic benchmark is not a real-world accuracy estimate.
