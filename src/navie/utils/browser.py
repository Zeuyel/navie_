"""
浏览器工具类
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
try:
    from config import (BROWSER_HEADLESS, BROWSER_TIMEOUT, CHROME_DRIVER_PATH,
                       PROXY_ENABLED, PROXY_API_URL, PROXY_PROTOCOL, PROXY_POOL_SIZE,
                       PROXY_HEALTH_CHECK_INTERVAL, PROXY_MAX_FAIL_COUNT)
except ImportError:
    # 设置默认值
    BROWSER_HEADLESS = False
    BROWSER_TIMEOUT = 30
    CHROME_DRIVER_PATH = None
    PROXY_ENABLED = False
    PROXY_API_URL = None
    PROXY_PROTOCOL = 'http'
    PROXY_POOL_SIZE = 10
    PROXY_HEALTH_CHECK_INTERVAL = 300
    PROXY_MAX_FAIL_COUNT = 3

try:
    from .logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    try:
        from src.navie.utils.logger import setup_logger
        logger = setup_logger(__name__)
    except ImportError:
        import logging
        logger = logging.getLogger(__name__)

try:
    from .proxy_manager import ProxyManager, ProxyProtocol
except ImportError:
    try:
        from src.navie.utils.proxy_manager import ProxyManager, ProxyProtocol
    except ImportError:
        ProxyManager = None
        ProxyProtocol = None

class BrowserManager:
    """浏览器管理器"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.proxy_manager = None
    
    async def start_browser(self):
        """启动浏览器"""
        try:
            # 不再自动初始化代理管理器，由外部设置
            # 代理管理器应该通过 proxy_pool_init_task 独立初始化

            options = Options()
            if BROWSER_HEADLESS:
                options.add_argument('--headless')

            # 极简浏览器设置 - 只保留绝对必要的设置
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            # 暂时移除 AutomationControlled 禁用，看是否影响JavaScript
            # options.add_argument('--disable-blink-features=AutomationControlled')

            # User-Agent伪装
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            options.add_argument(f'--user-agent={user_agent}')

            # 窗口大小设置
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')

            # 语言和地区设置
            options.add_argument('--lang=en-US')
            options.add_argument('--accept-lang=en-US,en;q=0.9')

            # 添加代理配置
            if self.proxy_manager and self.proxy_manager.is_enabled:
                proxy_args = self.proxy_manager.get_chrome_proxy_args()
                for arg in proxy_args:
                    options.add_argument(arg)

            # 暂时禁用所有实验性选项，让浏览器保持原生状态
            # options.add_experimental_option("excludeSwitches", ["enable-automation"])
            # options.add_experimental_option('useAutomationExtension', False)

            # 简化首选项 - 只禁用通知，保持其他功能正常
            prefs = {
                "profile.default_content_setting_values": {
                    "notifications": 2,  # 禁用通知
                }
            }
            options.add_experimental_option("prefs", prefs)

            # 查找ChromeDriver路径
            driver_path = None
            import os
            import shutil

            # 方法1: 使用配置文件中指定的路径
            if CHROME_DRIVER_PATH and os.path.exists(CHROME_DRIVER_PATH):
                driver_path = CHROME_DRIVER_PATH
                logger.info(f"使用配置的ChromeDriver路径: {driver_path}")

            # 方法2: 在常见的默认存储路径中搜索
            if not driver_path:
                logger.info("在默认存储路径中搜索ChromeDriver...")
                default_paths = [
                    # Windows常见路径
                    os.path.expanduser("~/.wdm/drivers/chromedriver/win64/*/chromedriver-win32/chromedriver.exe"),
                    os.path.expanduser("~/.cache/selenium/chromedriver/win64/*/chromedriver.exe"),
                    "C:/chromedriver/chromedriver.exe",
                    "./chromedriver.exe",
                    # 项目目录下
                    os.path.join(os.getcwd(), "drivers", "chromedriver.exe"),
                ]

                import glob
                for path_pattern in default_paths:
                    if '*' in path_pattern:
                        # 使用glob匹配通配符路径
                        matches = glob.glob(path_pattern)
                        if matches:
                            # 选择最新的版本（按路径排序）
                            driver_path = sorted(matches)[-1]
                            logger.info(f"在默认路径找到ChromeDriver: {driver_path}")
                            break
                    elif os.path.exists(path_pattern):
                        driver_path = path_pattern
                        logger.info(f"在默认路径找到ChromeDriver: {driver_path}")
                        break

            # 方法3: 尝试使用系统PATH中的chromedriver
            if not driver_path:
                try:
                    system_driver = shutil.which('chromedriver')
                    if system_driver:
                        driver_path = system_driver
                        logger.info(f"使用系统PATH中的ChromeDriver: {driver_path}")
                except Exception as e:
                    logger.warning(f"系统PATH搜索失败: {e}")

            if driver_path:
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                # 最后尝试: 让selenium自动查找
                logger.info("尝试让selenium自动查找ChromeDriver...")
                try:
                    self.driver = webdriver.Chrome(options=options)
                except Exception as e:
                    logger.error(f"ChromeDriver未找到: {e}")
                    logger.error("请确保ChromeDriver已安装并配置正确的路径")
                    logger.error("可以在.env文件中设置CHROME_DRIVER_PATH指定ChromeDriver路径")
                    raise Exception("ChromeDriver未找到，请检查安装和配置")

            # 暂时禁用反检测脚本，避免影响JavaScript执行环境
            # self._execute_stealth_scripts()

            self.wait = WebDriverWait(self.driver, BROWSER_TIMEOUT)
            logger.info("浏览器启动成功")
            return True
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            logger.error("请确保Chrome浏览器已安装且版本兼容")
            return False
    
    def navigate_to(self, url: str):
        """导航到指定URL"""
        try:
            self.driver.get(url)
            logger.info(f"导航到: {url}")
            return True
        except Exception as e:
            logger.error(f"导航失败: {e}")
            return False
    
    def find_element(self, by, value, timeout=None):
        """查找元素"""
        try:
            if timeout:
                wait = WebDriverWait(self.driver, timeout)
                return wait.until(EC.presence_of_element_located((by, value)))
            else:
                return self.wait.until(EC.presence_of_element_located((by, value)))
        except Exception as e:
            logger.error(f"查找元素失败 {by}={value}: {e}")
            return None
    
    def find_elements(self, by, value):
        """查找多个元素"""
        try:
            return self.driver.find_elements(by, value)
        except Exception as e:
            logger.error(f"查找元素失败 {by}={value}: {e}")
            return []
    
    def wait_for_element_clickable(self, by, value, timeout=None):
        """等待元素可点击"""
        try:
            # 检查浏览器会话是否还有效
            if not self.driver or not self.driver.session_id:
                logger.error("浏览器会话已失效")
                return None

            if timeout:
                wait = WebDriverWait(self.driver, timeout)
                return wait.until(EC.element_to_be_clickable((by, value)))
            else:
                return self.wait.until(EC.element_to_be_clickable((by, value)))
        except Exception as e:
            logger.error(f"等待元素可点击失败 {by}={value}: {e}")
            return None
    
    def _execute_stealth_scripts(self):
        """执行反检测脚本"""
        try:
            # 基础webdriver属性隐藏
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # 隐藏自动化相关属性
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)

            # 伪装Chrome对象
            self.driver.execute_script("""
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
            """)

            # 伪装权限API
            self.driver.execute_script("""
                const originalQuery = window.navigator.permissions.query;
                return window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)

            # 隐藏自动化标识
            self.driver.execute_script("""
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            """)

            logger.info("反检测脚本执行完成")

        except Exception as e:
            logger.warning(f"执行反检测脚本失败: {e}")

    async def _initialize_proxy_manager(self):
        """初始化代理管理器"""
        try:
            logger.info(f"开始初始化代理管理器，启用状态: {PROXY_ENABLED}")

            # 解析代理协议
            protocol_map = {
                'http': ProxyProtocol.HTTP,
                'https': ProxyProtocol.HTTPS,
                'socks4': ProxyProtocol.SOCKS4,
                'socks5': ProxyProtocol.SOCKS5,
                'all': ProxyProtocol.ALL
            }

            protocol = protocol_map.get(PROXY_PROTOCOL.lower(), ProxyProtocol.HTTP)
            logger.info(f"代理配置 - 协议: {PROXY_PROTOCOL}, 池大小: {PROXY_POOL_SIZE}")

            self.proxy_manager = ProxyManager(
                api_url=PROXY_API_URL,
                protocol=protocol,
                pool_size=PROXY_POOL_SIZE,
                health_check_interval=PROXY_HEALTH_CHECK_INTERVAL,
                max_fail_count=PROXY_MAX_FAIL_COUNT
            )

            success = await self.proxy_manager.initialize()
            if success:
                logger.info("代理管理器初始化成功")
                # 显示代理状态
                status = self.proxy_manager.get_status()
                logger.info(f"代理池状态: {status}")
            else:
                logger.warning("代理管理器初始化失败，将使用直连模式")

        except Exception as e:
            logger.error(f"初始化代理管理器异常: {e}")
            self.proxy_manager = None

    def switch_proxy(self):
        """切换到下一个代理"""
        if self.proxy_manager and self.proxy_manager.is_enabled:
            next_proxy = self.proxy_manager.get_next_proxy()
            if next_proxy:
                logger.info(f"需要重启浏览器以使用新代理: {next_proxy.address}")
                return True
        return False

    def mark_current_proxy_failed(self):
        """标记当前代理失败"""
        if self.proxy_manager and self.proxy_manager.is_enabled:
            current_proxy = self.proxy_manager.get_current_proxy()
            if current_proxy:
                self.proxy_manager.mark_proxy_failed(current_proxy)
                logger.warning(f"标记代理失败: {current_proxy.address}")

    def get_proxy_status(self):
        """获取代理状态"""
        if self.proxy_manager:
            return self.proxy_manager.get_status()
        return {"enabled": False, "message": "代理管理器未初始化"}

    def close_browser(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")

        # 禁用代理管理器
        if self.proxy_manager:
            self.proxy_manager.disable()
