-- Add missing columns to audit_log table
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES "user"(id);
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS event_type VARCHAR(50) NOT NULL DEFAULT 'ENTITY_UPDATE';
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS event_metadata JSONB;
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS user_agent VARCHAR(255);

-- Update existing rows to have valid event_type
UPDATE audit_log SET event_type = 'ENTITY_UPDATE' WHERE event_type IS NULL;

-- Add the check constraint for valid event types
ALTER TABLE audit_log ADD CONSTRAINT valid_event_type CHECK (event_type IN ('LOGIN_SUCCESS','LOGIN_FAILED','MFA_FAILED','LOCKOUT','ROLE_CHANGE','TOKEN_REFRESH','LOGOUT','ROUTE_OVERRIDE','ENTITY_UPDATE','OTP_SENT','OTP_FAILED','EMAIL_VERIFIED','VERIFICATION_EMAIL_SENT'));
