"""
Dual logging system for CFST Data Extractor
Provides both console output (brief) and file output (detailed)
"""

import logging
import sys
from pathlib import Path


def setup_logger(log_file=None, console_level=logging.INFO, file_level=logging.DEBUG):
    """
    Configure dual logging system with console and file outputs.

    Args:
        log_file: Path to log file. If None, only console output is used.
        console_level: Logging level for console output (default: INFO)
        file_level: Logging level for file output (default: DEBUG)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('cfst_extractor')
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers to avoid duplication
    logger.handlers.clear()

    # Console Handler (increased information - show full page lists)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler (detailed - include all API interactions)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(exist_ok=True, parents=True)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(file_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
