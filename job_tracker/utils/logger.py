"""
Logging Configuration
Centralized logging setup for the application.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None, log_to_console: bool = True) -> None:
    """
    Configure logging for the entire application.
    Call this ONCE at application startup.

    :param log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :param log_file: Path to log file (optional)
    :param log_to_console: Whether to also print logs to console
    :return: None
    """
    # Convert string log_level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    if log_file is None:
        env_log_file = os.getenv("LOG_FILE")
        if env_log_file:
            log_file = env_log_file

    # Create custom formatters for file output
    detailed_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                           datefmt='%Y-%m-%d %H:%M:%S')

    # Simple formatter for console output
    simple_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                         datefmt='%Y-%m-%d %H:%M:%S')

    # Get root logger and set level
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add a console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)

    # Add a file handler if log_file is provided
    if log_file:
        # Create parent directories if they don't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    :param name: Name of the logger (typically pass __name__ from the calling module)
    :return: Logger instance for the module

    Example:
        logger = get_logger(__name__)
        logger.info("This is a message from my module")
    """
    return logging.getLogger(name)
