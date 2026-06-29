#!/usr/bin/env python3
"""Build script for Dioptra."""
import subprocess
import sys


def main() -> None:
    cmd = [sys.executable or "python", "-m", "PyInstaller", "dioptra.spec"]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
