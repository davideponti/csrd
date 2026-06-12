-- ============================================================
-- CSRD Comply — Patch schema Supabase (SICURO, solo ADD COLUMN)
-- Esegui nel SQL Editor di Supabase — NON cancella dati esistenti
-- ============================================================

-- Users: colonne auth/OTP
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_code VARCHAR(6);
ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_password_token VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_password_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0;

-- Reports: tutte le colonne richieste dal modello SQLAlchemy
ALTER TABLE reports ADD COLUMN IF NOT EXISTS table_data JSONB;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS review_comments JSONB;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS gap_analysis_results JSONB;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS narrative_content JSONB;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS ixbrl_tags_applied BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS ixbrl_metadata JSONB;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS approved_by UUID;

-- Unique constraint anti-duplicati report (ignora se già presente)
DO $$ BEGIN
    ALTER TABLE reports
        ADD CONSTRAINT uq_report_company_title_year
        UNIQUE (company_id, title, reporting_year);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Subscriptions: colonne billing
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS billing_cycle VARCHAR(20) NOT NULL DEFAULT 'monthly';
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS current_period_start DATE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS current_period_end DATE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS trial_end DATE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS canceled_at TIMESTAMP;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS auto_renew BOOLEAN NOT NULL DEFAULT true;

-- Alembic: aggiorna versione target (non cancellare dati)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
INSERT INTO alembic_version (version_num) VALUES ('d2d4919460f11')
ON CONFLICT (version_num) DO UPDATE SET version_num = EXCLUDED.version_num;

ALTER TABLE company_context_settings ADD COLUMN IF NOT EXISTS extended_kpis JSONB;

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'reports'
ORDER BY ordinal_position;
