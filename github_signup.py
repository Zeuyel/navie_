"""
GitHub自动注册系统 V2 - 任务队列+事件驱动架构
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from navie.core.event_bus import EventBus
from navie.core.state_manager import StateManager
from navie.core.task_manager import TaskManager
from navie.tasks.task_registry import create_all_tasks
from navie.utils.shan_mail_provider import ShanMailProvider
import config
import json


def setup_logging():
    """设置日志配置，避免重复输出"""
    import os

    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)

    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    log_filename = f'github_signup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    log_filepath = os.path.join(logs_dir, log_filename)
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    print(f"日志文件: {log_filepath}")


setup_logging()

logger = logging.getLogger(__name__)


class GitHubSignupManager:
    """GitHub注册管理器"""

    def __init__(self):
        self.event_bus = EventBus()
        self.state_manager = StateManager(self.event_bus)
        self.task_manager = TaskManager(
            event_bus=self.event_bus,
            state_manager=self.state_manager,
            max_concurrent_tasks=1  # 注册流程需要顺序执行
        )

        self._setup_event_listeners()
        logger.info("GitHubSignupManager 初始化完成")

    def _setup_event_listeners(self):
        """设置事件监听器"""
        self.event_bus.subscribe('task_failed', self._on_task_failed)
        self.event_bus.subscribe('state_changed', self._on_state_changed)
        self.event_bus.subscribe('registration_completed', self._on_registration_completed)
        self.event_bus.subscribe('error_occurred', self._on_error_occurred)

    async def _on_task_failed(self, event):
        task_name = event.data.get('task_name', 'Unknown')
        error = event.data.get('error', 'Unknown error')
        logger.error(f"任务失败: {task_name} - {error}")

    async def _on_state_changed(self, event):
        old_state = event.data.get('old_state')
        new_state = event.data.get('new_state')
        logger.info(f"状态变更: {old_state} -> {new_state}")

    async def _on_registration_completed(self, event):
        final_url = event.data.get('final_url', '')
        email = event.data.get('email', '')
        username = event.data.get('username', '')

        logger.info("=" * 60)
        logger.info("GitHub注册成功完成！")
        logger.info(f"邮箱: {email}")
        logger.info(f"用户名: {username}")
        logger.info(f"最终URL: {final_url}")
        logger.info("=" * 60)

    async def _on_error_occurred(self, event):
        error = event.data.get('error', 'Unknown error')
        error_type = event.data.get('type', 'unknown_error')
        logger.error(f"发生错误: {error} (类型: {error_type})")

    async def start_registration(self):
        """开始注册流程"""
        manager_task = None
        try:
            logger.info("=" * 60)
            logger.info("开始GitHub自动注册流程")
            logger.info("=" * 60)

            # 创建并注册所有任务
            tasks = create_all_tasks()
            self.task_manager.register_tasks(tasks)
            logger.info(f"已注册 {len(tasks)} 个任务")

            # 启动任务管理器（后台运行，避免阻塞后续逻辑）
            manager_task = asyncio.create_task(self.task_manager.start())

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
                logger.warning("任务状态不明确")
                return False

        except Exception as e:
            logger.error(f"注册流程异常: {e}")
            return False
        finally:
            # 停止任务管理器并等待后台任务退出
            try:
                await self.task_manager.stop()
            finally:
                if manager_task is not None:
                    try:
                        await manager_task
                    except Exception:
                        pass

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
        try:
            duration = float(report['state_stats'].get('current_state_duration') or 0)
        except Exception:
            duration = 0.0
        print(f"当前状态持续时间: {duration:.1f}s")

        print(f"\n事件总线统计:")
        print(f"  订阅者总数: {report['event_stats']['total_subscribers']}")
        print(f"  事件类型数: {report['event_stats']['event_types']}")
        print(f"  历史事件数: {report['event_stats']['history_count']}")

        print(f"\n任务状态")
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
    """从数据库加载邮箱配置"""
    import asyncpg

    async def load_from_db():
        try:
            conn = await asyncpg.connect(config.get_db_connection_string())

            accounts = await conn.fetch(
                """
                SELECT email, password, client_id, access_token, tfa_secret
                FROM email_accounts
                WHERE is_active = true
                ORDER BY created_at ASC
                """
            )

            current_index = await conn.fetchval(
                """
                SELECT config_value FROM email_config
                WHERE config_key = 'current_account_index'
                """
            )
            current_index = int(current_index) if current_index else 0

            await conn.close()

            json_accounts = []
            for account in accounts:
                json_account = {
                    'email': account['email'],
                    'password': account['password'],
                    'client_id': account['client_id'],
                    'access_token': account['access_token']
                }
                if account['tfa_secret']:
                    json_account['tfa_secret'] = account['tfa_secret']
                json_accounts.append(json_account)

            return {
                'accounts': json_accounts,
                'current_account_index': current_index
            }

        except Exception as e:
            logging.getLogger(__name__).error(f"从数据库加载邮箱配置失败: {e}")
            return {"accounts": [], "current_account_index": 0}

    try:
        # 检查是否已经有运行中的事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，使用asyncio.create_task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, load_from_db())
                return future.result()
        except RuntimeError:
            # 没有运行中的循环，创建新的
            return asyncio.run(load_from_db())
    except Exception as e:
        logging.getLogger(__name__).error(f"加载邮箱配置失败: {e}")
        return None


def save_email_config(config_data):
    """保存邮箱配置到数据库"""
    import asyncpg

    async def save_to_db():
        try:
            conn = await asyncpg.connect(config.get_db_connection_string())

            # 只插入或更新邮箱，不删除现有的
            accounts = config_data.get('accounts', [])
            for account in accounts:
                provider = 'outlook' if '@outlook.com' in account['email'] else 'hotmail'
                await conn.execute(
                    """
                    INSERT INTO email_accounts (email, password, client_id, access_token, tfa_secret, provider, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, true)
                    ON CONFLICT (email) DO UPDATE SET
                        password = EXCLUDED.password,
                        client_id = EXCLUDED.client_id,
                        access_token = EXCLUDED.access_token,
                        tfa_secret = EXCLUDED.tfa_secret,
                        provider = EXCLUDED.provider,
                        is_active = true,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    account['email'], account['password'], account['client_id'],
                    account.get('access_token'), account.get('tfa_secret'), provider
                )

            current_index = config_data.get('current_account_index', 0)
            await conn.execute(
                """
                INSERT INTO email_config (config_key, config_value)
                VALUES ('current_account_index', $1)
                ON CONFLICT (config_key)
                DO UPDATE SET config_value = EXCLUDED.config_value, updated_at = CURRENT_TIMESTAMP
                """,
                str(current_index)
            )

            await conn.close()
            return True

        except Exception as e:
            logging.getLogger(__name__).error(f"保存配置到数据库失败: {e}")
            return False

    try:
        # 检查是否已经有运行中的事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，使用线程池执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, save_to_db())
                return future.result()
        except RuntimeError:
            # 没有运行中的循环，创建新的
            return asyncio.run(save_to_db())
    except Exception as e:
        logging.getLogger(__name__).error(f"保存配置失败: {e}")
        return False


def update_current_account_index(new_index: int) -> bool:
    """将当前邮箱索引写入数据库。

    返回 True 表示成功，False 表示失败。
    """
    import asyncpg

    async def update_to_db():
        conn = None
        try:
            conn = await asyncpg.connect(config.get_db_connection_string())
            await conn.execute(
                """
                INSERT INTO email_config (config_key, config_value)
                VALUES ('current_account_index', $1)
                ON CONFLICT (config_key)
                DO UPDATE SET config_value = EXCLUDED.config_value, updated_at = CURRENT_TIMESTAMP
                """,
                str(int(new_index))
            )
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"更新当前邮箱索引失败: {e}")
            return False
        finally:
            if conn:
                await conn.close()

    try:
        # 检查是否已经有运行中的事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，使用线程池执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, update_to_db())
                return future.result()
        except RuntimeError:
            # 没有运行中的循环，创建新的
            return asyncio.run(update_to_db())
    except Exception as e:
        logging.getLogger(__name__).error(f"更新邮箱索引时发生异常: {e}")
        return False


def fetch_email_from_shan_mail():
    """从闪邮箱获取邮箱账号"""
    print("\n=== 闪邮箱取号注册 ===")

    card_key = config.SHAN_MAIL_CARD_KEY
    if not card_key:
        print("❌ 未配置闪邮箱 CARD KEY")
        print("请在环境变量中设置 SHAN_MAIL_CARD_KEY")
        return False

    try:
        provider = ShanMailProvider(card_key)

        print("正在测试连接...")
        if not provider.test_connection():
            print("❌ 闪邮箱连接失败，请检查 CARD KEY 是否正确")
            return False
        print("✓ 连接成功")

        balance = provider.get_balance()
        if balance is None:
            print("❌ 无法查询余额")
            return False
        print(f"当前余额: {balance}")

        if balance <= 0:
            print("❌ 余额不足，无法提取邮箱")
            return False

        email_type = config.SHAN_MAIL_EMAIL_TYPE
        print(f"正在提取 1 个 {email_type} 邮箱...")

        email_tokens = provider.fetch_emails(1, email_type)
        if not email_tokens:
            print("❌ 提取邮箱失败")
            return False

        parsed = provider.parse_email_token(email_tokens[0])
        if not parsed:
            print("❌ 解析邮箱失败")
            return False

        print(f"✓ 成功获取邮箱: {parsed['email']}")

        print("正在加载现有配置...")
        config_data = load_email_config()
        if config_data is None:
            print("❌ 无法加载配置")
            return False

        print(f"当前配置中有 {len(config_data['accounts'])} 个邮箱账号")

        config_data["accounts"].append({
            "email": parsed["email"],
            "password": parsed["password"],
            "client_id": parsed["client_id"],
            "access_token": parsed["access_token"]
        })

        new_index = len(config_data["accounts"]) - 1
        config_data["current_account_index"] = new_index

        print(f"正在保存邮箱到数据库（索引: {new_index}）...")
        if save_email_config(config_data):
            print("✓ 邮箱保存成功")
            # 再次确认并同步索引到数据库（防止并发或外部修改）
            print("正在更新当前邮箱索引...")
            if update_current_account_index(new_index):
                print("✓ 邮箱已添加到数据库并设置为当前邮箱")
                return True
            else:
                print("⚠️ 邮箱已保存但索引更新失败")
                return True  # 邮箱已保存，索引失败不影响主要功能
        else:
            print("❌ 保存配置失败")
            return False

    except Exception as e:
        logging.getLogger(__name__).error(f"闪邮箱操作失败: {e}")
        print(f"❌ 操作失败: {e}")
        return False


def choose_email_source():
    """选择邮箱来源"""
    print("\n=== 邮箱来源选择 ===")
    print("1. 使用数据库中的现有邮箱配置")
    print("2. 闪邮箱取号注册")

    while True:
        choice = input("\n请选择邮箱来源 (1-2): ").strip()

        if choice == '1':
            config_data = load_email_config()
            if not config_data or not config_data.get("accounts"):
                print("❌ 未找到现有邮箱配置，请先添加邮箱账号")
                print("可以运行 python email_manager_cli.py 来管理邮箱")
                continue

            current_index = config_data.get("current_account_index", 0)
            # 修正越界或负数索引，并同步到数据库
            if not isinstance(current_index, int):
                try:
                    current_index = int(current_index)
                except Exception:
                    current_index = 0
            if current_index < 0 or current_index >= len(config_data["accounts"]):
                print("⚠️ 检测到当前邮箱索引无效，已自动重置为 0")
                if update_current_account_index(0):
                    current_index = 0
                else:
                    print("❌ 无法更新数据库中的当前邮箱索引")
                    continue

            current_email = config_data["accounts"][current_index]["email"]
            print(f"✓ 使用现有邮箱: {current_email}")
            return True

        elif choice == '2':
            if fetch_email_from_shan_mail():
                return True
            else:
                print("闪邮箱获取失败，请重新选择")
                continue
        else:
            print("无效选择，请输入 1 或 2")


async def main():
    """主函数"""
    print("=" * 60)
    print("GitHub 自动注册系统 V2")
    print("=" * 60)

    if not choose_email_source():
        print("邮箱配置失败，程序退出")
        return 1

    signup_manager = GitHubSignupManager()

    try:
        success = await signup_manager.start_registration()

        signup_manager.print_status_report()

        if success:
            print("\nGitHub注册流程成功完成！")
            return 0
        else:
            print("\nGitHub注册流程失败！")
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
