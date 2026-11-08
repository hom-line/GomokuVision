"""Guard against the exact CS1001 floating-point literal regression in C# source.

This is a SOURCE guard, not a substitute for dotnet build on Windows.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def test_vision_detector_scores_are_valid_csharp_literals():
    source = (ROOT / "csharp" / "GomokuVision" / "VisionDetector.cs").read_text(encoding="utf-8")
    assert "double[] scores = new double[] { -1.0, -1.0 };" in source
    assert not re.search(r"(?<![\w.])\d+\.(?![\d\w.])", source)


def test_core_uses_separate_opencv_dependencies():
    csproj = (ROOT / "csharp" / "GomokuVision" / "GomokuVision.csproj").read_text(encoding="utf-8")
    assert 'Include="OpenCvSharp4"' in csproj
    assert 'Include="OpenCvSharp4.runtime.win"' in csproj
    assert 'Include="OpenCvSharp4.Windows"' not in csproj
