"""
Augment自动注册系统 V2 - 任务队列+事件驱动架构
"""

import asyncio
import logging
from datetime import datetime

from core.event_bus import EventBus
from core.state_manager import StateManager
from core.task_manager import TaskManager
from tasks.task_registry import create_augment_tasks
from utils.shan_mail_provider import ShanMailProvider
import config
import json

# 配置日志 - 避免重复日志
def setup_logging():
    """设置日志配置，避免重复输出"""
    import os

    root_logger = logging.getLogger()

    # 如果已经配置过，直接返回
    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)

    # 创建日志文件夹
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器 - 存储到logs文件夹
    log_filename = f'augment_signup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    log_filepath = os.path.join(logs_dir, log_filename)
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    print(f"日志文件: {log_filepath}")

setup_logging()

logger = logging.getLogger(__name__)

class AugmentSignupManager:
    """Augment注册管理器"""

    def __init__(self):
        # 初始化核心组件
        self.event_bus = EventBus()
        self.state_manager = StateManager(self.event_bus)
        self.task_manager = TaskManager(
            event_bus=self.event_bus,
            state_manager=self.state_manager,
            max_concurrent_tasks=1  # 注册流程需要顺序执行
        )

        # 设置事件监听
        self._setup_event_listeners()

        logger.info("AugmentSignupManager 初始化完成")

    def _setup_event_listeners(self):
        """设置事件监听器"""

        # 监听任务失败事件
        self.event_bus.subscribe('task_failed', self._on_task_failed)

        # 监听状态变更事件
        self.event_bus.subscribe('state_changed', self._on_state_changed)

        # 监听注册完成事件
        self.event_bus.subscribe('registration_completed', self._on_registration_completed)

        # 监听错误事件
        self.event_bus.subscribe('error_occurred', self._on_error_occurred)

    async def _on_task_failed(self, event):
        """处理任务失败事件"""
        task_name = event.data.get('task_name', 'Unknown')
        error = event.data.get('error', 'Unknown error')

        logger.error(f"任务失败: {task_name} - {error}")

        # 可以在这里添加失败处理逻辑，比如发送通知等

    async def _on_state_changed(self, event):
        """处理状态变更事件"""
        old_state = event.data.get('old_state')
        new_state = event.data.get('new_state')

        logger.info(f"状态变更: {old_state} -> {new_state}")

    async def _on_registration_completed(self, event):
        """处理注册完成事件"""
        final_url = event.data.get('final_url', '')
        email = event.data.get('email', '')
        username = event.data.get('username', '')

        logger.info("=" * 60)
        logger.info("Augment注册成功完成！")
        logger.info(f"邮箱: {email}")
        logger.info(f"用户名: {username}")
        logger.info(f"最终URL: {final_url}")
        logger.info("=" * 60)

    async def _on_error_occurred(self, event):
        """处理错误事件"""
        error = event.data.get('error', 'Unknown error')
        error_type = event.data.get('type', 'unknown_error')

        logger.error(f"发生错误: {error} (类型: {error_type})")

    async def start_registration(self):
        """开始注册流程"""
        try:
            logger.info("=" * 60)
            logger.info("开始Augment自动注册流程")
            logger.info("=" * 60)

            # 创建并注册所有任务
            tasks = create_augment_tasks()
            self.task_manager.register_tasks(tasks)

            logger.info(f"已注册 {len(tasks)} 个任务")

            # 重置所有任务状态，清理可能的残留状态
            self.task_manager.reset_all_tasks()

            # 启动任务管理器
            await self.task_manager.start()

            # 等待所有任务完成或失败
            while not self.task_manager.is_all_completed() and not self.task_manager.has_failed_tasks():
                await asyncio.sleep(1)

            # 检查最终结果
            if self.task_manager.is_all_completed():
                logger.info("所有任务已完成")
                return True
            elif self.task_manager.has_failed_tasks():
                logger.error("存在失败的任务")
                failed_tasks = self.task_manager.failed_tasks
                for task_id, error in failed_tasks.items():
                    logger.error(f"  - {task_id}: {error}")
                return False
            else:
                logger.warning("⚠️ 任务状态不明确")
                return False

        except Exception as e:
            logger.error(f"注册流程异常: {e}")
            return False
        finally:
            # 停止任务管理器
            await self.task_manager.stop()

    def get_status_report(self):
        """获取状态报告"""
        report = {
            'current_state': self.state_manager.get_state().value,
            'state_data': self.state_manager.get_all_data(),
            'task_status': self.task_manager.get_all_tasks_status(),
            'event_stats': self.event_bus.get_stats(),
            'state_stats': self.state_manager.get_stats()
        }
        return report

    def print_status_report(self):
        """打印状态报告"""
        report = self.get_status_report()

        print("\n" + "=" * 60)
        print("状态报告")
        print("=" * 60)

        print(f"当前状态: {report['current_state']}")
        print(f"状态数据键: {report['state_stats']['state_data_keys']}")
        print(f"状态转换次数: {report['state_stats']['transition_count']}")
        print(f"当前状态持续时间: {report['state_stats']['current_state_duration']:.1f}秒")

        print(f"\n事件总线统计:")
        print(f"  订阅者总数: {report['event_stats']['total_subscribers']}")
        print(f"  事件类型数: {report['event_stats']['event_types']}")
        print(f"  历史事件数: {report['event_stats']['history_count']}")

        print(f"\n任务状态:")
        for task_id, task_info in report['task_status'].items():
            status = task_info['status']
            name = task_info['name']
            retry_count = task_info['retry_count']

            status_emoji = {
                'pending': '[PENDING]',
                'running': '[RUNNING]',
                'completed': '[COMPLETED]',
                'failed': '[FAILED]',
                'cancelled': '[CANCELLED]',
                'skipped': '[SKIPPED]'
            }.get(status, '[UNKNOWN]')

            retry_info = f" (重试: {retry_count})" if retry_count > 0 else ""
            print(f"  {status_emoji} {name}: {status}{retry_info}")

        print("=" * 60)

def load_email_config():
    """加载邮箱配置"""
    try:
        with open('email_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"accounts": [], "current_account_index": 0}
    except Exception as e:
        logger.error(f"加载邮箱配置失败: {e}")
        return None

def save_email_config(config_data):
    """保存邮箱配置"""
    try:
        with open('email_config.json', 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存邮箱配置失败: {e}")
        return False

def fetch_email_from_shan_mail():
    """从闪邮箱获取邮箱账号"""
    print("\n=== 闪邮箱取号注册 ===")

    # 检查配置
    card_key = config.SHAN_MAIL_CARD_KEY
    if not card_key:
        print("❌ 未配置闪邮箱 CARD KEY")
        print("请在环境变量中设置 SHAN_MAIL_CARD_KEY")
        return False

    try:
        provider = ShanMailProvider(card_key)

        # 测试连接
        print("正在测试连接...")
        if not provider.test_connection():
            print("❌ 闪邮箱连接失败，请检查 CARD KEY 是否正确")
            return False
        print("✓ 连接成功")

        # 查询余额
        balance = provider.get_balance()
        if balance is None:
            print("❌ 无法查询余额")
            return False
        print(f"当前余额: {balance}")

        if balance <= 0:
            print("❌ 余额不足，无法提取邮箱")
            return False

        # 提取1个邮箱用于注册
        email_type = config.SHAN_MAIL_EMAIL_TYPE
        print(f"正在提取1个 {email_type} 邮箱...")

        email_tokens = provider.fetch_emails(1, email_type)
        if not email_tokens:
            print("❌ 提取邮箱失败")
            return False

        # 解析邮箱
        parsed = provider.parse_email_token(email_tokens[0])
        if not parsed:
            print("❌ 解析邮箱失败")
            return False

        print(f"✓ 成功获取邮箱: {parsed['email']}")

        # 添加到配置
        config_data = load_email_config()
        if config_data is None:
            print("❌ 无法加载配置文件")
            return False

        # 添加新邮箱
        config_data["accounts"].append({
            "email": parsed["email"],
            "password": parsed["password"],
            "client_id": parsed["client_id"],
            "access_token": parsed["access_token"]
        })

        # 设置为当前邮箱
        config_data["current_account_index"] = len(config_data["accounts"]) - 1

        # 保存配置
        if save_email_config(config_data):
            print(f"✓ 邮箱已添加到配置文件并设置为当前邮箱")
            return True
        else:
            print("❌ 保存配置文件失败")
            return False

    except Exception as e:
        logger.error(f"闪邮箱操作失败: {e}")
        print(f"❌ 操作失败: {e}")
        return False

def choose_email_account():
    """选择邮箱账号 - Augment专用（仅支持现有配置）"""
    print("\n=== 邮箱账号选择 ===")

    # 检查现有配置
    config_data = load_email_config()
    if not config_data or not config_data.get("accounts"):
        print("❌ 未找到现有邮箱配置，请先添加邮箱账号")
        print("可以运行 python email_manager_cli.py 来管理邮箱")
        return False

    accounts = config_data.get("accounts", [])
    current_index = config_data.get("current_account_index", 0)

    if current_index >= len(accounts):
        print("❌ 当前邮箱索引无效")
        return False

    # 显示当前邮箱账号信息
    current_account = accounts[current_index]
    current_email = current_account.get('email', 'N/A')

    print(f"当前邮箱账号: {current_email} (索引: {current_index})")
    print(f"总账号数: {len(accounts)}")

    # 显示所有账号列表
    print("\n所有可用邮箱账号:")
    for i, account in enumerate(accounts):
        email = account.get('email', 'N/A')
        status = " ← 当前" if i == current_index else ""
        print(f"  {i}: {email}{status}")

    print("\n选择操作:")
    print("1. 使用当前邮箱账号继续")
    print("2. 切换到其他邮箱账号")
    print("0. 退出程序")

    choice = input("\n请输入选择 (0-2): ").strip()

    if choice == '0':
        print("用户选择退出程序")
        return False
    elif choice == '2':
        # 切换邮箱账号
        try:
            new_index = int(input(f"请输入要切换到的账号索引 (0-{len(accounts)-1}): "))
            if new_index < 0 or new_index >= len(accounts):
                print("❌ 索引超出范围")
                return False

            # 更新配置文件
            config_data['current_account_index'] = new_index
            if save_email_config(config_data):
                new_email = accounts[new_index].get('email', 'N/A')
                print(f"✓ 已切换到邮箱账号: {new_email}")
                return True
            else:
                print("❌ 保存配置文件失败")
                return False

        except ValueError:
            print("❌ 请输入有效的数字")
            return False
        except Exception as e:
            print(f"❌ 切换失败: {e}")
            return False
    elif choice == '1':
        print(f"✓ 使用当前邮箱: {current_email}")
        return True
    else:
        print("❌ 无效选择")
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("Augment 自动注册系统 V2")
    print("=" * 60)

    # 选择邮箱账号
    if not choose_email_account():
        print("邮箱配置失败，程序退出")
        return 1

    signup_manager = AugmentSignupManager()

    try:
        success = await signup_manager.start_registration()

        # 打印最终状态报告
        signup_manager.print_status_report()

        if success:
            print("\nAugment注册流程成功完成！")
            return 0
        else:
            print("\nAugment注册流程失败！")
            return 1

    except KeyboardInterrupt:
        logger.info("用户中断程序")
        print("\n程序被用户中断")
        return 2
    except Exception as e:
        logger.error(f"程序异常: {e}")
        print(f"\n程序异常: {e}")
        return 3

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
