# Navie - GitHub自动注册系统

基于PostgreSQL的分布式GitHub自动注册系统，采用现代化的项目结构和Web管理界面。

## 🚀 功能特性

- 📧 邮箱账户管理（支持Outlook/Hotmail/Gmail）
- 🗄️ PostgreSQL数据库集成
- 🌐 现代化Web管理界面
- 🔧 CLI工具支持
- 📊 数据统计和监控
- 🔐 2FA支持
- 🚩 账户状态管理

## 📁 项目结构

```
navie_/
├── src/navie/           # 主包代码
│   ├── core/           # 核心组件
│   ├── tasks/          # 任务模块
│   ├── utils/          # 工具模块
│   ├── services/       # 服务模块
│   └── web/            # Web界面
├── config/             # 配置文件
├── scripts/            # 脚本文件
├── data/               # 数据文件
├── requirements/       # 依赖管理
└── logs/               # 日志文件
```

## 🛠️ 安装配置

### 1. 环境要求
- Python 3.8+
- PostgreSQL 13+

### 2. 安装依赖
```bash
# 基础依赖
pip install -r requirements/base.txt

# 开发环境依赖
pip install -r requirements/dev.txt
```

### 3. 数据库配置
```bash
# 创建数据库和用户
createdb github_account
createuser github_signup_user

# 导入数据库架构
psql -f data/email_accounts_schema.sql -d github_account -U github_signup_user
```

### 4. 数据迁移
```bash
python scripts/migrate_json_to_db.py
```

## 🚀 启动服务

### Web管理界面
```bash
python scripts/start_web.py
```
访问地址: http://localhost:5000

### CLI工具
```bash
python scripts/email_manager_cli.py
```

## 📊 Web界面功能

- ✅ 账户列表展示和搜索
- ✅ 添加/编辑/删除账户
- ✅ 账户状态管理（标记/取消标记）
- ✅ 当前账户设置
- ✅ 数据统计面板
- ✅ 2FA支持显示

## 🔧 开发

### 安装开发环境
```bash
pip install -e .
pip install -r requirements/dev.txt
```

### 代码格式化
```bash
black src/
isort src/
flake8 src/
```

## 📝 配置说明

数据库连接配置在 `config/config.py` 中：
```python
DATABASE_URL = "postgresql://github_signup_user:GhSignup2024!@localhost:5432/github_account"
```