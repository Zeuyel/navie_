#!/usr/bin/env python3
"""
邮件收件入口文件
独立的邮件接收功能，从 current_account_index 指定的邮箱中接收邮件
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.email_manager import EmailManagerFactory
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmailReceiver:
    """邮件接收器"""
    
    def __init__(self, config_file="email_config.json"):
        self.config_file = config_file
        self.email_manager = None
        self._load_current_account()
    
    def _load_current_account(self):
        """加载当前账号的邮箱管理器"""
        try:
            self.email_manager = EmailManagerFactory.load_from_config(self.config_file)
            if self.email_manager:
                logger.info(f"成功加载邮箱账号: {self.email_manager.email}")
                return True
            else:
                logger.error("无法加载邮箱管理器")
                return False
        except Exception as e:
            logger.error(f"加载邮箱管理器失败: {e}")
            return False
    
    def get_current_account_info(self):
        """获取当前账号信息"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            accounts = config.get('accounts', [])
            current_index = config.get('current_account_index', 0)
            
            if current_index < len(accounts):
                account = accounts[current_index]
                return {
                    'index': current_index,
                    'email': account.get('email'),
                    'total_accounts': len(accounts)
                }
            return None
        except Exception as e:
            logger.error(f"获取账号信息失败: {e}")
            return None
    
    def search_emails(self, subject_filter=None, from_filter=None, time_range_minutes=10, max_results=20):
        """搜索邮件"""
        if not self.email_manager:
            logger.error("邮箱管理器未初始化")
            return []
        
        try:
            emails = self.email_manager.search_emails(
                subject_filter=subject_filter,
                from_filter=from_filter,
                time_range_minutes=time_range_minutes,
                max_results=max_results
            )
            
            logger.info(f"搜索到 {len(emails)} 封邮件")
            return emails
            
        except Exception as e:
            logger.error(f"搜索邮件失败: {e}")
            return []
    
    def get_latest_emails(self, count=10, time_range_minutes=60):
        """获取最新邮件"""
        return self.search_emails(
            time_range_minutes=time_range_minutes,
            max_results=count
        )
    
    def get_verification_code(self, max_wait_minutes=5, retry_interval=20):
        """获取验证码（GitHub等）"""
        if not self.email_manager:
            logger.error("邮箱管理器未初始化")
            return None
        
        try:
            code = self.email_manager.get_github_verification_code(
                max_wait_minutes=max_wait_minutes,
                retry_interval=retry_interval
            )
            
            if code:
                logger.info(f"成功获取验证码: {code}")
            else:
                logger.warning("未获取到验证码")
            
            return code
            
        except Exception as e:
            logger.error(f"获取验证码失败: {e}")
            return None
    
    def extract_verification_code_from_email(self, email_content):
        """从邮件内容中提取验证码"""
        if not self.email_manager:
            logger.error("邮箱管理器未初始化")
            return None

        try:
            code = self.email_manager.extract_verification_code(email_content)
            if code:
                logger.info(f"从邮件内容提取验证码: {code}")
            return code
        except Exception as e:
            logger.error(f"提取验证码失败: {e}")
            return None

    def list_all_accounts(self):
        """列出所有邮箱账号"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            accounts = config.get('accounts', [])
            current_index = config.get('current_account_index', 0)

            if not accounts:
                print("没有配置的邮箱账号")
                return []

            print(f"\n邮箱账号列表 (共 {len(accounts)} 个):")
            print("=" * 60)
            for i, account in enumerate(accounts):
                email = account.get('email', 'N/A')
                status = " ← 当前" if i == current_index else ""
                print(f"{i:2d}. {email}{status}")
            print("=" * 60)

            return accounts

        except Exception as e:
            logger.error(f"列出账号失败: {e}")
            return []

    def switch_account(self, account_index):
        """切换到指定的邮箱账号"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            accounts = config.get('accounts', [])
            if account_index >= len(accounts):
                logger.error(f"账号索引 {account_index} 超出范围，共有 {len(accounts)} 个账号")
                return False

            # 更新当前账号索引
            config['current_account_index'] = account_index

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            # 重新加载邮箱管理器
            if self._load_current_account():
                email = accounts[account_index].get('email', 'N/A')
                logger.info(f"成功切换到邮箱: {email}")
                return True
            else:
                logger.error("切换账号后重新加载失败")
                return False

        except Exception as e:
            logger.error(f"切换账号失败: {e}")
            return False
    
    def display_email_summary(self, email):
        """显示邮件摘要"""
        try:
            subject = email.get('subject', 'N/A')
            from_info = email.get('from', {})
            if isinstance(from_info, dict):
                sender = from_info.get('emailAddress', {}).get('address', 'N/A')
            else:
                sender = str(from_info)

            received_time = email.get('receivedDateTime', 'N/A')
            body_preview = email.get('bodyPreview', '')[:100]

            print(f"主题: {subject}")
            print(f"发件人: {sender}")
            print(f"时间: {received_time}")
            print(f"预览: {body_preview}")
            print("-" * 50)

        except Exception as e:
            logger.error(f"显示邮件摘要失败: {e}")

    def display_email_full(self, email):
        """显示完整邮件内容"""
        try:
            subject = email.get('subject', 'N/A')
            from_info = email.get('from', {})
            if isinstance(from_info, dict):
                sender = from_info.get('emailAddress', {}).get('address', 'N/A')
            else:
                sender = str(from_info)

            received_time = email.get('receivedDateTime', 'N/A')

            # 获取完整邮件内容
            body_content = email.get('body', {}).get('content', '')
            if not body_content:
                body_content = email.get('bodyPreview', '')

            print(f"主题: {subject}")
            print(f"发件人: {sender}")
            print(f"时间: {received_time}")
            print(f"完整内容:")
            print("=" * 60)
            print(body_content)
            print("=" * 60)

        except Exception as e:
            logger.error(f"显示完整邮件失败: {e}")

def main():
    """主函数 - 命令行交互界面"""
    print("=" * 60)
    print("邮件收件系统")
    print("=" * 60)
    
    # 初始化邮件接收器
    receiver = EmailReceiver()
    
    # 显示当前账号信息
    account_info = receiver.get_current_account_info()
    if account_info:
        print(f"当前邮箱: {account_info['email']} (索引: {account_info['index']})")
        print(f"总账号数: {account_info['total_accounts']}")
    else:
        print("无法获取账号信息")
        return
    
    print("-" * 60)
    
    while True:
        print("\n请选择操作:")
        print("1. 获取最新邮件")
        print("2. 搜索邮件")
        print("3. 获取验证码")
        print("4. 显示当前账号信息")
        print("5. 重新加载账号")
        print("6. 切换邮箱账号")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-6): ").strip()
        
        if choice == '0':
            print("退出程序")
            break
        elif choice == '1':
            # 获取最新邮件
            try:
                count = int(input("请输入邮件数量 (默认10): ") or "10")
                time_range = int(input("请输入时间范围(分钟，默认60): ") or "60")
                
                print(f"\n正在获取最新 {count} 封邮件...")
                emails = receiver.get_latest_emails(count, time_range)
                
                if emails:
                    print(f"\n找到 {len(emails)} 封邮件:")
                    print("=" * 50)
                    for i, email in enumerate(emails, 1):
                        print(f"\n邮件 {i}:")
                        receiver.display_email_full(email)
                        print()  # 添加空行分隔
                else:
                    print("未找到邮件")
                    
            except ValueError:
                print("输入格式错误")
            except Exception as e:
                print(f"获取邮件失败: {e}")
        
        elif choice == '2':
            # 搜索邮件
            try:
                subject_filter = input("请输入主题关键词 (可选): ").strip() or None
                from_filter = input("请输入发件人关键词 (可选): ").strip() or None
                time_range = int(input("请输入时间范围(分钟，默认60): ") or "60")
                max_results = int(input("请输入最大结果数 (默认20): ") or "20")
                
                print(f"\n正在搜索邮件...")
                emails = receiver.search_emails(
                    subject_filter=subject_filter,
                    from_filter=from_filter,
                    time_range_minutes=time_range,
                    max_results=max_results
                )
                
                if emails:
                    print(f"\n找到 {len(emails)} 封邮件:")
                    print("=" * 50)
                    for i, email in enumerate(emails, 1):
                        print(f"\n邮件 {i}:")
                        receiver.display_email_full(email)
                        print()  # 添加空行分隔
                else:
                    print("未找到匹配的邮件")
                    
            except ValueError:
                print("输入格式错误")
            except Exception as e:
                print(f"搜索邮件失败: {e}")
        
        elif choice == '3':
            # 获取验证码
            try:
                max_wait = int(input("请输入最大等待时间(分钟，默认5): ") or "5")
                retry_interval = int(input("请输入重试间隔(秒，默认20): ") or "20")
                
                print(f"\n正在获取验证码，最大等待 {max_wait} 分钟...")
                code = receiver.get_verification_code(max_wait, retry_interval)
                
                if code:
                    print(f"\n✓ 成功获取验证码: {code}")
                else:
                    print("\n✗ 未获取到验证码")
                    
            except ValueError:
                print("输入格式错误")
            except Exception as e:
                print(f"获取验证码失败: {e}")
        
        elif choice == '4':
            # 显示当前账号信息
            account_info = receiver.get_current_account_info()
            if account_info:
                print(f"\n当前账号信息:")
                print(f"邮箱: {account_info['email']}")
                print(f"索引: {account_info['index']}")
                print(f"总账号数: {account_info['total_accounts']}")
            else:
                print("无法获取账号信息")
        
        elif choice == '5':
            # 重新加载账号
            print("\n正在重新加载账号...")
            if receiver._load_current_account():
                account_info = receiver.get_current_account_info()
                if account_info:
                    print(f"✓ 成功加载邮箱: {account_info['email']}")
                else:
                    print("✗ 加载失败")
            else:
                print("✗ 重新加载失败")

        elif choice == '6':
            # 切换邮箱账号
            accounts = receiver.list_all_accounts()
            if not accounts:
                print("没有可切换的邮箱账号")
            else:
                try:
                    index = int(input(f"\n请输入要切换到的账号索引 (0-{len(accounts)-1}): "))
                    if index < 0 or index >= len(accounts):
                        print("索引超出范围")
                    else:
                        print(f"\n正在切换到账号 {index}...")
                        if receiver.switch_account(index):
                            account_info = receiver.get_current_account_info()
                            if account_info:
                                print(f"✓ 成功切换到邮箱: {account_info['email']}")
                            else:
                                print("✓ 切换成功，但获取账号信息失败")
                        else:
                            print("✗ 切换失败")
                except ValueError:
                    print("输入格式错误")
                except Exception as e:
                    print(f"切换失败: {e}")

        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
