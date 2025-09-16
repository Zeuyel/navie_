"""
日志工具
"""
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_LEVEL, LOG_FORMAT

def setup_logger(name: str) -> logging.Logger:
    """设置日志记录器 - 不添加处理器，使用根日志记录器的配置"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # 不添加处理器，让子日志记录器使用根日志记录器的处理器
    # 这样避免重复日志输出

    return logger
