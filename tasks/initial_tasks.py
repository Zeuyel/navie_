"""
初始化任务 - 程序入口和初始设置
"""

import json
import logging
from core.task_manager import TaskResult
from utils.email_manager import EmailManagerFactory

logger = logging.getLogger(__name__)

async def email_account_select_task(state_manager, event_bus):
    """任务0: 邮箱账号选择入口"""
    logger.info("执行任务: email_account_select_task")
    
    try:
        # 加载邮箱配置
        try:
            with open("email_config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            raise Exception("邮箱配置文件 email_config.json 不存在")
        except json.JSONDecodeError:
            raise Exception("邮箱配置文件格式错误")
        
        accounts = config.get('accounts', [])
        current_index = config.get('current_account_index', 0)
        
        if not accounts:
            raise Exception("没有配置的邮箱账号，请先使用 email_manager_cli.py 添加邮箱账号")
        
        # 显示当前邮箱账号信息
        if current_index < len(accounts):
            current_account = accounts[current_index]
            current_email = current_account.get('email', 'N/A')
            logger.info(f"当前邮箱账号: {current_email} (索引: {current_index})")
            logger.info(f"总账号数: {len(accounts)}")
            
            # 显示所有账号列表
            logger.info("所有可用邮箱账号:")
            for i, account in enumerate(accounts):
                email = account.get('email', 'N/A')
                status = " ← 当前" if i == current_index else ""
                logger.info(f"  {i}: {email}{status}")
            
            # 询问是否要切换账号
            print("\n" + "=" * 60)
            print("GitHub 自动注册系统 - 邮箱账号选择")
            print("=" * 60)
            print(f"当前邮箱: {current_email} (索引: {current_index})")
            print(f"总账号数: {len(accounts)}")
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
                raise Exception("用户选择退出程序")
            elif choice == '2':
                # 切换邮箱账号
                try:
                    new_index = int(input(f"请输入要切换到的账号索引 (0-{len(accounts)-1}): "))
                    if new_index < 0 or new_index >= len(accounts):
                        raise ValueError("索引超出范围")
                    
                    # 更新配置文件
                    config['current_account_index'] = new_index
                    with open("email_config.json", 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    
                    new_email = accounts[new_index].get('email', 'N/A')
                    logger.info(f"已切换到邮箱账号: {new_email}")
                    print(f"✓ 已切换到邮箱账号: {new_email}")
                    
                except ValueError as e:
                    logger.warning(f"输入无效: {e}，使用当前账号继续")
                    print(f"输入无效: {e}，使用当前账号继续")
            else:
                # 使用当前账号继续
                logger.info(f"继续使用当前邮箱账号: {current_email}")
                print(f"继续使用当前邮箱账号: {current_email}")
            
            # 验证最终选择的邮箱账号
            email_manager = EmailManagerFactory.load_from_config()
            if not email_manager:
                raise Exception("无法加载邮箱管理器，请检查邮箱配置")
            
            final_email = email_manager.email
            logger.info(f"最终使用的邮箱: {final_email}")
            
            # 获取邮箱密码并检查格式
            email_password = email_manager.password
            if email_password and email_password.isalpha():
                email_password = email_password + "0"
                logger.info("邮箱密码全为字母，已添加数字0")
                print("⚠️  邮箱密码全为字母，已自动添加数字0以符合GitHub要求")

            # 保存邮箱信息到状态管理器
            state_manager.set_data('selected_email', final_email)
            state_manager.set_data('email_manager', email_manager)
            state_manager.set_data('email', final_email)
            state_manager.set_data('password', email_password)
            
            print(f"\n✓ 邮箱账号选择完成: {final_email}")
            print("🚀 开始 GitHub 注册流程...")
            print("=" * 60)
            
            return TaskResult(
                success=True,
                data={
                    'selected_email': final_email,
                    'account_index': config.get('current_account_index', 0)
                }
            )
        else:
            raise Exception(f"当前账号索引 {current_index} 超出范围")
            
    except Exception as e:
        logger.error(f"邮箱账号选择失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=False  # 用户交互失败不重试
        )

async def system_initialization_task(state_manager, event_bus):
    """任务-1: 系统初始化检查"""
    logger.info("执行任务: system_initialization_task")
    
    try:
        # 检查必要的配置文件
        config_files = ["email_config.json"]
        missing_files = []
        
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                logger.info(f"✓ 配置文件检查通过: {config_file}")
            except FileNotFoundError:
                missing_files.append(config_file)
            except json.JSONDecodeError:
                raise Exception(f"配置文件格式错误: {config_file}")
        
        if missing_files:
            raise Exception(f"缺少必要的配置文件: {', '.join(missing_files)}")
        
        # 检查邮箱配置
        email_manager = EmailManagerFactory.load_from_config()
        if not email_manager:
            raise Exception("无法加载邮箱管理器，请检查邮箱配置")
        
        logger.info("✓ 系统初始化检查完成")
        
        return TaskResult(
            success=True,
            data={'initialization_complete': True}
        )
        
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=False
        )

async def debug_task(state_manager, event_bus):
    """调试任务: 等待用户手动操作后继续"""
    logger.info("执行任务: debug_task")
    logger.info("=" * 60)
    logger.info("🔧 调试模式: 任务失败，等待用户手动操作")
    logger.info("请在浏览器中手动完成当前步骤，然后按 Enter 键继续...")
    logger.info("=" * 60)

    try:
        # 等待用户输入
        input("按 Enter 键继续测试后续部分...")

        logger.info("用户确认继续，调试任务完成")

        # 获取失败任务的依赖任务
        dependent_tasks = state_manager.get_data('debug_dependent_tasks', [])
        failed_task_id = state_manager.get_data('debug_failed_task_id')

        if dependent_tasks:
            logger.info(f"将触发失败任务 {failed_task_id} 的依赖任务: {dependent_tasks}")

        # 清理调试状态
        state_manager.set_data('debug_failed_task_id', None)
        state_manager.set_data('debug_dependent_tasks', None)

        return TaskResult(
            success=True,
            data={'debug_completed': True},
            next_tasks=dependent_tasks  # 触发依赖任务
        )

    except Exception as e:
        logger.error(f"调试任务失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=False
        )


async def github_account_setup_task(state_manager, event_bus):
    """任务: 设置GitHub账号信息 - 从email_config.json获取已注册的GitHub账号"""
    logger.info("执行任务: github_account_setup_task")

    try:
        # 从email_config.json获取GitHub账号信息
        try:
            with open('email_config.json', 'r', encoding='utf-8') as f:
                email_config = json.load(f)
        except FileNotFoundError:
            raise Exception("email_config.json 文件不存在")
        except json.JSONDecodeError:
            raise Exception("email_config.json 格式错误")

        accounts = email_config.get('accounts', [])
        current_index = email_config.get('current_account_index', 0)

        if not accounts:
            raise Exception("email_config.json 中没有账号信息")

        if current_index >= len(accounts):
            raise Exception("当前账号索引超出范围")

        current_account = accounts[current_index]

        # 获取GitHub账号信息
        github_username = current_account.get('github_username')
        github_password = current_account.get('github_password')

        if not github_username or not github_password:
            logger.warning("当前邮箱账号未包含GitHub账号信息")
            logger.info("请确保email_config.json中的账号包含github_username和github_password字段")

            # 即使没有配置也继续，因为可能已经登录了GitHub
            state_manager.set_data('github_username', '')
            state_manager.set_data('github_password', '')

            return TaskResult(
                success=True,
                data={'github_account_configured': False}
            )
        else:
            logger.info(f"已加载GitHub账号: {github_username}")
            state_manager.set_data('github_username', github_username)
            state_manager.set_data('github_password', github_password)

            return TaskResult(
                success=True,
                data={'github_account_configured': True}
            )

    except Exception as e:
        logger.error(f"设置GitHub账号信息失败: {e}")
        return TaskResult(
            success=False,
            error=str(e),
            should_retry=False
        )
