"""
日志工具函数
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path


class LoggingUtils:
    """日志工具类"""

    @staticmethod
    def setup_logging(
        log_dir: str = "logs",
        log_level: str = "INFO",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """
        设置日志系统

        Args:
            log_dir: 日志目录
            log_level: 日志级别
            max_bytes: 单个日志文件最大大小
            backup_count: 备份文件数量

        Returns:
            配置好的logger
        """
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)

        # 获取根logger
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, log_level.upper()))

        # 清除现有的handler
        logger.handlers.clear()

        # 控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 文件handler - 应用程序日志
        app_log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 错误日志handler
        error_log_file = os.path.join(log_dir, f"error_{datetime.now().strftime('%Y%m%d')}.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)

        # 设置第三方库的日志级别
        logging.getLogger('pdfplumber').setLevel(logging.WARNING)
        logging.getLogger('openai').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

        return logger

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        获取指定名称的logger

        Args:
            name: logger名称

        Returns:
            logger实例
        """
        return logging.getLogger(name)

    @staticmethod
    def log_exception(logger: logging.Logger, exception: Exception, context: str = ""):
        """
        记录异常信息

        Args:
            logger: logger实例
            exception: 异常对象
            context: 上下文信息
        """
        if context:
            logger.error(f"{context}: {str(exception)}", exc_info=True)
        else:
            logger.error(str(exception), exc_info=True)

    @staticmethod
    def log_performance(logger: logging.Logger, operation: str, duration: float):
        """
        记录性能信息

        Args:
            logger: logger实例
            operation: 操作名称
            duration: 持续时间（秒）
        """
        logger.info(f"性能 - {operation}: {duration:.3f}秒")

    @staticmethod
    def log_memory_usage(logger: logging.Logger):
        """
        记录内存使用情况

        Args:
            logger: logger实例
        """
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            logger.debug(f"内存使用 - RSS: {memory_info.rss / 1024 / 1024:.1f} MB, "
                        f"VMS: {memory_info.vms / 1024 / 1024:.1f} MB")
        except ImportError:
            pass

    @staticmethod
    def create_audit_logger(log_dir: str = "logs") -> logging.Logger:
        """
        创建审计日志logger

        Args:
            log_dir: 日志目录

        Returns:
            审计日志logger
        """
        os.makedirs(log_dir, exist_ok=True)

        audit_logger = logging.getLogger("audit")
        audit_logger.setLevel(logging.INFO)

        # 审计日志文件
        audit_log_file = os.path.join(log_dir, f"audit_{datetime.now().strftime('%Y%m%d')}.log")
        audit_handler = logging.FileHandler(audit_log_file, encoding='utf-8')
        audit_handler.setLevel(logging.INFO)

        # 审计日志格式
        audit_formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        audit_handler.setFormatter(audit_formatter)

        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False  # 不传播到根logger

        return audit_logger

    @staticmethod
    def log_audit_event(audit_logger: logging.Logger, event_type: str, user: str, details: str):
        """
        记录审计事件

        Args:
            audit_logger: 审计日志logger
            event_type: 事件类型
            user: 用户标识
            details: 事件详情
        """
        audit_logger.info(f"EVENT:{event_type} - USER:{user} - DETAILS:{details}")

    @staticmethod
    def cleanup_old_logs(log_dir: str, days_to_keep: int = 30):
        """
        清理旧日志文件

        Args:
            log_dir: 日志目录
            days_to_keep: 保留天数
        """
        import time
        if not os.path.exists(log_dir):
            return

        current_time = time.time()
        cutoff_time = current_time - (days_to_keep * 24 * 3600)

        for filename in os.listdir(log_dir):
            file_path = os.path.join(log_dir, filename)
            try:
                file_mtime = os.path.getmtime(file_path)
                if file_mtime < cutoff_time:
                    os.remove(file_path)
            except Exception as e:
                logging.error(f"清理旧日志失败 {file_path}: {e}")

    @staticmethod
    def get_log_file_paths(log_dir: str) -> dict:
        """
        获取日志文件路径

        Args:
            log_dir: 日志目录

        Returns:
            日志文件路径字典
        """
        if not os.path.exists(log_dir):
            return {}

        log_files = {}
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                file_type = filename.split('_')[0]
                log_files[file_type] = os.path.join(log_dir, filename)

        return log_files

    @staticmethod
    def log_system_info(logger: logging.Logger):
        """
        记录系统信息

        Args:
            logger: logger实例
        """
        import platform
        import sys

        system_info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "working_directory": os.getcwd(),
            "user": os.getenv("USERNAME") or os.getenv("USER")
        }

        logger.info("系统信息:")
        for key, value in system_info.items():
            logger.info(f"  {key}: {value}")

    @staticmethod
    def create_timed_rotating_logger(
        name: str,
        log_dir: str = "logs",
        when: str = "midnight",
        interval: int = 1,
        backup_count: int = 30
    ) -> logging.Logger:
        """
        创建按时间轮转的logger

        Args:
            name: logger名称
            log_dir: 日志目录
            when: 轮转时间（'S', 'M', 'H', 'D', 'midnight'）
            interval: 轮转间隔
            backup_count: 备份文件数量

        Returns:
            logger实例
        """
        os.makedirs(log_dir, exist_ok=True)

        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        log_file = os.path.join(log_dir, f"{name}.log")
        handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding='utf-8'
        )

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.propagate = False

        return logger