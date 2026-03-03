-- ============================================================================
-- CREATE TABLES
-- ============================================================================

-- Applications Statuses
CREATE TABLE IF NOT EXISTS application_statuses
(
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    is_terminal BOOLEAN     NOT NULL DEFAULT FALSE,
    CHECK (status_name <> '')
);

-- Positions
CREATE TABLE IF NOT EXISTS positions
(
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title      VARCHAR(50) NOT NULL,
    level      VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (title <> ''),
    CHECK (level <> '')
);

-- Companies
CREATE TABLE IF NOT EXISTS companies
(
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       VARCHAR(50) NOT NULL UNIQUE,
    industry   VARCHAR(50),
    location   VARCHAR(50),
    notes      VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (name <> ''),
    CHECK (industry IS NULL OR industry <> ''),
    CHECK (location IS NULL OR location <> '')
);

-- Recruiters
CREATE TABLE IF NOT EXISTS recruiters
(
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       VARCHAR(50) NOT NULL,
    email      VARCHAR(50) UNIQUE,
    phone      VARCHAR(50),
    company_id INTEGER     REFERENCES companies (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (name <> ''),
    CHECK (email IS NULL OR email <> ''),
    CHECK (phone IS NULL OR phone <> '')
);

-- Applications
CREATE TABLE IF NOT EXISTS applications
(
    id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id     INTEGER     NOT NULL REFERENCES companies (id) ON DELETE RESTRICT,
    position_id    INTEGER     NOT NULL REFERENCES positions (id) ON DELETE RESTRICT,
    recruiter_id   INTEGER     REFERENCES recruiters (id) ON DELETE SET NULL,
    job_id         VARCHAR(100),
    current_status INTEGER     NOT NULL REFERENCES application_statuses (id) ON DELETE RESTRICT,
    applied_date   DATE        NOT NULL DEFAULT CURRENT_DATE,
    notes          VARCHAR(255),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (job_id IS NULL OR job_id <> ''),
    CHECK (applied_date <= CURRENT_DATE),
    CHECK (applied_date >= CURRENT_DATE - INTERVAL '365 days')
);

-- Application Events
CREATE TABLE IF NOT EXISTS application_events
(
    id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id INTEGER      NOT NULL REFERENCES applications (id) ON DELETE CASCADE,
    event_type     VARCHAR(100) NOT NULL,
    event_date     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    notes          VARCHAR(255),
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (event_type <> ''),
    CHECK (event_date <= NOW())
);

-- ============================================================================
-- INDEXES FOR ANALYTICS PERFORMANCE
-- ============================================================================

-- Speed up company-based analytics and JOINs
CREATE INDEX IF NOT EXISTS idx_applications_company_id ON applications (company_id);

-- Speed up date range queries (past X days)
CREATE INDEX IF NOT EXISTS idx_applications_applied_date ON applications (applied_date);

-- Speed up position-based analytics and JOINs
CREATE INDEX IF NOT EXISTS idx_applications_position_id ON applications (position_id);

-- Speed up companies that haven't responded
CREATE INDEX IF NOT EXISTS idx_applications_current_status ON applications (current_status);

-- Speed up event timeline queries
CREATE INDEX IF NOT EXISTS idx_application_events_application_id ON application_events (application_id);

-- Case-insensitive company name lookups
CREATE INDEX IF NOT EXISTS idx_companies_name_lower ON companies (LOWER(name));

-- Speed up applications looked up by external posting ID
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications (job_id);
