"""
验证码处理工具
"""
import base64
import requests
import time
from io import BytesIO
from PIL import Image
from config import YESCAPTCHA_API_KEY, YESCAPTCHA_BASE_URL, MAX_RETRIES, RETRY_DELAY
from utils.logger import setup_logger

logger = setup_logger(__name__)

class CaptchaHandler:
    """验证码处理器"""
    
    def __init__(self):
        self.api_key = YESCAPTCHA_API_KEY
        self.base_url = YESCAPTCHA_BASE_URL
    
    def url_to_base64_selenium(self, driver, image_url):
        """使用Selenium从URL获取图片并转换为base64"""
        try:
            # 注入JavaScript函数到页面
            driver.execute_script("""
            function get_base64(url) {
              return new Promise((resolve, reject) => {
                var img = new Image();
                img.setAttribute('crossOrigin', 'anonymous');
                img.onload = function() {
                  var canvas = document.createElement('canvas');
                  canvas.width = this.naturalWidth;
                  canvas.height = this.naturalHeight;
                  var ctx = canvas.getContext('2d');
                  ctx.drawImage(this, 0, 0);
                  resolve(canvas.toDataURL('image/png'));
                };
                img.onerror = reject;
                img.src = url;
              });
            }
            """)

            # 调用函数并获取base64编码
            data_url = driver.execute_async_script("""
            var callback = arguments[arguments.length - 1];
            get_base64(arguments[0]).then(callback).catch(callback);
            """, image_url)

            if data_url and data_url.startswith('data:image'):
                logger.info(f"成功从URL获取图片: {len(data_url)} 字符")
                return data_url
            else:
                logger.error("获取图片失败或格式错误")
                return None

        except Exception as e:
            logger.error(f"Selenium获取图片失败: {e}")
            return None

    def screenshot_element(self, driver, element):
        """截取元素截图"""
        try:
            # 获取元素位置和大小
            location = element.location
            size = element.size

            # 截取整个页面
            screenshot = driver.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot))

            # 裁剪验证码区域
            left = location['x']
            top = location['y']
            right = left + size['width']
            bottom = top + size['height']

            captcha_image = image.crop((left, top, right, bottom))

            # 转换为base64
            buffer = BytesIO()
            captcha_image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            logger.error(f"截取验证码图片失败: {e}")
            return None
    
    def solve_funcaptcha(self, image_base64: str, question: str):
        """解决FunCaptcha验证码"""
        try:
            # 确保image_base64格式正确
            if not image_base64.startswith('data:image'):
                image_base64 = f"data:image/png;base64,{image_base64}"

            payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "FunCaptchaClassification",
                    "image": image_base64,
                    "question": question
                }
            }

            logger.info(f"发送验证码识别请求: {question}")
            response = requests.post(f"{self.base_url}/createTask", json=payload, timeout=30)

            if response.status_code != 200:
                logger.error(f"HTTP错误: {response.status_code} - {response.text}")
                return None

            result = response.json()
            logger.info(f"API响应: {result}")

            if result.get('errorId') == 0:
                solution = result.get('solution', {})
                objects = solution.get('objects', [])
                labels = solution.get('labels', [])

                if objects:
                    target_index = objects[0]
                    logger.info(f"验证码识别成功: 目标位置 {target_index}")
                    if labels and target_index < len(labels):
                        logger.info(f"目标对象: {labels[target_index]}")
                    return target_index
                else:
                    logger.error("验证码识别结果为空")
                    return None
            else:
                error_code = result.get('errorId')
                error_description = result.get('errorDescription', '未知错误')
                logger.error(f"验证码识别失败: 错误码 {error_code} - {error_description}")
                return None

        except requests.exceptions.Timeout:
            logger.error("验证码API请求超时")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"验证码API网络错误: {e}")
            return None
        except Exception as e:
            logger.error(f"验证码API调用失败: {e}")
            return None
    
    def extract_question_text(self, driver):
        """提取验证码问题文本"""
        try:
            # 根据GitHub页面结构查找问题文本
            # 这里需要根据实际的DOM结构来定位
            question_selectors = [
                "[data-testid='captcha-question']",
                ".captcha-question",
                "#captcha-question",
                "[class*='question']",
                "[class*='instruction']"
            ]
            
            for selector in question_selectors:
                try:
                    elements = driver.find_elements("css selector", selector)
                    if elements:
                        question = elements[0].text.strip()
                        if question:
                            logger.info(f"找到验证码问题: {question}")
                            return question
                except:
                    continue
            
            logger.warning("未找到验证码问题文本")
            return None
        except Exception as e:
            logger.error(f"提取验证码问题失败: {e}")
            return None
