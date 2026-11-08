# GomokuVision — Publication checklist / 公開驗收

- [x] Author confirmed rights to the modern source and synthetic demonstration assets, with MIT licensing.
- [x] Root [MIT License](../../LICENSE) and [third-party notices](../../THIRD_PARTY_NOTICES.md) are published.
- [x] Historical 2025 course MATLAB files and original third-party footage are excluded.
- [x] Modern MATLAB, Python and C# engines, Windows WPF and static Web Replay sources are published on `main`.
- [x] The README is one interleaved English–Traditional Chinese file.
- [x] Synthetic Windows 36/36 benchmark evidence, CSV and three-level timing methodology are published.
- [x] Existing [GomokuVision Release](https://github.com/hom-line/GomokuVision/releases/tag/GomokuVision) includes the v0.3.9 source ZIP and SHA-256 attachment.
- [x] Python and Windows CI recorded a successful run at commit `92ae3230` on 2026-11-08.
- [ ] Confirm the latest maintenance commit passes [Python and Windows CI](https://github.com/hom-line/GomokuVision/actions/workflows/ci.yml).
- [ ] Validate actual Web Replay behavior in supported browsers.
- [ ] Enable GitHub Pages if a public hosted replay URL is desired, and then verify it.

The browser page replays a **known synthetic reference timeline**, not live MATLAB, Python or C# inference. The 36 scenarios are permutations of **one** self-generated video, not 36 independent real-world clips. No documentation-only maintenance should silently replace the historical v0.3.9 source ZIP.
