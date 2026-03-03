"""
Database logging configuration and performance monitoring.

Provides centralized logging for database operations with execution metrics,
performance tracking, and structured log output to both file and console.
"""

import logging
import time
from functools import wraps
from typing import Callable, Any, Optional
from pathlib import Path


class DatabaseLogger:
    """
    Centralized database logging with performance metrics.

    Tracks all database operations including queries, connections, transactions,
    and errors. Maintains performance metrics for monitoring and optimization.
    """

    def __init__(self, log_dir: str = "logs", log_file: str = "database.log"):
        """
        Initialize database logger with file and console handlers.

        :param log_dir: Directory to store log files
        :param log_file: Name of the log file
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger("job_tracker.database")
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers if logger already configured
        if not self.logger.handlers:
            # File handler - detailed logs with DEBUG level
            file_handler = logging.FileHandler(
                self.log_dir / log_file,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)

            # Console handler - important events only (INFO and above)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(levelname)s: %(message)s'
            )
            console_handler.setFormatter(console_formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

        # Performance metrics
        self.query_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0

    def log_query(self, query: str, params: Optional[tuple] = None, execution_time: Optional[float] = None):
        """
        Log SQL query execution with optional parameters and timing.

        :param query: SQL query string
        :param params: Query parameters tuple
        :param execution_time: Query execution time in seconds
        """
        self.query_count += 1
        if execution_time:
            self.total_execution_time += execution_time

        # Truncate long queries for readability
        query_display = query[:100] + "..." if len(query) > 100 else query

        if execution_time:
            self.logger.debug(f"Query executed in {execution_time:.4f}s | {query_display}")
        else:
            self.logger.debug(f"Query executed | {query_display}")

        if params:
            self.logger.debug(f"Parameters: {params}")

    def log_connection(self, event: str, details: str = ""):
        """
        Log connection lifecycle events.

        :param event: Connection event type (established, closed, failed, etc.)
        :param details: Additional context information
        """
        message = f"Connection {event}"
        if details:
            message += f" | {details}"
        self.logger.info(message)

    def log_transaction(self, event: str, details: str = ""):
        """
        Log transaction lifecycle events.

        :param event: Transaction event type (started, committed, rolled back, etc.)
        :param details: Additional context information
        """
        message = f"Transaction {event}"
        if details:
            message += f" | {details}"
        self.logger.info(message)

    def log_error(self, error: Exception, context: str = ""):
        """
        Log database errors with context.

        :param error: Exception that occurred
        :param context: Additional context about where/why error occurred
        """
        self.error_count += 1
        error_type = type(error).__name__
        error_message = str(error)

        if context:
            self.logger.error(f"{context} | {error_type}: {error_message}")
        else:
            self.logger.error(f"{error_type}: {error_message}")

    def log_slow_query(self, query: str, execution_time: float, threshold: float = 0.1):
        """
        Log slow queries that exceed performance threshold.

        :param query: SQL query string
        :param execution_time: Query execution time in seconds
        :param threshold: Threshold in seconds for what constitutes a slow query
        """
        if execution_time > threshold:
            query_display = query[:100] + "..." if len(query) > 100 else query
            self.logger.warning(
                f"SLOW QUERY ({execution_time:.4f}s > {threshold:.4f}s) | {query_display}"
            )

    def get_metrics(self) -> dict:
        """
        Get current database performance metrics.

        :return: Dictionary containing performance metrics
        """
        avg_time = self.total_execution_time / self.query_count if self.query_count > 0 else 0
        return {
            "total_queries": self.query_count,
            "total_errors": self.error_count,
            "total_execution_time": round(self.total_execution_time, 4),
            "average_execution_time": round(avg_time, 4)
        }

    def reset_metrics(self):
        """Reset all performance metrics to zero."""
        self.query_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0
        self.logger.info("Metrics reset")


def log_execution_time(logger: DatabaseLogger):
    """
    Decorator to log function execution time.

    :param logger: DatabaseLogger instance
    :return: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time
                logger.logger.debug(f"{func.__name__} executed in {execution_time:.4f}s")
                return result
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                logger.log_error(e, f"{func.__name__} failed after {execution_time:.4f}s")
                raise
        return wrapper
    return decorator


# Global logger instance
db_logger = DatabaseLogger()

