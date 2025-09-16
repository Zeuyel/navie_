"""
验证码相关任务
"""

import asyncio
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from core.task_manager import TaskResult
from core.event_bus import create_event

logger = logging.getLogger(__name__)

async def captcha_detect_task(state_manager, event_bus):
    """任务10: 检测是否出现验证码"""
    logger.info("执行任务: captcha_detect_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")
        
        # 等待页面加载
        await asyncio.sleep(5)
        
        # 检查是否有验证码相关元素
        page_source = browser.driver.page_source.lower()
        
        # 检查多种验证码指示器
        captcha_indicators = [
            'visual challenge',
            'visual puzzle', 
            'captcha',
            'verify you are human',
            'octocaptcha'
        ]
        
        captcha_detected = any(indicator in page_source for indicator in captcha_indicators)
        
        if captcha_detected:
            logger.info("检测到验证码")
            
            # 发布验证码检测事件
            await event_bus.publish(create_event(
                name='captcha_detected',
                data={'captcha_type': 'visual_puzzle'},
                source='captcha_detect_task'
            ))
            
            return TaskResult(
                success=True,
                data={'captcha_detected': True},
                next_tasks=['visual_puzzle_button_find_task']
            )
        else:
            logger.info("未检测到验证码，可能直接进入邮箱验证")
            return TaskResult(
                success=True,
                data={'captcha_detected': False},
                next_tasks=['email_verification_detect_task']
            )
        
    except Exception as e:
        logger.error(f"验证码检测失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def visual_puzzle_button_find_task(state_manager, event_bus):
    """任务11: 查找Visual puzzle按钮"""
    logger.info("执行任务: visual_puzzle_button_find_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")
        
        # 轮询查找按钮，同时检查是否已进入邮箱验证
        max_attempts = 20
        for attempt in range(max_attempts):
            logger.info(f"第 {attempt + 1} 次尝试查找Visual challenge按钮...")

            # 使用JavaScript在所有iframe中搜索按钮
            found = await _search_visual_button_in_iframes(browser)

            if found:
                logger.info("Visual puzzle按钮找到并点击成功")
                return TaskResult(
                    success=True,
                    data={'button_found': True}
                )

            # 如果没找到按钮，检查是否已经进入邮箱验证页面
            logger.info("未找到Visual challenge按钮，检查是否已进入邮箱验证...")
            page_source = browser.driver.page_source.lower()
            email_verification_indicators = [
                'verify your email',
                'check your email',
                'verification email',
                'confirm your email',
                'email verification'
            ]

            email_verification_detected = any(indicator in page_source for indicator in email_verification_indicators)

            if email_verification_detected:
                logger.info("检测到GitHub跳过了验证码，直接进入邮箱验证阶段")
                return TaskResult(
                    success=True,
                    data={'captcha_skipped': True, 'email_verification_detected': True},
                    next_tasks=['email_verification_detect_task']  # 直接跳转到邮箱验证
                )

            # 等待后重试
            wait_time = 3 if attempt < 5 else 5
            logger.info(f"未找到按钮也未检测到邮箱验证，等待{wait_time}秒后重试...")
            await asyncio.sleep(wait_time)
        
        # 所有尝试都失败
        logger.error(f"尝试 {max_attempts} 次后既未找到Visual challenge按钮，也未检测到邮箱验证页面")
        return TaskResult(
            success=False,
            error=f"尝试 {max_attempts} 次后既未找到Visual challenge按钮，也未检测到邮箱验证页面",
            should_retry=False
        )
        
    except Exception as e:
        logger.error(f"查找Visual puzzle按钮失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def _search_visual_button_in_iframes(browser, depth=0, max_depth=3):
    """递归搜索所有iframe中的Visual challenge按钮"""
    if depth > max_depth:
        return False
    
    try:
        # 在当前上下文中查找按钮
        search_script = """
        let visualButton = document.querySelector('button[aria-label*="Visual challenge"]');
        if (visualButton) {
            console.log("找到Visual challenge按钮");
            visualButton.click();
            return true;
        }
        return false;
        """
        
        result = browser.driver.execute_script(search_script)
        if result:
            # 点击按钮后切换回主页面上下文
            browser.driver.switch_to.default_content()
            return True
        
        # 搜索所有iframe
        iframes = browser.driver.find_elements(By.TAG_NAME, "iframe")
        
        for i, iframe in enumerate(iframes):
            try:
                browser.driver.switch_to.frame(iframe)
                found = await _search_visual_button_in_iframes(browser, depth + 1, max_depth)
                
                if found:
                    return True
                
                browser.driver.switch_to.parent_frame()
                
            except Exception as iframe_error:
                logger.warning(f"处理iframe {i} 时出错: {iframe_error}")
                try:
                    browser.driver.switch_to.parent_frame()
                except:
                    pass
        
        return False
        
    except Exception as e:
        logger.error(f"递归搜索iframe失败 (深度 {depth}): {e}")
        return False

async def visual_puzzle_button_click_task(state_manager, event_bus):
    """任务12: 点击Visual puzzle按钮"""
    logger.info("执行任务: visual_puzzle_button_click_task")
    
    try:
        # 这个任务实际上在find任务中已经完成了点击
        # 这里主要是等待点击后的页面变化
        await asyncio.sleep(3)
        
        logger.info("Visual puzzle按钮点击完成，等待验证码加载")

        # 初始化第一轮验证码计数
        state_manager.set_data('captcha_completed_rounds', 1)
        logger.info("开始第 1 轮验证码处理")

        return TaskResult(
            success=True,
            data={'button_clicked': True},
            next_tasks=['captcha_iframe_locate_task']
        )
        
    except Exception as e:
        logger.error(f"Visual puzzle按钮点击失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def captcha_iframe_locate_task(state_manager, event_bus):
    """任务13: 定位验证码iframe"""
    logger.info("执行任务: captcha_iframe_locate_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")
        
        # 确保切换到主页面上下文
        browser.driver.switch_to.default_content()

        # 等待iframe加载
        await asyncio.sleep(3)

        # 查找octocaptcha iframe
        iframes = browser.driver.find_elements(By.TAG_NAME, "iframe")
        logger.info(f"页面共有 {len(iframes)} 个iframe")
        
        octocaptcha_iframe = None
        for i, iframe in enumerate(iframes):
            try:
                src = iframe.get_attribute('src') or ''
                title = iframe.get_attribute('title') or ''
                class_name = iframe.get_attribute('class') or ''
                
                logger.info(f"iframe {i}: src={src[:50]}..., title={title}, class={class_name}")
                
                if 'octocaptcha' in src.lower() or 'octocaptcha' in class_name.lower():
                    octocaptcha_iframe = iframe
                    logger.info(f"找到octocaptcha iframe: {i}")
                    break
            except Exception as e:
                logger.warning(f"检查iframe {i} 时出错: {e}")
        
        if octocaptcha_iframe:
            # 保存iframe引用
            state_manager.set_data('captcha_iframe', octocaptcha_iframe)
            
            return TaskResult(
                success=True,
                data={'iframe_found': True}
            )
        else:
            logger.error("未找到octocaptcha iframe")
            return TaskResult(
                success=False,
                error="未找到octocaptcha iframe",
                should_retry=True
            )
        
    except Exception as e:
        logger.error(f"定位验证码iframe失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def captcha_info_extract_task(state_manager, event_bus):
    """任务15: 提取验证码题目和图片"""
    logger.info("执行任务: captcha_info_extract_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 等待验证码内容加载
        await asyncio.sleep(2)

        # 提取验证码信息
        captcha_info = {}

        try:
            # 提取题目文本
            title_element = browser.driver.find_element(By.XPATH, "//*[@id='root']/div/div[1]/div/h2")
            captcha_info['title'] = title_element.text
            logger.info(f"验证码题目: {captcha_info['title']}")

            # 解析进度信息 "(X of Y)" 或 "X of Y"
            title_text = captcha_info['title']
            is_last_round = False
            if " of " in title_text:
                try:
                    # 使用正则表达式提取数字，处理括号等格式
                    import re
                    # 匹配 "(数字 of 数字)" 或 "数字 of 数字" 格式
                    pattern = r'\(?(\d+)\s+of\s+(\d+)\)?'
                    match = re.search(pattern, title_text)

                    if match:
                        current = int(match.group(1))
                        total = int(match.group(2))

                        logger.info(f"验证码进度: {current}/{total}")
                        captcha_info['current_round'] = current
                        captcha_info['total_rounds'] = total

                        # 判断是否为最后一轮
                        is_last_round = (current >= total)
                        if is_last_round:
                            logger.info("这是最后一轮验证码")
                        else:
                            logger.info(f"还需要继续，当前第{current}轮，共{total}轮")
                    else:
                        logger.warning(f"无法匹配进度格式: {title_text}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"解析进度信息失败: {e}")

            captcha_info['is_last_round'] = is_last_round

        except NoSuchElementException:
            logger.warning("未找到验证码题目")
            captcha_info['title'] = ""
            captcha_info['is_last_round'] = True  # 如果无法获取进度，默认为最后一轮

        try:
            # 提取图片 - 从style的background-image中获取URL并转换为base64
            img_selectors = [
                (By.CSS_SELECTOR, "img.key-frame-image"),  # 使用class名称
                (By.CSS_SELECTOR, "img[aria-label*='Match This']"),  # 使用aria-label属性
                (By.CSS_SELECTOR, "img.sc-168ufhb-1.jYBarg"),  # 使用完整class
                (By.XPATH, "//img[contains(@aria-label, 'Match This')]"),  # XPath with aria-label
                (By.XPATH, "//img[contains(@class, 'key-frame-image')]"),  # XPath with class
                (By.XPATH, "//*[@id='root']/div/div[1]/div/div/div[1]/img")  # 原始XPath作为备选
            ]

            img_element = None
            used_selector = None

            for by, selector in img_selectors:
                try:
                    img_element = browser.driver.find_element(by, selector)
                    used_selector = f"{by}={selector}"  # 修复：移除.value
                    logger.info(f"找到验证码图片元素，使用选择器: {used_selector}")
                    break
                except NoSuchElementException:
                    continue
                except Exception as e:
                    logger.warning(f"使用选择器 {by}={selector} 时出错: {e}")
                    continue

            if img_element:
                # 使用getComputedStyle获取计算后的background-image
                background_image_url = browser.driver.execute_script("""
                var element = arguments[0];
                var computedStyle = window.getComputedStyle(element);
                var backgroundImage = computedStyle.getPropertyValue('background-image');
                if (backgroundImage && backgroundImage !== 'none') {
                    var match = backgroundImage.match(/url\\(["\']?([^"\']+)["\']?\\)/);
                    return match ? match[1] : null;
                }
                return null;
                """, img_element)

                logger.info(f"提取到background-image URL: {background_image_url}")

                if background_image_url:
                    # 直接执行JS获取base64编码
                    data_url = browser.driver.execute_async_script("""
                    var url = arguments[0];
                    var callback = arguments[arguments.length - 1];

                    var img = new Image();
                    img.setAttribute('crossOrigin', 'anonymous');
                    img.onload = function() {
                      var canvas = document.createElement('canvas');
                      canvas.width = this.naturalWidth;
                      canvas.height = this.naturalHeight;
                      var ctx = canvas.getContext('2d');
                      ctx.drawImage(this, 0, 0);
                      callback(canvas.toDataURL('image/png'));
                    };
                    img.onerror = function() {
                      callback(null);
                    };
                    img.src = url;
                    """, background_image_url)

                    if data_url and data_url.startswith('data:image'):
                        # 提取base64部分
                        base64_data = data_url.split(',')[1]
                        captcha_info['image_base64'] = base64_data
                        captcha_info['image_url'] = background_image_url
                        logger.info(f"成功转换图片为base64，长度: {len(base64_data)}")
                    else:
                        logger.warning("JS转换图片失败或返回无效数据")
                        captcha_info['image_url'] = background_image_url
                else:
                    # 尝试从src属性获取
                    img_src = img_element.get_attribute('src')
                    captcha_info['image_url'] = img_src
                    logger.info(f"从src属性获取图片URL: {img_src[:50] if img_src else 'None'}...")
            else:
                logger.warning("使用所有选择器都未找到验证码图片")
                captcha_info['image_url'] = ""

        except Exception as e:
            logger.error(f"提取验证码图片时出错: {e}")
            captcha_info['image_url'] = ""

        # 检查是否提取到有效信息
        if not captcha_info['title'] and not captcha_info['image_url']:
            raise Exception("未能提取到验证码信息")

        # 保存验证码信息
        state_manager.set_data('captcha_info', captcha_info)

        return TaskResult(
            success=True,
            data=captcha_info,
            next_tasks=['captcha_solve_api_task']
        )

    except Exception as e:
        logger.error(f"提取验证码信息失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


async def captcha_solve_api_task(state_manager, event_bus):
    """任务17: 调用YesCaptcha API识别"""
    logger.info("执行任务: captcha_solve_api_task")

    try:
        captcha_info = state_manager.get_data('captcha_info', {})

        title = captcha_info.get('title', '')
        image_base64 = captcha_info.get('image_base64', '')

        if not title or not image_base64:
            raise Exception("验证码信息不完整")

        logger.info(f"调用YesCaptcha API识别验证码: {title}")
        logger.info(f"图片数据长度: {len(image_base64)} 字符")

        # 调用YesCaptcha API
        import requests
        import json

        # YesCaptcha API配置
        from config import YESCAPTCHA_API_KEY, YESCAPTCHA_BASE_URL, YESCAPTCHA_SOFT_ID

        if not YESCAPTCHA_API_KEY:
            raise Exception("YesCaptcha API密钥未配置，请在.env文件中设置YESCAPTCHA_API_KEY")

        api_url = f"{YESCAPTCHA_BASE_URL}/createTask"
        api_key = YESCAPTCHA_API_KEY
        soft_id = YESCAPTCHA_SOFT_ID

        logger.info(f"使用softID: {soft_id}")

        # 构造API请求 - 使用FunCaptchaClassification
        task_data = {
            "clientKey": api_key,
            "task": {
                "type": "FunCaptchaClassification",
                "image": image_base64,  # 直接传base64，不需要data:image前缀
                "question": title       # 传入完整的问题文本
            },
            "softID": soft_id  # 添加softID参数，传入数字
        }

        # 发送请求
        response = requests.post(api_url, json=task_data, timeout=30)

        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}")

        try:
            result_data = response.json()
        except ValueError as e:
            raise Exception(f"API响应JSON解析失败: {e}")

        # 检查API错误
        if result_data.get('errorId') != 0:
            error_desc = result_data.get('errorDescription', 'Unknown error')
            raise Exception(f"API返回错误: {error_desc}，可能是余额不足或服务错误")

        # 获取taskId用于可能的轮询
        task_id = result_data.get('taskId')
        if not task_id:
            raise Exception("API未返回taskId")

        # 检查初始状态
        status = result_data.get('status')
        logger.info(f"createTask返回状态: {status}")

        # 如果状态是ready，直接处理结果
        if status == 'ready':
            return _process_captcha_result(result_data, state_manager)

        # 如果状态不是ready，需要轮询getTaskResult
        logger.info(f"任务创建成功，开始轮询结果，taskId: {task_id}")

        # 轮询获取结果
        get_result_url = f"{YESCAPTCHA_BASE_URL}/getTaskResult"
        max_attempts = 20  # 最多轮询20次
        poll_interval = 3  # 3秒间隔，按照官方文档建议

        for attempt in range(max_attempts):
            await asyncio.sleep(poll_interval)

            result_request = {
                "clientKey": api_key,
                "taskId": task_id
            }

            try:
                result_response = requests.post(get_result_url, json=result_request, timeout=10)

                if result_response.status_code != 200:
                    logger.warning(f"轮询请求失败，状态码: {result_response.status_code}")
                    continue

                try:
                    result_json = result_response.json()
                except ValueError as e:
                    logger.warning(f"轮询响应JSON解析失败: {e}")
                    continue

                # 检查轮询结果的错误
                if result_json.get('errorId') != 0:
                    error_desc = result_json.get('errorDescription', 'Unknown error')
                    raise Exception(f"轮询获取结果失败: {error_desc}")

                poll_status = result_json.get('status')
                logger.info(f"轮询第{attempt + 1}次，状态: {poll_status}")

                if poll_status == 'ready':
                    # 结果准备好了，处理结果
                    return _process_captcha_result(result_json, state_manager)
                elif poll_status == 'processing':
                    # 仍在处理中，继续轮询
                    continue
                elif poll_status == 'failed':
                    raise Exception("验证码识别失败")
                else:
                    logger.warning(f"未知状态: {poll_status}，继续轮询")
                    continue

            except requests.RequestException as e:
                logger.warning(f"轮询请求异常: {e}")
                continue

        raise Exception(f"轮询超时，已尝试{max_attempts}次")

    except Exception as e:
        logger.error(f"调用YesCaptcha API失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

def _process_captcha_result(result_data, state_manager):
    """处理验证码识别结果"""
    solution = result_data.get('solution', {})
    objects = solution.get('objects', [])
    confidences = solution.get('confidences', [])
    label = solution.get('label', '')

    # 检查结果有效性
    if not objects or len(objects) == 0:
        raise Exception("API返回的solution中没有objects数据，可能是余额不足或服务错误")

    # objects[0]表示点击次数，confidences数组表示各位置的置信度
    click_count = objects[0]

    # 找到置信度最高的位置作为目标位置
    target_position = 0
    if confidences:
        max_confidence = max(confidences)
        target_position = confidences.index(max_confidence)
        actual_confidence = max_confidence
    else:
        actual_confidence = 0.95

    result = {
        'success': True,
        'objects': objects,
        'confidences': confidences,
        'label': label,
        'click_count': click_count,
        'target_position': target_position,
        'confidence': actual_confidence
    }

    logger.info(f"YesCaptcha API识别成功: 点击{click_count}次, 目标位置{target_position}, 置信度{actual_confidence}")

    # 保存识别结果
    state_manager.set_data('captcha_solution', result)

    return TaskResult(
        success=True,
        data=result
    )

async def captcha_answer_submit_task(state_manager, event_bus):
    """任务18: 提交验证码答案"""
    logger.info("执行任务: captcha_answer_submit_task")

    try:
        browser = state_manager.get_data('browser_instance')
        captcha_solution = state_manager.get_data('captcha_solution', {})

        if not browser:
            raise Exception("浏览器实例未找到")

        # 从新的结果格式中获取数据
        click_count = captcha_solution.get('click_count')
        target_position = captcha_solution.get('target_position')
        confidence = captcha_solution.get('confidence', 0)

        if click_count is None:
            raise Exception("验证码解决方案中未找到点击次数")

        logger.info(f"验证码解决方案: 点击{click_count}次, 目标位置{target_position}, 置信度{confidence}")
        logger.info(f"准备点击circle元素 {click_count} 次")

        # 查找circle元素（Navigate to next image按钮）
        try:
            circle_element = browser.driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Navigate to next image"]')

            # 点击指定次数
            for i in range(click_count):
                circle_element.click()
                logger.info(f"第 {i+1} 次点击circle元素完成")
                await asyncio.sleep(0.5)  # 点击间隔

        except NoSuchElementException:
            raise Exception("未找到circle元素（Navigate to next image按钮）")

        # 等待一下让界面更新
        await asyncio.sleep(1)

        # 点击Submit按钮提交答案
        try:
            submit_button = browser.driver.find_element(By.CSS_SELECTOR, 'button.sc-nkuzb1-0.yuVdl.button')
            submit_button.click()
            logger.info("Submit按钮点击完成")
        except NoSuchElementException:
            raise Exception("未找到Submit按钮")

        logger.info("验证码答案提交完成")

        # 根据是否最后一轮决定下一个任务
        captcha_info = state_manager.get_data('captcha_info', {})
        is_last_round = captcha_info.get('is_last_round', True)

        # 详细日志调试
        logger.info(f"验证码信息调试:")
        logger.info(f"  - 题目: {captcha_info.get('title', 'N/A')}")
        logger.info(f"  - 当前轮数: {captcha_info.get('current_round', 'N/A')}")
        logger.info(f"  - 总轮数: {captcha_info.get('total_rounds', 'N/A')}")
        logger.info(f"  - 是否最后一轮: {is_last_round}")

        if is_last_round:
            logger.info("✅ 最后一轮验证码，检查结果")
            next_tasks = ['captcha_result_check_task']
        else:
            logger.info("➡️ 不是最后一轮，继续下一轮验证码")
            next_tasks = ['captcha_next_round_task']

        return TaskResult(
            success=True,
            data={'answer_submitted': True, 'is_last_round': is_last_round},
            next_tasks=next_tasks
        )

    except Exception as e:
        logger.error(f"提交验证码答案失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def captcha_result_check_task(state_manager, event_bus):
    """任务19: 检查验证码结果"""
    logger.info("执行任务: captcha_result_check_task")

    try:
        browser = state_manager.get_data('browser_instance')
        if not browser:
            raise Exception("浏览器实例未找到")

        # 等待验证码处理结果
        await asyncio.sleep(3)

        # 首先检查是否有Try again按钮（验证码失败）
        try:
            try_again_button = browser.driver.find_element(By.CSS_SELECTOR, 'button.sc-nkuzb1-0.dJlpAa.button')
            logger.info("检测到Try again按钮，验证码失败，需要重新开始")

            # 点击Try again按钮
            try_again_button.click()
            logger.info("Try again按钮点击完成")

            # 等待页面重新加载
            await asyncio.sleep(2)

            return TaskResult(
                success=True,
                data={'need_retry': True},
                next_tasks=['captcha_iframe_locate_task']  # 重新开始验证码流程，从iframe定位开始
            )
        except NoSuchElementException:
            # 没有Try again按钮，继续检查其他状态
            pass

        # 如果没有Try again按钮，说明验证码成功完成
        logger.info("验证码成功完成，准备转移到邮箱验证")

        # 发布验证码完成事件
        await event_bus.publish(create_event(
            name='captcha_completed',
            data={},
            source='captcha_result_check_task'
        ))

        return TaskResult(
            success=True,
            data={'captcha_completed': True},
            next_tasks=['email_verification_detect_task']  # 验证码完成后触发邮箱验证检测
        )

    except Exception as e:
        logger.error(f"检查验证码结果失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def captcha_next_round_task(state_manager, event_bus):
    """任务20: 处理下一轮验证码"""
    logger.info("执行任务: captcha_next_round_task")

    try:
        # 检查是否已经达到最大轮数限制
        completed_rounds = state_manager.get_data('captcha_completed_rounds', 0)
        max_rounds = 15  # 最大轮数限制

        if completed_rounds >= max_rounds:
            logger.error(f"验证码轮数超过限制: {completed_rounds}/{max_rounds}")
            return TaskResult(
                success=False,
                error=f"验证码轮数超过限制: {completed_rounds}/{max_rounds}",
                should_retry=False
            )

        # 增加完成轮数计数（这里是第2轮开始，第1轮从Visual puzzle按钮开始）
        next_round = completed_rounds + 1
        state_manager.set_data('captcha_completed_rounds', next_round)

        logger.info(f"开始第 {next_round + 1} 轮验证码处理")

        # 等待新的验证码加载
        await asyncio.sleep(2)

        return TaskResult(
            success=True,
            data={'round': next_round + 1},
            next_tasks=['captcha_iframe_locate_task']  # 重新开始验证码流程，从iframe定位开始
        )

    except Exception as e:
        logger.error(f"处理下一轮验证码失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )

async def captcha_iframe_switch_task(state_manager, event_bus):
    """任务14: 切换到验证码iframe"""
    logger.info("执行任务: captcha_iframe_switch_task")
    
    try:
        browser = state_manager.get_data('browser_instance')
        captcha_iframe = state_manager.get_data('captcha_iframe')
        
        if not browser:
            raise Exception("浏览器实例未找到")
        if not captcha_iframe:
            raise Exception("验证码iframe未找到")
        
        # 切换到octocaptcha iframe
        browser.driver.switch_to.frame(captcha_iframe)
        logger.info("已切换到octocaptcha iframe")
        
        # 简化的iframe切换：octocaptcha → 中间iframe → game-core-frame
        await asyncio.sleep(2)

        try:
            # 第一步：查找title="Verification challenge"的中间iframe
            middle_iframe = browser.driver.find_element(By.XPATH, "//iframe[@title='Verification challenge']")
            browser.driver.switch_to.frame(middle_iframe)
            logger.info("已切换到中间iframe (title='Verification challenge')")

            # 第二步：在中间iframe中查找game-core-frame
            await asyncio.sleep(1)
            game_core_iframe = browser.driver.find_element(By.ID, "game-core-frame")
            browser.driver.switch_to.frame(game_core_iframe)
            logger.info("已切换到game-core-frame iframe")
            found = True

        except NoSuchElementException as e:
            logger.error(f"iframe切换失败: {e}")
            found = False
        except Exception as e:
            logger.error(f"iframe切换过程中出错: {e}")
            found = False

        if found:
            logger.info("已成功切换到game-core-frame iframe")

            # 只在第一次进入验证码时发布状态转换事件
            current_state = state_manager.get_state()
            if current_state.value == 'form_submitted':
                # 先发布验证码检测事件（转换到captcha_pending）
                await event_bus.publish(create_event(
                    name='captcha_detected',
                    data={},
                    source='captcha_iframe_switch_task'
                ))

                # 等待状态转换完成
                await asyncio.sleep(0.1)

                # 再发布验证码解决开始事件（转换到captcha_solving）
                await event_bus.publish(create_event(
                    name='captcha_solving_started',
                    data={},
                    source='captcha_iframe_switch_task'
                ))
            else:
                logger.info("验证码循环中，跳过状态转换事件")

            return TaskResult(
                success=True,
                data={'iframe_switched': True},
                next_tasks=['captcha_info_extract_task']
            )
        else:
            logger.error("递归查找未找到game-core-frame iframe")
            return TaskResult(
                success=False,
                error="递归查找未找到game-core-frame iframe",
                should_retry=True
            )
        
    except Exception as e:
        logger.error(f"切换到验证码iframe失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=True
        )


