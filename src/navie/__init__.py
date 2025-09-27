#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Navie - GitHub自动注册系统
主包初始化文件
"""

__version__ = "1.0.0"
__author__ = "Navie Team"
__description__ = "GitHub自动注册系统"

# 导出主要组件
from .core.event_bus import EventBus
from .core.state_manager import StateManager
from .core.task_manager import TaskManager

__all__ = [
    'EventBus',
    'StateManager', 
    'TaskManager'
]
