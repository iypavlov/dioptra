import hashlib
import sqlite3
import time
from pathlib import Path


class TranslationCache:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = str(Path.home() / ".screen-translator" / "cache.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                image_hash TEXT PRIMARY KEY,
                word TEXT,
                translation TEXT,
                source_lang TEXT,
                target_lang TEXT,
                created_at REAL
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_created ON cache(created_at)"
        )
        self._conn.commit()
        self._ttl = 3600

    def cleanup(self):
        self._conn.execute("DELETE FROM cache WHERE created_at <= ?", (time.time() - self._ttl,))
        self._conn.commit()

    def get(self, image_bytes: bytes, target_lang: str = "ru") -> tuple[str, str] | None:
        self.cleanup()
        h = self._hash(image_bytes)
        row = self._conn.execute(
            "SELECT word, translation FROM cache WHERE image_hash = ? AND target_lang = ?",
            (h, target_lang),
        ).fetchone()
        return row if row else None

    def set(self, image_bytes: bytes, word: str, translation: str, target_lang: str = "ru"):
        self.cleanup()
        h = self._hash(image_bytes)
        self._conn.execute(
            "INSERT OR REPLACE INTO cache VALUES (?, ?, ?, ?, ?, ?)",
            (h, word, translation, "en", target_lang, time.time()),
        )
        self._conn.commit()

    def _hash(self, data: bytes) -> str:
        return hashlib.md5(data).hexdigest()

    def close(self) -> None:
        self._conn.close()
