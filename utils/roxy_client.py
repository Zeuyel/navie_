"""
RoxyClient - 统一管理RoxyBrowser浏览器通信请求
基于用户提供的正确API格式
"""

import os
import requests
import logging
import json
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from .browser import BrowserManager

logger = logging.getLogger(__name__)

class RoxyClient:
    """RoxyBrowser客户端，管理浏览器实例的创建、打开、关闭和删除"""

    def __init__(self, port: int = 50000, token: str = None):
        """
        初始化RoxyClient

        Args:
            port: RoxyBrowser API服务端口
            token: RoxyBrowser API令牌，如果不提供则从环境变量获取
        """
        self.port = port
        self.host = "127.0.0.1"
        self.token = token or os.getenv('ROXY_API_KEY')
        self.url = f"http://{self.host}:{self.port}"
        self.workspace_id = None
        self.browser_id = None
        self.driver = None

        if not self.token:
            raise ValueError("RoxyBrowser API令牌未提供，请设置环境变量 ROXY_API_KEY")

        logger.info("RoxyClient 初始化完成")

    def _build_headers(self):
        """构建请求头"""
        return {"Content-Type": "application/json", "token": self.token}

    def _post(self, path, data=None):
        """发送POST请求"""
        return requests.post(self.url + path, json=data, headers=self._build_headers())

    def _get(self, path, data=None):
        """发送GET请求"""
        return requests.get(self.url + path, params=data, headers=self._build_headers())

    def workspace_project(self):
        """获取工作空间项目列表"""
        logger.info("获取工作空间项目列表...")
        result = self._get("/browser/workspace").json()

        logger.info(f"API响应内容: {result}")

        if result.get("code") == 0:
            # 获取第一个工作空间ID
            data = result.get("data", {})
            rows = data.get("rows", [])
            logger.info(f"工作空间数据: {data}")

            if rows:
                self.workspace_id = rows[0].get("id")
                logger.info(f"获取工作空间ID成功: {self.workspace_id}")
                return result
            else:
                logger.error("工作空间列表为空，无法继续")
                raise Exception("工作空间列表为空")

        raise Exception(f"获取工作空间失败: {result}")

    def browser_create(self, config: Dict[Any, Any] = None) -> str:
        """
        创建浏览器窗口

        Args:
            config: 浏览器配置参数

        Returns:
            browser_id: 浏览器ID
        """
        logger.info("创建浏览器窗口...")

        if not self.workspace_id:
            self.workspace_project()

        # 默认配置
        default_config = {
            "workspaceId": self.workspace_id,
            "windowName": "GitHub Auto Registration",
            "coreVersion": "117",
            "os": "Windows",
            "osVersion": "11",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "cookie": [],
            "searchEngine": "Google",
            "fingerInfo": {
                "isLanguageBaseIp": True,
                "language": "en-US",
                "isDisplayLanguageBaseIp": True,
                "displayLanguage": "en-US",
                "isTimeZone": True,
                "timeZone": "GMT-12:00 Etc/GMT+12",
                "position": 0,
                "isPositionBaseIp": True,
                "clearCacheFile": True,
                "clearCookie": True,
                "clearLocalStorage": True,
                "randomFingerprint": True,
                "forbidSavePassword": True,
                "stopOpenNet": True,
                "stopOpenIP": True,
                "stopOpenPosition": True,
                "openWorkbench": 1,
                "resolutionType": True
            }
        }

        if config:
            default_config.update(config)

        result = self._post('/browser/create', default_config).json()

        logger.info(f"创建浏览器响应: {result}")

        if result.get("code") == 0 and result.get("data"):
            self.browser_id = result["data"]["dirId"]
            logger.info(f"创建浏览器窗口成功: {self.browser_id}")
            return self.browser_id
        else:
            raise Exception(f"创建浏览器窗口失败: {result}")

    def browser_random_env(self, browser_id: str = None) -> Dict[Any, Any]:
        """
        生成随机指纹环境

        Args:
            browser_id: 浏览器ID，如果不提供则使用当前实例的browser_id

        Returns:
            随机指纹环境配置
        """
        browser_id = browser_id or self.browser_id
        if not browser_id:
            raise Exception("浏览器ID未提供，请先创建浏览器")

        logger.info(f"生成随机指纹环境: {browser_id}")

        data = {"workspaceId": self.workspace_id, "dirId": browser_id}
        result = self._post('/browser/random_env', data).json()

        logger.info(f"随机指纹响应: {result}")

        if result.get("code") == 0:
            logger.info("随机指纹环境生成成功")
            return result
        else:
            raise Exception(f"生成随机指纹失败: {result}")

    def browser_open(self, browser_id: str = None, args: list = None) -> webdriver.Chrome:
        """
        打开浏览器窗口并返回Selenium WebDriver实例

        Args:
            browser_id: 浏览器ID，如果不提供则使用当前实例的browser_id
            args: 浏览器启动参数

        Returns:
            Selenium WebDriver实例
        """
        browser_id = browser_id or self.browser_id
        if not browser_id:
            raise Exception("浏览器ID未提供，请先创建浏览器")

        logger.info(f"打开浏览器窗口: {browser_id}")

        data = {"dirId": browser_id, "args": args or []}
        result = self._post('/browser/open', data).json()

        logger.info(f"打开浏览器响应: {result}")

        if result.get("code") != 0:
            raise Exception(f"打开浏览器失败: {result}")

        data = result.get("data", {})
        debugger_address = data.get("http")
        driver_path = data.get("driver")

        if not debugger_address or not driver_path:
            raise Exception("打开浏览器失败，响应中缺少连接信息")

        logger.info(f"浏览器已打开，debuggerAddress: {debugger_address}, driverPath: {driver_path}")

        # 创建Selenium WebDriver连接
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", debugger_address)

        try:
            chrome_service = Service(driver_path)
            self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            logger.info("Selenium WebDriver连接成功")
            return self.driver
        except Exception as e:
            logger.error(f"Selenium WebDriver连接失败: {e}")
            raise Exception(f"连接到RoxyBrowser失败: {e}")

    def browser_close(self, browser_id: str = None) -> bool:
        """
        关闭浏览器窗口

        Args:
            browser_id: 浏览器ID，如果不提供则使用当前实例的browser_id

        Returns:
            是否成功关闭
        """
        browser_id = browser_id or self.browser_id
        if not browser_id:
            logger.warning("浏览器ID未提供，跳过关闭操作")
            return True

        logger.info(f"关闭浏览器窗口: {browser_id}")

        try:
            # 先关闭Selenium连接
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Selenium WebDriver已关闭")
        except Exception as e:
            logger.warning(f"关闭Selenium WebDriver失败: {e}")

        try:
            data = {"dirId": browser_id}
            result = self._post('/browser/close', data).json()

            logger.info(f"关闭浏览器响应: {result}")

            if result.get("code") == 0:
                logger.info("浏览器窗口关闭成功")
                return True
            else:
                logger.error(f"关闭浏览器窗口失败: {result}")
                return False
        except Exception as e:
            logger.error(f"关闭浏览器窗口失败: {e}")
            return False

    def browser_delete(self, browser_id: str = None) -> bool:
        """
        删除浏览器窗口

        Args:
            browser_id: 浏览器ID，如果不提供则使用当前实例的browser_id

        Returns:
            是否成功删除
        """
        browser_id = browser_id or self.browser_id
        if not browser_id:
            logger.warning("浏览器ID未提供，跳过删除操作")
            return True

        logger.info(f"删除浏览器窗口: {browser_id}")

        try:
            data = {"workspaceId": self.workspace_id, "dirIds": [browser_id]}
            result = self._post('/browser/delete', data).json()

            logger.info(f"删除浏览器响应: {result}")

            if result.get("code") == 0:
                logger.info("浏览器窗口删除成功")

                # 清理实例状态
                if browser_id == self.browser_id:
                    self.browser_id = None
                    self.driver = None

                return True
            else:
                logger.error(f"删除浏览器窗口失败: {result}")
                return False
        except Exception as e:
            logger.error(f"删除浏览器窗口失败: {e}")
            return False

    def cleanup(self):
        """清理资源，关闭并删除浏览器"""
        logger.info("开始清理RoxyClient资源...")

        if self.browser_id:
            self.browser_close()
            self.browser_delete()

        logger.info("RoxyClient资源清理完成")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动清理资源"""
        self.cleanup()


class RoxyBrowserManager(BrowserManager):
    """RoxyBrowser管理器，继承BrowserManager提供完整的浏览器功能"""

    def __init__(self):
        super().__init__()
        self.roxy_client = None
    
    def create_browser(self, config: Dict[Any, Any] = None) -> 'RoxyBrowserManager':
        """
        创建并打开浏览器

        Args:
            config: 浏览器配置

        Returns:
            自身实例，用于链式调用
        """
        try:
            self.roxy_client = RoxyClient()

            # 获取工作空间
            self.roxy_client.workspace_project()

            # 创建浏览器
            self.roxy_client.browser_create(config)

            # 生成随机指纹
            self.roxy_client.browser_random_env()

            # 打开浏览器
            self.driver = self.roxy_client.browser_open()

            # 设置WebDriverWait，与BrowserManager保持一致
            from selenium.webdriver.support.ui import WebDriverWait
            self.wait = WebDriverWait(self.driver, 10)

            logger.info("RoxyBrowser创建并打开成功")
            return self

        except Exception as e:
            logger.error(f"创建RoxyBrowser失败: {e}")
            self.cleanup()
            raise

    def cleanup(self):
        """清理资源"""
        if self.roxy_client:
            self.roxy_client.cleanup()
            self.roxy_client = None
        self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
