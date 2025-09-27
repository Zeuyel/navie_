"""
配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

# YesCaptcha API配置
YESCAPTCHA_API_KEY = os.getenv('YESCAPTCHA_API_KEY', '')
YESCAPTCHA_BASE_URL = 'https://api.yescaptcha.com'
YESCAPTCHA_SOFT_ID = int(os.getenv('YESCAPTCHA_SOFT_ID', '0'))

# 浏览器配置
BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'False').lower() == 'true'
BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', '30'))
CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH', '')

# GitHub注册配置
GITHUB_SIGNUP_URL = 'https://github.com/signup?source=login'

# 临时邮箱配置（暂时硬编码，后续完善）
TEMP_EMAIL = 'reginanavarrouw71719@outlook.com'

# 用户信息配置
DEFAULT_PASSWORD = '123456888adc'

# 用户名生成配置
USERNAME_MIN_LENGTH = int(os.getenv('USERNAME_MIN_LENGTH', '6'))
USERNAME_MAX_LENGTH = int(os.getenv('USERNAME_MAX_LENGTH', '20'))
USERNAME_INCLUDE_NUMBERS = os.getenv('USERNAME_INCLUDE_NUMBERS', 'True').lower() == 'true'
USERNAME_INCLUDE_HYPHENS = os.getenv('USERNAME_INCLUDE_HYPHENS', 'True').lower() == 'true'
USERNAME_AVOID_CONSECUTIVE_NUMBERS = os.getenv('USERNAME_AVOID_CONSECUTIVE_NUMBERS', 'True').lower() == 'true'
USERNAME_PREFERRED_STRATEGIES = os.getenv('USERNAME_PREFERRED_STRATEGIES', 'adjective_noun,word_combination,tech_style').split(',')

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒

# RoxyBrowser配置
ROXY_API_KEY = os.getenv('ROXY_API_KEY', '')

# Augment配置
AUGMENT_CLIENT_ID = os.getenv('AUGMENT_CLIENT_ID', 'v')
AUGMENT_BASE_URL = 'https://app.augmentcode.com'
AUGMENT_AUTH_URL = 'https://auth.augmentcode.com'

# 支付卡信息
CARD_NUMBER = os.getenv('CARD_NUMBER', '4242424242424242')
CARD_EXPIRY = os.getenv('CARD_EXPIRY', '12/25')
CARD_CVC = os.getenv('CARD_CVC', '123')
BILLING_ADDRESS_LINE1 = os.getenv('BILLING_ADDRESS_LINE1', 'Kqwjhgfd St')
BILLING_ADDRESS_LINE2 = os.getenv('BILLING_ADDRESS_LINE2', 'Apt Zxcvbn')
BILLING_POSTAL_CODE = os.getenv('BILLING_POSTAL_CODE', '12345')

# 代理配置
PROXY_ENABLED = os.getenv('PROXY_ENABLED', 'False').lower() == 'true'
PROXY_API_URL = os.getenv('PROXY_API_URL', 'https://proxy.scdn.io/api/get_proxy.php')
PROXY_PROTOCOL = os.getenv('PROXY_PROTOCOL', 'http')  # http, https, socks4, socks5, all
PROXY_POOL_SIZE = int(os.getenv('PROXY_POOL_SIZE', '10'))
PROXY_HEALTH_CHECK_INTERVAL = int(os.getenv('PROXY_HEALTH_CHECK_INTERVAL', '300'))  # 秒
PROXY_MAX_FAIL_COUNT = int(os.getenv('PROXY_MAX_FAIL_COUNT', '3'))

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 闪邮箱配置
SHAN_MAIL_ENABLED = os.getenv('SHAN_MAIL_ENABLED', 'False').lower() == 'true'
SHAN_MAIL_CARD_KEY = os.getenv('SHAN_MAIL_CARD_KEY', '')
SHAN_MAIL_EMAIL_TYPE = os.getenv('SHAN_MAIL_EMAIL_TYPE', 'hotmail')  # outlook 或 hotmail

# 数据库配置
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'github_account')
DB_USER = os.getenv('DB_USER', 'github_signup_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'GhSignup2024!')

def get_db_connection_string():
    """获取数据库连接字符串"""
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_db_connection_params():
    """获取数据库连接参数"""
    return {
        'host': DB_HOST,
        'port': DB_PORT,
        'database': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD
    }
