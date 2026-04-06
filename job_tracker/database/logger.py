"""
Database logging utilities.

Uses the standard Python logger hierarchy (job_tracker.database.*) so that
all log output is controlled by the single root configuration in utils/logger.py.
"""

import logging
import time
from functools import wraps
from typing import Callable, Any

_logger = logging.getLogger("job_tracker.database")

SLOW_QUERY_THRESHOLD_S = 0.1


def log_execution_time(func: Callable) -> Callable:
    """Decorator that logs function execution time at DEBUG level."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            _logger.debug("%s completed in %.4fs", func.__name__, time.perf_counter() - start)
            return result
        except Exception as e:
            _logger.error("%s failed after %.4fs: %s", func.__name__, time.perf_counter() - start, e)
            raise
    return wrapper


def log_slow_query(query: str, execution_time_s: float, threshold: float = SLOW_QUERY_THRESHOLD_S) -> None:
    """Emit a WARNING if a query exceeded the slow-query threshold."""
    if execution_time_s > threshold:
        preview = query[:100] + "..." if len(query) > 100 else query
        _logger.warning("SLOW QUERY (%.4fs > %.4fs): %s", execution_time_s, threshold, preview)
