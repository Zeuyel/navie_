"""
验证码解决器 - 支持HCaptcha
基于YesCaptcha API
"""

import asyncio
import logging
import aiohttp
from config import YESCAPTCHA_API_KEY, YESCAPTCHA_BASE_URL

logger = logging.getLogger(__name__)

async def solve_hcaptcha(site_key, page_url, max_wait_time=300):
    """
    解决HCaptcha验证码
    
    Args:
        site_key: HCaptcha站点密钥
        page_url: 页面URL
        max_wait_time: 最大等待时间（秒）
        
    Returns:
        验证码解决结果，失败返回None
    """
    if not YESCAPTCHA_API_KEY:
        logger.error("YesCaptcha API密钥未配置")
        return None
    
    logger.info(f"开始解决HCaptcha - site_key: {site_key}, url: {page_url}")
    
    try:
        # 创建任务
        task_id = await create_hcaptcha_task(site_key, page_url)
        if not task_id:
            logger.error("创建HCaptcha任务失败")
            return None
        
        logger.info(f"HCaptcha任务创建成功，任务ID: {task_id}")
        
        # 等待任务完成
        result = await wait_for_hcaptcha_result(task_id, max_wait_time)
        
        if result:
            logger.info("HCaptcha解决成功")
            return result
        else:
            logger.error("HCaptcha解决失败")
            return None
            
    except Exception as e:
        logger.error(f"解决HCaptcha时发生错误: {e}")
        return None


async def create_hcaptcha_task(site_key, page_url):
    """
    创建HCaptcha任务
    
    Args:
        site_key: HCaptcha站点密钥
        page_url: 页面URL
        
    Returns:
        任务ID，失败返回None
    """
    url = f"{YESCAPTCHA_BASE_URL}/createTask"
    
    data = {
        "clientKey": YESCAPTCHA_API_KEY,
        "task": {
            "type": "HCaptchaTaskProxyless",
            "websiteURL": page_url,
            "websiteKey": site_key
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                response_data = await response.json()
                
                if response_data.get('errorId') == 0:
                    task_id = response_data.get('taskId')
                    logger.info(f"HCaptcha任务创建成功: {task_id}")
                    return task_id
                else:
                    error_code = response_data.get('errorCode')
                    error_description = response_data.get('errorDescription')
                    logger.error(f"创建HCaptcha任务失败: {error_code} - {error_description}")
                    return None
                    
    except Exception as e:
        logger.error(f"创建HCaptcha任务时发生错误: {e}")
        return None


async def wait_for_hcaptcha_result(task_id, max_wait_time=300):
    """
    等待HCaptcha任务完成
    
    Args:
        task_id: 任务ID
        max_wait_time: 最大等待时间（秒）
        
    Returns:
        验证码解决结果，失败返回None
    """
    url = f"{YESCAPTCHA_BASE_URL}/getTaskResult"
    
    data = {
        "clientKey": YESCAPTCHA_API_KEY,
        "taskId": task_id
    }
    
    start_time = asyncio.get_event_loop().time()
    check_interval = 5  # 每5秒检查一次
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    response_data = await response.json()
                    
                    if response_data.get('errorId') == 0:
                        status = response_data.get('status')
                        
                        if status == 'ready':
                            # 任务完成
                            solution = response_data.get('solution', {})
                            gRecaptchaResponse = solution.get('gRecaptchaResponse')
                            
                            if gRecaptchaResponse:
                                logger.info("HCaptcha任务完成")
                                return gRecaptchaResponse
                            else:
                                logger.error("HCaptcha解决结果为空")
                                return None
                                
                        elif status == 'processing':
                            # 任务处理中
                            elapsed_time = asyncio.get_event_loop().time() - start_time
                            if elapsed_time >= max_wait_time:
                                logger.error(f"HCaptcha任务超时 ({max_wait_time}秒)")
                                return None
                            
                            logger.info(f"HCaptcha任务处理中，已等待 {elapsed_time:.0f} 秒")
                            await asyncio.sleep(check_interval)
                            continue
                            
                        else:
                            logger.error(f"HCaptcha任务状态异常: {status}")
                            return None
                    else:
                        error_code = response_data.get('errorCode')
                        error_description = response_data.get('errorDescription')
                        logger.error(f"获取HCaptcha任务结果失败: {error_code} - {error_description}")
                        return None
                        
        except Exception as e:
            logger.error(f"检查HCaptcha任务状态时发生错误: {e}")
            await asyncio.sleep(check_interval)
            
            # 检查是否超时
            elapsed_time = asyncio.get_event_loop().time() - start_time
            if elapsed_time >= max_wait_time:
                logger.error(f"HCaptcha任务超时 ({max_wait_time}秒)")
                return None


async def solve_recaptcha_v2(site_key, page_url, max_wait_time=300):
    """
    解决reCAPTCHA v2验证码
    
    Args:
        site_key: reCAPTCHA站点密钥
        page_url: 页面URL
        max_wait_time: 最大等待时间（秒）
        
    Returns:
        验证码解决结果，失败返回None
    """
    if not YESCAPTCHA_API_KEY:
        logger.error("YesCaptcha API密钥未配置")
        return None
    
    logger.info(f"开始解决reCAPTCHA v2 - site_key: {site_key}, url: {page_url}")
    
    try:
        # 创建任务
        task_id = await create_recaptcha_v2_task(site_key, page_url)
        if not task_id:
            logger.error("创建reCAPTCHA v2任务失败")
            return None
        
        logger.info(f"reCAPTCHA v2任务创建成功，任务ID: {task_id}")
        
        # 等待任务完成
        result = await wait_for_hcaptcha_result(task_id, max_wait_time)  # 复用等待函数
        
        if result:
            logger.info("reCAPTCHA v2解决成功")
            return result
        else:
            logger.error("reCAPTCHA v2解决失败")
            return None
            
    except Exception as e:
        logger.error(f"解决reCAPTCHA v2时发生错误: {e}")
        return None


async def create_recaptcha_v2_task(site_key, page_url):
    """
    创建reCAPTCHA v2任务
    
    Args:
        site_key: reCAPTCHA站点密钥
        page_url: 页面URL
        
    Returns:
        任务ID，失败返回None
    """
    url = f"{YESCAPTCHA_BASE_URL}/createTask"
    
    data = {
        "clientKey": YESCAPTCHA_API_KEY,
        "task": {
            "type": "NoCaptchaTaskProxyless",
            "websiteURL": page_url,
            "websiteKey": site_key
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                response_data = await response.json()
                
                if response_data.get('errorId') == 0:
                    task_id = response_data.get('taskId')
                    logger.info(f"reCAPTCHA v2任务创建成功: {task_id}")
                    return task_id
                else:
                    error_code = response_data.get('errorCode')
                    error_description = response_data.get('errorDescription')
                    logger.error(f"创建reCAPTCHA v2任务失败: {error_code} - {error_description}")
                    return None
                    
    except Exception as e:
        logger.error(f"创建reCAPTCHA v2任务时发生错误: {e}")
        return None


def get_account_balance():
    """
    获取YesCaptcha账户余额
    
    Returns:
        账户余额，失败返回None
    """
    import requests
    
    if not YESCAPTCHA_API_KEY:
        logger.error("YesCaptcha API密钥未配置")
        return None
    
    url = f"{YESCAPTCHA_BASE_URL}/getBalance"
    data = {"clientKey": YESCAPTCHA_API_KEY}
    
    try:
        response = requests.post(url, json=data)
        response_data = response.json()
        
        if response_data.get('errorId') == 0:
            balance = response_data.get('balance')
            logger.info(f"YesCaptcha账户余额: {balance}")
            return balance
        else:
            error_code = response_data.get('errorCode')
            error_description = response_data.get('errorDescription')
            logger.error(f"获取账户余额失败: {error_code} - {error_description}")
            return None
            
    except Exception as e:
        logger.error(f"获取账户余额时发生错误: {e}")
        return None
