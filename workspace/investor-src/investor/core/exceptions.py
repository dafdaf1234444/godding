"""
Exception hierarchy for the investor analysis system.
Provides standardized error handling with rich context and recovery guidance.
"""
from typing import Optional, Dict, Any
import logging


logger = logging.getLogger(__name__)


class InvestorSystemError(Exception):
    """
    Base exception for the investor system.
    
    Provides rich error context and standardized error handling patterns.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None, recoverable: bool = True):
        """
        Initialize system error with rich context.
        
        Args:
            message: Human-readable error message
            context: Additional context information (symbol, operation, etc.)
            cause: Original exception that caused this error
            recoverable: Whether this error can be recovered from
        """
        super().__init__(message)
        self.context = context or {}
        self.cause = cause
        self.recoverable = recoverable
        self.timestamp = None
        
        # Log error creation for debugging
        logger.debug(f"InvestorSystemError created: {message}, context: {context}")
    
    def __str__(self) -> str:
        """Return formatted error string with context."""
        base_msg = super().__str__()
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{base_msg} (Context: {context_str})"
        return base_msg
    
    def add_context(self, key: str, value: Any) -> 'InvestorSystemError':
        """Add context information to the error."""
        self.context[key] = value
        return self
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context value by key."""
        return self.context.get(key, default)
    
    def is_recoverable(self) -> bool:
        """Check if this error is recoverable."""
        return self.recoverable


class DataError(InvestorSystemError):
    """Data-related errors."""
    pass


class DataNotFoundError(DataError):
    """Raised when requested data is not found."""
    
    def __init__(self, message: str, symbol: Optional[str] = None, 
                 data_type: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if symbol:
            context['symbol'] = symbol
        if data_type:
            context['data_type'] = data_type
        super().__init__(message, context=context, **kwargs)


class DataValidationError(DataError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, validation_type: Optional[str] = None, 
                 failed_checks: Optional[list] = None, **kwargs):
        context = kwargs.pop('context', {})
        if validation_type:
            context['validation_type'] = validation_type
        if failed_checks:
            context['failed_checks'] = failed_checks
        super().__init__(message, context=context, **kwargs)


class AnalysisError(InvestorSystemError):
    """Analysis-related errors."""
    pass


class ForecastingError(AnalysisError):
    """Forecasting-related errors."""
    
    def __init__(self, message: str, model_type: Optional[str] = None, 
                 symbol: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if model_type:
            context['model_type'] = model_type
        if symbol:
            context['symbol'] = symbol
        super().__init__(message, context=context, **kwargs)


class AnomalyDetectionError(AnalysisError):
    """Anomaly detection-related errors."""
    
    def __init__(self, message: str, detector_type: Optional[str] = None, 
                 symbol: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if detector_type:
            context['detector_type'] = detector_type
        if symbol:
            context['symbol'] = symbol
        super().__init__(message, context=context, **kwargs)


class VisualizationError(InvestorSystemError):
    """Visualization-related errors."""
    
    def __init__(self, message: str, chart_type: Optional[str] = None, 
                 symbol: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if chart_type:
            context['chart_type'] = chart_type
        if symbol:
            context['symbol'] = symbol
        super().__init__(message, context=context, **kwargs)


class ConfigurationError(InvestorSystemError):
    """Configuration-related errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, 
                 config_file: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if config_key:
            context['config_key'] = config_key
        if config_file:
            context['config_file'] = config_file
        # Configuration errors are typically not recoverable
        kwargs.setdefault('recoverable', False)
        super().__init__(message, context=context, **kwargs)


class OutputError(InvestorSystemError):
    """Output and file management-related errors."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 operation: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if file_path:
            context['file_path'] = file_path
        if operation:
            context['operation'] = operation
        super().__init__(message, context=context, **kwargs)


class GitWorkflowError(OutputError):
    """Git workflow-related errors."""
    
    def __init__(self, message: str, git_command: Optional[str] = None, 
                 repository_path: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if git_command:
            context['git_command'] = git_command
        if repository_path:
            context['repository_path'] = repository_path
        super().__init__(message, context=context, **kwargs)