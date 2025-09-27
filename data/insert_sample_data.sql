-- Sample data for testing email accounts system
-- Run this after creating the schema

-- Insert sample email accounts
INSERT INTO email_accounts (email, password, client_id, access_token, provider, notes) VALUES
('test1@outlook.com', 'password123', '9e5f94bc-e8a4-4e73-b8be-63364c29d753', 'sample_token_1', 'outlook', 'Test account 1'),
('test2@gmail.com', 'password456', '9e5f94bc-e8a4-4e73-b8be-63364c29d753', 'sample_token_2', 'gmail', 'Test account 2'),
('test3@hotmail.com', 'password789', '9e5f94bc-e8a4-4e73-b8be-63364c29d753', 'sample_token_3', 'hotmail', 'Test account 3')
ON CONFLICT (email) DO NOTHING;

-- Insert configuration
INSERT INTO email_config (config_key, config_value) VALUES
('current_account_index', '0'),
('auto_rotate', 'true'),
('max_usage_per_account', '10'),
('flag_on_error', 'true')
ON CONFLICT (config_key) DO UPDATE SET 
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

-- Verify data
SELECT 'Email Accounts:' as info;
SELECT id, email, provider, is_active, created_at FROM email_accounts ORDER BY id;

SELECT 'Configuration:' as info;
SELECT config_key, config_value FROM email_config ORDER BY config_key;
