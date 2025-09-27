"""
浏览器相关任务
"""

import asyncio
import logging
from navie.core.task_manager import TaskResult
from navie.core.event_bus import create_event
from navie.utils.browser import BrowserManager
from navie.utils.roxy_client import RoxyBrowserManager
from navie.utils.proxy_manager import ProxyManager, ProxyProtocol
try:
    from config import (GITHUB_SIGNUP_URL, PROXY_ENABLED, PROXY_API_URL, PROXY_PROTOCOL,
                       PROXY_POOL_SIZE, PROXY_HEALTH_CHECK_INTERVAL, PROXY_MAX_FAIL_COUNT, ROXY_API_KEY)
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from config import (GITHUB_SIGNUP_URL, PROXY_ENABLED, PROXY_API_URL, PROXY_PROTOCOL,
                       PROXY_POOL_SIZE, PROXY_HEALTH_CHECK_INTERVAL, PROXY_MAX_FAIL_COUNT, ROXY_API_KEY)

logger = logging.getLogger(__name__)

async def proxy_pool_init_task(state_manager, event_bus):
    """代理池初始化任务 - 独立于浏览器启动"""
    logger.info("执行任务: proxy_pool_init_task")

    try:
        if not PROXY_ENABLED:
            logger.info("代理功能未启用，跳过代理池初始化")
            return TaskResult(
                success=True,
                data={'proxy_enabled': False}
            )

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

        # 创建代理管理器
        proxy_manager = ProxyManager(
            api_url=PROXY_API_URL,
            protocol=protocol,
            pool_size=PROXY_POOL_SIZE,
            health_check_interval=PROXY_HEALTH_CHECK_INTERVAL,
            max_fail_count=PROXY_MAX_FAIL_COUNT
        )

        # 初始化代理池
        success = await proxy_manager.initialize()

        if success:
            # 保存代理管理器到状态
            state_manager.set_data('proxy_manager', proxy_manager)

            # 显示代理状态
            status = proxy_manager.get_status()
            logger.info(f"代理池初始化成功: {status}")

            # 发布代理池初始化完成事件
            await event_bus.publish(create_event(
                name='proxy_pool_initialized',
                data={'proxy_manager': proxy_manager, 'status': status},
                source='proxy_pool_init_task'
            ))

            return TaskResult(
                success=True,
                data={'proxy_manager': proxy_manager, 'status': status}
            )
        else:
            logger.warning("代理池初始化失败，将使用直连模式")
            return TaskResult(
                success=True,  # 不阻塞其他任务
                data={'proxy_enabled': False, 'fallback_to_direct': True}
            )

    except Exception as e:
        logger.error(f"代理池初始化异常: {e}")
        return TaskResult(
            success=True,  # 不阻塞其他任务
            error=str(e),
            data={'proxy_enabled': False, 'error': str(e)}
        )

async def browser_init_task(state_manager, event_bus):
    """任务1: 启动浏览器 - 不依赖代理池初始化"""
    logger.info("执行任务: browser_init_task")

    try:
        # 使用Chrome浏览器进行GitHub注册
        logger.info("使用Chrome浏览器启动")

        # 获取代理管理器（如果可用）
        proxy_manager = state_manager.get_data('proxy_manager')
        if not proxy_manager:
            logger.info("代理管理器未就绪，使用直连模式启动浏览器")

        # 创建Chrome浏览器管理器
        from navie.utils.browser import BrowserManager
        browser_manager = BrowserManager()

        # 设置代理管理器
        if proxy_manager:
            browser_manager.proxy_manager = proxy_manager

        success = await browser_manager.start_browser()

        if success:
            # 保存浏览器实例到状态管理器
            state_manager.set_data('browser_instance', browser_manager)
            state_manager.set_data('browser_type', 'chrome')

            logger.info("Chrome浏览器启动成功")
        else:
            raise Exception("Chrome浏览器启动失败")

        # 发布浏览器初始化开始事件
        await event_bus.publish(create_event(
            name='browser_init_started',
            data={'browser_initialized': True},
            source='browser_init_task'
        ))

        return TaskResult(
            success=True,
            data={'browser_initialized': True}
        )

    except Exception as e:
        logger.error(f"浏览器启动失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def roxy_browser_init_task(state_manager, event_bus):
    """任务1: 启动RoxyBrowser - 专用于Augment注册"""
    logger.info("执行任务: roxy_browser_init_task")

    try:
        # 全程使用RoxyBrowser
        logger.info("使用RoxyBrowser启动浏览器")

        # 检查是否有RoxyBrowser API密钥
        if not ROXY_API_KEY:
            raise Exception("RoxyBrowser API密钥未配置")

        # 创建RoxyBrowser管理器
        from navie.utils.roxy_client import RoxyBrowserManager
        browser_manager = RoxyBrowserManager()

        # 创建并打开浏览器
        browser_manager.create_browser()

        # 保存浏览器实例到状态管理器
        state_manager.set_data('browser_instance', browser_manager)
        state_manager.set_data('browser_type', 'roxy')

        logger.info("RoxyBrowser启动成功")

        return TaskResult(
            success=True,
            data={'browser_started': True}
        )

    except Exception as e:
        logger.error(f"RoxyBrowser启动失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def navigate_to_signup_task(state_manager, event_bus):
    """任务2: 导航到注册页面"""
    logger.info("执行任务: navigate_to_signup_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")
        
        # 导航到GitHub注册页面
        browser.navigate_to(GITHUB_SIGNUP_URL)
        
        logger.info(f"导航到注册页面: {GITHUB_SIGNUP_URL}")
        
        return TaskResult(
            success=True,
            data={'current_url': GITHUB_SIGNUP_URL}
        )
        
    except Exception as e:
        logger.error(f"导航失败: {e}")

        # 检查是否可能是IP被屏蔽导致的失败
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ['timeout', 'connection', 'refused', 'blocked']):
            logger.warning("导航失败可能由于IP被屏蔽，触发IP检查")
            return TaskResult(
                success=False,
                error=str(e),
                should_retry=True,
                next_tasks=['check_ip_blocked_task']  # 触发IP检查
            )

        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def page_load_wait_task(state_manager, event_bus):
    """任务3: 等待页面完全加载"""
    logger.info("执行任务: page_load_wait_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 检查页面是否正确加载
        current_url = browser.driver.current_url
        page_title = browser.driver.title
        
        logger.info(f"页面加载完成 - URL: {current_url}, Title: {page_title}")
        
        # 发布浏览器就绪事件
        await event_bus.publish(create_event(
            name='browser_ready',
            data={
                'current_url': current_url,
                'page_title': page_title
            },
            source='page_load_wait_task'
        ))
        
        return TaskResult(
            success=True,
            data={
                'current_url': current_url,
                'page_title': page_title
            }
        )
        
    except Exception as e:
        logger.error(f"页面加载等待失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def proxy_switch_task(state_manager, event_bus):
    """代理切换任务 - 当检测到IP被屏蔽时切换代理"""
    logger.info("执行任务: proxy_switch_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 标记当前代理失败
        browser.mark_current_proxy_failed()

        # 检查是否可以切换代理
        if browser.switch_proxy():
            # 关闭当前浏览器
            browser.close_browser()

            # 重新启动浏览器（使用新代理）
            await browser.start_browser()

            # 更新状态管理器中的浏览器实例
            state_manager.set_data('browser_instance', browser)

            logger.info("代理切换成功，浏览器已重启")

            return TaskResult(
                success=True,
                data={'proxy_switched': True},
                next_tasks=['navigate_to_signup_task']  # 重新导航到注册页面
            )
        else:
            logger.warning("无法切换代理，可能没有可用代理")
            return TaskResult(
                success=False,
                error="无法切换代理",
                should_retry=False
            )

    except Exception as e:
        logger.error(f"代理切换失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def check_ip_blocked_task(state_manager, event_bus):
    """检查IP是否被屏蔽"""
    logger.info("执行任务: check_ip_blocked_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 检查页面内容是否包含屏蔽相关信息
        page_source = browser.driver.page_source.lower()

        # GitHub常见的屏蔽/限制提示
        blocked_indicators = [
            'rate limit',
            'too many requests',
            'access denied',
            'blocked',
            'forbidden',
            'your ip has been temporarily blocked',
            'unusual traffic',
            'captcha required'
        ]

        is_blocked = any(indicator in page_source for indicator in blocked_indicators)

        if is_blocked:
            logger.warning("检测到IP可能被屏蔽")

            # 发布IP屏蔽事件
            await event_bus.publish(create_event(
                name='ip_blocked_detected',
                data={'blocked': True},
                source='check_ip_blocked_task'
            ))

            return TaskResult(
                success=True,
                data={'ip_blocked': True},
                next_tasks=['proxy_switch_task']  # 触发代理切换
            )
        else:
            logger.info("IP状态正常")
            return TaskResult(
                success=True,
                data={'ip_blocked': False}
            )

    except Exception as e:
        logger.error(f"检查IP状态失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def browser_switch_to_roxy_task(state_manager, event_bus):
    """任务: 切换到RoxyBrowser"""
    logger.info("执行任务: browser_switch_to_roxy_task")

    try:
        # 关闭当前Chrome浏览器
        current_browser = state_manager.get_data('browser_instance')
        if current_browser:
            logger.info("关闭当前Chrome浏览器...")
            if hasattr(current_browser, 'driver') and current_browser.driver:
                current_browser.driver.quit()
            state_manager.set_data('browser_instance', None)

        # 启动RoxyBrowser
        logger.info("启动RoxyBrowser...")
        from navie.utils.roxy_client import RoxyBrowserManager

        roxy_browser = RoxyBrowserManager()
        roxy_browser.create_browser()

        # 保存RoxyBrowser实例到状态管理器
        state_manager.set_data('browser_instance', roxy_browser)

        logger.info("已成功切换到RoxyBrowser")
        return TaskResult(
            success=True,
            data={'browser_switched_to_roxy': True}
        )

    except Exception as e:
        logger.error(f"切换到RoxyBrowser失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )
