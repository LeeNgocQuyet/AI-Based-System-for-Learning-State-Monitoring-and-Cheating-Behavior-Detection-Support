-- Grant one existing session to one pre-provisioned active instructor.
-- Run only from a trusted developer/admin environment with psql variables.
-- Example: psql "$DATABASE_URL" -v instructor_email='...' -v session_id='...' -f this-file.sql

INSERT INTO instructor_session_access (instructor_id, session_id)
SELECT u.user_id, s.session_id
FROM users AS u
JOIN sessions AS s ON s.session_id = :'session_id'::UUID
WHERE LOWER(u.email) = LOWER(:'instructor_email')
  AND u.role = 'INSTRUCTOR'
  AND u.status = 'ACTIVE'
ON CONFLICT (instructor_id, session_id) DO NOTHING;

-- If zero rows were inserted, verify the instructor email, account status and session_id.
