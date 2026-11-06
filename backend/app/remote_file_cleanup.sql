BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS remote_file_cleanup (
    file_id TEXT PRIMARY KEY,
    key_digest TEXT NOT NULL,
    retry_after INTEGER NOT NULL DEFAULT 0
);
PRAGMA user_version = 4;
COMMIT;
