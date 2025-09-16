"""
双重密钥验证码工具
用于根据双重密钥生成验证码
"""

import pyotp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TwoFactorAuthenticator:
    """双重密钥验证码生成器"""
    
    def __init__(self):
        """初始化双重密钥验证码生成器"""
        pass
    
    def get_verification_code(self, secret_key: str) -> Optional[str]:
        """
        根据双重密钥生成验证码

        Args:
            secret_key: 双重密钥字符串

        Returns:
            6位数字验证码，失败返回None
        """
        try:
            if not secret_key:
                logger.error("双重密钥不能为空")
                return None

            # 创建TOTP对象
            totp = pyotp.TOTP(secret_key)

            # 生成当前时间的验证码
            verification_code = totp.now()

            logger.info(f"成功生成验证码: {verification_code}")
            return verification_code

        except Exception as e:
            logger.error(f"生成验证码失败: {e}")
            return None
    
    def verify_code(self, secret_key: str, code: str, window: int = 1) -> bool:
        """
        验证验证码是否正确

        Args:
            secret_key: 双重密钥字符串
            code: 要验证的验证码
            window: 时间窗口，允许前后几个时间段的验证码

        Returns:
            验证是否成功
        """
        try:
            if not secret_key or not code:
                logger.error("双重密钥和验证码不能为空")
                return False

            # 创建TOTP对象
            totp = pyotp.TOTP(secret_key)

            # 验证验证码
            is_valid = totp.verify(code, window=window)

            if is_valid:
                logger.info(f"验证码验证成功: {code}")
            else:
                logger.warning(f"验证码验证失败: {code}")

            return is_valid

        except Exception as e:
            logger.error(f"验证验证码失败: {e}")
            return False
    
    def get_provisioning_uri(self, secret_key: str, account_name: str, issuer_name: str = "GitHub") -> Optional[str]:
        """
        生成二维码URI，用于设置双重认证

        Args:
            secret_key: 双重密钥字符串
            account_name: 账户名称（通常是邮箱）
            issuer_name: 发行者名称

        Returns:
            二维码URI字符串
        """
        try:
            if not secret_key or not account_name:
                logger.error("双重密钥和账户名称不能为空")
                return None

            # 创建TOTP对象
            totp = pyotp.TOTP(secret_key)

            # 生成二维码URI
            uri = totp.provisioning_uri(
                name=account_name,
                issuer_name=issuer_name
            )

            logger.info(f"生成二维码URI成功: {account_name}")
            return uri

        except Exception as e:
            logger.error(f"生成二维码URI失败: {e}")
            return None

# 全局实例
two_factor_auth = TwoFactorAuthenticator()

def get_2fa_code(secret_key: str) -> Optional[str]:
    """
    便捷函数：根据双重密钥获取验证码
    
    Args:
        secret_key: 双重密钥字符串
        
    Returns:
        6位数字验证码，失败返回None
    """
    return two_factor_auth.get_verification_code(secret_key)

def verify_2fa_code(secret_key: str, code: str) -> bool:
    """
    便捷函数：验证双重认证验证码
    
    Args:
        secret_key: 双重密钥字符串
        code: 要验证的验证码
        
    Returns:
        验证是否成功
    """
    return two_factor_auth.verify_code(secret_key, code)

if __name__ == "__main__":
    # 测试代码
    import time
    
    # 示例密钥（实际使用时应该从安全的地方获取）
    test_secret = "JBSWY3DPEHPK3PXP"
    
    authenticator = TwoFactorAuthenticator()
    
    print("=== 双重密钥验证码工具测试 ===")
    
    # 生成验证码
    code1 = authenticator.get_verification_code(test_secret)
    if code1:
        print(f"生成的验证码: {code1}")
        
        # 验证验证码
        is_valid = authenticator.verify_code(test_secret, code1)
        print(f"验证结果: {'成功' if is_valid else '失败'}")
        
        # 等待30秒后再次生成验证码（验证码每30秒更新一次）
        print("等待30秒后生成新验证码...")
        time.sleep(30)
        
        code2 = authenticator.get_verification_code(test_secret)
        if code2:
            print(f"新的验证码: {code2}")
            print(f"验证码是否不同: {code1 != code2}")
    
    # 生成二维码URI
    uri = authenticator.get_provisioning_uri(test_secret, "test@example.com", "TestApp")
    if uri:
        print(f"二维码URI: {uri}")
    
    print("测试完成")
