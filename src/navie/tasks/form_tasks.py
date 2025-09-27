"""
表单相关任务
"""

import asyncio
import logging
import random
import string
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from navie.core.task_manager import TaskResult
from navie.core.event_bus import create_event
from navie.utils.email_manager import EmailManagerFactory
try:
    from config import (DEFAULT_PASSWORD, USERNAME_MIN_LENGTH,
                       USERNAME_MAX_LENGTH, USERNAME_INCLUDE_NUMBERS, USERNAME_INCLUDE_HYPHENS,
                       USERNAME_AVOID_CONSECUTIVE_NUMBERS, USERNAME_PREFERRED_STRATEGIES)
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from config import (DEFAULT_PASSWORD, USERNAME_MIN_LENGTH,
                       USERNAME_MAX_LENGTH, USERNAME_INCLUDE_NUMBERS, USERNAME_INCLUDE_HYPHENS,
                       USERNAME_AVOID_CONSECUTIVE_NUMBERS, USERNAME_PREFERRED_STRATEGIES)

logger = logging.getLogger(__name__)

async def email_input_task(state_manager, event_bus):
    """任务4: 定位并填写邮箱字段"""
    logger.info("执行任务: email_input_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 从状态管理器获取已选择的邮箱地址
        email_address = state_manager.get_data('selected_email')
        if not email_address:
            # 如果没有预选择的邮箱，则从配置文件加载
            email_manager = EmailManagerFactory.load_from_config()
            if not email_manager:
                raise Exception("无法加载邮箱配置，请检查 email_config.json")
            email_address = email_manager.email

        logger.info(f"使用邮箱地址: {email_address}")

        # 发布表单填写开始事件
        await event_bus.publish(create_event(
            name='form_filling_started',
            data={},
            source='email_input_task'
        ))

        # 等待邮箱输入框出现
        wait = WebDriverWait(browser.driver, 10)
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))

        # 清空并填写邮箱
        email_input.clear()
        email_input.send_keys(email_address)

        # 保存邮箱到状态
        state_manager.set_data('email', email_address)

        logger.info(f"邮箱填写成功: {email_address}")

        return TaskResult(
            success=True,
            data={'email': email_address}
        )
        
    except TimeoutException:
        logger.error("邮箱输入框未找到")
        return TaskResult(
            success=False,
            error="邮箱输入框未找到",
            should_retry=True
        )
    except Exception as e:
        logger.error(f"邮箱填写失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def password_input_task(state_manager, event_bus):
    """任务5: 定位并填写密码字段"""
    logger.info("执行任务: password_input_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")
        
        # 等待密码输入框出现
        wait = WebDriverWait(browser.driver, 10)
        password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
        
        # 获取邮箱配置中的密码
        email_manager = EmailManagerFactory.load_from_config()
        if email_manager and hasattr(email_manager, 'password') and email_manager.password:
            password_to_use = email_manager.password
            logger.info("使用邮箱配置中的密码")

            # 检查密码是否为纯字母，如果是则添加"0"
            if password_to_use.isalpha():
                password_to_use = password_to_use + "0"
                logger.info("密码为纯字母，已添加'0'后缀")
        else:
            password_to_use = DEFAULT_PASSWORD
            logger.info("使用默认密码")

        # 清空并填写密码
        password_input.clear()
        password_input.send_keys(password_to_use)

        logger.info("密码填写成功")
        
        return TaskResult(
            success=True,
            data={'password_filled': True}
        )
        
    except TimeoutException:
        logger.error("密码输入框未找到")
        return TaskResult(
            success=False,
            error="密码输入框未找到",
            should_retry=True
        )
    except Exception as e:
        logger.error(f"密码填写失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def username_generate_task(state_manager, event_bus):
    """任务6: 生成用户名 - 使用邮箱前缀作为用户名"""
    logger.info("执行任务: username_generate_task")

    try:
        # 获取邮箱地址
        email_address = state_manager.get_data('email')
        if not email_address:
            # 如果状态中没有邮箱，尝试从配置加载
            email_manager = EmailManagerFactory.load_from_config()
            if email_manager:
                email_address = email_manager.email
            else:
                raise Exception("无法获取邮箱地址")

        # 使用邮箱前缀作为用户名
        email_prefix = email_address.split('@')[0]
        logger.info(f"使用邮箱前缀作为用户名: {email_prefix}")

        # 确保符合GitHub用户名要求
        username = email_prefix.lower()
        username = ''.join(c for c in username if c.isalnum() or c == '-')

        # 限制长度 (GitHub最大用户名长度为39)
        if len(username) > 39:
            username = username[:39]

        # 确保最小长度 (GitHub最小用户名长度为1)
        if len(username) < 1:
            username = "user" + ''.join(random.choices(string.digits, k=6))

        # 保存用户名到状态
        state_manager.set_data('current_username', username)

        logger.info(f"用户名生成成功: {username} (策略: email_prefix)")

        return TaskResult(
            success=True,
            data={'username': username, 'generation_method': 'email_prefix'}
        )

    except Exception as e:
        logger.error(f"邮箱前缀用户名生成失败，使用备用方法: {e}")

        # 备用方法：使用原来的简单生成
        try:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            username = f"user{random_suffix}"

            state_manager.set_data('current_username', username)
            logger.info(f"备用用户名生成成功: {username}")

            return TaskResult(
                success=True,
                data={'username': username, 'generation_method': 'fallback'}
            )
        except Exception as fallback_error:
            logger.error(f"备用用户名生成也失败: {fallback_error}")
            return TaskResult(
                success=False,
                error=str(fallback_error),
                should_retry=False
            )

async def username_input_task(state_manager, event_bus):
    """任务7: 填写用户名"""
    logger.info("执行任务: username_input_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        username = state_manager.get_data('current_username')
        
        if not browser:
            raise Exception("浏览器实例未找到")
        if not username:
            raise Exception("用户名未生成")
        
        # 等待用户名输入框出现
        wait = WebDriverWait(browser.driver, 10)
        username_input = wait.until(EC.presence_of_element_located((By.ID, "login")))
        
        # 清空并填写用户名
        username_input.clear()
        username_input.send_keys(username)
        
        logger.info(f"用户名填写成功: {username}")
        
        return TaskResult(
            success=True,
            data={'username_filled': True}
        )
        
    except TimeoutException:
        logger.error("用户名输入框未找到")
        return TaskResult(
            success=False,
            error="用户名输入框未找到",
            should_retry=True
        )
    except Exception as e:
        logger.error(f"用户名填写失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def username_validate_task(state_manager, event_bus):
    """任务8: 验证用户名可用性"""
    logger.info("执行任务: username_validate_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")
        
        # 等待验证结果
        await asyncio.sleep(2)
        
        # 检查是否有错误提示
        try:
            error_element = browser.driver.find_element(By.CSS_SELECTOR, "#login-err")
            if error_element.is_displayed():
                error_text = error_element.text
                logger.warning(f"用户名验证失败: {error_text}")
                
                # 如果用户名不可用，生成新的用户名
                return TaskResult(
                    success=False,
                    error=f"用户名不可用: {error_text}",
                    should_retry=False  # 不重试，而是生成新用户名
                )
        except:
            # 没有找到错误元素，说明验证通过
            pass
        
        logger.info("用户名验证通过")
        
        return TaskResult(
            success=True,
            data={'username_validated': True}
        )
        
    except Exception as e:
        logger.error(f"用户名验证失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def country_select_task(state_manager, event_bus):
    """任务9: 选择国家/地区"""
    logger.info("执行任务: country_select_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        wait = WebDriverWait(browser.driver, 10)

        # 第一步：查找并点击国家选择按钮来激活下拉框
        # 尝试多种可能的按钮选择器
        button_selectors = [
            "button[id*='select-panel'][id*='button']",  # 通用模式
            "button[data-view-component='true'][role='combobox']",  # GitHub特定模式
            "button.ActionListContent",  # 可能的类名
            "div[data-testid='country-select'] button",  # 容器中的按钮
            "[id*='select-panel'] button"  # 包含select-panel的元素中的按钮
        ]

        country_button = None
        for selector in button_selectors:
            try:
                country_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                logger.info(f"找到国家选择按钮，使用选择器: {selector}")
                break
            except TimeoutException:
                continue

        if not country_button:
            raise Exception("未找到国家选择按钮")

        # 点击按钮激活下拉框
        try:
            country_button.click()
            logger.info("已点击国家选择按钮，激活下拉框")
        except Exception as click_error:
            logger.warning(f"点击国家选择按钮失败: {click_error}")

            # 检查是否有cookie同意横幅阻挡
            try:
                # 查找Accept按钮
                accept_selectors = [
                    "button._1XuCi2WhiqeWRUVp3pnFG3.erL690_8JwUW-R4bJRcfl",  # 具体的类名
                    "button:contains('Accept')",  # 包含Accept文本的按钮
                    "[id*='wcpConsentBanner'] button",  # cookie横幅中的按钮
                    "div[role='alert'] button",  # alert角色的div中的按钮
                    "button[type='button']:contains('Accept')"  # 类型为button且包含Accept的按钮
                ]

                accept_button = None
                for selector in accept_selectors:
                    try:
                        if ":contains(" in selector:
                            # 对于包含文本的选择器，使用XPath
                            xpath_selector = f"//button[contains(text(), 'Accept')]"
                            accept_button = browser.driver.find_element(By.XPATH, xpath_selector)
                        else:
                            accept_button = browser.driver.find_element(By.CSS_SELECTOR, selector)

                        if accept_button and accept_button.is_displayed():
                            logger.info(f"找到Accept按钮，使用选择器: {selector}")
                            break
                    except:
                        continue

                if accept_button:
                    accept_button.click()
                    logger.info("已点击Accept按钮，关闭cookie同意横幅")
                    await asyncio.sleep(1)

                    # 重新尝试点击国家选择按钮
                    country_button.click()
                    logger.info("重新点击国家选择按钮成功")
                else:
                    raise click_error  # 如果没找到Accept按钮，抛出原始错误

            except Exception as accept_error:
                logger.error(f"处理cookie横幅失败: {accept_error}")
                raise click_error  # 抛出原始的点击错误

        # 等待下拉框出现
        await asyncio.sleep(1)

        # 第二步：查找并点击美国选项
        # 查找美国选项 (data-item-id="US")
        us_option_selectors = [
            "li[data-item-id='US'] button",  # 主要选择器
            "button[data-value='US']",  # 备用选择器
            "li[data-item-id='US']",  # 如果button不可点击，尝试li
            "[data-item-id='US']"  # 最通用的选择器
        ]

        us_option = None
        for selector in us_option_selectors:
            try:
                us_option = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                logger.info(f"找到美国选项，使用选择器: {selector}")
                break
            except TimeoutException:
                continue

        if not us_option:
            raise Exception("未找到美国选项")

        # 点击美国选项
        us_option.click()
        logger.info("已选择美国")

        # 等待选择完成
        await asyncio.sleep(0.5)

        logger.info("国家选择完成")

        return TaskResult(
            success=True,
            data={'country_selected': True, 'selected_country': 'US'}
        )

    except Exception as e:
        logger.error(f"国家选择失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def form_submit_task(state_manager, event_bus):
    """任务9: 提交表单"""
    logger.info("执行任务: form_submit_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")
        
        # 查找并点击提交按钮 - 使用多种选择器
        wait = WebDriverWait(browser.driver, 10)

        # 尝试多种可能的提交按钮选择器 - 按精确度排序
        submit_selectors = [
            # 最精确的选择器 - 基于最新的按钮HTML结构
            "button[aria-describedby='terms-of-service'][type='button'].js-octocaptcha-load-captcha.signup-form-fields__button",
            "button[aria-describedby='terms-of-service'][type='button'].js-octocaptcha-load-captcha",
            "button.js-octocaptcha-load-captcha.signup-form-fields__button.Button--primary",
            "button.js-octocaptcha-load-captcha.signup-form-fields__button",

            # 基于 aria-describedby 的选择器
            "button[aria-describedby='terms-of-service'][type='button']",
            "button[aria-describedby='terms-of-service']",

            # 基于 class 的选择器
            "button.js-octocaptcha-load-captcha",
            "button.signup-form-fields__button",
            "button.Button--primary.Button--fullWidth",
            "button.Button--primary.Button--medium",

            # 基于文本内容的选择器
            "//button[contains(text(), 'Create account')]",
            "//button[.//span[contains(text(), 'Create account')]]",

            # 通用选择器
            "button[type='submit']",  # 通用提交按钮
            "button.btn-primary",  # Bootstrap样式按钮
            "form button:last-child",  # 表单中的最后一个按钮
            "[data-testid='signup-button']",  # 测试ID
            ".signup-form button",  # 注册表单中的按钮
            "button.js-signup-form-submit",  # 可能的类名
        ]

        submit_button = None
        for selector in submit_selectors:
            try:
                # 判断是否为XPath选择器
                if selector.startswith("//"):
                    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                logger.info(f"找到提交按钮，使用选择器: {selector}")
                break
            except TimeoutException:
                continue

        # 如果所有选择器都失败，尝试更多文本查找
        if not submit_button:
            text_options = ['Create account', 'Sign up', 'Continue', 'Submit', 'Register']
            for text in text_options:
                try:
                    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{text}')]")))
                    logger.info(f"找到提交按钮，使用文本: {text}")
                    break
                except TimeoutException:
                    continue

        if not submit_button:
            raise Exception("未找到提交按钮")

        submit_button.click()

        logger.info("表单提交成功")
        
        # 发布表单提交事件
        await event_bus.publish(create_event(
            name='form_submitted',
            data={
                'email': state_manager.get_data('email'),
                'username': state_manager.get_data('current_username')
            },
            source='form_submit_task'
        ))
        
        return TaskResult(
            success=True,
            data={'form_submitted': True}
        )
        
    except TimeoutException:
        logger.error("提交按钮未找到")
        return TaskResult(
            success=False,
            error="提交按钮未找到",
            should_retry=True
        )
    except Exception as e:
        logger.error(f"表单提交失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )
