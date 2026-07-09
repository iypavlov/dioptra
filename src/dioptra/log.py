import logging
import os
import sys
from pathlib import Path

_LOG_FILE: Path | None = None
_LOGGER_INITIALIZED = False


def setup_logger(
    name: str = "dioptra",
    debug: bool | None = None,
    log_file: str | Path | None = None,
) -> logging.Logger:
    global _LOG_FILE, _LOGGER_INITIALIZED

    if _LOGGER_INITIALIZED:
        return logging.getLogger(name)

    if debug is None:
        debug = os.environ.get("DIOPTRA_DEBUG", "").lower() in ("1", "true", "yes", "debug")

    level = logging.DEBUG if debug else logging.INFO

    if log_file is None:
        log_dir = Path.home() / ".screen-translator"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "dioptra.log"

    _LOG_FILE = Path(log_file)

    # File handler always enabled
    file_handler = logging.FileHandler(str(_LOG_FILE), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter("[Dioptra] %(message)s")
    console_handler.setFormatter(console_formatter)

    root = logging.getLogger(name)
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    if debug:
        root.info("Debug mode enabled")

    _LOGGER_INITIALIZED = True
    return root


def get_logger(name: str = "dioptra") -> logging.Logger:
    if not _LOGGER_INITIALIZED:
        return setup_logger(name.split(".")[0] if "." in name else name)
    return logging.getLogger(name)


def debug_mode() -> bool:
    return logging.getLogger("dioptra").getEffectiveLevel() <= logging.DEBUG


def log_path() -> Path | None:
    return _LOG_FILE
