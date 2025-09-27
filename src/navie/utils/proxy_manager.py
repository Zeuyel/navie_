"""
代理池管理器
"""

import asyncio
import logging
import random
import time
from typing import List, Optional, Dict, Any
import requests
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ProxyProtocol(Enum):
    """代理协议类型"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
    ALL = "all"

@dataclass
class ProxyInfo:
    """代理信息"""
    host: str
    port: int
    protocol: ProxyProtocol
    is_working: bool = True
    last_check: float = 0
    fail_count: int = 0
    response_time: float = 0

    @property
    def address(self) -> str:
        """获取代理地址"""
        return f"{self.host}:{self.port}"
    
    @property
    def url(self) -> str:
        """获取代理URL"""
        return f"{self.protocol.value}://{self.address}"

class ProxyManager:
    """代理池管理器"""
    
    def __init__(self, 
                 api_url: str = "https://proxy.scdn.io/api/get_proxy.php",
                 protocol: ProxyProtocol = ProxyProtocol.HTTP,
                 pool_size: int = 10,
                 health_check_interval: int = 300,  # 5分钟
                 max_fail_count: int = 3):
        
        self.api_url = api_url
        self.protocol = protocol
        self.pool_size = pool_size
        self.health_check_interval = health_check_interval
        self.max_fail_count = max_fail_count
        
        self.proxy_pool: List[ProxyInfo] = []
        self.current_proxy_index = 0
        self.is_enabled = True
        
        logger.info(f"代理池管理器初始化 - 协议: {protocol.value}, 池大小: {pool_size}")

    async def initialize(self) -> bool:
        """初始化代理池"""
        try:
            logger.info("开始初始化代理池...")
            success = await self._fetch_proxies()
            if success and self.proxy_pool:
                logger.info(f"代理池初始化成功，获得 {len(self.proxy_pool)} 个代理")

                # 立即进行一次健康检查，确保有可用代理
                logger.info("开始初始健康检查...")
                await self._check_all_proxies()

                working_proxies = [p for p in self.proxy_pool if p.is_working]
                if working_proxies:
                    logger.info(f"初始健康检查完成，可用代理: {len(working_proxies)}/{len(self.proxy_pool)}")
                    # 启动健康检查任务
                    asyncio.create_task(self._health_check_loop())
                    return True
                else:
                    logger.warning("初始健康检查后没有可用代理，尝试获取更多代理...")
                    # 尝试再获取一批代理
                    retry_success = await self._fetch_proxies()
                    if retry_success:
                        await self._check_all_proxies()
                        working_proxies = [p for p in self.proxy_pool if p.is_working]
                        if working_proxies:
                            logger.info(f"重试后可用代理: {len(working_proxies)}/{len(self.proxy_pool)}")
                            asyncio.create_task(self._health_check_loop())
                            return True

                    logger.warning("多次尝试后仍无可用代理，将使用直连模式")
                    self.is_enabled = False
                    return False
            else:
                logger.warning("代理池初始化失败，将使用直连模式")
                self.is_enabled = False
                return False
        except Exception as e:
            logger.error(f"代理池初始化异常: {e}")
            self.is_enabled = False
            return False

    async def _fetch_proxies(self) -> bool:
        """从API获取代理列表"""
        try:
            params = {
                'protocol': self.protocol.value,
                'count': self.pool_size
            }
            
            logger.info(f"请求代理API: {self.api_url}, 参数: {params}")
            
            # 使用同步请求，避免异步HTTP库依赖
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') != 200:
                logger.error(f"API返回错误: {data.get('message', 'Unknown error')}")
                return False
            
            proxy_addresses = data.get('data', {}).get('proxies', [])
            if not proxy_addresses:
                logger.error("API未返回代理地址")
                return False
            
            # 解析代理地址
            new_proxies = []
            for address in proxy_addresses:
                try:
                    host, port = address.split(':')
                    proxy_info = ProxyInfo(
                        host=host.strip(),
                        port=int(port.strip()),
                        protocol=self.protocol,
                        is_working=False,  # 新代理默认为未验证状态
                        last_check=time.time()
                    )
                    new_proxies.append(proxy_info)
                    logger.info(f"添加代理: {proxy_info.address}")
                except ValueError as e:
                    logger.warning(f"解析代理地址失败: {address}, 错误: {e}")
                    continue
            
            if new_proxies:
                # 如果是初始化（代理池为空），直接设置新代理
                if not self.proxy_pool:
                    self.proxy_pool = new_proxies
                    self.current_proxy_index = 0
                    logger.info(f"成功获取 {len(new_proxies)} 个代理")
                    return True
                else:
                    # 如果是补充代理，先对新代理进行并发健康检查
                    logger.info(f"对新获取的 {len(new_proxies)} 个代理进行并发健康检查...")

                    # 创建并发检查任务
                    check_tasks = []
                    for proxy in new_proxies:
                        task = asyncio.create_task(self._check_single_proxy(proxy))
                        check_tasks.append(task)

                    # 等待所有检查完成
                    await asyncio.gather(*check_tasks, return_exceptions=True)

                    # 收集健康的新代理
                    healthy_new_proxies = [p for p in new_proxies if p.is_working]

                    # 保留现有健康的代理，添加通过检查的新代理
                    healthy_existing_proxies = [p for p in self.proxy_pool if p.is_working]
                    self.proxy_pool = healthy_existing_proxies + healthy_new_proxies
                    self.current_proxy_index = 0
                    logger.info(f"成功添加 {len(healthy_new_proxies)} 个健康代理，当前池中共有 {len(self.proxy_pool)} 个代理")
                    return len(healthy_new_proxies) > 0
            else:
                logger.error("没有有效的代理地址")
                return False
                
        except requests.RequestException as e:
            logger.error(f"请求代理API失败: {e}")
            return False
        except Exception as e:
            logger.error(f"获取代理列表异常: {e}")
            return False

    def get_current_proxy(self) -> Optional[ProxyInfo]:
        """获取当前代理"""
        if not self.is_enabled or not self.proxy_pool:
            return None
        
        # 过滤可用代理
        working_proxies = [p for p in self.proxy_pool if p.is_working]
        if not working_proxies:
            logger.warning("没有可用的代理")
            return None
        
        # 确保索引有效
        if self.current_proxy_index >= len(working_proxies):
            self.current_proxy_index = 0
        
        return working_proxies[self.current_proxy_index]

    def get_next_proxy(self) -> Optional[ProxyInfo]:
        """切换到下一个代理"""
        if not self.is_enabled or not self.proxy_pool:
            return None
        
        working_proxies = [p for p in self.proxy_pool if p.is_working]
        if not working_proxies:
            logger.warning("没有可用的代理")
            return None
        
        # 轮换到下一个代理
        self.current_proxy_index = (self.current_proxy_index + 1) % len(working_proxies)
        current_proxy = working_proxies[self.current_proxy_index]
        
        logger.info(f"切换到代理: {current_proxy.address}")
        return current_proxy

    def mark_proxy_failed(self, proxy: ProxyInfo):
        """标记代理失败"""
        proxy.fail_count += 1
        logger.warning(f"代理失败计数: {proxy.address} ({proxy.fail_count}/{self.max_fail_count})")
        
        if proxy.fail_count >= self.max_fail_count:
            proxy.is_working = False
            logger.error(f"代理已禁用: {proxy.address}")
            
            # 如果当前代理失效，切换到下一个
            if proxy == self.get_current_proxy():
                self.get_next_proxy()

    async def _health_check_loop(self):
        """代理健康检查循环"""
        while self.is_enabled:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._check_all_proxies()
            except Exception as e:
                logger.error(f"健康检查循环异常: {e}")
                await asyncio.sleep(60)  # 出错时等待1分钟再重试

    async def _check_all_proxies(self):
        """检查所有代理的健康状态 - 并发检查"""
        if not self.proxy_pool:
            return

        logger.info("开始代理健康检查...")

        # 创建并发任务
        tasks = []
        for proxy in self.proxy_pool:
            task = asyncio.create_task(self._check_single_proxy(proxy))
            tasks.append(task)

        # 等待所有检查完成
        await asyncio.gather(*tasks, return_exceptions=True)

        working_count = sum(1 for p in self.proxy_pool if p.is_working)
        logger.info(f"健康检查完成，可用代理: {working_count}/{len(self.proxy_pool)}")

        # 如果可用代理太少，尝试获取新代理
        if working_count < self.pool_size // 2:
            logger.info("可用代理不足，尝试获取新代理...")
            success = await self._fetch_proxies()
            # _fetch_proxies 已经对新代理进行了健康检查，无需重复检查

    async def _check_single_proxy(self, proxy: ProxyInfo):
        """检查单个代理的健康状态 - 包装方法"""
        try:
            is_working = await self._check_proxy_health(proxy)
            proxy.is_working = is_working
            proxy.last_check = time.time()

            if is_working:
                proxy.fail_count = 0  # 重置失败计数
                logger.debug(f"代理健康: {proxy.address}")
            else:
                proxy.fail_count += 1
                logger.warning(f"代理不健康: {proxy.address}")

        except Exception as e:
            logger.error(f"检查代理健康异常 {proxy.address}: {e}")
            proxy.fail_count += 1
            proxy.is_working = False

    async def _check_proxy_health(self, proxy: ProxyInfo) -> bool:
        """检查单个代理的健康状态 - 异步并发测试GitHub注册页面连通性"""
        def _sync_check():
            try:
                # 根据代理协议构建代理字典
                if proxy.protocol in [ProxyProtocol.SOCKS4, ProxyProtocol.SOCKS5]:
                    proxy_dict = {
                        'http': f'socks5://{proxy.address}',
                        'https': f'socks5://{proxy.address}'
                    }
                else:
                    proxy_dict = {
                        'http': f'http://{proxy.address}',
                        'https': f'http://{proxy.address}'
                    }

                # 先进行快速基础连通性测试
                try:
                    basic_response = requests.get("http://httpbin.org/ip", proxies=proxy_dict, timeout=5)
                    if basic_response.status_code != 200:
                        return False
                except Exception:
                    return False

                # 基础连通性通过后，测试GitHub注册页面
                test_url = "https://github.com/signup?source=login"
                start_time = time.time()
                response = requests.get(test_url, proxies=proxy_dict, timeout=15,
                                      headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                response_time = time.time() - start_time

                # 检查响应状态和内容
                if response.status_code == 200 and 'github' in response.text.lower():
                    proxy.response_time = response_time
                    logger.info(f"代理健康检查成功: {proxy.address}, 响应时间: {response_time:.2f}s, 可访问GitHub")
                    return True
                else:
                    return False

            except Exception as e:
                logger.debug(f"代理健康检查异常: {proxy.address}, 错误: {e}")
                return False

        # 在线程池中运行同步检查，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_check)

    def get_chrome_proxy_args(self) -> List[str]:
        """获取Chrome代理参数"""
        current_proxy = self.get_current_proxy()
        if not current_proxy:
            return []

        # 根据代理协议生成正确的参数
        if current_proxy.protocol == ProxyProtocol.SOCKS4:
            proxy_arg = f"--proxy-server=socks4://{current_proxy.address}"
        elif current_proxy.protocol == ProxyProtocol.SOCKS5:
            proxy_arg = f"--proxy-server=socks5://{current_proxy.address}"
        else:
            # HTTP/HTTPS代理
            proxy_arg = f"--proxy-server=http://{current_proxy.address}"

        logger.info(f"使用代理: {proxy_arg}")

        return [proxy_arg]

    def get_status(self) -> Dict[str, Any]:
        """获取代理池状态"""
        if not self.is_enabled:
            return {"enabled": False, "message": "代理池已禁用"}
        
        working_proxies = [p for p in self.proxy_pool if p.is_working]
        current_proxy = self.get_current_proxy()
        
        return {
            "enabled": True,
            "total_proxies": len(self.proxy_pool),
            "working_proxies": len(working_proxies),
            "current_proxy": current_proxy.address if current_proxy else None,
            "protocol": self.protocol.value
        }

    def disable(self):
        """禁用代理池"""
        self.is_enabled = False
        logger.info("代理池已禁用")

    def enable(self):
        """启用代理池"""
        self.is_enabled = True
        logger.info("代理池已启用")
