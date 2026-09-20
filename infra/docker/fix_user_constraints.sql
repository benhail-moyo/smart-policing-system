-- Fix user table constraints to match the model
DO $$
BEGIN
    -- Drop existing unique constraints if they exist
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'user_email_key'
    ) THEN
        ALTER TABLE "user" DROP CONSTRAINT user_email_key;
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'user_officer_id_key'
    ) THEN
        ALTER TABLE "user" DROP CONSTRAINT user_officer_id_key;
    END IF;

    -- Create partial unique indexes that allow NULL values
    CREATE UNIQUE INDEX IF NOT EXISTS ix_user_email ON "user"(email) WHERE email IS NOT NULL;
    CREATE UNIQUE INDEX IF NOT EXISTS ix_user_officer_id ON "user"(officer_id) WHERE officer_id IS NOT NULL;
END $$;
