-- ============================================================
-- CSRD Comply — Complete Database Schema
-- Esegui tutto in una volta nel Supabase SQL Editor
-- ============================================================

-- 1. Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Create ENUM types
DO $$ BEGIN
    CREATE TYPE userrole AS ENUM ('admin', 'contributor', 'viewer');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE reportstatus AS ENUM ('draft', 'review', 'final', 'filed');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE assessmentstatus AS ENUM ('draft', 'in_progress', 'completed', 'audited');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE subscriptiontier AS ENUM ('free', 'pro', 'team', 'enterprise');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- 3. Companies
CREATE TABLE IF NOT EXISTS companies (
    company_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL,
    vat_number VARCHAR(50) UNIQUE,
    country VARCHAR(5) NOT NULL,
    sector VARCHAR(10) NOT NULL,
    employee_count INTEGER,
    turnover FLOAT,
    balance_sheet_total FLOAT,
    csrd_wave INTEGER NOT NULL,
    reporting_year INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 4. Users
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role userrole NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login TIMESTAMP,
    token_version INTEGER NOT NULL DEFAULT 0,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    otp_code VARCHAR(6),
    otp_expires_at TIMESTAMP,
    otp_attempts INTEGER NOT NULL DEFAULT 0,
    reset_password_token VARCHAR(255),
    reset_password_expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);

-- 5. ESRS Datapoints
CREATE TABLE IF NOT EXISTS esrs_datapoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    standard_ref VARCHAR(50) NOT NULL,
    paragraph_ref VARCHAR(50),
    disclosure_requirement TEXT NOT NULL,
    data_type VARCHAR(20) NOT NULL,
    unit VARCHAR(50),
    is_mandatory BOOLEAN NOT NULL DEFAULT false,
    is_conditional BOOLEAN NOT NULL DEFAULT false,
    phase_in_year INTEGER,
    sfd_ref VARCHAR(100)
);
CREATE INDEX IF NOT EXISTS ix_esrs_datapoints_standard_ref ON esrs_datapoints (standard_ref);

-- 6. Reports (with table_data column)
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    reporting_year INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    status reportstatus NOT NULL DEFAULT 'draft',
    xhtml_content TEXT,
    xbrl_validation_passed BOOLEAN,
    filed_at TIMESTAMP,
    filed_to VARCHAR(100),
    table_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 7. Emissions Data
CREATE TABLE IF NOT EXISTS emissions_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    reporting_year INTEGER NOT NULL,
    scope VARCHAR(10) NOT NULL,
    category VARCHAR(50),
    value FLOAT NOT NULL,
    unit VARCHAR(20) NOT NULL,
    calculation_method VARCHAR(50),
    emission_factor_source VARCHAR(50),
    verified BOOLEAN NOT NULL DEFAULT false,
    verification_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 8. Materiality Assessment
CREATE TABLE IF NOT EXISTS materiality_assessment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    assessment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status assessmentstatus NOT NULL DEFAULT 'draft',
    methodology_version VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 9. Materiality Scores
CREATE TABLE IF NOT EXISTS materiality_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES materiality_assessment(id),
    datapoint_id UUID NOT NULL REFERENCES esrs_datapoints(id),
    impact_scale INTEGER,
    impact_scope INTEGER,
    impact_irremediability INTEGER,
    impact_likelihood INTEGER,
    financial_magnitude INTEGER,
    financial_likelihood INTEGER,
    total_impact_score FLOAT,
    total_financial_score FLOAT,
    is_material BOOLEAN NOT NULL DEFAULT false,
    rationale TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 10. Subscriptions (with all columns)
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) UNIQUE,
    tier subscriptiontier NOT NULL DEFAULT 'free',
    is_active BOOLEAN NOT NULL DEFAULT true,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),
    billing_cycle VARCHAR(20) NOT NULL DEFAULT 'monthly',
    current_period_start DATE,
    current_period_end DATE,
    trial_end DATE,
    canceled_at TIMESTAMP,
    auto_renew BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 11. Sustainability Matters
CREATE TABLE IF NOT EXISTS sustainability_matters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    standard VARCHAR(20) NOT NULL,
    topic_name VARCHAR(255) NOT NULL,
    sub_topic VARCHAR(255),
    sub_sub_topic VARCHAR(255),
    category VARCHAR(20) NOT NULL,
    mandatory BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX IF NOT EXISTS ix_sustainability_matters_standard ON sustainability_matters (standard);

-- 12. Company Context
CREATE TABLE IF NOT EXISTS company_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) UNIQUE,
    value_chain_description TEXT,
    key_activities JSON,
    business_relationships JSON,
    geographical_scope JSON,
    stakeholder_groups JSON,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 13. Regulatory Updates
CREATE TABLE IF NOT EXISTS regulatory_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    regulation VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    effective_date DATE NOT NULL,
    affected_standards JSON,
    source_url VARCHAR(500),
    ai_summary TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 14. ESRS Datapoint Cache
CREATE TABLE IF NOT EXISTS esrs_datapoint_cache (
    cache_key VARCHAR(512) PRIMARY KEY,
    cache_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_esrs_datapoint_cache_key ON esrs_datapoint_cache (cache_key);

-- 15. Company Context Settings
CREATE TABLE IF NOT EXISTS company_context_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id) UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    company_name VARCHAR(255),
    country VARCHAR(255),
    sector VARCHAR(255),
    reporting_year INTEGER,
    employee_count_total INTEGER,
    employee_count_permanent INTEGER,
    employee_count_temporary INTEGER,
    employee_count_male INTEGER,
    employee_count_female INTEGER,
    employee_count_other INTEGER,
    employee_count_by_geography JSON,
    annual_revenue_eur FLOAT,
    operational_sites_count INTEGER,
    scope1_emissions FLOAT,
    scope2_location_based FLOAT,
    scope2_market_based FLOAT,
    scope3_total FLOAT,
    scope3_material_categories JSON,
    emissions_baseline_year INTEGER,
    emissions_methodology VARCHAR(255),
    tier1_suppliers_count INTEGER,
    tier2_suppliers_count INTEGER,
    value_chain_countries JSON,
    high_risk_countries JSON,
    suppliers_code_of_conduct_pct FLOAT,
    supplier_audits_last_year INTEGER,
    ltifr FLOAT,
    fatal_accidents INTEGER,
    voluntary_turnover_pct FLOAT,
    avg_training_hours_per_year FLOAT,
    women_in_management_pct FLOAT,
    gender_pay_gap_pct FLOAT,
    union_coverage_pct FLOAT,
    employee_engagement_score FLOAT,
    standard_payment_terms_days INTEGER,
    avg_actual_payment_time_days FLOAT,
    invoices_paid_within_terms_pct FLOAT,
    invoices_paid_late_pct FLOAT,
    anti_corruption_training_pct FLOAT,
    corruption_incidents_last_year INTEGER,
    whistleblowing_reports_received INTEGER
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_company_context_settings_company_id ON company_context_settings (company_id);

-- 16. Create and set Alembic version
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('d2d4919460f8');
