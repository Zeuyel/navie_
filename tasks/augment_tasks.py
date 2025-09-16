"""
Augment注册相关任务
基于tfa.md中的任务一和任务二实现
"""

import asyncio
import logging
import json
import os
import hashlib
import base64
import secrets
import random
import string
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

from core.task_manager import TaskResult
from core.event_bus import create_event
from config import (AUGMENT_BASE_URL, AUGMENT_AUTH_URL, AUGMENT_CLIENT_ID,
                   CARD_NUMBER, CARD_EXPIRY, CARD_CVC,
                   BILLING_ADDRESS_LINE1, BILLING_ADDRESS_LINE2, BILLING_POSTAL_CODE)

logger = logging.getLogger(__name__)

async def augment_navigate_task(state_manager, event_bus):
    """任务: 导航到Augment注册页面"""
    logger.info("执行任务: augment_navigate_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")
        
        # 在新标签页中打开Augment主页
        logger.info(f"在新标签页中打开Augment主页: {AUGMENT_BASE_URL}")

        # 使用JavaScript在新标签页中打开Augment
        browser.driver.execute_script(f"window.open('{AUGMENT_BASE_URL}', '_blank');")

        # 切换到新标签页
        browser.driver.switch_to.window(browser.driver.window_handles[-1])
        logger.info("已切换到新标签页")

        # 等待页面加载
        await asyncio.sleep(5)
        
        # 直接查找并点击 "Continue with GitHub" 按钮
        wait = WebDriverWait(browser.driver, 15)
        try:
            # 使用更精确的选择器
            github_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-provider='github']")))

            # 使用人性化点击
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(browser.driver)
            actions.move_to_element(github_button).pause(random.uniform(0.5, 1.0)).click().perform()

            logger.info("已点击 Continue with GitHub 按钮")
            await asyncio.sleep(3 + random.uniform(0.5, 1.5))
        except Exception as e:
            logger.error(f"点击 Continue with GitHub 按钮失败: {e}")
            # 尝试备用选择器
            try:
                github_button_alt = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'c2cff1259') and @data-provider='github']")))
                actions = ActionChains(browser.driver)
                actions.move_to_element(github_button_alt).pause(random.uniform(0.5, 1.0)).click().perform()
                logger.info("已使用备用选择器点击 Continue with GitHub 按钮")
                await asyncio.sleep(3 + random.uniform(0.5, 1.5))
            except Exception as e2:
                logger.error(f"备用选择器也失败: {e2}")
                raise Exception("无法找到或点击 Continue with GitHub 按钮")
        
        return TaskResult(
            success=True,
            data={'augment_navigation_completed': True},
            next_tasks=['augment_github_authorize_task']
        )
        
    except Exception as e:
        logger.error(f"Augment导航失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


async def augment_github_authorize_task(state_manager, event_bus):
    """任务: GitHub OAuth授权 - 直接使用密码登录"""
    logger.info("执行任务: augment_github_authorize_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 检测是否需要先登录GitHub
        logger.info("检测是否需要先登录GitHub...")
        login_needed = await check_github_login_required(browser, state_manager)

        if login_needed:
            logger.info("检测到需要先登录GitHub，开始登录流程...")
            login_success = await perform_github_login(browser, state_manager)

            if not login_success:
                logger.error("GitHub登录失败")
                raise Exception("GitHub登录失败，无法继续授权")

            logger.info("GitHub登录成功，等待页面自动重定向...")
            # 登录成功后等待页面自动重定向
            await asyncio.sleep(5)
        else:
            logger.info("无需登录，页面可能已经授权或重定向")
            await asyncio.sleep(2)
        
        # 检查页面重定向结果
        current_url = browser.driver.current_url
        logger.info(f"授权后页面URL: {current_url}")
        
        # 检查是否重定向到订阅页面
        if 'subscription' in current_url:
            logger.info("成功重定向到订阅页面")
            return TaskResult(
                success=True,
                data={'github_authorization_success': True, 'redirected_to_subscription': True},
                next_tasks=['augment_payment_setup_task']
            )
        else:
            # 检查是否出现signup-rejected或其他错误
            page_source = browser.driver.page_source.lower()
            if 'signup-rejected' in page_source or 'rejected' in page_source:
                logger.warning("注册被拒绝，记录到flagged.json")

                # 从email_config.json获取邮箱信息并记录到flagged.json
                try:
                    with open('email_config.json', 'r', encoding='utf-8') as f:
                        email_config = json.load(f)

                    accounts = email_config.get('accounts', [])
                    current_index = email_config.get('current_account_index', 0)

                    if accounts and current_index < len(accounts):
                        current_account = accounts[current_index]
                        flagged_data = {
                            "email": current_account.get('email', ''),
                            "password": current_account.get('password', ''),
                            "tfa_secret": current_account.get('tfa_secret', ''),
                            "client_id": current_account.get('client_id', ''),
                            "access_token": current_account.get('access_token', ''),
                            "reason": "signup-rejected"
                        }

                        # 保存到flagged.json
                        flagged_file = "flagged.json"
                        try:
                            if os.path.exists(flagged_file):
                                with open(flagged_file, 'r', encoding='utf-8') as f:
                                    flagged_list = json.load(f)
                            else:
                                flagged_list = []

                            flagged_list.append(flagged_data)

                            with open(flagged_file, 'w', encoding='utf-8') as f:
                                json.dump(flagged_list, f, indent=2, ensure_ascii=False)

                            logger.info(f"已将账号记录到 {flagged_file}")
                        except Exception as e:
                            logger.error(f"保存到flagged.json失败: {e}")
                    else:
                        logger.error("无法获取当前邮箱账号信息")

                except Exception as e:
                    logger.error(f"读取email_config.json失败: {e}")
                
                return TaskResult(
                    success=False,
                    error="注册被拒绝",
                    should_retry=False
                )
            else:
                logger.warning("未知的重定向结果，继续尝试")
                return TaskResult(
                    success=False,
                    error="未知的授权结果",
                    should_retry=True
                )
        
    except Exception as e:
        logger.error(f"GitHub授权失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


async def augment_payment_setup_task(state_manager, event_bus):
    """任务: 设置支付方式"""
    logger.info("执行任务: augment_payment_setup_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")
        
        # 等待并点击 "Confirm payment method" 按钮
        wait = WebDriverWait(browser.driver, 15)
        try:
            confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirm payment method')]")))
            confirm_button.click()
            logger.info("已点击 Confirm payment method 按钮")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"点击确认支付按钮失败: {e}")
            raise Exception("无法找到或点击确认支付按钮")
        
        # 等待重定向到Stripe支付页面
        current_url = browser.driver.current_url
        logger.info(f"支付页面URL: {current_url}")
        
        if 'billing.augmentcode.com' not in current_url:
            raise Exception("未正确重定向到支付页面")
        
        return TaskResult(
            success=True,
            data={'payment_page_loaded': True},
            next_tasks=['augment_stripe_form_task']
        )
        
    except Exception as e:
        logger.error(f"支付设置失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


async def augment_stripe_form_task(state_manager, event_bus):
    """任务: 填写Stripe支付表单"""
    logger.info("执行任务: augment_stripe_form_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")
        
        wait = WebDriverWait(browser.driver, 15)
        
        # 等待Stripe iframe加载
        await asyncio.sleep(3)
        
        # 查找并切换到卡号iframe - 使用多种选择器策略
        try:
            # 尝试多种iframe选择器
            iframe_selectors = [
                "iframe[name*='__privateStripeFrame']",
                "iframe[src*='stripe']",
                "iframe[title*='card']",
                "iframe[title*='Secure card number input frame']",
                ".StripeElement iframe"
            ]

            card_number_iframe = None
            for selector in iframe_selectors:
                try:
                    iframes = browser.driver.find_elements(By.CSS_SELECTOR, selector)
                    if iframes:
                        # 对于Stripe，通常第一个iframe是卡号输入框
                        card_number_iframe = iframes[0]
                        logger.info(f"找到卡号iframe，使用选择器: {selector}")
                        break
                except:
                    continue

            if not card_number_iframe:
                raise Exception("无法找到卡号iframe")

            browser.driver.switch_to.frame(card_number_iframe)

            # 输入卡号 - 尝试多种输入框选择器
            input_selectors = ["#cardNumber", "[name='cardnumber']", "[placeholder*='card number']", "input[type='text']"]
            card_number_input = None

            for selector in input_selectors:
                try:
                    card_number_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue

            if not card_number_input:
                raise Exception("无法找到卡号输入框")

            card_number_input.clear()
            card_number_input.send_keys(CARD_NUMBER)
            logger.info("已输入卡号")

            # 切换回主框架
            browser.driver.switch_to.default_content()

        except Exception as e:
            logger.error(f"输入卡号失败: {e}")
            raise Exception("无法输入卡号")
        
        # 输入过期日期 - 使用改进的iframe查找策略
        try:
            # 获取所有Stripe iframe
            all_iframes = browser.driver.find_elements(By.CSS_SELECTOR, "iframe[name*='__privateStripeFrame'], iframe[src*='stripe'], .StripeElement iframe")

            if len(all_iframes) < 2:
                raise Exception("找不到足够的Stripe iframe")

            # 通常第二个iframe是过期日期
            expiry_iframe = all_iframes[1]
            browser.driver.switch_to.frame(expiry_iframe)

            # 尝试多种过期日期输入框选择器
            expiry_selectors = ["#cardExpiry", "[name='exp-date']", "[placeholder*='expiry']", "[placeholder*='MM']", "input[type='text']"]
            expiry_input = None

            for selector in expiry_selectors:
                try:
                    expiry_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue

            if not expiry_input:
                raise Exception("无法找到过期日期输入框")

            expiry_input.clear()
            expiry_input.send_keys(CARD_EXPIRY)
            logger.info("已输入过期日期")

            # 切换回主框架
            browser.driver.switch_to.default_content()

        except Exception as e:
            logger.error(f"输入过期日期失败: {e}")
            raise Exception("无法输入过期日期")
        
        # 输入CVC - 使用改进的iframe查找策略
        try:
            # 获取所有Stripe iframe
            all_iframes = browser.driver.find_elements(By.CSS_SELECTOR, "iframe[name*='__privateStripeFrame'], iframe[src*='stripe'], .StripeElement iframe")

            if len(all_iframes) < 3:
                raise Exception("找不到足够的Stripe iframe")

            # 通常第三个iframe是CVC
            cvc_iframe = all_iframes[2]
            browser.driver.switch_to.frame(cvc_iframe)

            # 尝试多种CVC输入框选择器
            cvc_selectors = ["#cardCvc", "[name='cvc']", "[placeholder*='CVC']", "[placeholder*='CVV']", "input[type='text']"]
            cvc_input = None

            for selector in cvc_selectors:
                try:
                    cvc_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue

            if not cvc_input:
                raise Exception("无法找到CVC输入框")

            cvc_input.clear()
            cvc_input.send_keys(CARD_CVC)
            logger.info("已输入CVC")

            # 切换回主框架
            browser.driver.switch_to.default_content()

        except Exception as e:
            logger.error(f"输入CVC失败: {e}")
            raise Exception("无法输入CVC")
        
        return TaskResult(
            success=True,
            data={'stripe_card_info_filled': True},
            next_tasks=['augment_billing_address_task']
        )

    except Exception as e:
        logger.error(f"填写Stripe表单失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


async def augment_billing_address_task(state_manager, event_bus):
    """任务: 填写账单地址"""
    logger.info("执行任务: augment_billing_address_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        wait = WebDriverWait(browser.driver, 15)

        # 输入姓名
        try:
            import random
            import string
            # 生成随机姓名
            random_name = ''.join(random.choices(string.ascii_lowercase, k=8))

            billing_name_input = wait.until(EC.presence_of_element_located((By.ID, "billingName")))
            billing_name_input.clear()
            billing_name_input.send_keys(random_name)
            logger.info(f"已输入姓名: {random_name}")
        except Exception as e:
            logger.error(f"输入姓名失败: {e}")
            raise Exception("无法输入姓名")

        # 选择国家（美国）
        try:
            # 点击国家选择框
            country_select = wait.until(EC.element_to_be_clickable((By.ID, "billingCountry")))
            country_select.click()
            logger.info("已点击国家选择框")
            await asyncio.sleep(1)

            # 选择美国选项
            us_option = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "option[value='US']")))
            us_option.click()
            logger.info("已选择美国")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"选择国家失败: {e}")
            raise Exception("无法选择国家")

        # 点击手动输入地址
        try:
            manual_address_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Enter address manually')]")))
            manual_address_button.click()
            logger.info("已点击手动输入地址")
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"点击手动输入地址失败: {e}")
            raise Exception("无法点击手动输入地址")

        # 输入地址行1
        try:
            address_line1_input = wait.until(EC.presence_of_element_located((By.ID, "billingAddressLine1")))
            address_line1_input.clear()
            address_line1_input.send_keys(BILLING_ADDRESS_LINE1)
            logger.info("已输入地址行1")
        except Exception as e:
            logger.error(f"输入地址行1失败: {e}")
            raise Exception("无法输入地址行1")

        # 输入地址行2
        try:
            address_line2_input = wait.until(EC.presence_of_element_located((By.ID, "billingAddressLine2")))
            address_line2_input.clear()
            address_line2_input.send_keys(BILLING_ADDRESS_LINE2)
            logger.info("已输入地址行2")
        except Exception as e:
            logger.error(f"输入地址行2失败: {e}")
            raise Exception("无法输入地址行2")

        # 输入城市（美国特有字段）
        try:
            # 生成随机城市名
            random_city = ''.join(random.choices(string.ascii_lowercase, k=6))

            city_input = wait.until(EC.presence_of_element_located((By.ID, "billingLocality")))
            city_input.clear()
            city_input.send_keys(random_city)
            logger.info(f"已输入城市: {random_city}")
        except Exception as e:
            logger.error(f"输入城市失败: {e}")
            raise Exception("无法输入城市")

        # 输入邮政编码
        try:
            postal_code_input = wait.until(EC.presence_of_element_located((By.ID, "billingPostalCode")))
            postal_code_input.clear()
            postal_code_input.send_keys(BILLING_POSTAL_CODE)
            logger.info("已输入邮政编码")
        except Exception as e:
            logger.error(f"输入邮政编码失败: {e}")
            raise Exception("无法输入邮政编码")

        return TaskResult(
            success=True,
            data={'billing_address_filled': True},
            next_tasks=['augment_captcha_detect_task']
        )

    except Exception as e:
        logger.error(f"填写账单地址失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


async def augment_captcha_detect_task(state_manager, event_bus):
    """任务: 检测HCaptcha"""
    logger.info("执行任务: augment_captcha_detect_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 检查是否出现HCaptcha
        try:
            hcaptcha_element = browser.driver.find_element(By.CSS_SELECTOR, ".h-captcha, [data-hcaptcha], iframe[src*='hcaptcha']")
            if hcaptcha_element and hcaptcha_element.is_displayed():
                logger.info("检测到HCaptcha，需要解决")
                return TaskResult(
                    success=True,
                    data={'hcaptcha_detected': True},
                    next_tasks=['augment_hcaptcha_solve_task']
                )
        except:
            pass

        # 如果没有检测到验证码，直接提交表单
        logger.info("未检测到HCaptcha，直接提交表单")
        return TaskResult(
            success=True,
            data={'hcaptcha_detected': False},
            next_tasks=['augment_form_submit_task']
        )

    except Exception as e:
        logger.error(f"检测HCaptcha失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


async def augment_hcaptcha_solve_task(state_manager, event_bus):
    """任务: 解决HCaptcha"""
    logger.info("执行任务: augment_hcaptcha_solve_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 获取HCaptcha站点密钥
        try:
            hcaptcha_element = browser.driver.find_element(By.CSS_SELECTOR, "[data-sitekey]")
            site_key = hcaptcha_element.get_attribute("data-sitekey")
            logger.info(f"获取到HCaptcha站点密钥: {site_key}")
        except Exception as e:
            logger.error(f"获取HCaptcha站点密钥失败: {e}")
            raise Exception("无法获取HCaptcha站点密钥")

        # 使用YesCaptcha API解决HCaptcha
        from utils.captcha_solver import solve_hcaptcha

        current_url = browser.driver.current_url
        captcha_result = await solve_hcaptcha(site_key, current_url)

        if not captcha_result:
            raise Exception("HCaptcha解决失败")

        # 将验证码结果注入到页面
        script = f"""
        document.querySelector('[name="h-captcha-response"]').value = '{captcha_result}';
        document.querySelector('[name="g-recaptcha-response"]').value = '{captcha_result}';
        """
        browser.driver.execute_script(script)

        logger.info("HCaptcha解决成功")

        return TaskResult(
            success=True,
            data={'hcaptcha_solved': True},
            next_tasks=['augment_form_submit_task']
        )

    except Exception as e:
        logger.error(f"解决HCaptcha失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


async def augment_form_submit_task(state_manager, event_bus):
    """任务: 提交支付表单"""
    logger.info("执行任务: augment_form_submit_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 查找并点击提交按钮
        wait = WebDriverWait(browser.driver, 15)
        try:
            submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], .submit-button, [data-testid='hosted-payment-submit-button']")))
            submit_button.click()
            logger.info("已点击提交按钮")
            await asyncio.sleep(10)  # 等待支付处理
        except Exception as e:
            logger.error(f"点击提交按钮失败: {e}")
            raise Exception("无法找到或点击提交按钮")

        # 检查是否成功跳转回订阅页面
        current_url = browser.driver.current_url
        logger.info(f"提交后页面URL: {current_url}")

        if 'app.augmentcode.com/account/subscription' in current_url:
            logger.info("支付成功，已跳转回订阅页面")
            return TaskResult(
                success=True,
                data={'payment_completed': True},
                next_tasks=['augment_token_generation_task']
            )
        else:
            logger.warning("支付可能失败或页面未正确跳转")
            return TaskResult(
                success=False,
                error="支付未成功完成",
                should_retry=True
            )

    except Exception as e:
        logger.error(f"提交支付表单失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


async def augment_token_generation_task(state_manager, event_bus):
    """任务: 生成OAuth状态并获取授权码"""
    logger.info("执行任务: augment_token_generation_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 生成OAuth状态
        oauth_state = generate_oauth_state()
        state_manager.set_data('oauth_state', oauth_state)

        # 生成授权URL
        authorize_url = generate_authorize_url(oauth_state)
        logger.info(f"生成的授权URL: {authorize_url}")

        # 导航到授权URL
        browser.driver.get(authorize_url)
        await asyncio.sleep(3)

        # 点击 "Continue with GitHub" 按钮
        wait = WebDriverWait(browser.driver, 15)
        try:
            github_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-provider='github']")))
            github_button.click()
            logger.info("已点击 Continue with GitHub 按钮")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"点击 Continue with GitHub 按钮失败: {e}")
            raise Exception("无法找到或点击 Continue with GitHub 按钮")

        return TaskResult(
            success=True,
            data={'oauth_state_generated': True, 'authorize_url': authorize_url},
            next_tasks=['augment_code_extract_task']
        )

    except Exception as e:
        logger.error(f"生成OAuth状态失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


async def augment_code_extract_task(state_manager, event_bus):
    """任务: 提取授权码和状态"""
    logger.info("执行任务: augment_code_extract_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 等待页面跳转到授权码显示页面
        wait = WebDriverWait(browser.driver, 30)

        # 查找包含授权码的input元素
        try:
            code_input = wait.until(EC.presence_of_element_located((By.ID, "codeDisplay")))
            code_json_str = code_input.get_attribute("value")
            logger.info(f"获取到授权码JSON: {code_json_str}")
        except Exception as e:
            logger.error(f"获取授权码失败: {e}")
            raise Exception("无法找到授权码显示元素")

        # 解析JSON数据
        try:
            code_data = json.loads(code_json_str)
            auth_code = code_data.get('code')
            state = code_data.get('state')
            tenant_url = code_data.get('tenant_url')

            if not all([auth_code, state, tenant_url]):
                raise Exception("授权码数据不完整")

            logger.info(f"解析成功 - code: {auth_code}, state: {state}, tenant_url: {tenant_url}")

            # 保存到状态管理器
            state_manager.set_data('auth_code', auth_code)
            state_manager.set_data('auth_state', state)
            state_manager.set_data('tenant_url', tenant_url)

        except json.JSONDecodeError as e:
            logger.error(f"解析授权码JSON失败: {e}")
            raise Exception("授权码JSON格式错误")

        return TaskResult(
            success=True,
            data={'code_extracted': True, 'auth_code': auth_code, 'tenant_url': tenant_url},
            next_tasks=['augment_access_token_task']
        )

    except Exception as e:
        logger.error(f"提取授权码失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


async def augment_access_token_task(state_manager, event_bus):
    """任务: 获取访问令牌"""
    logger.info("执行任务: augment_access_token_task")

    try:
        # 获取必要的数据
        oauth_state = state_manager.get_data('oauth_state')
        auth_code = state_manager.get_data('auth_code')
        tenant_url = state_manager.get_data('tenant_url')

        if not all([oauth_state, auth_code, tenant_url]):
            raise Exception("缺少必要的OAuth数据")

        # 获取访问令牌
        access_token = await get_access_token(tenant_url, oauth_state['codeVerifier'], auth_code)

        if not access_token:
            raise Exception("获取访问令牌失败")

        logger.info("访问令牌获取成功")

        # 保存令牌到状态管理器
        state_manager.set_data('augment_access_token', access_token)

        return TaskResult(
            success=True,
            data={'access_token_obtained': True, 'access_token': access_token},
            next_tasks=['augment_token_save_task']
        )

    except Exception as e:
        logger.error(f"获取访问令牌失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


async def augment_token_save_task(state_manager, event_bus):
    """任务: 保存令牌到文件"""
    logger.info("执行任务: augment_token_save_task")

    try:
        # 获取所有必要的数据
        augment_access_token = state_manager.get_data('augment_access_token')
        tenant_url = state_manager.get_data('tenant_url')

        # 获取邮箱信息
        email_address = state_manager.get_data('email')
        email_manager = state_manager.get_data('email_manager')

        if not email_manager:
            from utils.email_manager import EmailManagerFactory
            email_manager = EmailManagerFactory.load_from_config()

        if not email_manager:
            raise Exception("无法获取邮箱信息")

        # 构建令牌数据
        token_data = {
            "email": email_manager.email,
            "password": email_manager.password,
            "tfa_secret": getattr(email_manager, 'tfa_secret', ''),
            "client_id": email_manager.client_id,
            "access_token": email_manager.access_token,  # 邮箱的token
            "tenant_url": tenant_url,
            "augment_token": augment_access_token  # Augment的token
        }

        # 保存到augment_token.json
        token_file = "augment_token.json"
        try:
            if os.path.exists(token_file):
                with open(token_file, 'r', encoding='utf-8') as f:
                    token_list = json.load(f)
            else:
                token_list = []

            token_list.append(token_data)

            with open(token_file, 'w', encoding='utf-8') as f:
                json.dump(token_list, f, indent=2, ensure_ascii=False)

            logger.info(f"令牌已保存到 {token_file}")

        except Exception as e:
            logger.error(f"保存令牌文件失败: {e}")
            raise Exception(f"保存令牌失败: {e}")

        return TaskResult(
            success=True,
            data={'token_saved': True, 'token_file': token_file}
        )

    except Exception as e:
        logger.error(f"保存令牌失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=False
        )


# OAuth辅助函数
def base64url_encode(data):
    """Base64URL编码"""
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')


def generate_oauth_state():
    """生成OAuth状态"""
    # 生成code verifier
    code_verifier_bytes = secrets.token_bytes(32)
    code_verifier = base64url_encode(code_verifier_bytes)

    # 生成code challenge
    code_challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64url_encode(code_challenge_bytes)

    # 生成state
    state_bytes = secrets.token_bytes(8)
    state = base64url_encode(state_bytes)

    return {
        'codeVerifier': code_verifier,
        'codeChallenge': code_challenge,
        'state': state,
        'creationTime': int(asyncio.get_event_loop().time() * 1000)
    }


def generate_authorize_url(oauth_state):
    """生成授权URL"""
    from urllib.parse import urlencode

    params = {
        'response_type': 'code',
        'code_challenge': oauth_state['codeChallenge'],
        'client_id': AUGMENT_CLIENT_ID,
        'state': oauth_state['state'],
        'prompt': 'login'
    }

    return f"{AUGMENT_AUTH_URL}/authorize?{urlencode(params)}"


async def get_access_token(tenant_url, code_verifier, code):
    """获取访问令牌"""
    import aiohttp

    # 确保tenant_url以/结尾
    if not tenant_url.endswith('/'):
        tenant_url = tenant_url + '/'

    token_url = f"{tenant_url}token"

    data = {
        'grant_type': 'authorization_code',
        'client_id': AUGMENT_CLIENT_ID,
        'code_verifier': code_verifier,
        'redirect_uri': '',
        'code': code
    }

    logger.info(f"请求令牌URL: {token_url}")
    logger.info(f"请求数据: {data}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, json=data, headers={'Content-Type': 'application/json'}) as response:
                response_text = await response.text()
                logger.info(f"API响应状态: {response.status}")
                logger.info(f"API响应内容: {response_text}")

                if response.status == 200:
                    response_json = await response.json()
                    access_token = response_json.get('access_token')
                    if access_token:
                        return access_token
                    else:
                        logger.error(f"响应中没有access_token: {response_json}")
                        return None
                else:
                    logger.error(f"API请求失败，状态码: {response.status}")
                    return None

    except Exception as e:
        logger.error(f"请求令牌失败: {e}")
        return None


async def check_github_login_required(browser, state_manager):
    """检测是否需要先登录GitHub"""
    try:
        current_url = browser.driver.current_url
        logger.info(f"当前页面URL: {current_url}")

        # 检查是否在GitHub登录页面
        if 'github.com/login' in current_url:
            logger.info("检测到GitHub登录页面")
            return True

        # 检查页面是否包含登录表单
        try:
            login_form = browser.driver.find_element(By.CSS_SELECTOR, "form[action='/session']")
            if login_form:
                logger.info("检测到GitHub登录表单")
                return True
        except:
            pass

        # 检查是否有用户名/密码输入框
        try:
            username_field = browser.driver.find_element(By.ID, "login_field")
            password_field = browser.driver.find_element(By.ID, "password")
            if username_field and password_field:
                logger.info("检测到GitHub登录输入框")
                return True
        except:
            pass

        # 检查页面标题
        page_title = browser.driver.title.lower()
        if 'sign in to github' in page_title or 'login' in page_title:
            logger.info("检测到GitHub登录页面标题")
            return True

        logger.info("未检测到GitHub登录需求")
        return False

    except Exception as e:
        logger.error(f"检测GitHub登录需求失败: {e}")
        return False


async def perform_github_login(browser, state_manager):
    """执行GitHub登录"""
    try:
        # 从当前邮箱配置获取GitHub登录信息（邮箱+密码）
        try:
            with open('email_config.json', 'r', encoding='utf-8') as f:
                email_config = json.load(f)

            accounts = email_config.get('accounts', [])
            current_index = email_config.get('current_account_index', 0)

            if not accounts or current_index >= len(accounts):
                logger.error("无法获取当前邮箱账号信息")
                return False

            current_account = accounts[current_index]
            github_username = current_account.get('email')  # 使用邮箱作为GitHub登录用户名
            github_password = current_account.get('password')  # 使用邮箱密码作为GitHub登录密码

        except Exception as e:
            logger.error(f"读取邮箱配置失败: {e}")
            return False

        if not github_username or not github_password:
            logger.error("当前邮箱账号信息不完整")
            return False

        logger.info(f"开始GitHub登录，用户名: {github_username}")

        # 等待登录表单加载
        wait = WebDriverWait(browser.driver, 10)

        # 输入用户名
        try:
            username_field = wait.until(EC.presence_of_element_located((By.ID, "login_field")))
            username_field.clear()
            username_field.send_keys(github_username)
            logger.info("已输入GitHub用户名")
        except Exception as e:
            logger.error(f"输入用户名失败: {e}")
            return False

        # 输入密码
        try:
            password_field = browser.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(github_password)
            logger.info("已输入GitHub密码")
        except Exception as e:
            logger.error(f"输入密码失败: {e}")
            return False

        # 点击登录按钮
        try:
            login_button = browser.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Sign in']")
            login_button.click()
            logger.info("已点击GitHub登录按钮")

            # 等待登录完成
            await asyncio.sleep(5)

            # 检查登录结果
            current_url = browser.driver.current_url
            logger.info(f"登录后页面URL: {current_url}")

            # 如果还在登录页面（但不是授权页面），说明登录失败
            if 'github.com/login' in current_url and 'oauth/authorize' not in current_url:
                logger.error("GitHub登录失败，仍在登录页面")
                return False

            # 检查是否出现了授权按钮
            try:
                wait = WebDriverWait(browser.driver, 10)
                authorize_button = wait.until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    "button[name='authorize'], button.js-oauth-authorize-btn, input[name='authorize']"
                )))
                logger.info("检测到GitHub授权按钮，自动点击授权")
                authorize_button.click()
                await asyncio.sleep(3)
                logger.info("已点击GitHub授权按钮")
            except Exception as e:
                logger.info(f"未检测到授权按钮或点击失败: {e}")
                # 这不是错误，可能已经授权过了

            logger.info("GitHub登录成功")
            return True

        except Exception as e:
            logger.error(f"点击登录按钮失败: {e}")
            return False

    except Exception as e:
        logger.error(f"GitHub登录过程失败: {e}")
        return False
