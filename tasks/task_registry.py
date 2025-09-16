"""
任务注册器 - 定义所有任务及其依赖关系
"""

from core.task_manager import Task
from .initial_tasks import (
    system_initialization_task,
    email_account_select_task
)
from .browser_tasks import (
    proxy_pool_init_task,
    browser_init_task,
    roxy_browser_init_task,
    navigate_to_signup_task,
    page_load_wait_task,
    proxy_switch_task,
    check_ip_blocked_task
)
from .form_tasks import (
    email_input_task,
    password_input_task,
    username_generate_task,
    username_input_task,
    username_validate_task,
    country_select_task,
    form_submit_task
)
from .captcha_tasks import (
    captcha_detect_task,
    visual_puzzle_button_find_task,
    visual_puzzle_button_click_task,
    captcha_iframe_locate_task,
    captcha_iframe_switch_task,
    captcha_info_extract_task,
    captcha_solve_api_task,
    captcha_answer_submit_task,
    captcha_result_check_task,
    captcha_next_round_task
)
from .email_tasks import (
    email_verification_detect_task,
    email_fetch_task,
    verification_link_extract_task,
    verification_link_click_task,
    verification_code_input_task,
    email_login_task,
    two_factor_auth_task,
    mock_email_login_task,
    registration_complete_check_task
)
from .augment_tasks import (
    augment_navigate_task,
    augment_github_authorize_task,
    augment_payment_setup_task,
    augment_stripe_form_task,
    augment_billing_address_task,
    augment_captcha_detect_task,
    augment_hcaptcha_solve_task,
    augment_form_submit_task,
    augment_token_generation_task,
    augment_code_extract_task,
    augment_access_token_task,
    augment_token_save_task
)

def create_all_tasks():
    """创建所有任务实例"""
    
    tasks = [
        # 阶段-1: 系统初始化
        Task(
            task_id="system_initialization_task",
            name="系统初始化检查",
            handler=system_initialization_task,
            dependencies=[],
            max_retries=0,
            timeout=30.0
        ),

        # 阶段0: 邮箱账号选择
        Task(
            task_id="email_account_select_task",
            name="邮箱账号选择",
            handler=email_account_select_task,
            dependencies=["system_initialization_task"],
            max_retries=0,  # 用户交互任务不重试
            timeout=300.0   # 给用户足够时间选择
        ),

        # 阶段1: 代理池和浏览器初始化（并行）
        # 暂时禁用代理池初始化，使用直连模式
        # Task(
        #     task_id="proxy_pool_init_task",
        #     name="初始化代理池",
        #     handler=proxy_pool_init_task,
        #     dependencies=["email_account_select_task"],
        #     max_retries=1,
        #     timeout=120.0  # 代理池初始化可能需要更长时间
        # ),

        Task(
            task_id="browser_init_task",
            name="启动浏览器",
            handler=browser_init_task,
            dependencies=["email_account_select_task"],  # 不依赖代理池初始化
            max_retries=2,
            timeout=30.0
        ),
        
        Task(
            task_id="navigate_to_signup_task",
            name="导航到注册页面",
            handler=navigate_to_signup_task,
            dependencies=["browser_init_task"],
            max_retries=2,
            timeout=20.0
        ),
        
        Task(
            task_id="page_load_wait_task",
            name="等待页面加载",
            handler=page_load_wait_task,
            dependencies=["navigate_to_signup_task"],
            max_retries=2,
            timeout=15.0
        ),
        
        # 阶段2: 表单填写
        Task(
            task_id="email_input_task",
            name="填写邮箱",
            handler=email_input_task,
            dependencies=["page_load_wait_task"],
            max_retries=2,
            timeout=15.0
        ),
        
        Task(
            task_id="password_input_task",
            name="填写密码",
            handler=password_input_task,
            dependencies=["email_input_task"],
            max_retries=2,
            timeout=15.0
        ),
        
        Task(
            task_id="username_generate_task",
            name="生成用户名",
            handler=username_generate_task,
            dependencies=["password_input_task"],
            max_retries=0,  # 生成失败不重试，直接重新生成
            timeout=5.0
        ),
        
        Task(
            task_id="username_input_task",
            name="填写用户名",
            handler=username_input_task,
            dependencies=["username_generate_task"],
            max_retries=2,
            timeout=15.0
        ),
        
        Task(
            task_id="username_validate_task",
            name="验证用户名",
            handler=username_validate_task,
            dependencies=["username_input_task"],
            max_retries=2,
            timeout=10.0
        ),

        Task(
            task_id="country_select_task",
            name="选择国家/地区",
            handler=country_select_task,
            dependencies=["username_validate_task"],
            max_retries=2,
            timeout=15.0
        ),

        Task(
            task_id="form_submit_task",
            name="提交表单",
            handler=form_submit_task,
            dependencies=["country_select_task"],
            max_retries=2,
            timeout=15.0
        ),
        
        # 阶段3: 验证码处理
        Task(
            task_id="visual_puzzle_button_find_task",
            name="查找Visual puzzle按钮",
            handler=visual_puzzle_button_find_task,
            dependencies=["form_submit_task"],  # 表单提交后直接查找按钮
            max_retries=1,
            timeout=60.0
        ),
        
        Task(
            task_id="visual_puzzle_button_click_task",
            name="点击Visual puzzle按钮",
            handler=visual_puzzle_button_click_task,
            dependencies=["visual_puzzle_button_find_task"],
            max_retries=2,
            timeout=10.0
        ),

        Task(
            task_id="captcha_detect_task",
            name="检测验证码",
            handler=captcha_detect_task,
            dependencies=["visual_puzzle_button_click_task"],  # 点击按钮后才检测验证码
            max_retries=2,
            timeout=20.0
        ),
        
        Task(
            task_id="captcha_iframe_locate_task",
            name="定位验证码iframe",
            handler=captcha_iframe_locate_task,
            dependencies=["visual_puzzle_button_click_task"],
            max_retries=2,
            timeout=15.0
        ),
        
        Task(
            task_id="captcha_iframe_switch_task",
            name="切换到验证码iframe",
            handler=captcha_iframe_switch_task,
            dependencies=["captcha_iframe_locate_task"],
            max_retries=2,
            timeout=10.0
        ),
        
        Task(
            task_id="captcha_info_extract_task",
            name="提取验证码信息",
            handler=captcha_info_extract_task,
            dependencies=["captcha_iframe_switch_task"],
            max_retries=2,
            timeout=15.0
        ),
        
        Task(
            task_id="captcha_solve_api_task",
            name="调用API识别验证码",
            handler=captcha_solve_api_task,
            dependencies=["captcha_info_extract_task"],
            max_retries=1,
            timeout=30.0
        ),
        
        Task(
            task_id="captcha_answer_submit_task",
            name="提交验证码答案",
            handler=captcha_answer_submit_task,
            dependencies=["captcha_solve_api_task"],
            max_retries=2,
            timeout=15.0
        ),
        
        Task(
            task_id="captcha_result_check_task",
            name="检查验证码结果",
            handler=captcha_result_check_task,
            dependencies=["captcha_answer_submit_task"],
            max_retries=2,
            timeout=15.0
        ),
        
        Task(
            task_id="captcha_next_round_task",
            name="处理下一轮验证码",
            handler=captcha_next_round_task,
            dependencies=[],  # 移除依赖，通过next_tasks直接触发
            is_loop_task=True,  # 标记为循环任务，防止初始化时自动入队
            max_retries=1,
            timeout=10.0
        ),
        
        # 阶段4: 邮箱验证
        Task(
            task_id="email_verification_detect_task",
            name="检测邮箱验证",
            handler=email_verification_detect_task,
            dependencies=[],  # 移除固定依赖，通过next_tasks触发
            is_loop_task=True,  # 标记为循环任务，防止初始化时自动入队
            max_retries=5,  # 增加重试次数，因为可能需要等待验证码完成
            timeout=15.0
        ),
        
        Task(
            task_id="email_fetch_task",
            name="获取验证邮件",
            handler=email_fetch_task,
            dependencies=["email_verification_detect_task"],
            max_retries=1,
            timeout=120.0  # 邮件可能需要较长时间到达
        ),

        Task(
            task_id="verification_link_extract_task",
            name="提取验证链接",
            handler=verification_link_extract_task,
            dependencies=["email_fetch_task"],
            max_retries=2,
            timeout=15.0
        ),

        Task(
            task_id="verification_link_click_task",
            name="访问验证链接",
            handler=verification_link_click_task,
            dependencies=["verification_link_extract_task"],
            max_retries=2,
            timeout=20.0
        ),

        Task(
            task_id="verification_code_input_task",
            name="输入验证码",
            handler=verification_code_input_task,
            dependencies=[],  # 通过next_tasks触发
            is_loop_task=True,  # 标记为循环任务，避免自动入队
            max_retries=2,
            timeout=15.0
        ),

        Task(
            task_id="email_login_task",
            name="邮箱登录",
            handler=email_login_task,
            dependencies=[],  # 通过next_tasks触发
            is_loop_task=True,  # 标记为循环任务，避免自动入队
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="two_factor_auth_task",
            name="双重认证",
            handler=two_factor_auth_task,
            dependencies=[],  # 通过next_tasks触发
            is_loop_task=True,  # 标记为循环任务，避免自动入队
            max_retries=2,
            timeout=20.0
        ),



        # Augment注册任务
        Task(
            task_id="augment_navigate_task",
            name="导航到Augment注册页面",
            handler=augment_navigate_task,
            dependencies=[],  # 通过next_tasks触发
            is_loop_task=True,
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_github_authorize_task",
            name="GitHub OAuth授权",
            handler=augment_github_authorize_task,
            dependencies=[],
            is_loop_task=True,
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_payment_setup_task",
            name="设置支付方式",
            handler=augment_payment_setup_task,
            dependencies=[],
            is_loop_task=True,
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_stripe_form_task",
            name="填写Stripe支付表单",
            handler=augment_stripe_form_task,
            dependencies=[],
            is_loop_task=True,
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_billing_address_task",
            name="填写账单地址",
            handler=augment_billing_address_task,
            dependencies=[],
            is_loop_task=True,
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_captcha_detect_task",
            name="检测HCaptcha",
            handler=augment_captcha_detect_task,
            dependencies=[],
            is_loop_task=True,
            max_retries=2,
            timeout=15.0
        ),

        Task(
            task_id="augment_hcaptcha_solve_task",
            name="解决HCaptcha",
            handler=augment_hcaptcha_solve_task,
            dependencies=[],
            is_loop_task=True,
            max_retries=2,
            timeout=300.0  # HCaptcha解决可能需要较长时间
        ),

        Task(
            task_id="augment_form_submit_task",
            name="提交支付表单",
            handler=augment_form_submit_task,
            dependencies=[],
            is_loop_task=True,
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_token_generation_task",
            name="生成OAuth状态并获取授权码",
            handler=augment_token_generation_task,
            dependencies=[],
            is_loop_task=True,
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_code_extract_task",
            name="提取授权码和状态",
            handler=augment_code_extract_task,
            dependencies=[],
            is_loop_task=True,
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_access_token_task",
            name="获取访问令牌",
            handler=augment_access_token_task,
            dependencies=[],
            is_loop_task=True,
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_token_save_task",
            name="保存令牌到文件",
            handler=augment_token_save_task,
            dependencies=[],
            is_loop_task=True,
            max_retries=1,
            timeout=15.0
        ),

        Task(
            task_id="mock_email_login_task",
            name="Mock邮箱登录",
            handler=mock_email_login_task,
            dependencies=[],  # 通过next_tasks触发
            is_loop_task=True,  # 标记为循环任务，避免自动入队
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="registration_complete_check_task",
            name="检查注册完成",
            handler=registration_complete_check_task,
            dependencies=[],  # 通过next_tasks触发
            is_loop_task=True,  # 标记为循环任务，避免自动入队
            max_retries=2,
            timeout=15.0
        ),

        # 代理管理任务
        Task(
            task_id="check_ip_blocked_task",
            name="检查IP是否被屏蔽",
            handler=check_ip_blocked_task,
            dependencies=[],  # 可以在任何时候调用
            is_loop_task=True,  # 标记为循环任务
            max_retries=1,
            timeout=10.0
        ),

        Task(
            task_id="proxy_switch_task",
            name="切换代理",
            handler=proxy_switch_task,
            dependencies=[],  # 通过next_tasks触发
            is_loop_task=True,  # 标记为循环任务
            max_retries=2,
            timeout=30.0
        )
    ]
    
    return tasks

def get_task_dependency_graph():
    """获取任务依赖关系图（用于文档和调试）"""
    tasks = create_all_tasks()
    
    dependency_graph = {}
    for task in tasks:
        dependency_graph[task.task_id] = {
            'name': task.name,
            'dependencies': task.dependencies,
            'max_retries': task.max_retries,
            'timeout': task.timeout
        }
    
    return dependency_graph

def print_task_dependency_tree():
    """打印任务依赖树（调试用）"""
    graph = get_task_dependency_graph()
    
    print("任务依赖关系树:")
    print("=" * 50)
    
    # 找到根任务（没有依赖的任务）
    root_tasks = [task_id for task_id, info in graph.items() if not info['dependencies']]
    
    def print_task_tree(task_id, level=0):
        indent = "  " * level
        task_info = graph[task_id]
        print(f"{indent}- {task_info['name']} ({task_id})")
        
        # 找到依赖此任务的其他任务
        dependent_tasks = [
            tid for tid, info in graph.items() 
            if task_id in info['dependencies']
        ]
        
        for dep_task in dependent_tasks:
            print_task_tree(dep_task, level + 1)
    
    for root_task in root_tasks:
        print_task_tree(root_task)

def create_github_tasks():
    """创建GitHub注册任务"""
    return [
        # 初始化任务 - 暂时禁用代理池
        # Task(
        #     task_id="proxy_pool_init_task",
        #     name="代理池初始化",
        #     handler=proxy_pool_init_task,
        #     dependencies=[],
        #     max_retries=1,
        #     timeout=30.0
        # ),

        Task(
            task_id="browser_init_task",
            name="启动浏览器",
            handler=browser_init_task,
            dependencies=[],  # 不依赖代理池初始化
            max_retries=2,
            timeout=60.0
        ),

        Task(
            task_id="navigate_to_signup_task",
            name="导航到注册页面",
            handler=navigate_to_signup_task,
            dependencies=["browser_init_task"],
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="page_load_wait_task",
            name="等待页面加载",
            handler=page_load_wait_task,
            dependencies=["navigate_to_signup_task"],
            max_retries=1,
            timeout=15.0
        ),

        # 表单填写任务
        Task(
            task_id="email_input_task",
            name="输入邮箱",
            handler=email_input_task,
            dependencies=["page_load_wait_task"],
            max_retries=2,
            timeout=20.0
        ),

        Task(
            task_id="password_input_task",
            name="输入密码",
            handler=password_input_task,
            dependencies=["email_input_task"],
            max_retries=2,
            timeout=20.0
        ),

        Task(
            task_id="username_generate_task",
            name="生成用户名",
            handler=username_generate_task,
            dependencies=["password_input_task"],
            max_retries=0,  # 生成失败不重试，直接重新生成
            timeout=5.0
        ),

        Task(
            task_id="username_input_task",
            name="输入用户名",
            handler=username_input_task,
            dependencies=["username_generate_task"],
            max_retries=3,
            timeout=30.0
        ),

        Task(
            task_id="country_select_task",
            name="选择国家/地区",
            handler=country_select_task,
            dependencies=["username_input_task"],
            max_retries=2,
            timeout=20.0
        ),

        Task(
            task_id="form_submit_task",
            name="提交表单",
            handler=form_submit_task,
            dependencies=["country_select_task"],
            max_retries=2,
            timeout=30.0
        ),

        # 验证码处理任务
        Task(
            task_id="captcha_detect_task",
            name="检测验证码",
            handler=captcha_detect_task,
            dependencies=["form_submit_task"],
            max_retries=1,
            timeout=10.0
        ),

        Task(
            task_id="captcha_solve_task",
            name="解决验证码",
            handler=captcha_solve_api_task,
            dependencies=[],  # 通过next_tasks触发
            is_loop_task=True,  # 标记为循环任务，避免自动入队
            max_retries=3,
            timeout=120.0
        ),

        Task(
            task_id="captcha_next_round_task",
            name="验证码下一轮",
            handler=captcha_next_round_task,
            dependencies=[],  # 通过next_tasks触发
            is_loop_task=True,  # 标记为循环任务，避免自动入队
            max_retries=1,
            timeout=10.0
        ),

        # 邮箱验证任务
        Task(
            task_id="email_verification_detect_task",
            name="检测邮箱验证页面",
            handler=email_verification_detect_task,
            dependencies=["captcha_detect_task"],
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="email_fetch_task",
            name="获取验证邮件",
            handler=email_fetch_task,
            dependencies=["email_verification_detect_task"],
            max_retries=1,
            timeout=120.0  # 邮件可能需要较长时间到达
        ),

        Task(
            task_id="verification_link_extract_task",
            name="提取验证链接",
            handler=verification_link_extract_task,
            dependencies=["email_fetch_task"],
            max_retries=2,
            timeout=15.0
        ),

        Task(
            task_id="verification_link_click_task",
            name="访问验证链接",
            handler=verification_link_click_task,
            dependencies=["verification_link_extract_task"],
            max_retries=2,
            timeout=20.0
        ),

        Task(
            task_id="verification_code_input_task",
            name="输入验证码",
            handler=verification_code_input_task,
            dependencies=["verification_link_click_task"],
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="email_login_task",
            name="邮箱登录",
            handler=email_login_task,
            dependencies=["verification_code_input_task"],
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="registration_complete_check_task",
            name="检查注册完成状态",
            handler=registration_complete_check_task,
            dependencies=["email_login_task"],
            max_retries=1,
            timeout=15.0
        ),


    ]

def create_augment_tasks():
    """创建Augment注册任务"""
    return [
        # 初始化任务 - 暂时禁用代理池，使用普通浏览器
        # Task(
        #     task_id="proxy_pool_init_task",
        #     name="代理池初始化",
        #     handler=proxy_pool_init_task,
        #     dependencies=[],
        #     max_retries=1,
        #     timeout=30.0
        # ),

        Task(
            task_id="browser_init_task",
            name="启动RoxyBrowser",
            handler=roxy_browser_init_task,
            dependencies=[],
            max_retries=2,
            timeout=60.0
        ),

        # Augment注册任务
        Task(
            task_id="augment_navigate_task",
            name="导航到Augment注册页面",
            handler=augment_navigate_task,
            dependencies=["browser_init_task"],
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_github_authorize_task",
            name="GitHub登录授权",
            handler=augment_github_authorize_task,
            dependencies=["augment_navigate_task"],
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_payment_setup_task",
            name="设置支付方式",
            handler=augment_payment_setup_task,
            dependencies=["augment_github_authorize_task"],
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_stripe_form_task",
            name="填写Stripe支付表单",
            handler=augment_stripe_form_task,
            dependencies=["augment_payment_setup_task"],
            max_retries=2,
            timeout=60.0
        ),

        Task(
            task_id="augment_billing_address_task",
            name="填写账单地址",
            handler=augment_billing_address_task,
            dependencies=["augment_stripe_form_task"],
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_captcha_detect_task",
            name="检测HCaptcha",
            handler=augment_captcha_detect_task,
            dependencies=["augment_billing_address_task"],
            max_retries=1,
            timeout=10.0
        ),

        Task(
            task_id="augment_hcaptcha_solve_task",
            name="解决HCaptcha",
            handler=augment_hcaptcha_solve_task,
            dependencies=[],
            is_loop_task=True,
            max_retries=2,
            timeout=120.0
        ),

        Task(
            task_id="augment_form_submit_task",
            name="提交Augment表单",
            handler=augment_form_submit_task,
            dependencies=["augment_captcha_detect_task"],
            max_retries=2,
            timeout=30.0
        ),

        Task(
            task_id="augment_token_generation_task",
            name="生成OAuth令牌",
            handler=augment_token_generation_task,
            dependencies=["augment_form_submit_task"],
            max_retries=2,
            timeout=60.0
        ),

        Task(
            task_id="augment_code_extract_task",
            name="提取授权码",
            handler=augment_code_extract_task,
            dependencies=["augment_token_generation_task"],
            max_retries=2,
            timeout=30.0
        ),
    ]

if __name__ == "__main__":
    print_task_dependency_tree()
