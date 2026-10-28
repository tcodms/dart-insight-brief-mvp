import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, path: Path):
        self.path = path

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            version = conn.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1):
                raise RuntimeError('Unsupported database schema version')
            conn.execute('PRAGMA journal_mode = WAL')
            if version == 0:
                conn.executescript(Path(__file__).with_name('schema.sql').read_text(encoding='utf-8'))

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        try:
            with conn:
                yield conn
        finally:
            conn.close()
