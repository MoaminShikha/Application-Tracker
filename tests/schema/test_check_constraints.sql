-- ============================================================================
-- TEST 2: CHECK CONSTRAINTS (All Should FAIL)
-- ============================================================================
-- Purpose: Verify CHECK constraints prevent invalid data
-- Expected: All inserts FAIL with CHECK constraint violations

-- Note: Run test_valid_inserts.sql first to populate required reference data


-- Test 2.1: Empty String in status_name
-- Expected: FAIL - CHECK constraint violated (status_name <> '')
INSERT INTO application_statuses (status_name)
VALUES ('');


-- Test 2.2: Empty String in company name
-- Expected: FAIL - CHECK constraint violated (name <> '')
INSERT INTO companies (name, location)
VALUES ('', 'New York');


-- Test 2.3: Empty String in company location
-- Expected: FAIL - CHECK constraint violated (location <> '')
INSERT INTO companies (name, location)
VALUES ('Valid Company', '');


-- Test 2.4: Empty String in industry (when provided)
-- Expected: FAIL - CHECK constraint violated (industry IS NULL OR industry <> '')
INSERT INTO companies (name, location, industry)
VALUES ('Valid Company', 'Valid Location', '');


-- Test 2.5: Empty String in position title
-- Expected: FAIL - CHECK constraint violated (title <> '')
INSERT INTO positions (title, level)
VALUES ('', 'Mid');


-- Test 2.6: Empty String in position level
-- Expected: FAIL - CHECK constraint violated (level <> '')
INSERT INTO positions (title, level)
VALUES ('Software Engineer', '');


-- Test 2.7: Empty String in recruiter name
-- Expected: FAIL - CHECK constraint violated (name <> '')
INSERT INTO recruiters (name, email)
VALUES ('', 'test@email.com');


-- Test 2.8: Empty String in recruiter email (when provided)
-- Expected: FAIL - CHECK constraint violated (email IS NULL OR email <> '')
INSERT INTO recruiters (name, email)
VALUES ('John Doe', '');


-- Test 2.9: Empty String in recruiter phone (when provided)
-- Expected: FAIL - CHECK constraint violated (phone IS NULL OR phone <> '')
INSERT INTO recruiters (name, phone)
VALUES ('John Doe', '');


-- Test 2.10: Future applied_date
-- Expected: FAIL - CHECK constraint violated (applied_date <= CURRENT_DATE)
INSERT INTO applications (company_id, position_id, current_status, applied_date)
VALUES (1, 1, 1, CURRENT_DATE + INTERVAL '10 days');


-- Test 2.11: applied_date older than 365 days
-- Expected: FAIL - CHECK constraint violated (applied_date >= CURRENT_DATE - 365 days)
INSERT INTO applications (company_id, position_id, current_status, applied_date)
VALUES (1, 1, 1, CURRENT_DATE - INTERVAL '400 days');


-- Test 2.12: Empty String in event_type
-- Expected: FAIL - CHECK constraint violated (event_type <> '')
INSERT INTO application_events (application_id, event_type)
VALUES (1, '');


-- Test 2.13: Future event_date
-- Expected: FAIL - CHECK constraint violated (event_date <= NOW())
INSERT INTO application_events (application_id, event_type, event_date)
VALUES (1, 'Application Sent', NOW() + INTERVAL '1 day');


-- ============================================================================
-- SUMMARY: CHECK Constraints Test
-- ============================================================================
-- Expected Results:
-- All 13 tests should FAIL with CHECK constraint violations
-- This proves CHECK constraints are working correctly
--
-- Constraints Tested:
-- - Empty string prevention (name, title, level, status_name, event_type, etc.)
-- - Date validation (no future dates, no dates older than 365 days)
-- - Conditional empty string checks (email, phone, industry when provided)

