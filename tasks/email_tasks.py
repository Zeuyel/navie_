"""
邮箱验证相关任务
"""

import asyncio
import logging
import re
import random
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from core.task_manager import TaskResult
from core.event_bus import create_event
from utils.email_manager import EmailManagerFactory

logger = logging.getLogger(__name__)

def extract_verification_code(text):
    """从文本中提取验证码"""
    import re

    if not text:
        return None

    # 多种验证码模式
    patterns = [
        r'\b(\d{8})\b',           # 8位数字
        r'\b(\d{6})\b',           # 6位数字
        r'code[:\s]+(\d+)',       # "code: 12345" 格式
        r'验证码[:\s]+(\d+)',      # 中文验证码格式
        r'launch code[:\s]*\n*\s*(\d+)',  # GitHub launch code格式
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # 返回最长的匹配（通常验证码比较长）
            return max(matches, key=len)

    return None

def extract_verification_link(email_content):
    """从邮件内容中提取验证链接"""
    import re

    if not email_content:
        return None

    # GitHub验证链接的多种模式
    link_patterns = [
        # 标准的GitHub账户验证链接
        r'https://github\.com/account_verifications/confirm/[a-f0-9\-]+/\d+',
        # 通用的GitHub验证链接
        r'https://github\.com/[^"\s<>]+verify[^"\s<>]*',
        r'https://github\.com/[^"\s<>]+confirm[^"\s<>]*',
        # 可能的其他格式
        r'https://[^"\s<>]*github[^"\s<>]*verify[^"\s<>]*',
        r'https://[^"\s<>]*verify[^"\s<>]*github[^"\s<>]*'
    ]

    for pattern in link_patterns:
        matches = re.findall(pattern, email_content, re.IGNORECASE)
        if matches:
            # 返回第一个匹配的链接
            return matches[0]

    return None

def test_verification_link_extraction():
    """测试验证链接提取功能"""
    print("\n=== 测试验证链接提取功能 ===")

    # 测试用例1: 标准GitHub验证邮件内容
    test_email_1 = """
    Please verify your email address

    Click the link below to verify your email address:
    https://github.com/account_verifications/confirm/d93fbc4e-9502-458e-bcaf-cb0f517ad9e5/36625987

    Or enter this code: 12345678

    Not able to enter the code? Paste the following link into your browser:
    https://github.com/account_verifications/confirm/d93fbc4e-9502-458e-bcaf-cb0f517ad9e5/36625987
    """

    # 测试用例2: HTML格式的邮件
    test_email_2 = """
    <html>
    <body>
    <p>Please verify your email address</p>
    <a href="https://github.com/account_verifications/confirm/abc123-def456-ghi789/98765432">Verify Email</a>
    <p>Your verification code is: 87654321</p>
    </body>
    </html>
    """

    # 测试用例3: 不包含链接的邮件
    test_email_3 = """
    Your verification code is: 11223344
    Please enter this code on the GitHub website.
    """

    test_cases = [
        ("标准验证邮件", test_email_1),
        ("HTML格式邮件", test_email_2),
        ("无链接邮件", test_email_3)
    ]

    for case_name, email_content in test_cases:
        print(f"\n--- 测试: {case_name} ---")

        # 测试验证码提取
        code = extract_verification_code(email_content)
        print(f"提取的验证码: {code}")

        # 测试链接提取
        link = extract_verification_link(email_content)
        print(f"提取的验证链接: {link}")

        if link:
            print(f"✅ 成功提取链接: {link[:50]}...")
        else:
            print("❌ 未找到验证链接")

    print("\n=== 测试完成 ===")
    return True

def get_full_email_body(email_manager, email_id):
    """获取完整的邮件内容"""
    try:
        headers = email_manager.get_headers()
        if not headers:
            return None

        import requests
        url = f"{email_manager.base_url}/me/messages/{email_id}"
        params = {
            '$select': 'body,bodyPreview'
        }

        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code == 200:
            email_data = response.json()
            body = email_data.get('body', {})
            if isinstance(body, dict):
                return body.get('content', '')
            return str(body)
        else:
            logger.warning(f"获取邮件内容失败: {response.status_code}")
            return None

    except Exception as e:
        logger.warning(f"获取邮件内容异常: {e}")
        return None

async def email_verification_detect_task(state_manager, event_bus):
    """任务21: 检测邮箱验证页面"""
    logger.info("执行任务: email_verification_detect_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 检查当前页面内容
        page_source = browser.driver.page_source.lower()
        current_url = browser.driver.current_url
        
        logger.info(f"当前URL: {current_url}")
        
        # 检查邮箱验证相关指示器
        email_verification_indicators = [
            'verify your email',
            'check your email',
            'verification email',
            'confirm your email',
            'email verification'
        ]
        
        email_verification_detected = any(indicator in page_source for indicator in email_verification_indicators)
        
        if email_verification_detected:
            logger.info("检测到邮箱验证页面")
            
            # 发布邮箱验证事件
            await event_bus.publish(create_event(
                name='email_verification_required',
                data={'current_url': current_url},
                source='email_verification_detect_task'
            ))
            
            return TaskResult(
                success=True,
                data={'email_verification_required': True}
            )
        else:
            # 检查是否已经完成注册
            if 'welcome' in page_source or 'dashboard' in current_url or 'github.com' in current_url:
                logger.info("注册可能已完成")
                return TaskResult(
                    success=True,
                    data={'registration_completed': True}
                )
            else:
                logger.warning("未检测到邮箱验证页面，页面状态不明")
                return TaskResult(
                    success=False,
                    error="未检测到邮箱验证页面，页面状态不明",
                    should_retry=True
                )
        
    except Exception as e:
        logger.error(f"检测邮箱验证页面失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def email_fetch_task(state_manager, event_bus):
    """任务22: 获取验证邮件"""
    logger.info("执行任务: email_fetch_task")
    
    try:
        email_address = state_manager.get_data('email')
        if not email_address:
            raise Exception("邮箱地址未找到")
        
        # 创建邮箱管理器
        email_manager = EmailManagerFactory.load_from_config()
        if not email_manager:
            raise Exception("无法加载邮箱管理器，请检查邮箱配置")

        # 等待邮件到达
        max_attempts = 10
        resend_attempts = 0  # 重发次数计数
        max_resend_attempts = 2  # 最多重发2次

        for attempt in range(max_attempts):
            logger.info(f"第 {attempt + 1} 次尝试获取验证邮件...")

            try:
                # 获取最近2分钟内的邮件
                emails = email_manager.search_emails(
                    subject_filter=None,
                    from_filter=None,
                    time_range_minutes=2,  # 只获取最近2分钟的邮件
                    max_results=10
                )
                
                # 打印所有邮件信息用于调试
                logger.info(f"找到 {len(emails)} 封邮件:")
                for i, email in enumerate(emails):
                    subject = email.get('subject', '')
                    from_info = email.get('from', {})
                    if isinstance(from_info, dict):
                        sender = from_info.get('emailAddress', {}).get('address', '')
                    else:
                        sender = str(from_info)

                    body_preview = email.get('bodyPreview', '')[:100]
                    received_time = email.get('receivedDateTime', '')

                    print(f"\n=== 邮件 {i+1} ===")
                    print(f"主题: {subject}")
                    print(f"发件人: {sender}")
                    print(f"时间: {received_time}")
                    print(f"预览: {body_preview}")
                    print("=" * 50)

                # 查找GitHub验证邮件
                github_emails = []
                for email in emails:
                    subject = email.get('subject', '').lower()
                    from_info = email.get('from', {})
                    if isinstance(from_info, dict):
                        sender = from_info.get('emailAddress', {}).get('address', '').lower()
                    else:
                        sender = str(from_info).lower()

                    # 检查是否为GitHub相关邮件
                    if 'github' in subject or 'github' in sender:
                        github_emails.append(email)
                        logger.info(f"找到GitHub相关邮件: {email.get('subject', '')}")

                if github_emails:
                    # 选择最新的GitHub邮件并提取验证码和验证链接
                    latest_email = None
                    latest_email_time = None
                    verification_code = None
                    verification_link = None

                    for email in github_emails:
                        received_time_str = email.get('receivedDateTime', '')
                        if received_time_str:
                            try:
                                from datetime import datetime
                                email_time = datetime.fromisoformat(received_time_str.replace('Z', '+00:00'))
                                if latest_email_time is None or email_time > latest_email_time:
                                    latest_email = email
                                    latest_email_time = email_time
                            except:
                                if latest_email is None:
                                    latest_email = email

                    if latest_email:
                        logger.info(f"找到验证邮件: {latest_email.get('subject', '')}")

                        # 提取验证码
                        body_preview = latest_email.get('bodyPreview', '')
                        verification_code = extract_verification_code(body_preview)

                        if not verification_code:
                            # 如果预览中没有，获取完整内容
                            full_body = get_full_email_body(email_manager, latest_email.get('id'))
                            if full_body:
                                verification_code = extract_verification_code(full_body)

                        # 提取验证链接
                        if not verification_link:
                            full_body = get_full_email_body(email_manager, latest_email.get('id'))
                            if full_body:
                                verification_link = extract_verification_link(full_body)

                        logger.info(f"提取到验证码: {verification_code}")
                        logger.info(f"提取到验证链接: {verification_link}")

                        # 保存邮件信息、验证码和验证链接
                        state_manager.set_data('verification_email', latest_email)
                        state_manager.set_data('verification_code', verification_code)
                        state_manager.set_data('verification_link', verification_link)

                        return TaskResult(
                            success=True,
                            data={
                                'email_found': True,
                                'email': latest_email,
                                'verification_code': verification_code,
                                'verification_link': verification_link
                            }
                        )
                    else:
                        logger.warning("未找到有效的GitHub邮件")
                else:
                    logger.warning("未找到GitHub相关邮件")
                
            except Exception as e:
                logger.warning(f"获取邮件失败: {e}")

            # 检查是否需要重发验证码
            if (attempt + 1) % 3 == 0 and resend_attempts < max_resend_attempts:
                logger.info(f"尝试 {attempt + 1} 次后仍未找到邮件，尝试重发验证码...")

                try:
                    # 获取浏览器实例
                    browser = state_manager.get_data('browser_instance')
                    if browser:
                        # 查找重发按钮
                        resend_button = None
                        try:
                            # 尝试多种选择器
                            selectors = [
                                'button.ResendEmailHelpText-module__resendButton--TSWq_',
                                'button[type="button"]:contains("Resend the code")',
                                'button:contains("Resend")',
                                '.ResendEmailHelpText-module__resendButton--TSWq_',
                                '[class*="resendButton"]'
                            ]

                            for selector in selectors:
                                try:
                                    if 'contains' in selector:
                                        # 使用XPath查找包含文本的按钮
                                        xpath = f"//button[contains(text(), 'Resend')]"
                                        resend_button = browser.driver.find_element(By.XPATH, xpath)
                                    else:
                                        resend_button = browser.driver.find_element(By.CSS_SELECTOR, selector)

                                    if resend_button and resend_button.is_displayed():
                                        logger.info(f"找到重发按钮，使用选择器: {selector}")
                                        break
                                except:
                                    continue

                            if resend_button and resend_button.is_displayed():
                                logger.info("点击重发验证码按钮...")
                                resend_button.click()
                                resend_attempts += 1
                                logger.info(f"已重发验证码 (第 {resend_attempts} 次)")

                                # 重发后等待更长时间
                                await asyncio.sleep(30)
                                continue
                            else:
                                logger.warning("未找到重发按钮或按钮不可见")

                        except Exception as btn_e:
                            logger.warning(f"查找或点击重发按钮失败: {btn_e}")
                    else:
                        logger.warning("浏览器实例未找到，无法重发验证码")

                except Exception as resend_e:
                    logger.error(f"重发验证码过程失败: {resend_e}")

            # 等待后重试
            wait_time = 10 if attempt < 5 else 20
            logger.info(f"未找到验证邮件，等待{wait_time}秒后重试...")
            await asyncio.sleep(wait_time)
        
        # 所有尝试都失败
        logger.error(f"尝试 {max_attempts} 次后仍未找到验证邮件")
        return TaskResult(
            success=False,
            error=f"尝试 {max_attempts} 次后仍未找到验证邮件",
            should_retry=False
        )
        
    except Exception as e:
        logger.error(f"获取验证邮件失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def verification_code_input_task(state_manager, event_bus):
    """任务: 输入验证码到GitHub页面"""
    logger.info("执行任务: verification_code_input_task")

    try:
        browser = state_manager.get_data('browser_instance')
        verification_code = state_manager.get_data('verification_code')

        if not browser:
            raise Exception("浏览器实例未找到")

        if not verification_code:
            raise Exception("验证码未找到")

        logger.info(f"准备输入验证码: {verification_code}")

        # 确保验证码是8位数字
        if len(verification_code) != 8 or not verification_code.isdigit():
            raise Exception(f"验证码格式错误，应为8位数字，实际: {verification_code}")

        # 等待页面加载
        await asyncio.sleep(2)

        # 检查当前页面状态
        current_url = browser.driver.current_url
        page_title = browser.driver.title

        logger.info(f"验证码输入任务 - 当前URL: {current_url}")
        logger.info(f"验证码输入任务 - 页面标题: {page_title}")

        # 如果已经跳转到登录页面，说明注册已完成，无需输入验证码
        if "login" in current_url.lower() or "sign in" in page_title.lower():
            logger.info("页面已跳转到登录页面，注册已完成，无需输入验证码")
            return TaskResult(
                success=True,
                data={'verification_code_skipped': True, 'reason': 'already_completed'},
                next_tasks=['registration_complete_check_task']
            )

        # 检查验证码输入框是否存在
        try:
            first_input = browser.driver.find_element(By.ID, 'launch-code-0')
            if not first_input:
                raise Exception("验证码输入框不存在")
        except Exception as e:
            logger.warning(f"验证码输入框不存在: {e}")
            logger.info("可能注册已完成，触发注册完成检查")
            return TaskResult(
                success=True,
                data={'verification_code_skipped': True, 'reason': 'input_not_found'},
                next_tasks=['registration_complete_check_task']
            )

        # 通过ID逐个输入每位数字，使用JavaScript触发事件
        for i, digit in enumerate(verification_code):
            try:
                # 使用JavaScript设置值并触发事件
                script = f"""
                const input = document.getElementById('launch-code-{i}');
                input.value = '{digit}';
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                """
                browser.driver.execute_script(script)
                logger.info(f"输入第{i+1}位数字: {digit}")
                await asyncio.sleep(0.2)  # 短暂延迟，模拟人工输入
            except Exception as e:
                logger.error(f"输入第{i+1}位数字失败: {e}")
                raise Exception(f"输入验证码第{i+1}位失败")

        logger.info("验证码输入完成")

        # 等待一下让页面处理
        await asyncio.sleep(1)

        # 查找并点击提交按钮
        try:
            # 常见的提交按钮选择器
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("Continue")',
                'button:contains("Verify")',
                'button:contains("Submit")',
                '.btn-primary',
                '[data-testid="submit-button"]'
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = browser.driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_button.is_enabled():
                        break
                except:
                    continue

            if submit_button:
                submit_button.click()
                logger.info("提交按钮点击完成")
            else:
                logger.warning("未找到提交按钮，验证码可能自动提交")

        except Exception as e:
            logger.warning(f"点击提交按钮失败: {e}")

        return TaskResult(
            success=True,
            data={'verification_code_submitted': True},
            next_tasks=['registration_complete_check_task']
        )

    except Exception as e:
        logger.error(f"输入验证码失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def verification_link_extract_task(state_manager, event_bus):
    """任务23: 检查验证链接（已在email_fetch_task中提取）"""
    logger.info("执行任务: verification_link_extract_task")

    try:
        verification_link = state_manager.get_data('verification_link')
        verification_code = state_manager.get_data('verification_code')

        if not verification_link:
            raise Exception("验证链接未找到，可能邮件提取失败")

        if not verification_code:
            raise Exception("验证码未找到，可能邮件提取失败")

        logger.info(f"验证链接: {verification_link}")
        logger.info(f"验证码: {verification_code}")

        return TaskResult(
            success=True,
            data={
                'link_found': True,
                'link': verification_link,
                'code_found': True,
                'code': verification_code
            }
        )

    except Exception as e:
        logger.error(f"检查验证信息失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def verification_link_click_task(state_manager, event_bus):
    """任务24: 点击验证链接"""
    logger.info("执行任务: verification_link_click_task")

    try:
        browser = state_manager.get_data('browser_instance')
        verification_link = state_manager.get_data('verification_link')

        if not browser:
            raise Exception("浏览器实例未找到")
        if not verification_link:
            raise Exception("验证链接未找到")

        logger.info(f"准备访问验证链接: {verification_link}")

        # 添加随机延迟模拟人类行为
        import random
        delay = random.uniform(1.0, 3.0)
        logger.info(f"随机延迟 {delay:.1f} 秒...")
        await asyncio.sleep(delay)

        # 导航到验证链接
        browser.navigate_to(verification_link)

        logger.info("已访问验证链接，等待页面加载...")

        # 等待页面加载，使用随机延迟
        load_delay = random.uniform(3.0, 6.0)
        await asyncio.sleep(load_delay)

        # 检查页面是否正确加载
        current_url = browser.driver.current_url
        page_title = browser.driver.title

        logger.info(f"当前页面URL: {current_url}")
        logger.info(f"页面标题: {page_title}")

        # 检查是否出现反自动化检测错误
        page_source = browser.driver.page_source.lower()

        if "your browser did something unexpected" in page_source:
            logger.error("检测到反自动化错误页面")
            return TaskResult(
                success=False,
                error="检测到反自动化错误，需要调整浏览器设置",
                should_retry=True
            )

        # 检查页面状态，判断下一步操作
        if "login" in current_url.lower() or "sign in" in page_title.lower():
            logger.info("验证链接点击后直接跳转到登录页面，转到邮箱登录任务")

            # 可以选择使用Mock任务或真实任务
            use_mock = state_manager.get_data('use_mock_login', False)
            next_task = 'mock_email_login_task' if use_mock else 'email_login_task'

            logger.info(f"使用{'Mock' if use_mock else '真实'}登录任务: {next_task}")

            return TaskResult(
                success=True,
                data={'link_clicked': True, 'requires_login': True, 'page_url': current_url, 'page_title': page_title},
                next_tasks=[next_task]
            )
        elif "verify" in page_source or "verification" in page_source:
            logger.info("成功到达验证页面，需要输入验证码")
            return TaskResult(
                success=True,
                data={'link_clicked': True, 'page_url': current_url, 'page_title': page_title},
                next_tasks=['verification_code_input_task']  # 需要输入验证码
            )
        else:
            logger.warning("页面内容不符合预期，优先检查注册完成状态")
            return TaskResult(
                success=True,
                data={'link_clicked': True, 'page_url': current_url, 'page_title': page_title, 'warning': 'unexpected_page_content'},
                next_tasks=['registration_complete_check_task']  # 优先检查注册完成
            )

    except Exception as e:
        logger.error(f"访问验证链接失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def email_login_task(state_manager, event_bus):
    """任务26: 在验证链接页面输入邮箱密码进行登录"""
    logger.info("执行任务: email_login_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 获取当前邮箱账号信息
        current_email = state_manager.get_data('email')
        current_password = state_manager.get_data('password')

        if not current_email or not current_password:
            raise Exception("邮箱或密码信息未找到")

        logger.info(f"准备使用邮箱 {current_email} 进行登录")

        # 等待页面加载
        await asyncio.sleep(2)

        current_url = browser.driver.current_url
        page_source = browser.driver.page_source.lower()

        logger.info(f"当前页面URL: {current_url}")

        # 检查是否在登录页面
        login_indicators = [
            'sign in',
            'login',
            'email',
            'password',
            'sign_in',
            'session'
        ]

        is_login_page = any(indicator in page_source for indicator in login_indicators)

        if not is_login_page:
            logger.info("当前页面不是登录页面，可能已经自动登录或跳转")
            return TaskResult(
                success=True,
                data={'login_not_required': True, 'current_url': current_url},
                next_tasks=['registration_complete_check_task']
            )

        # 查找邮箱输入框
        email_selectors = [
            'input[name="login"]',
            'input[name="email"]',
            'input[type="email"]',
            'input[id="login_field"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="username" i]'
        ]

        email_input = None
        for selector in email_selectors:
            try:
                email_input = browser.driver.find_element("css selector", selector)
                if email_input and email_input.is_displayed():
                    logger.info(f"找到邮箱输入框: {selector}")
                    break
            except:
                continue

        if not email_input:
            logger.warning("未找到邮箱输入框，尝试查找其他登录方式")
            return TaskResult(
                success=True,
                data={'email_input_not_found': True},
                next_tasks=['registration_complete_check_task']
            )

        # 输入邮箱
        email_input.clear()
        email_input.send_keys(current_email)
        logger.info("已输入邮箱地址")

        await asyncio.sleep(1)

        # 查找密码输入框
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[id="password"]'
        ]

        password_input = None
        for selector in password_selectors:
            try:
                password_input = browser.driver.find_element("css selector", selector)
                if password_input and password_input.is_displayed():
                    logger.info(f"找到密码输入框: {selector}")
                    break
            except:
                continue

        if not password_input:
            logger.error("未找到密码输入框")
            return TaskResult(
                success=False,
                error="未找到密码输入框",
                should_retry=True
            )

        # 输入密码
        password_input.clear()
        password_input.send_keys(current_password)
        logger.info("已输入密码")

        await asyncio.sleep(1)

        # 查找登录按钮
        login_button_selectors = [
            'input[type="submit"]',
            'button[type="submit"]',
            'button[name="commit"]',
            'input[value*="Sign in" i]',
            'button:contains("Sign in")',
            '.btn-primary',
            '[data-signin-label]'
        ]

        login_button = None
        for selector in login_button_selectors:
            try:
                if ':contains(' in selector:
                    # 使用XPath处理contains
                    xpath = f"//button[contains(text(), 'Sign in')]"
                    login_button = browser.driver.find_element("xpath", xpath)
                else:
                    login_button = browser.driver.find_element("css selector", selector)

                if login_button and login_button.is_displayed():
                    logger.info(f"找到登录按钮: {selector}")
                    break
            except:
                continue

        if not login_button:
            logger.error("未找到登录按钮")
            return TaskResult(
                success=False,
                error="未找到登录按钮",
                should_retry=True
            )

        # 点击登录按钮
        login_button.click()
        logger.info("已点击登录按钮")

        # 等待登录处理
        await asyncio.sleep(3)

        # 检查登录结果
        new_url = browser.driver.current_url
        new_page_source = browser.driver.page_source.lower()

        logger.info(f"登录后页面URL: {new_url}")

        # 检查是否登录成功
        success_indicators = [
            'dashboard' in new_url,
            'github.com' in new_url and 'login' not in new_url,
            'welcome' in new_page_source,
            'successfully' in new_page_source
        ]

        login_success = any(success_indicators)

        if login_success:
            logger.info("邮箱登录成功")

            # 关闭浏览器
            try:
                browser.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出现警告: {e}")

            # 清理浏览器实例
            state_manager.set_data('browser_instance', None)

            return TaskResult(
                success=True,
                data={'email_login_success': True, 'final_url': new_url, 'browser_closed': True},
                next_tasks=[]  # 不触发后续任务，流程结束
            )
        else:
            # 检查是否需要双重认证
            if '2fa' in new_page_source or 'two-factor' in new_page_source or 'verification' in new_page_source:
                logger.info("需要双重认证")
                return TaskResult(
                    success=True,
                    data={'requires_2fa': True, 'current_url': new_url},
                    next_tasks=['two_factor_auth_task']
                )
            else:
                logger.warning("登录状态不明确，继续检查注册完成状态")
                return TaskResult(
                    success=True,
                    data={'login_status_unclear': True, 'current_url': new_url},
                    next_tasks=['registration_complete_check_task']
                )

    except Exception as e:
        logger.error(f"邮箱登录失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def two_factor_auth_task(state_manager, event_bus):
    """任务27: 处理双重认证"""
    logger.info("执行任务: two_factor_auth_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 获取双重密钥（如果有的话）
        two_factor_secret = state_manager.get_data('two_factor_secret')

        if not two_factor_secret:
            logger.warning("未配置双重密钥，无法自动处理双重认证")
            return TaskResult(
                success=False,
                error="未配置双重密钥，需要手动处理双重认证",
                should_retry=False
            )

        # 使用双重密钥生成验证码
        from utils.two_factor_auth import get_2fa_code
        verification_code = get_2fa_code(two_factor_secret)

        if not verification_code:
            logger.error("生成双重认证验证码失败")
            return TaskResult(
                success=False,
                error="生成双重认证验证码失败",
                should_retry=True
            )

        logger.info(f"生成的双重认证验证码: {verification_code}")

        # 查找验证码输入框
        code_input_selectors = [
            'input[name="otp"]',
            'input[name="code"]',
            'input[type="text"][maxlength="6"]',
            'input[placeholder*="code" i]',
            'input[autocomplete="one-time-code"]'
        ]

        code_input = None
        for selector in code_input_selectors:
            try:
                code_input = browser.driver.find_element("css selector", selector)
                if code_input and code_input.is_displayed():
                    logger.info(f"找到验证码输入框: {selector}")
                    break
            except:
                continue

        if not code_input:
            logger.error("未找到双重认证验证码输入框")
            return TaskResult(
                success=False,
                error="未找到双重认证验证码输入框",
                should_retry=True
            )

        # 输入验证码
        code_input.clear()
        code_input.send_keys(verification_code)
        logger.info("已输入双重认证验证码")

        await asyncio.sleep(1)

        # 查找提交按钮
        submit_button_selectors = [
            'input[type="submit"]',
            'button[type="submit"]',
            'button[name="commit"]',
            '.btn-primary'
        ]

        submit_button = None
        for selector in submit_button_selectors:
            try:
                submit_button = browser.driver.find_element("css selector", selector)
                if submit_button and submit_button.is_displayed():
                    logger.info(f"找到提交按钮: {selector}")
                    break
            except:
                continue

        if not submit_button:
            logger.error("未找到双重认证提交按钮")
            return TaskResult(
                success=False,
                error="未找到双重认证提交按钮",
                should_retry=True
            )

        # 点击提交按钮
        submit_button.click()
        logger.info("已提交双重认证验证码")

        # 等待处理
        await asyncio.sleep(3)

        # 检查认证结果
        current_url = browser.driver.current_url
        page_source = browser.driver.page_source.lower()

        logger.info(f"双重认证后页面URL: {current_url}")

        # 检查是否认证成功
        success_indicators = [
            'dashboard' in current_url,
            'github.com' in current_url and '2fa' not in current_url,
            'welcome' in page_source,
            'successfully' in page_source
        ]

        auth_success = any(success_indicators)

        if auth_success:
            logger.info("双重认证成功")

            # 关闭浏览器
            try:
                browser.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出现警告: {e}")

            # 清理浏览器实例
            state_manager.set_data('browser_instance', None)

            return TaskResult(
                success=True,
                data={'two_factor_auth_success': True, 'final_url': current_url, 'browser_closed': True},
                next_tasks=[]  # 不触发后续任务，流程结束
            )
        else:
            logger.error("双重认证失败")
            return TaskResult(
                success=False,
                error="双重认证验证码可能错误或已过期",
                should_retry=True
            )

    except Exception as e:
        logger.error(f"双重认证处理失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )





async def mock_email_login_task(state_manager, event_bus):
    """Mock任务：模拟邮箱登录页面操作"""
    logger.info("执行Mock任务: mock_email_login_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 获取当前邮箱账号信息
        current_email = state_manager.get_data('email')
        current_password = state_manager.get_data('password')

        if not current_email or not current_password:
            raise Exception("邮箱或密码信息未找到")

        logger.info(f"Mock登录任务 - 邮箱: {current_email}")

        # 等待页面加载
        await asyncio.sleep(2)

        current_url = browser.driver.current_url
        page_title = browser.driver.title

        logger.info(f"当前页面URL: {current_url}")
        logger.info(f"页面标题: {page_title}")

        # 使用Playwright风格的元素查找来分析页面结构
        page_source = browser.driver.page_source

        # Mock: 分析页面元素
        logger.info("=== Mock页面元素分析 ===")

        # 模拟查找邮箱输入框的多种可能选择器
        email_selectors = [
            'input[name="login"]',
            'input[name="email"]',
            'input[type="email"]',
            'input[id="login_field"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="username" i]',
            '#email',
            '#username',
            '.email-input',
            '[data-testid="email"]'
        ]

        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[id="password"]',
            '#password',
            '.password-input',
            '[data-testid="password"]'
        ]

        login_button_selectors = [
            'input[type="submit"]',
            'button[type="submit"]',
            'button[name="commit"]',
            'input[value*="Sign in" i]',
            'button:contains("Sign in")',
            '.btn-primary',
            '[data-signin-label]',
            '#login-button',
            '.login-btn'
        ]

        # Mock: 检查页面中是否存在这些元素
        found_elements = {
            'email_inputs': [],
            'password_inputs': [],
            'login_buttons': []
        }

        # 检查邮箱输入框
        for selector in email_selectors:
            try:
                if ':contains(' in selector:
                    continue  # 跳过复杂选择器的Mock检查
                elements = browser.driver.find_elements("css selector", selector)
                if elements:
                    found_elements['email_inputs'].append({
                        'selector': selector,
                        'count': len(elements),
                        'visible': any(elem.is_displayed() for elem in elements)
                    })
            except:
                pass

        # 检查密码输入框
        for selector in password_selectors:
            try:
                elements = browser.driver.find_elements("css selector", selector)
                if elements:
                    found_elements['password_inputs'].append({
                        'selector': selector,
                        'count': len(elements),
                        'visible': any(elem.is_displayed() for elem in elements)
                    })
            except:
                pass

        # 检查登录按钮
        for selector in login_button_selectors:
            try:
                if ':contains(' in selector:
                    continue  # 跳过复杂选择器的Mock检查
                elements = browser.driver.find_elements("css selector", selector)
                if elements:
                    found_elements['login_buttons'].append({
                        'selector': selector,
                        'count': len(elements),
                        'visible': any(elem.is_displayed() for elem in elements)
                    })
            except:
                pass

        # 记录找到的元素
        logger.info("找到的邮箱输入框:")
        for elem in found_elements['email_inputs']:
            logger.info(f"  - {elem['selector']}: {elem['count']}个, 可见: {elem['visible']}")

        logger.info("找到的密码输入框:")
        for elem in found_elements['password_inputs']:
            logger.info(f"  - {elem['selector']}: {elem['count']}个, 可见: {elem['visible']}")

        logger.info("找到的登录按钮:")
        for elem in found_elements['login_buttons']:
            logger.info(f"  - {elem['selector']}: {elem['count']}个, 可见: {elem['visible']}")

        # Mock: 模拟登录操作
        logger.info("=== Mock登录操作 ===")

        # 选择最佳的邮箱输入框
        best_email_selector = None
        for elem in found_elements['email_inputs']:
            if elem['visible']:
                best_email_selector = elem['selector']
                break

        # 选择最佳的密码输入框
        best_password_selector = None
        for elem in found_elements['password_inputs']:
            if elem['visible']:
                best_password_selector = elem['selector']
                break

        # 选择最佳的登录按钮
        best_login_selector = None
        for elem in found_elements['login_buttons']:
            if elem['visible']:
                best_login_selector = elem['selector']
                break

        if best_email_selector and best_password_selector and best_login_selector:
            logger.info(f"Mock: 将使用邮箱选择器: {best_email_selector}")
            logger.info(f"Mock: 将使用密码选择器: {best_password_selector}")
            logger.info(f"Mock: 将使用登录按钮选择器: {best_login_selector}")

            # 这里是Mock操作，实际实现时会执行真实的输入和点击
            logger.info("Mock: 输入邮箱地址")
            logger.info("Mock: 输入密码")
            logger.info("Mock: 点击登录按钮")
            logger.info("Mock: 等待登录结果")

            return TaskResult(
                success=True,
                data={
                    'mock_login_success': True,
                    'email_selector': best_email_selector,
                    'password_selector': best_password_selector,
                    'login_selector': best_login_selector,
                    'page_elements': found_elements
                },
                next_tasks=['registration_complete_check_task']
            )
        else:
            logger.warning("Mock: 未找到完整的登录表单元素")
            return TaskResult(
                success=False,
                error="未找到完整的登录表单元素",
                should_retry=True
            )

    except Exception as e:
        logger.error(f"Mock邮箱登录失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def registration_complete_check_task(state_manager, event_bus):
    """任务25: 检查注册完成状态"""
    logger.info("执行任务: registration_complete_check_task")

    try:
        # 检查是否已经完成注册，避免重复处理
        if state_manager.get_data('registration_completed'):
            logger.info("注册已完成，跳过重复检查")
            return TaskResult(
                success=True,
                data={'registration_completed': True, 'already_processed': True}
            )

        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 等待页面完全加载
        await asyncio.sleep(3)
        
        current_url = browser.driver.current_url
        page_source = browser.driver.page_source.lower()
        page_title = browser.driver.title
        
        logger.info(f"检查注册完成状态 - URL: {current_url}")
        logger.info(f"页面标题: {page_title}")
        
        # 检查注册完成的指示器
        completion_indicators = [
            'welcome to github',
            'dashboard',
            'your repositories',
            'github.com' in current_url and 'verify' not in current_url,
            'successfully verified' in page_source,
            'account created' in page_source
        ]
        
        registration_completed = any(indicator for indicator in completion_indicators if isinstance(indicator, bool) and indicator) or \
                                any(indicator in page_source for indicator in completion_indicators if isinstance(indicator, str))
        
        if registration_completed:
            logger.info("注册流程已完成！")

            # 标记注册已完成，防止重复处理
            state_manager.set_data('registration_completed', True)

            # 关闭浏览器
            try:
                browser.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出现警告: {e}")

            # 清理浏览器实例
            state_manager.set_data('browser_instance', None)

            # 发布注册完成事件
            await event_bus.publish(create_event(
                name='registration_completed',
                data={
                    'final_url': current_url,
                    'page_title': page_title,
                    'email': state_manager.get_data('email'),
                    'username': state_manager.get_data('current_username'),
                    'browser_closed': True
                },
                source='registration_complete_check_task'
            ))

            # update github_signup_date in email_config.json for current account
            try:
                with open('email_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)

                accounts = config.get('accounts', [])
                current_index = config.get('current_account_index', 0)
                target_index = None

                if isinstance(current_index, int) and 0 <= current_index < len(accounts):
                    target_index = current_index
                else:
                    current_email = state_manager.get_data('email')
                    if current_email:
                        for i, acc in enumerate(accounts):
                            if acc.get('email') == current_email:
                                target_index = i
                                break

                if target_index is not None:
                    accounts[target_index]['github_signup_date'] = datetime.now().isoformat()
                    with open('email_config.json', 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=2)
                    logger.info("已更新 github_signup_date 到 email_config.json")
                else:
                    logger.warning("未匹配到当前账号，跳过写入 github_signup_date")
            except Exception as cfg_e:
                logger.warning(f"更新 email_config.json 失败: {cfg_e}")

            return TaskResult(
                success=True,
                data={'registration_completed': True, 'browser_closed': True}
            )
        else:
            logger.warning("注册状态不明确，可能需要额外步骤")
            return TaskResult(
                success=False,
                error="注册状态不明确",
                should_retry=True
            )
        
    except Exception as e:
        logger.error(f"检查注册完成状态失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )
