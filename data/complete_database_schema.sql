-- Complete Database Schema for Navie Email Management System
-- PostgreSQL database schema for production deployment

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

-- Email configuration table (extended for environment variables)
CREATE TABLE IF NOT EXISTS email_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(50) DEFAULT 'system',
    description TEXT,
    is_sensitive BOOLEAN DEFAULT false,
    category VARCHAR(50) DEFAULT 'general',
    data_type VARCHAR(20) DEFAULT 'string',
    default_value TEXT,
    validation_pattern VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Environment variable configuration template table (for ShanMail only)
CREATE TABLE IF NOT EXISTS env_config_templates (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    data_type VARCHAR(20) DEFAULT 'string',
    default_value TEXT,
    is_required BOOLEAN DEFAULT false,
    is_sensitive BOOLEAN DEFAULT false,
    validation_pattern VARCHAR(255),
    help_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_email_accounts_email ON email_accounts(email);
CREATE INDEX IF NOT EXISTS idx_email_accounts_provider ON email_accounts(provider);
CREATE INDEX IF NOT EXISTS idx_email_accounts_active ON email_accounts(is_active);
CREATE INDEX IF NOT EXISTS idx_email_accounts_flagged ON email_accounts(is_flagged);
CREATE INDEX IF NOT EXISTS idx_email_config_key ON email_config(config_key);
CREATE INDEX IF NOT EXISTS idx_email_config_type ON email_config(config_type);
CREATE INDEX IF NOT EXISTS idx_email_config_category ON email_config(category);
CREATE INDEX IF NOT EXISTS idx_env_config_templates_category ON env_config_templates(category);
CREATE INDEX IF NOT EXISTS idx_env_config_templates_key ON env_config_templates(config_key);

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to update updated_at timestamp
CREATE TRIGGER update_email_accounts_updated_at 
    BEFORE UPDATE ON email_accounts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_config_updated_at 
    BEFORE UPDATE ON email_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_env_config_templates_updated_at 
    BEFORE UPDATE ON env_config_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default system configuration
INSERT INTO email_config (config_key, config_value, config_type, category, description) VALUES
('current_account_index', '0', 'system', 'system', 'Current account index in use'),
('auto_rotate', 'true', 'system', 'system', 'Whether to auto rotate accounts'),
('max_usage_per_account', '10', 'system', 'system', 'Maximum usage count per account'),
('flag_on_error', 'true', 'system', 'system', 'Whether to flag account on error')
ON CONFLICT (config_key) DO UPDATE SET 
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

-- Insert ShanMail configuration templates
INSERT INTO env_config_templates (config_key, display_name, description, category, data_type, default_value, is_required, is_sensitive, help_text) VALUES
('SHAN_MAIL_ENABLED', 'Enable ShanMail Service', 'Whether to enable ShanMail email service', 'email_provider', 'boolean', 'false', false, false, 'Enable to fetch email accounts from ShanMail service'),
('SHAN_MAIL_CARD_KEY', 'ShanMail Card Key', 'ShanMail service card key', 'email_provider', 'string', '', true, true, 'Card key purchased from ShanMail service'),
('SHAN_MAIL_EMAIL_TYPE', 'ShanMail Email Type', 'Type of email accounts from ShanMail', 'email_provider', 'string', 'outlook', false, false, 'Options: outlook or hotmail')
ON CONFLICT (config_key) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    data_type = EXCLUDED.data_type,
    default_value = EXCLUDED.default_value,
    is_required = EXCLUDED.is_required,
    is_sensitive = EXCLUDED.is_sensitive,
    help_text = EXCLUDED.help_text,
    updated_at = CURRENT_TIMESTAMP;

-- Sample data for testing (optional - remove for production)
-- INSERT INTO email_accounts (email, password, client_id, access_token, provider, notes) VALUES
-- ('test1@outlook.com', 'password123', '9e5f94bc-e8a4-4e73-b8be-63364c29d753', 'sample_token_1', 'outlook', 'Test account 1'),
-- ('test2@hotmail.com', 'password456', '9e5f94bc-e8a4-4e73-b8be-63364c29d753', 'sample_token_2', 'hotmail', 'Test account 2')
-- ON CONFLICT (email) DO NOTHING;

-- Verify installation
SELECT 'Database Schema Installation Complete' as status;
SELECT 'Email Accounts Table:' as info;
SELECT COUNT(*) as total_accounts FROM email_accounts;
SELECT 'Email Config Table:' as info;
SELECT COUNT(*) as total_configs FROM email_config;
SELECT 'Environment Config Templates:' as info;
SELECT COUNT(*) as total_templates FROM env_config_templates;

-- Show table structure
SELECT 'Tables created:' as info;
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('email_accounts', 'email_config', 'env_config_templates')
ORDER BY table_name;
