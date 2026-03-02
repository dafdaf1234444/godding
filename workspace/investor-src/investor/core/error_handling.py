"""
Standardized error handling utilities for the investor analysis system.
Provides consistent error handling patterns, logging, and recovery strategies.
"""
import logging
import traceback
from typing import Any, Callable, Optional, Dict, List
from functools import wraps
from contextlib import contextmanager

from .exceptions import (
    InvestorSystemError, DataError, DataNotFoundError, DataValidationError,
    ConfigurationError, OutputError
)


logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Centralized error handling with consistent logging and recovery patterns.
    """
    
    @staticmethod
    def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None, 
                    operation: Optional[str] = None, symbol: Optional[str] = None,
                    recoverable: bool = True) -> InvestorSystemError:
        """
        Transform any exception into a standardized InvestorSystemError.
        
        Args:
            error: Original exception
            context: Additional context information
            operation: Operation being performed when error occurred
            symbol: Symbol being processed (if applicable)
            recoverable: Whether this error can be recovered from
            
        Returns:
            Standardized InvestorSystemError with rich context
        """
        # Build context dictionary
        error_context = context or {}
        if operation:
            error_context['operation'] = operation
        if symbol:
            error_context['symbol'] = symbol
        
        # Add original error details
        error_context['original_error_type'] = type(error).__name__
        error_context['original_error_message'] = str(error)
        
        # If it's already an InvestorSystemError, enhance it
        if isinstance(error, InvestorSystemError):
            error.add_context('operation', operation)
            if symbol:
                error.add_context('symbol', symbol)
            return error
        
        # Convert to appropriate InvestorSystemError subclass
        if isinstance(error, (FileNotFoundError, KeyError)):
            return DataNotFoundError(
                f"Data not found during {operation or 'operation'}: {str(error)}",
                context=error_context, cause=error, recoverable=recoverable
            )
        elif isinstance(error, (ValueError, TypeError)):
            return DataValidationError(
                f"Data validation failed during {operation or 'operation'}: {str(error)}",
                context=error_context, cause=error, recoverable=recoverable
            )
        else:
            return InvestorSystemError(
                f"Unexpected error during {operation or 'operation'}: {str(error)}",
                context=error_context, cause=error, recoverable=recoverable
            )
    
    @staticmethod
    def log_error(error: Exception, level: str = 'error', 
                 include_traceback: bool = False) -> None:
        """
        Log error with consistent formatting and context.
        
        Args:
            error: Exception to log
            level: Log level ('error', 'warning', 'info', 'debug')
            include_traceback: Whether to include full traceback
        """
        log_func = getattr(logger, level.lower(), logger.error)
        
        # Format error message
        if isinstance(error, InvestorSystemError):
            msg = f"{type(error).__name__}: {str(error)}"
            if error.context:
                context_str = ", ".join(f"{k}={v}" for k, v in error.context.items())
                msg += f" [Context: {context_str}]"
        else:
            msg = f"{type(error).__name__}: {str(error)}"
        
        # Log the error
        log_func(msg)
        
        # Include traceback if requested
        if include_traceback:
            log_func(f"Traceback: {traceback.format_exc()}")
    
    @staticmethod
    def should_continue_processing(error: Exception, symbol: Optional[str] = None,
                                  total_symbols: int = 1) -> bool:
        """
        Determine if processing should continue after an error.
        
        Args:
            error: Exception that occurred
            symbol: Symbol being processed (if applicable)
            total_symbols: Total number of symbols being processed
            
        Returns:
            True if processing should continue, False otherwise
        """
        # If it's an InvestorSystemError, check if it's recoverable
        if isinstance(error, InvestorSystemError):
            if not error.is_recoverable():
                return False
        
        # For single symbol processing, most errors are not recoverable
        if total_symbols == 1:
            return False
        
        # For multi-symbol processing, continue with remaining symbols
        # unless it's a system-level error
        if isinstance(error, (ConfigurationError, OutputError)):
            return False
        
        return True


def handle_errors(operation: str = None, symbol: str = None, 
                 recoverable: bool = True, log_level: str = 'error',
                 continue_on_error: bool = False, default_return: Any = None):
    """
    Decorator for standardized error handling.
    
    Args:
        operation: Description of the operation being performed
        symbol: Symbol being processed (if applicable)
        recoverable: Whether errors should be marked as recoverable
        log_level: Log level for errors
        continue_on_error: Whether to continue processing or re-raise
        default_return: Default value to return if continue_on_error is True
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Build context from function arguments
                context = {
                    'function': func.__name__,
                    'module': func.__module__,
                }
                
                # Extract symbol from args if not provided
                func_symbol = symbol
                if not func_symbol and args:
                    # Look for symbol in common argument positions
                    for arg in args:
                        if isinstance(arg, str) and len(arg) <= 10 and arg.isupper():
                            func_symbol = arg
                            break
                
                # Handle and log error
                handled_error = ErrorHandler.handle_error(
                    e, context=context, operation=operation, 
                    symbol=func_symbol, recoverable=recoverable
                )
                
                ErrorHandler.log_error(handled_error, level=log_level)
                
                # Either continue with default return or re-raise
                if continue_on_error:
                    return default_return
                else:
                    raise handled_error
        
        return wrapper
    return decorator


@contextmanager
def error_context(operation: str, symbol: str = None, 
                 continue_on_error: bool = False, default_return: Any = None):
    """
    Context manager for standardized error handling.
    
    Args:
        operation: Description of the operation being performed
        symbol: Symbol being processed (if applicable)
        continue_on_error: Whether to suppress errors and return default
        default_return: Default value to return if continue_on_error is True
        
    Yields:
        Context for the operation
        
    Example:
        with error_context("loading data", symbol="AAPL"):
            data = load_data("AAPL")
    """
    try:
        yield
    except Exception as e:
        # Handle and log error
        handled_error = ErrorHandler.handle_error(
            e, operation=operation, symbol=symbol
        )
        
        ErrorHandler.log_error(handled_error)
        
        # Either continue with default return or re-raise
        if continue_on_error:
            return default_return
        else:
            raise handled_error


class ErrorRecoveryStrategy:
    """
    Provides common error recovery patterns.
    """
    
    @staticmethod
    def retry_with_backoff(func: Callable, max_retries: int = 3,
                          backoff_factor: float = 1.0, 
                          exceptions: tuple = (Exception,)) -> Any:
        """
        Retry function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for backoff delay
            exceptions: Exceptions to catch and retry on
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        import time
        
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                return func()
            except exceptions as e:
                last_exception = e
                if attempt < max_retries:
                    delay = backoff_factor * (2 ** attempt)
                    logger.warning(f"Retry attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"All {max_retries} retry attempts failed")
        
        raise last_exception
    
    @staticmethod
    def fallback_chain(functions: List[Callable], 
                      operation: str = "operation") -> Any:
        """
        Execute functions in sequence until one succeeds.
        
        Args:
            functions: List of functions to try in order
            operation: Description of the operation for error messages
            
        Returns:
            Result from first successful function
            
        Raises:
            DataError if all functions fail
        """
        errors = []
        
        for i, func in enumerate(functions):
            try:
                result = func()
                if i > 0:
                    logger.info(f"Fallback {i + 1} succeeded for {operation}")
                return result
            except Exception as e:
                errors.append(e)
                logger.warning(f"Fallback {i + 1} failed for {operation}: {e}")
        
        # All functions failed
        error_messages = [str(e) for e in errors]
        raise DataError(
            f"All fallback options failed for {operation}: {'; '.join(error_messages)}",
            context={'fallback_count': len(functions), 'errors': error_messages}
        )


# Convenience decorators for common error handling patterns
def handle_data_errors(operation: str = None, symbol: str = None):
    """Decorator for data operation error handling."""
    return handle_errors(
        operation=operation, symbol=symbol, recoverable=True,
        log_level='warning', continue_on_error=False
    )


def handle_analysis_errors(operation: str = None, symbol: str = None, 
                          continue_on_error: bool = True):
    """Decorator for analysis operation error handling."""
    return handle_errors(
        operation=operation, symbol=symbol, recoverable=True,
        log_level='error', continue_on_error=continue_on_error,
        default_return={}
    )


def handle_visualization_errors(operation: str = None, symbol: str = None):
    """Decorator for visualization operation error handling."""
    return handle_errors(
        operation=operation, symbol=symbol, recoverable=True,
        log_level='warning', continue_on_error=True,
        default_return=None
    )