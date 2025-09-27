-- 添加GitHub注册状态字段
-- 执行命令: psql -f data/add_github_registered_field.sql -d github_account -U github_signup_user

-- 添加github_registered字段
ALTER TABLE email_accounts 
ADD COLUMN IF NOT EXISTS github_registered BOOLEAN DEFAULT false;

-- 添加注释
COMMENT ON COLUMN email_accounts.github_registered IS '是否已注册GitHub账户';

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_email_accounts_github_registered 
ON email_accounts(github_registered);

-- 显示更新结果
SELECT 
    COUNT(*) as total_accounts,
    COUNT(*) FILTER (WHERE github_registered = true) as registered_accounts,
    COUNT(*) FILTER (WHERE github_registered = false) as unregistered_accounts
FROM email_accounts;

COMMIT;
