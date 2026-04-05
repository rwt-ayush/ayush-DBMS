-- =============================================================================
-- Placement Management System — Database Schema
-- Equivalent to Django migrations: 0001_initial + 0002_company_password
-- Compatible with SQLite (default) and easily adaptable to PostgreSQL / MySQL.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. placement_placementsection
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS placement_placementsection (
    section_id   INTEGER      PRIMARY KEY AUTOINCREMENT,
    section_name VARCHAR(120) NOT NULL,
    email        VARCHAR(254) NOT NULL DEFAULT '',
    phone        VARCHAR(30)  NOT NULL DEFAULT '',
    password     VARCHAR(128) NOT NULL DEFAULT ''
);

-- -----------------------------------------------------------------------------
-- 2. placement_student
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS placement_student (
    student_id  INTEGER      PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(120) NOT NULL,
    roll_no     VARCHAR(50)  NOT NULL UNIQUE,
    email       VARCHAR(254) NOT NULL UNIQUE,
    phone       VARCHAR(30)  NOT NULL DEFAULT '',
    password    VARCHAR(128) NOT NULL,
    profile_pic VARCHAR(200) NOT NULL DEFAULT '',
    github      VARCHAR(200) NOT NULL DEFAULT '',
    linkedin    VARCHAR(200) NOT NULL DEFAULT '',
    resume      VARCHAR(200) NOT NULL DEFAULT '',
    skills      TEXT         NOT NULL DEFAULT ''
);

-- -----------------------------------------------------------------------------
-- 3. placement_company  (includes password column added in migration 0002)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS placement_company (
    company_id   INTEGER      PRIMARY KEY AUTOINCREMENT,
    name         VARCHAR(150) NOT NULL,
    description  TEXT         NOT NULL DEFAULT '',
    website_link VARCHAR(200) NOT NULL DEFAULT '',
    location     VARCHAR(120) NOT NULL DEFAULT '',
    password     VARCHAR(128) NOT NULL DEFAULT ''
);

-- -----------------------------------------------------------------------------
-- 4. placement_job
--    FK → placement_company  (CASCADE DELETE)
--    FK → placement_placementsection  (SET NULL on delete)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS placement_job (
    job_id         INTEGER      PRIMARY KEY AUTOINCREMENT,
    company_id     INTEGER      NOT NULL
                                REFERENCES placement_company(company_id)
                                ON DELETE CASCADE
                                DEFERRABLE INITIALLY DEFERRED,
    section_id     INTEGER      NULL
                                REFERENCES placement_placementsection(section_id)
                                ON DELETE SET NULL
                                DEFERRABLE INITIALLY DEFERRED,
    position       VARCHAR(120) NOT NULL,
    description    TEXT         NOT NULL DEFAULT '',
    max_applicants INTEGER      NOT NULL DEFAULT 100 CHECK (max_applicants >= 0),
    pay_rate       VARCHAR(80)  NOT NULL DEFAULT '',
    post_date      DATE         NOT NULL DEFAULT (DATE('now'))
);

CREATE INDEX IF NOT EXISTS placement_job_company_id
    ON placement_job (company_id);

CREATE INDEX IF NOT EXISTS placement_job_section_id
    ON placement_job (section_id);

-- -----------------------------------------------------------------------------
-- 5. placement_application
--    FK → placement_student  (CASCADE DELETE)
--    FK → placement_job      (CASCADE DELETE)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS placement_application (
    app_id     INTEGER     PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER     NOT NULL
                           REFERENCES placement_student(student_id)
                           ON DELETE CASCADE
                           DEFERRABLE INITIALLY DEFERRED,
    job_id     INTEGER     NOT NULL
                           REFERENCES placement_job(job_id)
                           ON DELETE CASCADE
                           DEFERRABLE INITIALLY DEFERRED,
    status     VARCHAR(60) NOT NULL DEFAULT 'pending',
    applied_at DATETIME    NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

CREATE INDEX IF NOT EXISTS placement_application_student_id
    ON placement_application (student_id);

CREATE INDEX IF NOT EXISTS placement_application_job_id
    ON placement_application (job_id);
