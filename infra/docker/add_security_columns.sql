-- Add security columns to user table
DO $$
BEGIN
    -- Add officer_id column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user' AND column_name = 'officer_id'
    ) THEN
        ALTER TABLE "user" ADD COLUMN officer_id VARCHAR(50);
        CREATE UNIQUE INDEX ix_user_officer_id ON "user"(officer_id) WHERE officer_id IS NOT NULL;
    END IF;

    -- Add totp_secret column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user' AND column_name = 'totp_secret'
    ) THEN
        ALTER TABLE "user" ADD COLUMN totp_secret VARCHAR(64);
    END IF;

    -- Add totp_enabled column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user' AND column_name = 'totp_enabled'
    ) THEN
        ALTER TABLE "user" ADD COLUMN totp_enabled BOOLEAN DEFAULT FALSE;
    END IF;

    -- Add failed_login_count column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user' AND column_name = 'failed_login_count'
    ) THEN
        ALTER TABLE "user" ADD COLUMN failed_login_count INTEGER DEFAULT 0;
    END IF;

    -- Add locked_until column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user' AND column_name = 'locked_until'
    ) THEN
        ALTER TABLE "user" ADD COLUMN locked_until TIMESTAMP NULL;
    END IF;

    -- Add role constraint if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'valid_role'
    ) THEN
        ALTER TABLE "user" ADD CONSTRAINT valid_role CHECK (role IN ('community','officer','admin'));
    END IF;
END $$;

-- Create refresh_tokens table if it doesn't exist
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id) NOT NULL,
    token_hash VARCHAR(128) NOT NULL,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE
);

-- Create audit_log table if it doesn't exist
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id),
    event_type VARCHAR(50) NOT NULL,
    event_metadata JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_event_type CHECK (event_type IN ('LOGIN_SUCCESS','LOGIN_FAILED','MFA_FAILED','LOCKOUT','ROLE_CHANGE','TOKEN_REFRESH','LOGOUT'))
);

-- Make email nullable in user table if it's currently NOT NULL
DO $$
BEGIN
    -- Check if email column is NOT NULL and make it nullable
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user' AND column_name = 'email' AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE "user" ALTER COLUMN email DROP NOT NULL;
    END IF;
END $$;
