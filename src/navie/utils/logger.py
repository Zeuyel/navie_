"""
日志工具
"""
import logging
import sys
import os

def setup_logger(name: str) -> logging.Logger:
    """设置日志记录器 - 不添加处理器，使用根日志记录器的配置"""
    logger = logging.getLogger(name)

    # 尝试从config导入日志配置，失败时使用默认值
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from config import LOG_LEVEL, LOG_FORMAT
        logger.setLevel(getattr(logging, LOG_LEVEL))
    except ImportError:
        # 使用默认日志级别
        logger.setLevel(logging.INFO)

    # 不添加处理器，让子日志记录器使用根日志记录器的处理器
    # 这样避免重复日志输出

    return logger
