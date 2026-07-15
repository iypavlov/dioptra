from dioptra.app_paths import app_root, asset_path


def test_app_root_points_to_project_root():
    root = app_root()
    assert (root / "src" / "dioptra" / "__main__.py").is_file()
    assert (root / "assets" / "icon.png").is_file()


def test_asset_path_resolves_correctly():
    path = asset_path("icon.png")
    assert path.is_file()
    assert path.name == "icon.png"
