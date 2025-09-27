-- Upgrade email_config table for ShanMail configuration management
-- Run this script to extend existing email_config table for ShanMail only

-- Add new columns to email_config table
ALTER TABLE email_config 
ADD COLUMN IF NOT EXISTS config_type VARCHAR(50) DEFAULT 'system',
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS is_sensitive BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'general',
ADD COLUMN IF NOT EXISTS data_type VARCHAR(20) DEFAULT 'string',
ADD COLUMN IF NOT EXISTS default_value TEXT,
ADD COLUMN IF NOT EXISTS validation_pattern VARCHAR(255);

-- Create environment variable configuration template table
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

-- Insert only ShanMail configuration templates (others remain in .env)
INSERT INTO env_config_templates (config_key, display_name, description, category, data_type, default_value, is_required, is_sensitive, help_text) VALUES
-- ShanMail configuration
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

-- Add trigger for new table
CREATE TRIGGER update_env_config_templates_updated_at 
    BEFORE UPDATE ON env_config_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_env_config_templates_category ON env_config_templates(category);
CREATE INDEX IF NOT EXISTS idx_env_config_templates_key ON env_config_templates(config_key);
CREATE INDEX IF NOT EXISTS idx_email_config_type ON email_config(config_type);
CREATE INDEX IF NOT EXISTS idx_email_config_category ON email_config(category);

-- Update existing email_config records
UPDATE email_config SET 
    config_type = 'system',
    category = 'system',
    description = CASE 
        WHEN config_key = 'current_account_index' THEN 'Current account index in use'
        WHEN config_key = 'auto_rotate' THEN 'Whether to auto rotate accounts'
        WHEN config_key = 'max_usage_per_account' THEN 'Maximum usage count per account'
        WHEN config_key = 'flag_on_error' THEN 'Whether to flag account on error'
        ELSE 'System configuration item'
    END
WHERE config_type IS NULL;

-- Verify data
SELECT 'Environment Config Templates:' as info;
SELECT config_key, display_name, category, data_type, is_required, is_sensitive FROM env_config_templates ORDER BY category, config_key;

SELECT 'Updated Email Config:' as info;
SELECT config_key, config_value, config_type, category FROM email_config ORDER BY category, config_key;
