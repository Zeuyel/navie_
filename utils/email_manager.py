"""
邮箱管理模块 - 使用Microsoft Graph API处理Outlook邮箱
"""
import requests
import json
import time
import re
from datetime import datetime, timedelta
from utils.logger import setup_logger
from utils.wmemail_provider import WMEmailProvider, WMEmailAccount

logger = setup_logger(__name__)

class OutlookEmailManager:
    """Outlook邮箱管理器"""
    
    def __init__(self, email, password, client_id, access_token=None):
        self.email = email
        self.password = password
        self.client_id = client_id
        # 这里的access_token实际上是refresh_token
        if access_token:
            self.access_token = access_token.strip()
            # 移除可能的Bearer前缀
            if self.access_token.startswith('Bearer '):
                self.access_token = self.access_token[7:]
        else:
            self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"

        # 添加token缓存
        self.cached_access_token = None
        self.token_expires_at = None
        
    def refresh_access_token(self):
        """使用refresh_token获取新的access_token"""
        if not self.access_token:
            logger.error("没有refresh_token")
            return None

        try:
            # Microsoft OAuth2 token endpoint - 使用consumers端点
            token_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"

            # 请求参数 - 使用默认scope
            data = {
                'client_id': self.client_id,
                'grant_type': 'refresh_token',
                'refresh_token': self.access_token,  # 这里实际是refresh_token
                'scope': 'https://graph.microsoft.com/.default'
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            logger.info("正在刷新access_token...")
            response = requests.post(token_url, data=data, headers=headers, timeout=30)

            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data.get('access_token')
                new_refresh_token = token_data.get('refresh_token')
                expires_in = token_data.get('expires_in')

                logger.info(f"成功获取新的access_token，有效期: {expires_in}秒")

                # 更新token
                if new_refresh_token:
                    self.access_token = new_refresh_token  # 更新refresh_token

                return new_access_token
            else:
                logger.error(f"刷新token失败: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"刷新token异常: {e}")
            return None

    def get_access_token(self):
        """获取访问令牌（带缓存）"""
        from datetime import datetime, timedelta

        # 检查缓存的token是否仍然有效
        if self.cached_access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                logger.info("使用缓存的access_token")
                return self.cached_access_token

        # 缓存失效或不存在，刷新获取新的access_token
        logger.info("正在刷新access_token...")
        new_token = self.refresh_access_token()

        if new_token:
            self.cached_access_token = new_token
            # 设置过期时间为55分钟后（token通常有效期1小时）
            self.token_expires_at = datetime.now() + timedelta(minutes=55)

        return new_token
    
    def refresh_token(self):
        """刷新访问令牌"""
        # TODO: 实现令牌刷新逻辑
        logger.info("需要实现令牌刷新逻辑")
        pass
    
    def get_headers(self):
        """获取请求头"""
        token = self.get_access_token()
        if not token:
            logger.error("无法获取有效的access_token")
            return None

        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def search_emails(self, subject_filter=None, from_filter=None, time_range_minutes=10, max_results=20):
        """搜索邮件"""
        try:
            headers = self.get_headers()
            if not headers:
                return []

            # API请求参数
            url = f"{self.base_url}/me/messages"

            # 如果没有主题和发件人过滤条件，只使用时间过滤
            if not subject_filter and not from_filter:
                # 只有时间过滤器，使用正确的ISO 8601格式
                time_threshold = datetime.utcnow() - timedelta(minutes=time_range_minutes)
                # 格式化为ISO 8601并添加Z后缀表示UTC时间
                time_filter = f"receivedDateTime ge {time_threshold.strftime('%Y-%m-%dT%H:%M:%SZ')}"

                params = {
                    '$filter': time_filter,
                    '$orderby': 'receivedDateTime desc',
                    '$top': min(max_results, 50),
                    '$select': 'id,subject,from,receivedDateTime,body,bodyPreview'
                }
                logger.info(f"获取最近 {time_range_minutes} 分钟内的 {max_results} 封邮件")
                logger.info(f"时间过滤条件: {time_filter}")
            else:
                # 构建搜索过滤器
                filters = []

                # 时间过滤器 - 只在指定时间范围时使用
                if time_range_minutes and time_range_minutes > 0:
                    time_threshold = datetime.utcnow() - timedelta(minutes=time_range_minutes)
                    # 使用正确的ISO 8601格式，添加Z后缀表示UTC时间
                    time_filter = f"receivedDateTime ge {time_threshold.strftime('%Y-%m-%dT%H:%M:%SZ')}"
                    filters.append(time_filter)

                # 主题过滤器 - 支持多个关键词
                if subject_filter:
                    if isinstance(subject_filter, list):
                        # 多个主题关键词，使用OR连接
                        subject_conditions = []
                        for keyword in subject_filter:
                            keyword_encoded = keyword.replace("'", "''")
                            subject_conditions.append(f"contains(subject, '{keyword_encoded}')")
                        subject_filter_combined = "(" + " or ".join(subject_conditions) + ")"
                        filters.append(subject_filter_combined)
                    else:
                        # 单个主题关键词
                        subject_filter_encoded = subject_filter.replace("'", "''")
                        filters.append(f"contains(subject, '{subject_filter_encoded}')")

                # 发件人过滤器 - 支持多个发件人
                if from_filter:
                    if isinstance(from_filter, list):
                        # 多个发件人，使用OR连接
                        from_conditions = []
                        for sender in from_filter:
                            from_conditions.append(f"contains(from/emailAddress/address, '{sender}')")
                        from_filter_combined = "(" + " or ".join(from_conditions) + ")"
                        filters.append(from_filter_combined)
                    else:
                        # 单个发件人
                        filters.append(f"contains(from/emailAddress/address, '{from_filter}')")

                # 组合过滤器
                params = {
                    '$orderby': 'receivedDateTime desc',
                    '$top': min(max_results, 50),  # 限制最大结果数
                    '$select': 'id,subject,from,receivedDateTime,body,bodyPreview'
                }

                if filters:
                    filter_string = " and ".join(filters)
                    params['$filter'] = filter_string
                    logger.info(f"搜索邮件 - 时间范围: {time_range_minutes}分钟, 最大结果: {max_results}")
                    logger.info(f"过滤条件: {filter_string}")
                else:
                    logger.info(f"搜索邮件 - 无过滤条件, 最大结果: {max_results}")

            response = requests.get(url, headers=headers, params=params, timeout=30)

            logger.info(f"API响应状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                emails = result.get('value', [])

                # 按接收时间排序（最新的在前）
                emails.sort(key=lambda x: x.get('receivedDateTime', ''), reverse=True)

                logger.info(f"找到 {len(emails)} 封邮件")

                # 记录邮件详情用于调试
                for i, email in enumerate(emails[:3]):  # 只记录前3封
                    subject = email.get('subject', 'N/A')
                    from_addr = email.get('from', {}).get('emailAddress', {}).get('address', 'N/A')
                    received_time = email.get('receivedDateTime', 'N/A')
                    logger.info(f"邮件 {i+1}: {subject} | 发件人: {from_addr} | 时间: {received_time}")

                return emails

            elif response.status_code == 401:
                logger.error("认证失败 - access_token无效或已过期")
                logger.error(f"响应详情: {response.text}")
                return []
            elif response.status_code == 403:
                logger.error("权限不足 - 请检查应用权限配置")
                logger.error(f"响应详情: {response.text}")
                return []
            elif response.status_code == 429:
                logger.error("请求频率限制 - 请稍后重试")
                return []
            else:
                logger.error(f"搜索邮件失败: {response.status_code} - {response.text}")
                return []

        except requests.exceptions.Timeout:
            logger.error("邮件搜索请求超时")
            return []
        except requests.exceptions.ConnectionError:
            logger.error("网络连接错误")
            return []
        except Exception as e:
            logger.error(f"搜索邮件异常: {e}")
            return []
    
    def extract_verification_code(self, email_body):
        """从邮件内容中提取验证码"""
        try:
            if not email_body:
                logger.warning("邮件内容为空")
                return None

            # 清理HTML标签和特殊字符
            import re
            clean_body = re.sub(r'<[^>]+>', ' ', email_body)  # 移除HTML标签
            clean_body = re.sub(r'&[a-zA-Z0-9#]+;', ' ', clean_body)  # 移除HTML实体
            clean_body = re.sub(r'\s+', ' ', clean_body)  # 合并多个空格

            logger.info(f"清理后的邮件内容长度: {len(clean_body)} 字符")

            # GitHub验证码模式 - 按优先级排序
            patterns = [
                # 高优先级：明确的验证码格式
                r'verification\s+code[:\s]*(\d{8})',  # "verification code: 12345678"
                r'verify\s+code[:\s]*(\d{8})',  # "verify code: 12345678"
                r'security\s+code[:\s]*(\d{8})',  # "security code: 12345678"
                r'access\s+code[:\s]*(\d{8})',  # "access code: 12345678"
                r'confirmation\s+code[:\s]*(\d{8})',  # "confirmation code: 12345678"

                # 中优先级：代码相关格式
                r'code[:\s]*(\d{8})',  # "code: 12345678"
                r'enter[:\s]*(\d{8})',  # "enter: 12345678"
                r'use[:\s]*(\d{8})',  # "use: 12345678"

                # 低优先级：纯数字格式
                r'\b(\d{8})\b',  # 独立的8位数字
                r'(\d{8})',  # 任何8位数字

                # 备用：6位数字（某些情况下可能是6位）
                r'verification\s+code[:\s]*(\d{6})',
                r'code[:\s]*(\d{6})',
                r'\b(\d{6})\b'
            ]

            # 按优先级尝试匹配
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, clean_body, re.IGNORECASE)
                if matches:
                    for match in matches:
                        code = match.strip()
                        # 验证码长度检查
                        if len(code) in [6, 8] and code.isdigit():
                            # 避免匹配到明显不是验证码的数字（如日期、时间戳等）
                            if not self._is_likely_timestamp_or_date(code):
                                logger.info(f"使用模式 {i+1} 提取到验证码: {code}")
                                return code

            # 如果没有找到，尝试在邮件的特定部分查找
            # 查找可能包含验证码的关键段落
            key_sections = self._extract_key_sections(clean_body)
            for section in key_sections:
                for pattern in patterns[:5]:  # 只使用高优先级模式
                    matches = re.findall(pattern, section, re.IGNORECASE)
                    if matches:
                        code = matches[0].strip()
                        if len(code) in [6, 8] and code.isdigit():
                            logger.info(f"从关键段落提取到验证码: {code}")
                            return code

            logger.warning("未能从邮件中提取到验证码")
            logger.debug(f"邮件内容前500字符: {clean_body[:500]}")
            return None

        except Exception as e:
            logger.error(f"提取验证码失败: {e}")
            return None

    def _is_likely_timestamp_or_date(self, code):
        """判断数字是否可能是时间戳或日期"""
        try:
            # 检查是否是时间戳格式
            if len(code) == 8:
                # 检查是否是日期格式 YYYYMMDD
                year = int(code[:4])
                month = int(code[4:6])
                day = int(code[6:8])
                if 2020 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                    return True

            # 检查是否是明显的序列号或ID
            if code.startswith('0000') or code.endswith('0000'):
                return True

            return False
        except:
            return False

    def _extract_key_sections(self, email_body):
        """提取邮件中可能包含验证码的关键段落"""
        try:
            sections = []

            # 按段落分割
            paragraphs = email_body.split('\n')

            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if len(paragraph) < 10:  # 跳过太短的段落
                    continue

                # 查找包含关键词的段落
                keywords = [
                    'verification', 'verify', 'code', 'security',
                    'access', 'confirmation', 'enter', 'use'
                ]

                if any(keyword in paragraph.lower() for keyword in keywords):
                    sections.append(paragraph)

            return sections
        except:
            return []
    
    def get_github_verification_code(self, max_wait_minutes=5, retry_interval=20):
        """获取GitHub验证码"""
        try:
            logger.info(f"开始获取GitHub验证码 - 最大等待时间: {max_wait_minutes}分钟")

            start_time = time.time()
            max_wait_seconds = max_wait_minutes * 60
            attempt = 0

            # 记录开始时间，用于过滤新邮件（使用UTC时间）
            search_start_time = datetime.utcnow()

            while time.time() - start_time < max_wait_seconds:
                attempt += 1
                logger.info(f"第 {attempt} 次尝试获取验证码")

                # 简化邮件搜索 - 只获取最新邮件，然后在代码中过滤
                emails = self.search_emails(
                    subject_filter=None,  # 不在API层过滤主题
                    from_filter=None,     # 不在API层过滤发件人
                    time_range_minutes=max_wait_minutes + 5,
                    max_results=10  # 只获取最新10封邮件
                )

                if emails:
                    logger.info(f"找到 {len(emails)} 封邮件")

                    # 过滤GitHub相关邮件
                    github_emails = []
                    for email in emails:
                        subject = email.get('subject', '').lower()
                        from_address = email.get('from', {}).get('emailAddress', {}).get('address', '').lower()

                        # 检查是否为GitHub相关邮件
                        is_github_subject = any(keyword in subject for keyword in ['github', 'verification', 'verify', 'confirm', 'code'])
                        is_github_sender = any(sender in from_address for sender in ['github.com', 'noreply@github.com', 'no-reply@github.com'])

                        if is_github_subject or is_github_sender:
                            # 检查时间是否在搜索范围内
                            received_time_str = email.get('receivedDateTime', '')
                            if received_time_str:
                                try:
                                    # 解析UTC时间并转换为无时区的datetime进行比较
                                    received_time = datetime.fromisoformat(received_time_str.replace('Z', '+00:00'))
                                    received_time_utc = received_time.replace(tzinfo=None)
                                    if received_time_utc >= search_start_time - timedelta(minutes=2):
                                        github_emails.append(email)
                                        logger.info(f"找到GitHub邮件: {subject[:50]}... 来自: {from_address}")
                                except:
                                    # 时间解析失败，仍然包含
                                    github_emails.append(email)
                                    logger.info(f"找到GitHub邮件(时间解析失败): {subject[:50]}... 来自: {from_address}")

                    if github_emails:
                        logger.info(f"找到 {len(github_emails)} 封GitHub相关邮件")

                    # 处理邮件（优先处理GitHub相关的）
                    emails_to_process = github_emails

                    for i, email in enumerate(emails_to_process):
                        subject = email.get('subject', '')
                        from_addr = email.get('from', {}).get('emailAddress', {}).get('address', '')
                        received_time = email.get('receivedDateTime', '')

                        logger.info(f"处理邮件 {i+1}: {subject} | 发件人: {from_addr}")

                        # 检查是否是验证码邮件
                        verification_keywords = [
                            'verification', 'verify', 'code', 'security',
                            'confirm', 'authentication', 'access'
                        ]

                        if any(keyword in subject.lower() for keyword in verification_keywords):
                            logger.info(f"识别为验证码邮件: {subject}")

                            # 获取邮件正文
                            body_content = email.get('body', {}).get('content', '')
                            if not body_content:
                                # 尝试使用bodyPreview
                                body_content = email.get('bodyPreview', '')

                            if body_content:
                                # 提取验证码
                                code = self.extract_verification_code(body_content)
                                if code:
                                    logger.info(f"成功提取验证码: {code} (来源邮件: {subject})")
                                    return code
                                else:
                                    logger.warning(f"邮件中未找到有效的验证码: {subject}")
                            else:
                                logger.warning(f"邮件内容为空: {subject}")
                        else:
                            logger.debug(f"跳过非验证码邮件: {subject}")
                else:
                    logger.info("未找到相关邮件")

                # 计算剩余等待时间
                elapsed_time = time.time() - start_time
                remaining_time = max_wait_seconds - elapsed_time

                if remaining_time > retry_interval:
                    logger.info(f"等待 {retry_interval} 秒后重试... (剩余时间: {remaining_time:.0f}秒)")
                    time.sleep(retry_interval)
                else:
                    logger.info(f"剩余时间不足 {retry_interval} 秒，结束等待")
                    break

            logger.error(f"在 {max_wait_minutes} 分钟内未找到有效的验证码")
            return None

        except Exception as e:
            logger.error(f"获取GitHub验证码失败: {e}")
            return None

class EmailManagerFactory:
    """邮箱管理器工厂"""

    @staticmethod
    def create_outlook_manager(email, password, client_id, access_token=None):
        """创建Outlook邮箱管理器"""
        return OutlookEmailManager(email, password, client_id, access_token)

    @staticmethod
    def create_wmemail_provider():
        """创建WMEmail供应商"""
        return WMEmailProvider()

    @staticmethod
    def purchase_wmemail_account(commodity_id: int = None) -> WMEmailAccount:
        """
        从WMEmail购买邮箱账号

        Args:
            commodity_id: 商品ID，如果不提供则自动查找Hotmail商品

        Returns:
            WMEmail账号信息
        """
        provider = EmailManagerFactory.create_wmemail_provider()

        if commodity_id:
            return provider.purchase_email(commodity_id)
        else:
            return provider.get_hotmail_account()

    @staticmethod
    def get_wmemail_goods_list():
        """获取WMEmail商品列表"""
        provider = EmailManagerFactory.create_wmemail_provider()
        return provider.get_goods_list()

    @staticmethod
    def get_wmemail_balance():
        """获取WMEmail余额"""
        provider = EmailManagerFactory.create_wmemail_provider()
        return provider.get_balance()

    @staticmethod
    def load_from_config(config_file="email_config.json", account_index=None):
        """从配置文件加载邮箱管理器"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            accounts = config.get('accounts', [])
            if not accounts:
                logger.error("配置文件中没有邮箱账号")
                return None

            # 确定使用哪个账号
            if account_index is None:
                account_index = config.get('current_account_index', 0)

            if account_index >= len(accounts):
                logger.error(f"账号索引 {account_index} 超出范围，共有 {len(accounts)} 个账号")
                return None

            account = accounts[account_index]
            email = account.get('email')
            password = account.get('password')
            client_id = account.get('client_id')
            access_token = account.get('access_token')

            if not all([email, password, client_id]):
                logger.error(f"账号 {account_index} 配置信息不完整")
                return None

            logger.info(f"加载邮箱账号: {email}")
            return EmailManagerFactory.create_outlook_manager(
                email, password, client_id, access_token
            )

        except FileNotFoundError:
            logger.error(f"配置文件 {config_file} 不存在")
            return None
        except json.JSONDecodeError:
            logger.error(f"配置文件 {config_file} 格式错误")
            return None
        except Exception as e:
            logger.error(f"加载邮箱配置失败: {e}")
            return None

    @staticmethod
    def parse_account_string(account_string):
        """解析账号字符串格式: 邮箱----密码----client_id----令牌"""
        try:
            parts = account_string.split('----')
            if len(parts) < 3:
                logger.error("账号字符串格式错误，至少需要: 邮箱----密码----client_id")
                return None

            email = parts[0].strip()
            password = parts[1].strip()
            client_id = parts[2].strip()
            access_token = parts[3].strip() if len(parts) > 3 and parts[3].strip() else None

            if not all([email, password, client_id]):
                logger.error("邮箱、密码或client_id不能为空")
                return None

            return {
                'email': email,
                'password': password,
                'client_id': client_id,
                'access_token': access_token
            }

        except Exception as e:
            logger.error(f"解析账号字符串失败: {e}")
            return None

    @staticmethod
    def add_account(account_string_or_email, password=None, client_id=None, access_token=None, config_file="email_config.json"):
        """添加邮箱账号到配置文件"""
        try:
            # 判断是字符串格式还是分离参数格式
            if password is None and client_id is None:
                # 字符串格式: 邮箱----密码----client_id----令牌
                account_info = EmailManagerFactory.parse_account_string(account_string_or_email)
                if not account_info:
                    return False
                email = account_info['email']
                password = account_info['password']
                client_id = account_info['client_id']
                access_token = account_info['access_token']
            else:
                # 分离参数格式
                email = account_string_or_email

            # 读取现有配置
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except FileNotFoundError:
                config = {"accounts": [], "current_account_index": 0}

            accounts = config.get('accounts', [])

            # 检查邮箱是否已存在
            for i, account in enumerate(accounts):
                if account.get('email') == email:
                    logger.warning(f"邮箱 {email} 已存在，更新配置")
                    accounts[i] = {
                        "email": email,
                        "password": password,
                        "client_id": client_id,
                        "access_token": access_token
                    }
                    break
            else:
                # 添加新账号
                new_account = {
                    "email": email,
                    "password": password,
                    "client_id": client_id,
                    "access_token": access_token
                }
                accounts.append(new_account)
                logger.info(f"添加新邮箱账号: {email}")

            # 更新配置
            config['accounts'] = accounts
            if 'current_account_index' not in config:
                config['current_account_index'] = 0

            # 保存配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"邮箱配置已保存到 {config_file}")
            return True

        except Exception as e:
            logger.error(f"添加邮箱账号失败: {e}")
            return False

    @staticmethod
    def list_accounts(config_file="email_config.json"):
        """列出所有邮箱账号"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            accounts = config.get('accounts', [])
            current_index = config.get('current_account_index', 0)

            logger.info(f"共有 {len(accounts)} 个邮箱账号:")
            for i, account in enumerate(accounts):
                email = account.get('email', 'N/A')
                status = " (当前)" if i == current_index else ""
                logger.info(f"  {i}: {email}{status}")

            return accounts

        except FileNotFoundError:
            logger.error(f"配置文件 {config_file} 不存在")
            return []
        except Exception as e:
            logger.error(f"列出邮箱账号失败: {e}")
            return []

    @staticmethod
    def set_current_account(account_index, config_file="email_config.json"):
        """设置当前使用的邮箱账号"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            accounts = config.get('accounts', [])
            if account_index >= len(accounts):
                logger.error(f"账号索引 {account_index} 超出范围，共有 {len(accounts)} 个账号")
                return False

            config['current_account_index'] = account_index

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            email = accounts[account_index].get('email', 'N/A')
            logger.info(f"当前邮箱账号设置为: {email}")
            return True

        except Exception as e:
            logger.error(f"设置当前账号失败: {e}")
            return False

    @staticmethod
    def get_next_available_account(config_file="email_config.json"):
        """获取下一个可用的邮箱账号"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            accounts = config.get('accounts', [])
            current_index = config.get('current_account_index', 0)

            if not accounts:
                logger.error("没有可用的邮箱账号")
                return None

            # 循环到下一个账号
            next_index = (current_index + 1) % len(accounts)

            # 更新当前账号索引
            config['current_account_index'] = next_index
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            account = accounts[next_index]
            email = account.get('email')
            logger.info(f"切换到下一个邮箱账号: {email}")

            return EmailManagerFactory.create_outlook_manager(
                account.get('email'),
                account.get('password'),
                account.get('client_id'),
                account.get('access_token')
            )

        except Exception as e:
            logger.error(f"获取下一个账号失败: {e}")
            return None

    @staticmethod
    def update_account_tfa_secret(email, tfa_secret, config_file="email_config.json"):
        """更新指定邮箱账号的tfa_secret"""
        try:
            # 读取现有配置
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            accounts = config.get('accounts', [])
            if not accounts:
                logger.error("配置文件中没有邮箱账号")
                return False

            # 查找匹配的邮箱账号
            account_found = False
            for account in accounts:
                if account.get('email') == email:
                    account['tfa_secret'] = tfa_secret
                    account_found = True
                    logger.info(f"已更新邮箱 {email} 的 tfa_secret")
                    break

            if not account_found:
                logger.error(f"未找到邮箱账号: {email}")
                return False

            # 保存更新后的配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"tfa_secret 已保存到配置文件: {config_file}")
            return True

        except Exception as e:
            logger.error(f"更新 tfa_secret 失败: {e}")
            return False

    @staticmethod
    def delete_account(account_index, config_file="email_config.json"):
        """删除邮箱账号"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            accounts = config.get('accounts', [])
            if account_index >= len(accounts):
                logger.error(f"账号索引 {account_index} 超出范围，共有 {len(accounts)} 个账号")
                return False

            # 获取要删除的邮箱地址
            email = accounts[account_index].get('email', 'N/A')

            # 删除账号
            del accounts[account_index]

            # 调整 current_account_index
            current_index = config.get('current_account_index', 0)
            if account_index == current_index:
                # 删除的是当前账号，设置为第一个账号
                config['current_account_index'] = 0 if accounts else 0
            elif account_index < current_index:
                # 删除的账号在当前账号之前，索引需要减1
                config['current_account_index'] = current_index - 1

            # 如果没有账号了，重置索引
            if not accounts:
                config['current_account_index'] = 0

            config['accounts'] = accounts

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"邮箱账号 {email} 删除成功")
            return True

        except Exception as e:
            logger.error(f"删除邮箱账号失败: {e}")
            return False

    @staticmethod
    def update_account(account_index, email=None, password=None, client_id=None, access_token=None, config_file="email_config.json"):
        """更新邮箱账号信息"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            accounts = config.get('accounts', [])
            if account_index >= len(accounts):
                logger.error(f"账号索引 {account_index} 超出范围，共有 {len(accounts)} 个账号")
                return False

            account = accounts[account_index]

            # 更新非空字段
            if email is not None:
                account['email'] = email
            if password is not None:
                account['password'] = password
            if client_id is not None:
                account['client_id'] = client_id
            if access_token is not None:
                account['access_token'] = access_token

            accounts[account_index] = account
            config['accounts'] = accounts

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"邮箱账号 {account.get('email')} 更新成功")
            return True

        except Exception as e:
            logger.error(f"更新邮箱账号失败: {e}")
            return False
