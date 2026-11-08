"""Windows PowerShell 5.1-safe Python engine preflight.

Avoids `python -c '... "quoted text" ...'`, where PowerShell native-command
argument parsing can strip embedded quotes before Python receives the code.
This script imports modules without processing any video files.
"""
from __future__ import annotations

import importlib
import sys

REQUIRED = (
    ("cv2", "opencv-python"),
    ("numpy", "numpy"),
    ("pytest", "pytest"),
)


def main() -> int:
    missing = []
    for module, package in REQUIRED:
        try:
            loaded = importlib.import_module(module)
        except Exception as error:
            missing.append(f"{package}: {type(error).__name__}: {error}")
            continue
        print(f"DEPENDENCY_OK: {package} {getattr(loaded, '__version__', 'installed')}")

    if missing:
        print("DEPENDENCY_CHECK_FAIL: could not import required packages:", file=sys.stderr)
        for item in missing:
            print(f"  - {item}", file=sys.stderr)
        print(r"REMEDY: python -m pip install -r python\requirements-dev.txt", file=sys.stderr)
        return 2

    print("DEPENDENCY_CHECK_PASS: OpenCV, NumPy, pytest imported successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
