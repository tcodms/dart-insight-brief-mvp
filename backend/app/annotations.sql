CREATE TABLE IF NOT EXISTS report_annotations (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 brief_id TEXT, personal_analysis_id TEXT, content_version TEXT NOT NULL,
 start_offset INTEGER NOT NULL CHECK(start_offset >= 0),
 end_offset INTEGER NOT NULL CHECK(end_offset > start_offset),
 quote TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
 CHECK((brief_id IS NOT NULL) != (personal_analysis_id IS NOT NULL)),
 FOREIGN KEY(brief_id,user_id) REFERENCES company_briefs(id,user_id) ON DELETE CASCADE,
 FOREIGN KEY(personal_analysis_id,user_id) REFERENCES personal_analyses(id,user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS annotations_brief ON report_annotations(user_id,brief_id);
CREATE INDEX IF NOT EXISTS annotations_personal ON report_annotations(user_id,personal_analysis_id);
PRAGMA user_version = 2;
