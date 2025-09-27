"""
GitHub鑷姩娉ㄥ唽绯荤粺 V2 - 浠诲姟闃熷垪+浜嬩欢椹卞姩鏋舵瀯
"""

import asyncio
import logging
from datetime import datetime

from core.event_bus import EventBus
from core.state_manager import StateManager
from core.task_manager import TaskManager
from tasks.task_registry import create_all_tasks
from utils.shan_mail_provider import ShanMailProvider
import config
import json

# 閰嶇疆鏃ュ織 - 閬垮厤閲嶅鏃ュ織
def setup_logging():
    """璁剧疆鏃ュ織閰嶇疆锛岄伩鍏嶉噸澶嶈緭鍑?""
    import os

    root_logger = logging.getLogger()

    # 濡傛灉宸茬粡閰嶇疆杩囷紝鐩存帴杩斿洖
    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)

    # 鍒涘缓鏃ュ織鏂囦欢澶?    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # 鍒涘缓鏍煎紡鍖栧櫒
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 鎺у埗鍙板鐞嗗櫒
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 鏂囦欢澶勭悊鍣?- 瀛樺偍鍒發ogs鏂囦欢澶?    log_filename = f'github_signup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    log_filepath = os.path.join(logs_dir, log_filename)
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    print(f"鏃ュ織鏂囦欢: {log_filepath}")

setup_logging()

logger = logging.getLogger(__name__)

class GitHubSignupManager:
    """GitHub娉ㄥ唽绠＄悊鍣?""
    
    def __init__(self):
        # 鍒濆鍖栨牳蹇冪粍浠?        self.event_bus = EventBus()
        self.state_manager = StateManager(self.event_bus)
        self.task_manager = TaskManager(
            event_bus=self.event_bus,
            state_manager=self.state_manager,
            max_concurrent_tasks=1  # 娉ㄥ唽娴佺▼闇€瑕侀『搴忔墽琛?        )
        
        # 璁剧疆浜嬩欢鐩戝惉
        self._setup_event_listeners()
        
        logger.info("GitHubSignupManager 鍒濆鍖栧畬鎴?)
    
    def _setup_event_listeners(self):
        """璁剧疆浜嬩欢鐩戝惉鍣?""
        
        # 鐩戝惉浠诲姟澶辫触浜嬩欢
        self.event_bus.subscribe('task_failed', self._on_task_failed)
        
        # 鐩戝惉鐘舵€佸彉鏇翠簨浠?        self.event_bus.subscribe('state_changed', self._on_state_changed)
        
        # 鐩戝惉娉ㄥ唽瀹屾垚浜嬩欢
        self.event_bus.subscribe('registration_completed', self._on_registration_completed)
        
        # 鐩戝惉閿欒浜嬩欢
        self.event_bus.subscribe('error_occurred', self._on_error_occurred)
    
    async def _on_task_failed(self, event):
        """澶勭悊浠诲姟澶辫触浜嬩欢"""
        task_name = event.data.get('task_name', 'Unknown')
        error = event.data.get('error', 'Unknown error')
        
        logger.error(f"浠诲姟澶辫触: {task_name} - {error}")
        
        # 鍙互鍦ㄨ繖閲屾坊鍔犲け璐ュ鐞嗛€昏緫锛屾瘮濡傚彂閫侀€氱煡绛?    
    async def _on_state_changed(self, event):
        """澶勭悊鐘舵€佸彉鏇翠簨浠?""
        old_state = event.data.get('old_state')
        new_state = event.data.get('new_state')
        
        logger.info(f"鐘舵€佸彉鏇? {old_state} -> {new_state}")
    
    async def _on_registration_completed(self, event):
        """澶勭悊娉ㄥ唽瀹屾垚浜嬩欢"""
        final_url = event.data.get('final_url', '')
        email = event.data.get('email', '')
        username = event.data.get('username', '')
        
        logger.info("=" * 60)
        logger.info("GitHub娉ㄥ唽鎴愬姛瀹屾垚锛?)
        logger.info(f"閭: {email}")
        logger.info(f"鐢ㄦ埛鍚? {username}")
        logger.info(f"鏈€缁圲RL: {final_url}")
        logger.info("=" * 60)
    
    async def _on_error_occurred(self, event):
        """澶勭悊閿欒浜嬩欢"""
        error = event.data.get('error', 'Unknown error')
        error_type = event.data.get('type', 'unknown_error')
        
        logger.error(f"鍙戠敓閿欒: {error} (绫诲瀷: {error_type})")
    
    async def start_registration(self):
        """寮€濮嬫敞鍐屾祦绋?""
        try:
            logger.info("=" * 60)
            logger.info("寮€濮婫itHub鑷姩娉ㄥ唽娴佺▼")
            logger.info("=" * 60)
            
            # 鍒涘缓骞舵敞鍐屾墍鏈変换鍔?            tasks = create_all_tasks()
            self.task_manager.register_tasks(tasks)

            logger.info(f"宸叉敞鍐?{len(tasks)} 涓换鍔?)

            # 閲嶇疆鎵€鏈変换鍔＄姸鎬侊紝娓呯悊鍙兘鐨勬畫鐣欑姸鎬?            self.task_manager.reset_all_tasks()

            # 鍚姩浠诲姟绠＄悊鍣?            await self.task_manager.start()
            
            # 绛夊緟鎵€鏈変换鍔″畬鎴愭垨澶辫触
            while not self.task_manager.is_all_completed() and not self.task_manager.has_failed_tasks():
                await asyncio.sleep(1)
            
            # 妫€鏌ユ渶缁堢粨鏋?            if self.task_manager.is_all_completed():
                logger.info("鎵€鏈変换鍔″凡瀹屾垚")
                return True
            elif self.task_manager.has_failed_tasks():
                logger.error("瀛樺湪澶辫触鐨勪换鍔?)
                failed_tasks = self.task_manager.failed_tasks
                for task_id, error in failed_tasks.items():
                    logger.error(f"  - {task_id}: {error}")
                return False
            else:
                logger.warning("鈿狅笍 浠诲姟鐘舵€佷笉鏄庣‘")
                return False
                
        except Exception as e:
            logger.error(f"娉ㄥ唽娴佺▼寮傚父: {e}")
            return False
        finally:
            # 鍋滄浠诲姟绠＄悊鍣?            await self.task_manager.stop()
    
    def get_status_report(self):
        """鑾峰彇鐘舵€佹姤鍛?""
        report = {
            'current_state': self.state_manager.get_state().value,
            'state_data': self.state_manager.get_all_data(),
            'task_status': self.task_manager.get_all_tasks_status(),
            'event_stats': self.event_bus.get_stats(),
            'state_stats': self.state_manager.get_stats()
        }
        return report
    
    def print_status_report(self):
        """鎵撳嵃鐘舵€佹姤鍛?""
        report = self.get_status_report()
        
        print("\n" + "=" * 60)
        print("鐘舵€佹姤鍛?)
        print("=" * 60)
        
        print(f"褰撳墠鐘舵€? {report['current_state']}")
        print(f"鐘舵€佹暟鎹敭: {report['state_stats']['state_data_keys']}")
        print(f"鐘舵€佽浆鎹㈡鏁? {report['state_stats']['transition_count']}")
        print(f"褰撳墠鐘舵€佹寔缁椂闂? {report['state_stats']['current_state_duration']:.1f}绉?)
        
        print(f"\n浜嬩欢鎬荤嚎缁熻:")
        print(f"  璁㈤槄鑰呮€绘暟: {report['event_stats']['total_subscribers']}")
        print(f"  浜嬩欢绫诲瀷鏁? {report['event_stats']['event_types']}")
        print(f"  鍘嗗彶浜嬩欢鏁? {report['event_stats']['history_count']}")
        
        print(f"\n浠诲姟鐘舵€?")
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
            
            retry_info = f" (閲嶈瘯: {retry_count})" if retry_count > 0 else ""
            print(f"  {status_emoji} {name}: {status}{retry_info}")
        
        print("=" * 60)

def load_email_config():
    """鍔犺浇閭閰嶇疆"""
    try:
        with open('email_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"accounts": [], "current_account_index": 0}
    except Exception as e:
        logger.error(f"鍔犺浇閭閰嶇疆澶辫触: {e}")
        return None

def save_email_config(config_data):
    """淇濆瓨閭閰嶇疆"""
    try:
        with open('email_config.json', 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"淇濆瓨閭閰嶇疆澶辫触: {e}")
        return False

def fetch_email_from_shan_mail():
    """浠庨棯閭鑾峰彇閭璐﹀彿"""
    print("\n=== 闂偖绠卞彇鍙锋敞鍐?===")

    # 妫€鏌ラ厤缃?    card_key = config.SHAN_MAIL_CARD_KEY
    if not card_key:
        print("鉂?鏈厤缃棯閭 CARD KEY")
        print("璇峰湪鐜鍙橀噺涓缃?SHAN_MAIL_CARD_KEY")
        return False

    try:
        provider = ShanMailProvider(card_key)

        # 娴嬭瘯杩炴帴
        print("姝ｅ湪娴嬭瘯杩炴帴...")
        if not provider.test_connection():
            print("鉂?闂偖绠辫繛鎺ュけ璐ワ紝璇锋鏌?CARD KEY 鏄惁姝ｇ‘")
            return False
        print("鉁?杩炴帴鎴愬姛")

        # 鏌ヨ浣欓
        balance = provider.get_balance()
        if balance is None:
            print("鉂?鏃犳硶鏌ヨ浣欓")
            return False
        print(f"褰撳墠浣欓: {balance}")

        if balance <= 0:
            print("鉂?浣欓涓嶈冻锛屾棤娉曟彁鍙栭偖绠?)
            return False

        # 鎻愬彇1涓偖绠辩敤浜庢敞鍐?        email_type = config.SHAN_MAIL_EMAIL_TYPE
        print(f"姝ｅ湪鎻愬彇1涓?{email_type} 閭...")

        email_tokens = provider.fetch_emails(1, email_type)
        if not email_tokens:
            print("鉂?鎻愬彇閭澶辫触")
            return False

        # 瑙ｆ瀽閭
        parsed = provider.parse_email_token(email_tokens[0])
        if not parsed:
            print("鉂?瑙ｆ瀽閭澶辫触")
            return False

        print(f"鉁?鎴愬姛鑾峰彇閭: {parsed['email']}")

        # 娣诲姞鍒伴厤缃?        config_data = load_email_config()
        if config_data is None:
            print("鉂?鏃犳硶鍔犺浇閰嶇疆鏂囦欢")
            return False

        # 娣诲姞鏂伴偖绠?        config_data["accounts"].append({
            "email": parsed["email"],
            "password": parsed["password"],
            "client_id": parsed["client_id"],
            "access_token": parsed["access_token"]
        })

        # 璁剧疆涓哄綋鍓嶉偖绠?        config_data["current_account_index"] = len(config_data["accounts"]) - 1

        # 淇濆瓨閰嶇疆
        if save_email_config(config_data):
            print(f"鉁?閭宸叉坊鍔犲埌閰嶇疆鏂囦欢骞惰缃负褰撳墠閭")
            return True
        else:
            print("鉂?淇濆瓨閰嶇疆鏂囦欢澶辫触")
            return False

    except Exception as e:
        logger.error(f"闂偖绠辨搷浣滃け璐? {e}")
        print(f"鉂?鎿嶄綔澶辫触: {e}")
        return False

def choose_email_source():
    """閫夋嫨閭鏉ユ簮"""
    print("\n=== 閭鏉ユ簮閫夋嫨 ===")
    print("1. 浣跨敤鐜版湁閭閰嶇疆 (email_config.json)")
    print("2. 闂偖绠卞彇鍙锋敞鍐?)

    while True:
        choice = input("\n璇烽€夋嫨閭鏉ユ簮 (1-2): ").strip()

        if choice == '1':
            # 妫€鏌ョ幇鏈夐厤缃?            config_data = load_email_config()
            if not config_data or not config_data.get("accounts"):
                print("鉂?鏈壘鍒扮幇鏈夐偖绠遍厤缃紝璇峰厛娣诲姞閭璐﹀彿")
                print("鍙互杩愯 python email_manager_cli.py 鏉ョ鐞嗛偖绠?)
                continue

            current_index = config_data.get("current_account_index", 0)
            if current_index >= len(config_data["accounts"]):
                print("鉂?褰撳墠閭绱㈠紩鏃犳晥")
                continue

            current_email = config_data["accounts"][current_index]["email"]
            print(f"鉁?浣跨敤鐜版湁閭: {current_email}")
            return True

        elif choice == '2':
            # 闂偖绠卞彇鍙?            if fetch_email_from_shan_mail():
                return True
            else:
                print("闂偖绠辫幏鍙栧け璐ワ紝璇烽噸鏂伴€夋嫨")
                continue
        else:
            print("鏃犳晥閫夋嫨锛岃杈撳叆 1 鎴?2")

async def main():
    """涓诲嚱鏁?""
    print("=" * 60)
    print("GitHub 鑷姩娉ㄥ唽绯荤粺 V2")
    print("=" * 60)

    # 閫夋嫨閭鏉ユ簮
    if not choose_email_source():
        print("閭閰嶇疆澶辫触锛岀▼搴忛€€鍑?)
        return 1

    signup_manager = GitHubSignupManager()
    
    try:
        success = await signup_manager.start_registration()
        
        # 鎵撳嵃鏈€缁堢姸鎬佹姤鍛?        signup_manager.print_status_report()
        
        if success:
            print("\nGitHub娉ㄥ唽娴佺▼鎴愬姛瀹屾垚锛?)
            return 0
        else:
            print("\nGitHub娉ㄥ唽娴佺▼澶辫触锛?)
            return 1

    except KeyboardInterrupt:
        logger.info("鐢ㄦ埛涓柇绋嬪簭")
        print("\n绋嬪簭琚敤鎴蜂腑鏂?)
        return 2
    except Exception as e:
        logger.error(f"绋嬪簭寮傚父: {e}")
        print(f"\n绋嬪簭寮傚父: {e}")
        return 3

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
