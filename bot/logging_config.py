import logging
import os
from logging.handlers import RotatingFileHandler

LOG_FILE = "trading_bot.log"
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 3


def setup_logging(log_file: str = LOG_FILE, level: int = logging.DEBUG) -> logging.Logger:
    """Configure root logger with both file and console handlers."""
    logger = logging.getLogger("trading_bot")

    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler — keeps the log from growing unbounded
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler — INFO and above only so the terminal stays readable
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the trading_bot namespace."""
    return logging.getLogger(f"trading_bot.{name}")
