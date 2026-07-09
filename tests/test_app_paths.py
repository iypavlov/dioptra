import sys

from dioptra.app_paths import app_root, asset_path


def test_app_root_in_dev_points_to_project_root():
    root = app_root()
    assert (root / "src" / "dioptra" / "__main__.py").is_file()
    assert (root / "assets" / "icon.png").is_file()


def test_asset_path_in_dev():
    path = asset_path("icon.png")
    assert path.is_file()
    assert path.name == "icon.png"


def test_app_root_in_frozen_uses_meipass(monkeypatch, tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "icon.png").write_bytes(b"fake")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert app_root() == tmp_path
    assert asset_path("icon.png").is_file()
