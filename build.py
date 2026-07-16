"""Build Dioptra as a standalone executable with PyInstaller."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def ensure_icon() -> Path:
    assets = PROJECT_ROOT / "assets"
    png = assets / "icon.png"
    ico = assets / "icon.ico"

    if not ico.exists():
        try:
            from PIL import Image

            img = Image.open(png)
            img.save(ico, format="ICO", sizes=[(img.width, img.height)])
            print(f"Created {ico}")
        except Exception as e:
            print(f"Could not convert icon to .ico: {e}")

    return ico


def main() -> None:
    ensure_icon()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(PROJECT_ROOT / "dioptra.spec"),
    ]

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        sys.exit(result.returncode)

    # Remove the outer launcher EXE, keep only the directory version
    outer_exe = PROJECT_ROOT / "dist" / "Dioptra.exe"
    if outer_exe.exists():
        outer_exe.unlink()
        print("Removed outer Dioptra.exe (keeping only dist/Dioptra/Dioptra.exe)")

    # Quick smoke test: run the EXE briefly to check for import errors
    dir_exe = PROJECT_ROOT / "dist" / "Dioptra" / "Dioptra.exe"
    if dir_exe.exists():
        print(f"\nSmoke-testing {dir_exe} ...")
        proc = subprocess.Popen(
            [str(dir_exe)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=PROJECT_ROOT,
        )
        try:
            proc.wait(timeout=5)
            err = proc.stderr.read().decode("utf-8", errors="replace")
            if err:
                print("STDERR:", err[:2000])
            if proc.returncode != 0:
                print(f"SMOKE TEST FAILED (exit code {proc.returncode})")
                sys.exit(1)
        except subprocess.TimeoutExpired:
            proc.kill()
            print("Smoke test passed (process stayed alive for 5s)")
        finally:
            proc.stderr.close()
            proc.stdout.close()


if __name__ == "__main__":
    main()
