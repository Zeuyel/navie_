# GitHub自动注册系统 V2 - 单一+批量双模式

## 🎯 项目概述

GitHub自动注册系统V2采用**任务队列+事件驱动混合架构**，将复杂的注册流程分解为27个细粒度任务，实现真正的异步事件驱动机制。系统包含独立的邮箱管理工具，支持多邮箱账号管理和智能切换。

**🆕 V2.1 新增特性**：
- 🚀 **批量异步处理模式** - 支持多个email_token并发处理
- 🌐 **浏览器实例池** - 智能复用浏览器资源，降低内存消耗
- ⚡ **简单异步方案** - 基于asyncio.gather的轻量级并发
- 📊 **批量统计报告** - 详细的批量处理统计和结果导出

## ✨ 核心特性

- 🔄 **真正的事件驱动**: 每个小步骤都通过事件触发，彻底解决同步阻塞问题
- 📋 **细粒度任务**: 27个独立任务，每个任务职责单一，易于调试和维护
- 🎛️ **智能任务管理**: 自动处理任务依赖关系、重试机制和超时控制
- 📊 **完整监控**: 事件历史、状态转换、任务执行状态全程追踪
- 🔧 **灵活配置**: 生产环境快速失败，开发环境支持重试调试
- 📧 **邮箱管理**: 独立的邮箱管理工具，支持多账号CRUD和智能切换
- 🚀 **双模式运行**: 单一注册模式 + 批量异步处理模式

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EventBus      │    │  StateManager   │    │  TaskManager    │
│   事件总线       │◄──►│   状态管理器     │◄──►│   任务管理器     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        27个细粒度任务                            │
│  system_init → email_select → browser_init → navigate → ...     │
└─────────────────────────────────────────────────────────────────┘
```

## 🧩 核心组件详解

### 1. EventBus (事件总线)

**核心职责**: 作为系统的神经中枢，负责所有组件间的事件通信和协调。

**主要功能特性**:
- 🔄 **异步事件发布订阅**: 支持完全异步的事件处理机制
- ⚡ **事件优先级管理**: 关键事件可优先处理，确保系统响应性
- 🔧 **中间件支持**: 可插拔的事件处理中间件，支持日志、验证等
- 📚 **事件历史记录**: 保存最近1000个事件，便于调试和分析
- 🎯 **条件订阅**: 支持基于条件的智能事件订阅

**关键方法**:
```python
# 订阅事件
event_bus.subscribe('task_completed', handler, priority=EventPriority.HIGH)

# 发布事件
await event_bus.publish(create_event(
    name='browser_ready',
    data={'url': 'https://github.com/join'},
    source='BrowserTask'
))

# 发布并等待所有处理器完成
results = await event_bus.publish_and_wait(event, timeout=30.0)
```

**架构重要性**: EventBus是实现真正事件驱动架构的基石，它解耦了各个组件，使得任务间可以通过事件进行松耦合通信，大大提高了系统的可维护性和扩展性。

### 2. StateManager (状态管理器)

**核心职责**: 维护系统的全局状态，管理状态转换，确保系统状态的一致性和可追溯性。

**主要功能特性**:
- 🔄 **状态转换验证**: 确保只有合法的状态转换才能执行
- 📊 **状态历史追踪**: 记录所有状态变更的完整历史
- 🎯 **状态监听器**: 支持对特定状态变化的监听和响应
- 💾 **状态数据管理**: 统一管理跨任务的共享数据
- 📤 **状态导出**: 支持状态数据的序列化和导出

**状态流转图**:
```
INIT → BROWSER_INITIALIZING → BROWSER_READY → FORM_FILLING →
FORM_SUBMITTED → CAPTCHA_PENDING → CAPTCHA_SOLVING →
CAPTCHA_COMPLETED → EMAIL_VERIFICATION → COMPLETED
```

**关键方法**:
```python
# 状态转换
await state_manager.transition_to(
    RegistrationState.CAPTCHA_SOLVING,
    trigger_event='captcha_detected'
)

# 数据管理
state_manager.set_data('browser_instance', browser)
browser = state_manager.get_data('browser_instance')

# 添加状态监听器
state_manager.add_state_listener(
    RegistrationState.COMPLETED,
    on_registration_complete
)
```

**架构重要性**: StateManager确保了复杂异步流程中状态的一致性，通过状态转换验证避免了状态混乱，是系统稳定性的重要保障。

### 3. TaskManager (任务管理器)

**核心职责**: 负责任务的调度、执行、依赖管理和生命周期控制，是系统执行引擎的核心。

**主要功能特性**:
- 📋 **任务队列管理**: 智能的任务队列调度和执行
- 🔗 **依赖关系处理**: 自动解析和处理任务间的复杂依赖关系
- 🔄 **重试机制**: 灵活的任务重试策略，支持不同环境配置
- ⏱️ **超时控制**: 任务级别的精确超时管理
- 🎛️ **并发控制**: 可配置的任务并发执行数量

**任务生命周期**:
```
PENDING → RUNNING → COMPLETED
    ↓         ↓         ↑
CANCELLED  FAILED → RETRY (可选)
```

**关键方法**:
```python
# 注册任务
task_manager.register_task(Task(
    task_id="email_input_task",
    name="填写邮箱",
    handler=email_input_handler,
    dependencies=["page_load_wait_task"],
    max_retries=2,
    timeout=15.0
))

# 启动任务管理器
await task_manager.start()

# 获取任务状态
status = task_manager.get_task_status("email_input_task")
all_status = task_manager.get_all_tasks_status()
```

**使用场景示例**:
```python
# 任务函数实现
async def email_input_task(state_manager, event_bus):
    browser = state_manager.get_data('browser_instance')

    # 执行任务逻辑
    email_input = browser.driver.find_element(By.ID, "email")
    email_input.send_keys(TEMP_EMAIL)

    # 发布事件
    await event_bus.publish(create_event(
        name='email_filled',
        data={'email': TEMP_EMAIL},
        source='email_input_task'
    ))

    # 返回任务结果
    return TaskResult(
        success=True,
        data={'email': TEMP_EMAIL},
        next_tasks=['password_input_task']
    )
```

**架构重要性**: TaskManager是系统的执行引擎，它将复杂的业务流程分解为可管理的任务单元，通过依赖管理和智能调度，确保了系统的高效执行和可靠性。

### 🔄 组件协作机制

三个核心组件通过以下方式协同工作：

1. **TaskManager** 执行任务并通过 **EventBus** 发布事件
2. **StateManager** 监听事件并更新系统状态
3. **EventBus** 将状态变更事件广播给相关组件
4. **TaskManager** 根据任务结果和状态变化调度下一个任务

这种设计实现了高度解耦的异步架构，每个组件都可以独立测试和优化，同时保持了整体系统的协调性和一致性。

## 📁 项目结构

```
├── core/                          # 核心架构组件
│   ├── event_bus.py              # 事件总线（支持优先级、中间件）
│   ├── state_manager.py          # 状态管理器（状态转换验证）
│   └── task_manager.py           # 任务管理器（队列、依赖、重试）
├── tasks/                         # 任务实现
│   ├── initial_tasks.py          # 初始化任务（2个）
│   ├── browser_tasks.py          # 浏览器相关任务（3个）
│   ├── form_tasks.py             # 表单填写任务（6个）
│   ├── captcha_tasks.py          # 验证码处理任务（11个）
│   ├── email_tasks.py            # 邮箱验证任务（5个）
│   └── task_registry.py          # 任务注册器（依赖关系定义）
├── utils/                         # 工具模块
│   ├── browser.py                # 浏览器管理器
│   ├── captcha.py                # YesCaptcha API集成
│   └── email_manager.py          # 邮箱管理器
├── email_receiver.py             # 独立邮件收件工具
├── email_manager_cli.py          # 独立邮箱管理工具
├── github_signup_v2.py           # 主程序
├── email_config.json             # 邮箱配置文件
├── config.py                     # 配置文件
├── ARCHITECTURE.md               # 详细架构文档
└── README.md                     # 项目说明
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置邮箱
使用邮箱管理工具添加邮箱账号：
```bash
# 使用邮箱管理工具
python email_manager_cli.py

# 或者复制示例配置文件手动编辑
cp email_config.json.example email_config.json
```

邮箱账号格式：`邮箱----密码----client_id----令牌`

### 3. 运行程序

#### 3.1 单一注册模式
```bash
# 运行主程序（包含邮箱选择界面）
python github_signup_v2.py

# 或者使用独立的邮件收件工具
python email_receiver.py
```

#### 3.2 批量异步处理模式 🆕
支持多个email_token的并发处理，适合快速批量操作：

```bash
# 从文件批量处理（推荐）
python batch_cli.py --file tokens.txt --concurrent 3

# 直接指定tokens
python batch_cli.py --tokens "email1----pass1----client1----token1,email2----pass2----client2----token2" --concurrent 3

# 高级选项
python batch_cli.py --file tokens.txt --concurrent 5 --browser-pool 3 --output results.json --verbose

# 验证tokens格式（不实际执行）
python batch_cli.py --file tokens.txt --dry-run
```

**tokens文件格式** (`tokens.txt`):
```text
# 每行一个email_token，格式：email----password----client_id----access_token
test1@outlook.com----password123----client_id1----access_token1
test2@outlook.com----password456----client_id2----access_token2
test3@outlook.com----password789----client_id3----access_token3

# 注释行以#开头会被忽略
# 空行也会被忽略
```

**批量处理参数说明**:
- `--concurrent`: 最大并发数（默认3，建议3-5）
- `--browser-pool`: 浏览器实例池大小（默认3）
- `--output`: 结果输出文件（JSON格式）
- `--verbose`: 详细日志输出
- `--dry-run`: 验证模式，不实际执行

**性能预期**:
- 最大并发: 3-5个Session
- 适合任务量: 10-50个
- 资源需求: 2-4GB RAM
- 平均处理时间: 2-5分钟/个（含防检测延迟）

### 4. 查看任务依赖关系
```bash
python tasks/task_registry.py
```

## �️ 独立工具

### 邮箱管理工具 (email_manager_cli.py)
独立的邮箱账号管理工具，支持完整的CRUD操作：

```bash
python email_manager_cli.py
```

**功能特性**:
- ✅ 列出所有邮箱账号
- ✅ 添加邮箱账号（支持字符串格式）
- ✅ 删除邮箱账号
- ✅ 更新邮箱账号信息
- ✅ 设置当前使用的邮箱账号
- ✅ 测试邮箱连接

### 邮件收件工具 (email_receiver.py)
独立的邮件接收工具，从当前邮箱账号中收取邮件：

```bash
python email_receiver.py
```

**功能特性**:
- ✅ 获取最新邮件（显示完整内容）
- ✅ 搜索邮件（按主题、发件人、时间过滤）
- ✅ 获取验证码（GitHub等平台）
- ✅ 切换邮箱账号
- ✅ 显示当前账号信息

## �📋 任务流程

### 阶段-1: 系统初始化 (1个任务)
1. **system_initialization_task** - 系统初始化检查

### 阶段0: 邮箱选择 (1个任务)
2. **email_account_select_task** - 邮箱账号选择入口

### 阶段1: 浏览器初始化 (3个任务)
3. **browser_init_task** - 启动浏览器
4. **navigate_to_signup_task** - 导航到注册页面
5. **page_load_wait_task** - 等待页面完全加载

### 阶段2: 表单填写 (6个任务)
6. **email_input_task** - 定位并填写邮箱字段
7. **password_input_task** - 定位并填写密码字段
8. **username_generate_task** - 生成用户名
9. **username_input_task** - 填写用户名
10. **username_validate_task** - 验证用户名可用性
11. **form_submit_task** - 提交表单

### 阶段3: 验证码处理 (11个任务)
12. **captcha_detect_task** - 检测是否出现验证码
13. **visual_puzzle_button_find_task** - 查找Visual puzzle按钮
14. **visual_puzzle_button_click_task** - 点击按钮
15. **captcha_iframe_locate_task** - 定位验证码iframe
16. **captcha_iframe_switch_task** - 切换到验证码iframe
17. **captcha_info_extract_task** - 提取验证码题目和图片
18. **captcha_image_download_task** - 下载验证码图片
19. **captcha_solve_api_task** - 调用YesCaptcha API识别
20. **captcha_answer_submit_task** - 提交验证码答案
21. **captcha_result_check_task** - 检查验证码结果
22. **captcha_next_round_task** - 处理下一轮验证码(支持多轮)

### 阶段4: 邮箱验证 (5个任务)
23. **email_verification_detect_task** - 检测邮箱验证页面
24. **email_fetch_task** - 获取验证邮件
25. **verification_link_extract_task** - 提取验证链接
26. **verification_link_click_task** - 点击验证链接
27. **registration_complete_check_task** - 检查注册完成状态

## 🔄 事件驱动机制

### 核心事件流
```
browser_init_started → browser_ready → form_filling_started → 
form_submitted → captcha_detected → captcha_solving_started → 
captcha_completed → email_verification_required → registration_completed
```

### 任务依赖示例
```
browser_init_task → navigate_to_signup_task → page_load_wait_task →
email_input_task → password_input_task → username_generate_task →
username_input_task → username_validate_task → form_submit_task →
captcha_detect_task → ...
```

## 🎛️ 配置选项

### 重试策略
- **生产环境**: `max_retries = 0` (快速失败)
- **开发环境**: `max_retries = 1-2` (允许重试调试)

### 超时控制
- **短任务**: 5-15秒 (表单填写、点击等)
- **中等任务**: 20-30秒 (页面加载、API调用)
- **长任务**: 60-120秒 (邮件获取、复杂查找)

### 并发控制
- `max_concurrent_tasks = 1` (注册流程需要严格顺序)

## 📊 监控与调试

### 自动生成日志
程序运行时会自动生成带时间戳的日志文件：
```
github_signup_YYYYMMDD_HHMMSS.log
```

### 状态报告
程序结束后自动打印详细状态报告，包括：
- 当前状态信息
- 任务执行状态
- 事件总线统计
- 失败任务详情

### 调试功能
- 事件历史记录（最近1000个事件）
- 状态转换历史
- 任务执行时间统计
- 详细的错误信息

## 🎯 架构优势

1. **高度模块化**: 每个任务职责单一，易于测试和维护
2. **真正异步**: 彻底解决同步阻塞问题，提高执行效率
3. **灵活重试**: 可针对不同环境和任务类型配置重试策略
4. **完整追踪**: 所有操作都有事件记录，便于调试和分析
5. **状态管理**: 清晰的状态转换，避免状态混乱
6. **易于扩展**: 新增任务只需实现handler函数并注册即可

## 🔧 开发指南

### 添加新任务
1. 在对应的tasks文件中实现任务函数
2. 在`task_registry.py`中注册任务
3. 定义任务依赖关系
4. 配置重试和超时参数

### 添加新事件
1. 在任务中使用`event_bus.publish()`发布事件
2. 在`state_manager.py`中添加状态转换规则
3. 在其他组件中订阅事件

## 📚 详细文档

- [架构文档](ARCHITECTURE.md) - 详细的系统架构说明
- [任务依赖关系图](tasks/task_registry.py) - 运行查看完整依赖关系

## 🎉 更新日志

### V2.1.0 (当前版本) 🆕
- ✅ 新增批量异步处理模式，支持多email_token并发
- ✅ 实现浏览器实例池，优化资源利用
- ✅ 添加批量处理CLI工具 (`batch_cli.py`)
- ✅ 支持批量统计报告和结果导出
- ✅ 基于asyncio.gather的轻量级并发架构
- ✅ 智能资源复用和防检测延迟平衡

### V2.0.0
- ✅ 重构为任务队列+事件驱动架构
- ✅ 实现25个细粒度任务
- ✅ 添加完整的监控和调试功能
- ✅ 支持灵活的重试和超时配置
- ✅ 真正的异步事件驱动机制

### V1.0.0 (已废弃)
- ❌ 传统的handler架构
- ❌ 大步骤异步，小步骤同步
- ❌ 分支逻辑判断混乱

## 🔧 技术栈
- **Python 3.12** - 主要编程语言
- **Selenium** - 浏览器自动化
- **asyncio** - 异步编程
- **YesCaptcha API** - 验证码识别服务
- **临时邮箱服务** - 邮箱验证

## ⚠️ 注意事项
- 需要稳定的网络连接
- 验证码识别依赖第三方API
- 建议在测试环境中运行
- 请遵守GitHub的使用条款和相关法律法规
