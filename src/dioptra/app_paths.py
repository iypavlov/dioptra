from pathlib import Path


def app_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def asset_path(name: str) -> Path:
    return app_root() / "assets" / name
