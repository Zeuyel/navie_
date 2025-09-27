"""
GitHub登录脚本
用于Web界面调用，实现自动打开RoxyBrowser登录GitHub功能
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import random
import time

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

# 设置环境变量，确保能找到.env文件
os.chdir(project_root)

# 设置日志（在导入之前）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from src.navie.utils.roxy_client import RoxyBrowserManager
    logger.info("RoxyBrowserManager导入成功")
except ImportError as e:
    logger.error(f"导入RoxyBrowserManager失败: {e}")
    try:
        # 尝试其他导入路径
        sys.path.append(os.path.join(project_root, 'src', 'navie', 'utils'))
        from roxy_client import RoxyBrowserManager
        logger.info("RoxyBrowserManager通过备用路径导入成功")
    except ImportError as e2:
        logger.error(f"备用路径导入也失败: {e2}")
        RoxyBrowserManager = None

class GitHubLoginManager:
    """GitHub登录管理器"""
    
    def __init__(self):
        self.browser_manager = None
        self.driver = None
        self.wait = None
        
    def setup_browser(self, headless=False):
        """设置RoxyBrowser浏览器"""
        if not RoxyBrowserManager:
            logger.error("RoxyBrowserManager未导入，请检查依赖")
            return False

        try:
            logger.info("启动RoxyBrowser...")

            # 创建RoxyBrowser管理器
            self.browser_manager = RoxyBrowserManager()
            logger.info("RoxyBrowserManager创建成功")

            # 创建并打开浏览器
            logger.info("正在创建RoxyBrowser实例...")
            self.browser_manager.create_browser()
            logger.info("RoxyBrowser实例创建成功")

            # 获取driver和wait
            self.driver = self.browser_manager.driver
            if not self.driver:
                logger.error("RoxyBrowser driver为空")
                return False

            self.wait = WebDriverWait(self.driver, 30)

            logger.info("RoxyBrowser启动成功")
            return True

        except Exception as e:
            logger.error(f"RoxyBrowser启动失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    async def login_github(self, username, password, tfa_secret=None):
        """登录GitHub"""
        try:
            logger.info(f"开始GitHub登录，用户名: {username}")
            
            # 导航到GitHub登录页面
            self.driver.get("https://github.com/login")
            await asyncio.sleep(3)
            
            # 输入用户名
            try:
                username_field = self.wait.until(EC.presence_of_element_located((By.ID, "login_field")))
                username_field.clear()
                username_field.send_keys(username)
                logger.info("已输入用户名")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"输入用户名失败: {e}")
                return False
            
            # 输入密码
            try:
                password_field = self.driver.find_element(By.ID, "password")
                password_field.clear()
                password_field.send_keys(password)
                logger.info("已输入密码")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"输入密码失败: {e}")
                return False
            
            # 点击登录按钮
            try:
                login_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Sign in']")
                login_button.click()
                logger.info("已点击登录按钮")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"点击登录按钮失败: {e}")
                return False
            
            # 检查是否需要2FA
            current_url = self.driver.current_url
            logger.info(f"登录后页面URL: {current_url}")
            
            if 'two-factor' in current_url or 'sessions/two-factor' in current_url:
                logger.info("检测到2FA验证页面")
                if tfa_secret:
                    return await self.handle_2fa(tfa_secret)
                else:
                    logger.warning("需要2FA验证但未提供2FA密钥，请手动完成验证")
                    return await self.wait_for_manual_2fa()
            
            # 检查登录结果
            if 'github.com/login' in current_url:
                logger.error("登录失败，仍在登录页面")
                return False

            logger.info("GitHub登录成功")
            # 处理登录后的页面（如passkey提示等）
            return await self.handle_post_login_pages()
            
        except Exception as e:
            logger.error(f"GitHub登录失败: {e}")
            return False
    
    async def handle_2fa(self, tfa_secret):
        """处理2FA验证"""
        try:
            logger.info("开始处理2FA验证")

            # 生成TOTP验证码
            totp_code = self.generate_totp(tfa_secret)
            if not totp_code:
                logger.error("生成TOTP验证码失败")
                return await self.wait_for_manual_2fa()

            logger.info(f"生成TOTP验证码: {totp_code}")

            # 查找2FA输入框
            try:
                totp_input = self.wait.until(EC.presence_of_element_located((By.ID, "app_totp")))
                totp_input.clear()
                totp_input.send_keys(totp_code)
                logger.info("已输入TOTP验证码")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"输入TOTP验证码失败: {e}")
                return await self.wait_for_manual_2fa()

            # 点击验证按钮
            try:
                verify_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                verify_button.click()
                logger.info("已点击验证按钮")
                await asyncio.sleep(3)
            except Exception as e:
                logger.error(f"点击验证按钮失败: {e}")
                return False

            # 检查验证结果
            current_url = self.driver.current_url
            if 'two-factor' not in current_url and 'sessions/two-factor' not in current_url:
                if 'github.com/login' not in current_url:
                    logger.info("2FA验证成功")
                    # 检查是否有passkey提示页面
                    return await self.handle_post_login_pages()
                else:
                    logger.error("2FA验证失败，仍在登录页面")
                    return False
            else:
                logger.warning("2FA验证可能失败，等待手动处理")
                return await self.wait_for_manual_2fa()

        except Exception as e:
            logger.error(f"2FA验证失败: {e}")
            return False

    def generate_totp(self, secret):
        """生成TOTP验证码"""
        try:
            import pyotp
            totp = pyotp.TOTP(secret)
            return totp.now()
        except ImportError:
            logger.error("pyotp模块未安装，无法生成TOTP验证码")
            logger.info("请安装pyotp: pip install pyotp")
            return None
        except Exception as e:
            logger.error(f"生成TOTP验证码失败: {e}")
            return None

    async def handle_post_login_pages(self):
        """处理登录后的各种页面（如passkey提示等）"""
        try:
            logger.info("检查登录后页面...")
            await asyncio.sleep(2)  # 等待页面加载

            current_url = self.driver.current_url
            logger.info(f"当前页面URL: {current_url}")

            # 检查是否有passkey提示页面
            try:
                # 查找"Ask me later"按钮
                ask_later_button = self.driver.find_element(By.CSS_SELECTOR, 'input[value="Ask me later"]')
                if ask_later_button:
                    logger.info("发现passkey提示页面，点击'Ask me later'")
                    ask_later_button.click()
                    await asyncio.sleep(2)
                    logger.info("已跳过passkey设置")
            except Exception as e:
                logger.debug(f"未发现passkey提示页面: {e}")

            # 检查是否还有其他需要处理的页面
            current_url = self.driver.current_url
            if 'github.com/login' in current_url:
                logger.error("登录失败，仍在登录页面")
                return False

            logger.info("登录成功，已处理所有登录后页面")
            return True

        except Exception as e:
            logger.error(f"处理登录后页面失败: {e}")
            # 即使处理失败，如果不在登录页面，也认为登录成功
            current_url = self.driver.current_url
            return 'github.com/login' not in current_url
    
    async def wait_for_manual_2fa(self):
        """等待用户手动完成2FA验证"""
        try:
            logger.info("等待用户手动完成2FA验证...")
            
            # 等待用户手动完成2FA，最多等待120秒
            for i in range(120):
                current_url = self.driver.current_url
                if 'two-factor' not in current_url and 'sessions/two-factor' not in current_url:
                    if 'github.com/login' not in current_url:
                        logger.info("2FA验证完成，登录成功")
                        return True
                    else:
                        logger.error("2FA验证失败，仍在登录页面")
                        return False
                await asyncio.sleep(1)
            
            logger.error("2FA验证超时")
            return False
            
        except Exception as e:
            logger.error(f"等待2FA验证失败: {e}")
            return False
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.browser_manager:
                # RoxyBrowser会自动管理资源，不需要手动关闭
                # 让浏览器保持打开状态，用户可以继续操作
                logger.info("GitHub登录完成，RoxyBrowser保持打开状态")
            else:
                logger.info("无需清理资源")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")

async def github_login_main(username, password, tfa_secret=None, headless=False):
    """主要的GitHub登录函数"""
    login_manager = GitHubLoginManager()
    
    try:
        # 设置浏览器
        if not login_manager.setup_browser(headless=headless):
            return {
                'success': False,
                'message': 'RoxyBrowser启动失败，请检查配置和网络连接'
            }
        
        # 执行登录
        success = await login_manager.login_github(username, password, tfa_secret)
        
        if success:
            return {
                'success': True,
                'message': 'GitHub登录成功，浏览器已打开'
            }
        else:
            return {
                'success': False,
                'message': 'GitHub登录失败'
            }
            
    except Exception as e:
        logger.error(f"GitHub登录过程异常: {e}")
        return {
            'success': False,
            'message': f'登录过程异常: {str(e)}'
        }
    finally:
        # 不自动关闭浏览器，让用户可以继续操作
        # login_manager.cleanup()
        pass

if __name__ == "__main__":
    # 命令行调用示例
    if len(sys.argv) < 3:
        print("用法: python github_login.py <username> <password> [tfa_secret] [headless]")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    tfa_secret = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
    headless = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else False
    
    # 运行登录
    result = asyncio.run(github_login_main(username, password, tfa_secret, headless))
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False))
