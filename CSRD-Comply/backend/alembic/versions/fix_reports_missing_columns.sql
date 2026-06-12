-- Fix: Aggiunge le colonne mancanti alla tabella `reports`
-- Esegui questo script direttamente sul database PostgreSQL
-- (se Alembic upgrade fallisce)

ALTER TABLE reports ADD COLUMN IF NOT EXISTS review_comments JSON;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS gap_analysis_results JSON;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS narrative_content JSON;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS ixbrl_tags_applied BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS ixbrl_metadata JSON;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS approved_by UUID;
