-- FIX per Supabase: crea lo schema di migrazione mancante
CREATE SCHEMA IF NOT EXISTS supabase_migrations;

CREATE TABLE IF NOT EXISTS supabase_migrations.schema_migrations (
    version TEXT NOT NULL PRIMARY KEY,
    statements TEXT[],
    name TEXT,
    inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Inserisci il record della migrazione già eseguita
INSERT INTO supabase_migrations.schema_migrations (version, name)
VALUES ('20260611000100', 'initial_schema')
ON CONFLICT (version) DO NOTHING;