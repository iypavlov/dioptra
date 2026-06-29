import time
import tempfile
from pathlib import Path

from src.cache import TranslationCache


def test_set_and_get() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        cache = TranslationCache(db_path=str(db_path))
        img = b"fake_image_bytes_123"
        cache.set(img, "hello", "привет")
        result = cache.get(img)
        assert result is not None
        word, translation = result
        assert word == "hello"
        assert translation == "привет"
        cache.close()


def test_get_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        cache = TranslationCache(db_path=str(db_path))
        result = cache.get(b"nonexistent")
        assert result is None
        cache.close()


def test_language_specific() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        cache = TranslationCache(db_path=str(db_path))
        img = b"test_image"
        cache.set(img, "hello", "привет", target_lang="ru")
        result_ru = cache.get(img, target_lang="ru")
        result_de = cache.get(img, target_lang="de")
        assert result_ru is not None
        assert result_de is None
        cache.close()


def test_ttl_expiry() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        cache = TranslationCache(db_path=str(db_path))
        cache._ttl = 0
        img = b"expired_image"
        cache.set(img, "hello", "привет")
        result = cache.get(img)
        assert result is None
        cache.close()


def test_cleanup_removes_expired() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        cache = TranslationCache(db_path=str(db_path))
        cache._ttl = -1
        img = b"cleanup_test"
        cache.set(img, "hello", "привет")
        row = cache._conn.execute(
            "SELECT COUNT(*) FROM cache WHERE image_hash = ?",
            (cache._hash(img),),
        ).fetchone()
        assert row[0] == 1
        cache.cleanup()
        row = cache._conn.execute(
            "SELECT COUNT(*) FROM cache WHERE image_hash = ?",
            (cache._hash(img),),
        ).fetchone()
        assert row[0] == 0
        cache.close()


def test_overwrite() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        cache = TranslationCache(db_path=str(db_path))
        img = b"overwrite_test"
        cache.set(img, "hello", "привет")
        cache.set(img, "hello", "здравствуйте")
        result = cache.get(img)
        assert result is not None
        assert result[1] == "здравствуйте"
        cache.close()
