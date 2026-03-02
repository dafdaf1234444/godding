"""
Shared utilities for data providers.
"""
import time
import logging
import pandas as pd
from typing import Dict, List, Any, Callable
from functools import wraps
import concurrent.futures
from pathlib import Path

logger = logging.getLogger(__name__)


def profile_performance(func: Callable) -> Callable:
    """Decorator to profile function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        # Log performance for optimization tracking
        if hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__
            logger.info(f"{class_name}.{func.__name__} completed in {duration:.2f}s")
        else:
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
        
        return result
    return wrapper


class ParallelDataFetcher:
    """Utility for parallel data fetching operations."""
    
    def __init__(self, max_workers: int = 10):
        """Initialize parallel fetcher."""
        self.max_workers = max_workers
    
    @profile_performance
    def fetch_parallel(
        self,
        items: List[str],
        fetch_function: Callable[[str], Any],
        use_parallel: bool = True,
        batch_size: int = None
    ) -> Dict[str, Any]:
        """
        Fetch data for multiple items in parallel.
        
        Args:
            items: List of items to fetch
            fetch_function: Function to fetch single item
            use_parallel: Whether to use parallel processing
            batch_size: Size of parallel batches
            
        Returns:
            Dictionary mapping items to their results
        """
        if not use_parallel or len(items) <= 2:
            return self._fetch_sequential(items, fetch_function)
        
        return self._fetch_parallel(items, fetch_function, batch_size)
    
    def _fetch_sequential(self, items: List[str], fetch_function: Callable) -> Dict[str, Any]:
        """Fetch items sequentially."""
        results = {}
        
        for item in items:
            logger.info(f"Fetching data for {item}")
            try:
                result = fetch_function(item)
                results[item] = result
            except Exception as e:
                logger.error(f"Error fetching {item}: {e}")
                results[item] = None
                
        return results
    
    def _fetch_parallel(self, items: List[str], fetch_function: Callable, batch_size: int = None) -> Dict[str, Any]:
        """Fetch items in parallel."""
        results = {}
        effective_workers = min(self.max_workers, len(items))
        
        logger.info(f"Fetching data for {len(items)} items in parallel (max_workers={effective_workers})")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=effective_workers) as executor:
            # Submit all fetch tasks
            future_to_item = {
                executor.submit(fetch_function, item): item 
                for item in items
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results[item] = result
                    logger.debug(f"Completed fetch for {item}")
                except Exception as e:
                    logger.error(f"Error fetching {item}: {e}")
                    results[item] = None
        
        logger.info(f"Parallel fetch completed for {len(results)} items")
        return results


class DataNormalizer:
    """Utility for data normalization operations."""
    
    @staticmethod
    def normalize_dates(df: pd.DataFrame, date_column: str = 'Date') -> pd.DataFrame:
        """Normalize date column to datetime if needed."""
        if date_column in df.columns and not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column])
        return df
    
    @staticmethod
    def normalize_numeric_columns(df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
        """Normalize numeric columns to appropriate data types."""
        if df.empty:
            return df
        
        df = df.copy()
        
        if columns is None:
            columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        for col in columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    @staticmethod
    def add_symbol_column(df: pd.DataFrame, symbol: str, symbol_column: str = 'Symbol') -> pd.DataFrame:
        """Add symbol column if not present."""
        if df.empty:
            return df
        
        df = df.copy()
        if symbol_column not in df.columns:
            df[symbol_column] = symbol
        
        return df
    
    @staticmethod
    def reset_index_to_column(df: pd.DataFrame, column_name: str = 'Date') -> pd.DataFrame:
        """Reset index to column if it's a datetime index."""
        if df.empty:
            return df
        
        if pd.api.types.is_datetime64_any_dtype(df.index):
            df = df.reset_index()
            if df.columns[0] not in ['Date', column_name]:
                df = df.rename(columns={df.columns[0]: column_name})
        
        return df


class CacheKeyGenerator:
    """Utility for generating consistent cache keys."""
    
    @staticmethod
    def generate_key(provider_type: str, symbol: str, period: str, interval: str, **kwargs) -> str:
        """Generate cache key from parameters."""
        base_key = f"{provider_type}_{symbol}_{period}_{interval}"
        
        if kwargs:
            # Sort kwargs for consistent key generation
            extra_params = "_".join(f"{k}_{v}" for k, v in sorted(kwargs.items()))
            base_key = f"{base_key}_{extra_params}"
        
        return base_key
    
    @staticmethod
    def parse_key(cache_key: str) -> Dict[str, str]:
        """Parse cache key back to components."""
        parts = cache_key.split('_')
        if len(parts) >= 4:
            return {
                'provider_type': parts[0],
                'symbol': parts[1],
                'period': parts[2],
                'interval': parts[3]
            }
        return {}


class DataValidator:
    """Utility for common data validation operations."""
    
    @staticmethod
    def is_valid_dataframe(df: pd.DataFrame, required_columns: List[str] = None) -> bool:
        """Check if DataFrame is valid for processing."""
        if df is None or df.empty:
            return False
        
        if required_columns:
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                logger.warning(f"Missing required columns: {missing_columns}")
                return False
        
        return True
    
    @staticmethod
    def validate_price_data(df: pd.DataFrame) -> List[str]:
        """Validate price data for common issues."""
        issues = []
        
        if df.empty:
            return ["Empty DataFrame"]
        
        price_columns = ['Open', 'High', 'Low', 'Close']
        available_price_cols = [col for col in price_columns if col in df.columns]
        
        if not available_price_cols:
            issues.append("No price columns found")
            return issues
        
        # Check for negative prices
        for col in available_price_cols:
            if (df[col] < 0).any():
                issues.append(f"Negative values found in {col}")
        
        # Check for extreme price changes (>50% in a day)
        if 'Close' in df.columns and len(df) > 1:
            price_changes = df['Close'].pct_change().abs()
            extreme_moves = (price_changes > 0.5).sum()
            if extreme_moves > 0:
                issues.append(f"Found {extreme_moves} extreme price movements (>50%)")
        
        # Check for missing values
        for col in available_price_cols:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                issues.append(f"Missing values in {col}: {missing_count}")
        
        return issues
    
    @staticmethod
    def validate_date_range(df: pd.DataFrame, date_column: str = 'Date') -> List[str]:
        """Validate date range and continuity."""
        issues = []
        
        if df.empty or date_column not in df.columns:
            return issues
        
        dates = pd.to_datetime(df[date_column])
        
        # Check for future dates
        future_dates = dates > pd.Timestamp.now()
        if future_dates.any():
            issues.append(f"Found {future_dates.sum()} future dates")
        
        # Check for date gaps (basic check)
        if len(dates) > 1:
            date_diffs = dates.diff().dropna()
            if date_diffs.max() > pd.Timedelta(days=7):  # Assuming daily data
                issues.append("Potential data gaps detected")
        
        return issues


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists and return path."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(filename: str) -> str:
    """Generate safe filename by removing/replacing invalid characters."""
    import re
    # Remove or replace invalid filename characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return filename