"""
日志配置
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..config import settings


def setup_logging():
    """配置日志系统"""
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 创建日志文件路径
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"agent_{date_str}.log"

    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器

    Args:
        name: 日志器名称

    Returns:
        日志器实例
    """
    return logging.getLogger(name)


class LoggerMixin:
    """日志器混入类"""

    @property
    def logger(self) -> logging.Logger:
        """获取该类的日志器"""
        return get_logger(self.__class__.__name__)
