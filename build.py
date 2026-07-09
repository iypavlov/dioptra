"""Build script for Dioptra.

Usage:
    python build.py          # Production build (windowed)
    python build.py --debug  # Debug build (console window)
    python build.py --clean  # Clean build/dist directories first
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def clean_build() -> None:
    for d in ["build", "dist"]:
        p = Path(d)
        if p.exists():
            print(f"Removing {p}...")
            shutil.rmtree(p)
    for spec_p in Path(".").glob("*.spec"):
        if spec_p.name != "dioptra.spec":
            spec_p.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Dioptra")
    parser.add_argument("--debug", action="store_true", help="Build with console window for debugging")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts first")
    args = parser.parse_args()

    if args.clean:
        clean_build()

    python = sys.executable or "python"
    cmd = [python, "-m", "PyInstaller", "dioptra.spec"]

    if args.debug:
        print("Building DEBUG version (with console)")
        cmd.append("--debug")
        cmd.append("console")

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
