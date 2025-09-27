-- Email Accounts Database Schema
-- PostgreSQL database schema for email account management

-- Create database and user (run as postgres superuser)
-- CREATE DATABASE github_account;
-- CREATE USER github_signup_user WITH PASSWORD 'GhSignup2024!';
-- GRANT ALL PRIVILEGES ON DATABASE github_account TO github_signup_user;

-- Connect to github_account database before running the rest

-- Email accounts table
CREATE TABLE IF NOT EXISTS email_accounts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    tfa_secret VARCHAR(255),
    provider VARCHAR(50) DEFAULT 'outlook',
    is_active BOOLEAN DEFAULT true,
    is_flagged BOOLEAN DEFAULT false,
    flag_reason TEXT,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email configuration table
CREATE TABLE IF NOT EXISTS email_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_email_accounts_email ON email_accounts(email);
CREATE INDEX IF NOT EXISTS idx_email_accounts_provider ON email_accounts(provider);
CREATE INDEX IF NOT EXISTS idx_email_accounts_active ON email_accounts(is_active);
CREATE INDEX IF NOT EXISTS idx_email_accounts_flagged ON email_accounts(is_flagged);
CREATE INDEX IF NOT EXISTS idx_email_config_key ON email_config(config_key);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_email_accounts_updated_at 
    BEFORE UPDATE ON email_accounts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_config_updated_at 
    BEFORE UPDATE ON email_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW active_accounts AS
SELECT * FROM email_accounts WHERE is_active = true ORDER BY created_at ASC;

CREATE OR REPLACE VIEW flagged_accounts AS
SELECT * FROM email_accounts WHERE is_flagged = true ORDER BY updated_at DESC;

CREATE OR REPLACE VIEW account_stats AS
SELECT 
    COUNT(*) as total_accounts,
    COUNT(*) FILTER (WHERE is_active = true) as active_accounts,
    COUNT(*) FILTER (WHERE is_flagged = true) as flagged_accounts,
    COUNT(*) FILTER (WHERE tfa_secret IS NOT NULL) as tfa_accounts,
    COUNT(*) FILTER (WHERE provider = 'outlook') as outlook_accounts,
    COUNT(*) FILTER (WHERE provider = 'gmail') as gmail_accounts,
    COUNT(*) FILTER (WHERE provider = 'hotmail') as hotmail_accounts
FROM email_accounts;

-- Grant permissions to user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO github_signup_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO github_signup_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO github_signup_user;
