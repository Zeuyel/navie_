#!/usr/bin/env python3
"""
邮箱管理入口文件
独立的邮箱账号 CRUD 管理和 current_account_index 管理
"""

import sys
import os
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.email_manager import EmailManagerFactory
from utils.logger import setup_logger
from utils.shan_mail_provider import ShanMailProvider
import config

logger = setup_logger(__name__)

class EmailManagerCLI:
    """邮箱管理命令行界面"""
    
    def __init__(self, config_file="email_config.json"):
        self.config_file = config_file
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"accounts": [], "current_account_index": 0}
        except json.JSONDecodeError:
            logger.error(f"配置文件 {self.config_file} 格式错误")
            return None
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return None
    
    def save_config(self, config):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def list_accounts(self):
        """列出所有邮箱账号"""
        config = self.load_config()
        if config is None:
            print("无法加载配置文件")
            return
        
        accounts = config.get('accounts', [])
        current_index = config.get('current_account_index', 0)
        
        if not accounts:
            print("没有配置的邮箱账号")
            return
        
        print(f"\n邮箱账号列表 (共 {len(accounts)} 个):")
        print("=" * 80)
        for i, account in enumerate(accounts):
            email = account.get('email', 'N/A')
            client_id = account.get('client_id', 'N/A')
            has_token = "是" if account.get('access_token') else "否"
            status = " ← 当前" if i == current_index else ""
            
            print(f"{i:2d}. {email:30s} | Client ID: {client_id[:20]}... | Token: {has_token}{status}")
        print("=" * 80)
    
    def add_account(self):
        """添加邮箱账号"""
        print("\n添加邮箱账号")
        print("请输入账号信息，格式: 邮箱----密码----client_id----令牌")
        print("或者分别输入各项信息")
        print("-" * 50)
        
        choice = input("选择输入方式 (1: 字符串格式, 2: 分别输入) [默认1]: ").strip() or "1"
        
        if choice == '1':
            # 字符串格式
            account_string = input("请输入账号字符串: ").strip()
            if not account_string:
                print("输入不能为空")
                return
            
            success = EmailManagerFactory.add_account(account_string, config_file=self.config_file)
            if success:
                print("✓ 邮箱账号添加成功")
            else:
                print("✗ 邮箱账号添加失败")
        
        elif choice == '2':
            # 分别输入
            email = input("邮箱地址: ").strip()
            password = input("密码: ").strip()
            client_id = input("Client ID: ").strip()
            access_token = input("访问令牌 (可选): ").strip() or None
            
            if not all([email, password, client_id]):
                print("邮箱、密码和Client ID不能为空")
                return
            
            success = EmailManagerFactory.add_account(
                email, password, client_id, access_token, 
                config_file=self.config_file
            )
            if success:
                print("✓ 邮箱账号添加成功")
            else:
                print("✗ 邮箱账号添加失败")
        
        else:
            print("无效选择")
    
    def delete_account(self):
        """删除邮箱账号"""
        config = self.load_config()
        if config is None:
            print("无法加载配置文件")
            return
        
        accounts = config.get('accounts', [])
        if not accounts:
            print("没有可删除的邮箱账号")
            return
        
        self.list_accounts()
        
        try:
            index = int(input(f"\n请输入要删除的账号索引 (0-{len(accounts)-1}): "))
            if index < 0 or index >= len(accounts):
                print("索引超出范围")
                return
            
            email = accounts[index].get('email', 'N/A')
            confirm = input(f"确认删除邮箱 {email}? (y/N): ").strip().lower()
            
            if confirm == 'y':
                # 删除账号
                del accounts[index]
                
                # 调整 current_account_index
                current_index = config.get('current_account_index', 0)
                if index == current_index:
                    # 删除的是当前账号，设置为第一个账号
                    config['current_account_index'] = 0 if accounts else 0
                elif index < current_index:
                    # 删除的账号在当前账号之前，索引需要减1
                    config['current_account_index'] = current_index - 1
                
                # 如果没有账号了，重置索引
                if not accounts:
                    config['current_account_index'] = 0
                
                config['accounts'] = accounts
                
                if self.save_config(config):
                    print(f"✓ 邮箱 {email} 删除成功")
                else:
                    print("✗ 保存配置失败")
            else:
                print("取消删除")
                
        except ValueError:
            print("输入格式错误")
        except Exception as e:
            print(f"删除失败: {e}")
    
    def update_account(self):
        """更新邮箱账号"""
        config = self.load_config()
        if config is None:
            print("无法加载配置文件")
            return
        
        accounts = config.get('accounts', [])
        if not accounts:
            print("没有可更新的邮箱账号")
            return
        
        self.list_accounts()
        
        try:
            index = int(input(f"\n请输入要更新的账号索引 (0-{len(accounts)-1}): "))
            if index < 0 or index >= len(accounts):
                print("索引超出范围")
                return
            
            account = accounts[index]
            print(f"\n当前账号信息:")
            print(f"邮箱: {account.get('email', 'N/A')}")
            print(f"密码: {'*' * len(account.get('password', ''))}")
            print(f"Client ID: {account.get('client_id', 'N/A')}")
            print(f"访问令牌: {'已设置' if account.get('access_token') else '未设置'}")
            
            print("\n请输入新的信息 (直接回车保持不变):")
            
            new_email = input(f"邮箱 [{account.get('email', '')}]: ").strip()
            new_password = input("密码 [保持不变]: ").strip()
            new_client_id = input(f"Client ID [{account.get('client_id', '')}]: ").strip()
            new_access_token = input("访问令牌 [保持不变]: ").strip()
            
            # 更新非空字段
            if new_email:
                account['email'] = new_email
            if new_password:
                account['password'] = new_password
            if new_client_id:
                account['client_id'] = new_client_id
            if new_access_token:
                account['access_token'] = new_access_token
            
            accounts[index] = account
            config['accounts'] = accounts
            
            if self.save_config(config):
                print("✓ 账号信息更新成功")
            else:
                print("✗ 保存配置失败")
                
        except ValueError:
            print("输入格式错误")
        except Exception as e:
            print(f"更新失败: {e}")
    
    def set_current_account(self):
        """设置当前使用的邮箱账号"""
        config = self.load_config()
        if config is None:
            print("无法加载配置文件")
            return
        
        accounts = config.get('accounts', [])
        if not accounts:
            print("没有可设置的邮箱账号")
            return
        
        self.list_accounts()
        
        try:
            index = int(input(f"\n请输入要设置为当前的账号索引 (0-{len(accounts)-1}): "))
            if index < 0 or index >= len(accounts):
                print("索引超出范围")
                return
            
            config['current_account_index'] = index
            
            if self.save_config(config):
                email = accounts[index].get('email', 'N/A')
                print(f"✓ 当前邮箱账号设置为: {email}")
            else:
                print("✗ 保存配置失败")
                
        except ValueError:
            print("输入格式错误")
        except Exception as e:
            print(f"设置失败: {e}")
    
    def test_account(self):
        """测试邮箱账号连接"""
        config = self.load_config()
        if config is None:
            print("无法加载配置文件")
            return
        
        accounts = config.get('accounts', [])
        if not accounts:
            print("没有可测试的邮箱账号")
            return
        
        self.list_accounts()
        
        try:
            index = int(input(f"\n请输入要测试的账号索引 (0-{len(accounts)-1}): "))
            if index < 0 or index >= len(accounts):
                print("索引超出范围")
                return
            
            account = accounts[index]
            email = account.get('email')
            
            print(f"\n正在测试邮箱 {email}...")
            
            # 创建邮箱管理器并测试连接
            manager = EmailManagerFactory.create_outlook_manager(
                account.get('email'),
                account.get('password'),
                account.get('client_id'),
                account.get('access_token')
            )
            
            # 尝试获取访问令牌
            token = manager.get_access_token()
            if token:
                print(f"✓ 邮箱 {email} 连接测试成功")
                
                # 尝试获取最新邮件
                print("正在测试邮件获取...")
                emails = manager.search_emails(time_range_minutes=1, max_results=1)
                print(f"✓ 成功获取邮件，最近1分钟内有 {len(emails)} 封邮件")
            else:
                print(f"✗ 邮箱 {email} 连接测试失败")
                
        except ValueError:
            print("输入格式错误")
        except Exception as e:
            print(f"测试失败: {e}")

    def fetch_from_shan_mail(self):
        """从闪邮箱获取邮箱账号"""
        print("\n=== 闪邮箱取号注册 ===")

        # 检查配置
        card_key = config.SHAN_MAIL_CARD_KEY
        if not card_key:
            print("❌ 未配置闪邮箱 CARD KEY")
            print("请在环境变量中设置 SHAN_MAIL_CARD_KEY")
            return

        try:
            provider = ShanMailProvider(card_key)

            # 测试连接
            print("正在测试连接...")
            if not provider.test_connection():
                print("❌ 闪邮箱连接失败，请检查 CARD KEY 是否正确")
                return
            print("✓ 连接成功")

            # 查询余额
            balance = provider.get_balance()
            if balance is None:
                print("❌ 无法查询余额")
                return
            print(f"当前余额: {balance}")

            if balance <= 0:
                print("❌ 余额不足，无法提取邮箱")
                return

            # 查询库存
            stock = provider.get_stock()
            if stock:
                print(f"当前库存: {stock}")

            # 获取提取数量
            try:
                count = int(input(f"请输入要提取的邮箱数量 (1-{min(balance, 10)}): ").strip())
                if count <= 0 or count > balance or count > 10:
                    print("❌ 数量无效")
                    return
            except ValueError:
                print("❌ 请输入有效数字")
                return

            # 选择邮箱类型
            email_type = config.SHAN_MAIL_EMAIL_TYPE
            print(f"邮箱类型: {email_type}")

            # 提取邮箱
            print(f"正在提取 {count} 个邮箱...")
            email_tokens = provider.fetch_emails(count, email_type)

            if not email_tokens:
                print("❌ 提取邮箱失败")
                return

            print(f"✓ 成功提取 {len(email_tokens)} 个邮箱")

            # 解析并添加到配置
            config_data = self.load_config()
            if config_data is None:
                print("❌ 无法加载配置文件")
                return

            added_count = 0
            for i, email_token in enumerate(email_tokens):
                parsed = provider.parse_email_token(email_token)
                if parsed:
                    # 添加到配置
                    config_data["accounts"].append({
                        "email": parsed["email"],
                        "password": parsed["password"],
                        "client_id": parsed["client_id"],
                        "access_token": parsed["access_token"]
                    })
                    added_count += 1
                    print(f"✓ 添加邮箱 {i+1}: {parsed['email']}")
                else:
                    print(f"❌ 解析邮箱 {i+1} 失败: {email_token}")

            if added_count > 0:
                # 设置最后添加的邮箱为当前邮箱
                config_data["current_account_index"] = len(config_data["accounts"]) - 1

                # 保存配置
                if self.save_config(config_data):
                    print(f"\n✓ 成功添加 {added_count} 个邮箱到配置文件")
                    print(f"✓ 当前邮箱已设置为: {config_data['accounts'][-1]['email']}")
                else:
                    print("❌ 保存配置文件失败")
            else:
                print("❌ 没有成功添加任何邮箱")

        except Exception as e:
            logger.error(f"闪邮箱操作失败: {e}")
            print(f"❌ 操作失败: {e}")

def main():
    """主函数 - 命令行交互界面"""
    print("=" * 60)
    print("邮箱管理系统")
    print("=" * 60)
    
    manager = EmailManagerCLI()
    
    while True:
        print("\n请选择操作:")
        print("1. 列出所有邮箱账号")
        print("2. 添加邮箱账号")
        print("3. 删除邮箱账号")
        print("4. 更新邮箱账号")
        print("5. 设置当前邮箱账号")
        print("6. 测试邮箱连接")
        print("7. 闪邮箱取号注册")
        print("0. 退出")

        choice = input("\n请输入选择 (0-7): ").strip()
        
        if choice == '0':
            print("退出程序")
            break
        elif choice == '1':
            manager.list_accounts()
        elif choice == '2':
            manager.add_account()
        elif choice == '3':
            manager.delete_account()
        elif choice == '4':
            manager.update_account()
        elif choice == '5':
            manager.set_current_account()
        elif choice == '6':
            manager.test_account()
        elif choice == '7':
            manager.fetch_from_shan_mail()
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
