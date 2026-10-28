PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, google_sub TEXT NOT NULL UNIQUE, email TEXT NOT NULL,
 name TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 csrf_token TEXT NOT NULL, expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_expiry ON sessions(expires_at);
CREATE TABLE IF NOT EXISTS document_counters (
 user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 kind TEXT NOT NULL CHECK(kind IN ('report','cv','jd')), last_version INTEGER NOT NULL,
 PRIMARY KEY(user_id,kind)
);
CREATE TABLE IF NOT EXISTS documents (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 kind TEXT NOT NULL CHECK(kind IN ('report','cv','jd')), original_name TEXT NOT NULL,
 storage_key TEXT NOT NULL UNIQUE, version INTEGER NOT NULL CHECK(version > 0),
 content_hash TEXT NOT NULL, byte_size INTEGER NOT NULL, pages INTEGER NOT NULL CHECK(pages > 0),
 created_at TEXT NOT NULL, UNIQUE(id,user_id), UNIQUE(user_id,kind,version)
);
CREATE INDEX IF NOT EXISTS documents_owner ON documents(user_id,created_at);
CREATE TABLE IF NOT EXISTS company_briefs (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 report_document_id TEXT NOT NULL, company_name TEXT NOT NULL, report_year INTEGER,
 result_json TEXT NOT NULL CHECK(json_valid(result_json)), schema_version INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL, UNIQUE(id,user_id),
 FOREIGN KEY(report_document_id,user_id) REFERENCES documents(id,user_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS personal_analyses (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 brief_id TEXT NOT NULL, cv_document_id TEXT NOT NULL, jd_document_id TEXT, target_role TEXT NOT NULL,
 result_json TEXT NOT NULL CHECK(json_valid(result_json)), schema_version INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL, UNIQUE(id,user_id),
 FOREIGN KEY(brief_id,user_id) REFERENCES company_briefs(id,user_id) ON DELETE CASCADE,
 FOREIGN KEY(cv_document_id,user_id) REFERENCES documents(id,user_id) ON DELETE CASCADE,
 FOREIGN KEY(jd_document_id,user_id) REFERENCES documents(id,user_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS evidence (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 document_id TEXT NOT NULL, brief_id TEXT, personal_analysis_id TEXT,
 page INTEGER NOT NULL CHECK(page > 0), quote TEXT NOT NULL, section TEXT NOT NULL,
 CHECK((brief_id IS NOT NULL) != (personal_analysis_id IS NOT NULL)),
 FOREIGN KEY(document_id,user_id) REFERENCES documents(id,user_id) ON DELETE CASCADE,
 FOREIGN KEY(brief_id,user_id) REFERENCES company_briefs(id,user_id) ON DELETE CASCADE,
 FOREIGN KEY(personal_analysis_id,user_id) REFERENCES personal_analyses(id,user_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS analysis_jobs (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 job_type TEXT NOT NULL CHECK(job_type IN ('brief','personal')), report_document_id TEXT,
 brief_id TEXT, cv_document_id TEXT, jd_document_id TEXT, target_role TEXT,
 status TEXT NOT NULL CHECK(status IN ('queued','running','succeeded','failed','cancelled')),
 stage TEXT, result_id TEXT, error_code TEXT, created_at TEXT NOT NULL, finished_at TEXT,
 FOREIGN KEY(report_document_id,user_id) REFERENCES documents(id,user_id) ON DELETE CASCADE,
 FOREIGN KEY(brief_id,user_id) REFERENCES company_briefs(id,user_id) ON DELETE CASCADE,
 FOREIGN KEY(cv_document_id,user_id) REFERENCES documents(id,user_id) ON DELETE CASCADE,
 FOREIGN KEY(jd_document_id,user_id) REFERENCES documents(id,user_id) ON DELETE CASCADE
);
PRAGMA user_version = 1;
