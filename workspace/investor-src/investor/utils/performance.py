"""
Performance profiling utilities for the investor analysis system.
Provides decorators and utilities for measuring function execution time.
"""
import time
import logging
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def profile_performance(func: Callable) -> Callable:
    """
    Decorator to profile function performance.
    
    Logs the execution time of the decorated function with class context when available.
    
    Args:
        func: Function to profile
        
    Returns:
        Wrapped function with performance logging
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        # Log performance for optimization tracking
        if args and hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__
            logger.info(f"{class_name}.{func.__name__} completed in {duration:.2f}s")
        else:
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
        
        return result
    return wrapper


def time_function(func: Callable) -> Callable:
    """
    Simple timing decorator that returns timing information.
    
    Args:
        func: Function to time
        
    Returns:
        Wrapped function that returns (result, execution_time)
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> tuple[Any, float]:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        return result, duration
    return wrapper


class PerformanceMonitor:
    """Context manager for monitoring performance of code blocks."""
    
    def __init__(self, operation_name: str, log_level: int = logging.INFO):
        """
        Initialize performance monitor.
        
        Args:
            operation_name: Name of the operation being monitored
            log_level: Logging level for performance messages
        """
        self.operation_name = operation_name
        self.log_level = log_level
        self.start_time = 0.0
        self.duration = 0.0
    
    def __enter__(self) -> 'PerformanceMonitor':
        """Start timing the operation."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """End timing and log the result."""
        end_time = time.time()
        self.duration = end_time - self.start_time
        
        if exc_type is None:
            logger.log(self.log_level, f"{self.operation_name} completed in {self.duration:.2f}s")
        else:
            logger.log(self.log_level, f"{self.operation_name} failed after {self.duration:.2f}s")
    
    def get_duration(self) -> float:
        """Get the measured duration."""
        return self.duration