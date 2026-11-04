BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS public_briefs (
 id TEXT PRIMARY KEY, corp_code TEXT NOT NULL, receipt_no TEXT NOT NULL UNIQUE,
 company_name TEXT NOT NULL, filed_on TEXT NOT NULL, report_year INTEGER,
 report_name TEXT NOT NULL, content_hash TEXT NOT NULL, byte_size INTEGER NOT NULL,
 pages INTEGER NOT NULL, result_json TEXT NOT NULL CHECK(json_valid(result_json)),
 schema_version INTEGER NOT NULL, published_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS public_briefs_latest ON public_briefs(corp_code, filed_on DESC, receipt_no DESC);
CREATE TABLE IF NOT EXISTS public_brief_imports (
 user_id TEXT NOT NULL, public_brief_id TEXT NOT NULL REFERENCES public_briefs(id),
 brief_id TEXT NOT NULL, PRIMARY KEY(user_id, public_brief_id),
 FOREIGN KEY(brief_id,user_id) REFERENCES company_briefs(id,user_id) ON DELETE CASCADE
);
PRAGMA user_version = 3;
COMMIT;
