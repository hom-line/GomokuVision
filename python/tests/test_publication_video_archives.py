from pathlib import Path
import hashlib, lzma, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
VIDEOS=ROOT/'demo/full_game'
EXPECTED={
 'full_game_961.mp4': '0518c8f5e0627e396ca1e4d5a9e0ff687008f8c90efe0b9ac91875c29c594641',
 'full_game_synced_961_2x.mp4': 'dcaf2f52e04c7cf6958fc9f693a4dd6695787d4c1170076064206bf2f771c84b',
 'full_game_recognition_green_961_2x.mp4': '57e44acdae41fc28a2ae8e89b0e10249b87ac9fcfb662fcbef53c79374bb1e07',
 'full_game_recognition_prediction_green_961_2x.mp4': '533cb23731dd36d32ea6276ba9967315633c89ed8a4456e2c41ecdd34fa2ced0',
}
def test_archive_bytes_match_original_reference_video_sha():
    for name,sha in EXPECTED.items():
        packed=(VIDEOS/(name+'.xz'))
        assert packed.is_file()
        assert hashlib.sha256(lzma.decompress(packed.read_bytes())).hexdigest()==sha

def test_readme_bilingual_single_file_and_browser_video():
    text=(ROOT/'README.md').read_text('utf8')
    assert '## 📖 About / 專案簡介' in text
    assert '## ✨ Features / 主要功能' in text
    assert '2025 university final course assignment' in text
    assert '2025 年大學課程期末作業' in text
    assert 'README.md#繁體中文--traditional-chinese' not in (ROOT/'index.html').read_text(encoding='utf-8')
    assert not (ROOT/'README_zh_TW.md').exists()
    assert (VIDEOS/'full_game_961_web.mp4').is_file()
