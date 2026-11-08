from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[2]


def test_default_english_and_chinese_available():
    xaml=(ROOT/"csharp/GomokuVision.Desktop/MainWindow.xaml").read_text(encoding="utf-8")
    cs=(ROOT/"csharp/GomokuVision.Desktop/MainWindow.xaml.cs").read_text(encoding="utf-8")
    assert 'x:Name="LanguageBox" Width="142" Height="32" SelectedIndex="1"' in xaml
    assert '<ComboBoxItem Content="繁體中文"/>' in xaml
    assert '<ComboBoxItem Content="English"/>' in xaml
    assert 'private bool English => LanguageBox.SelectedIndex == 1;' in cs
    assert 'ApplyLanguage();' in cs


def test_english_docs_and_public_evidence_are_deidentified():
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    assert readme.startswith("# GomokuVision")
    assert 'English-first' in readme
    assert '## 繁體中文 / Traditional Chinese' in readme
    assert (ROOT/"docs/PUBLICATION_READINESS.md").is_file()
    with (ROOT/"docs/benchmarks/windows_36_case_results_2026-11-08.csv").open(encoding="utf-8", newline="") as file:
        rows=list(csv.DictReader(file))
    assert len(rows)==36
    assert all(row['status']=='PASS' and row['oracle_verified']=='PASS' for row in rows)
    assert {row['playback_speed'] for row in rows}=={'1','2','4'}
    assert 'result_dir' not in rows[0] and 'log_file' not in rows[0]
