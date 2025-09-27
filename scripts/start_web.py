#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动Web管理界面
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from navie.web.email_web_manager import app

if __name__ == '__main__':
    print("🚀 启动 Navie 邮箱管理器...")
    print("📧 访问地址: http://localhost:5000")
    print("🗄️ 确保PostgreSQL数据库正在运行")
    app.run(host='0.0.0.0', port=5000, debug=True)
