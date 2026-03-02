"""
Base data downloader class to eliminate duplicate download functionality.
Provides common patterns for downloading financial data with caching and error handling.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path
import abc

from ..utils.performance import profile_performance
from ..utils.parallel_processing import SymbolProcessor
from ..core.error_handling import handle_data_errors

logger = logging.getLogger(__name__)


class BaseDataDownloader(abc.ABC):
    """
    Abstract base class for data downloaders.
    
    Provides common functionality for:
    - Symbol downloading with yfinance
    - Caching management
    - Error handling
    - Parallel processing
    - Data validation
    """
    
    def __init__(
        self, 
        cache_dir: Optional[str] = None,
        max_workers: int = 10,
        default_period: str = "2y",
        default_interval: str = "1d"
    ):
        """
        Initialize base downloader.
        
        Args:
            cache_dir: Directory to cache downloaded data
            max_workers: Maximum parallel workers for downloads
            default_period: Default period for data downloads
            default_interval: Default interval for data downloads
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / "data"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_workers = max_workers
        self.default_period = default_period
        self.default_interval = default_interval
        
        # Initialize parallel processor for symbol downloads
        self.symbol_processor = SymbolProcessor(max_workers=max_workers)
        
    @abc.abstractmethod
    def get_data_type_name(self) -> str:
        """Return the name of the data type (e.g., 'stock', 'crypto', 'earnings')."""
        pass
    
    @abc.abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol is appropriate for this downloader.
        
        Args:
            symbol: Symbol to validate
            
        Returns:
            True if symbol is valid for this downloader
        """
        pass
    
    def download_symbol_data(
        self,
        symbol: str,
        period: str = None,
        interval: str = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        save_to_cache: bool = True,
        **kwargs
    ) -> pd.DataFrame:
        """
        Download data for a single symbol using yfinance.
        
        Args:
            symbol: Symbol to download (e.g., 'AAPL', 'BTC-USD')
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            start: Start date for data download
            end: End date for data download
            save_to_cache: Whether to save data to cache
            **kwargs: Additional parameters for subclasses
            
        Returns:
            DataFrame with downloaded data
        """
        period = period or self.default_period
        interval = interval or self.default_interval
        
        # Validate symbol
        if not self.validate_symbol(symbol):
            logger.warning(f"Invalid {self.get_data_type_name()} symbol: {symbol}")
            return pd.DataFrame()
        
        try:
            # Create yfinance ticker
            ticker = yf.Ticker(symbol)
            
            # Download data
            if start and end:
                data = ticker.history(start=start, end=end, interval=interval)
            else:
                data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No {self.get_data_type_name()} data found for {symbol}")
                return pd.DataFrame()
            
            # Post-process the data
            data = self._post_process_data(data, symbol, period, interval, **kwargs)
            
            # Save to cache if requested
            if save_to_cache and not data.empty:
                self._save_to_cache(data, symbol, period, interval)
            
            logger.info(f"Downloaded {len(data)} rows for {self.get_data_type_name()} {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error downloading {self.get_data_type_name()} data for {symbol}: {e}")
            return pd.DataFrame()
    
    @profile_performance
    def download_multiple_symbols(
        self,
        symbols: List[str],
        period: str = None,
        interval: str = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        save_to_cache: bool = True,
        use_parallel: bool = True,
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        Download data for multiple symbols with parallel processing.
        
        Args:
            symbols: List of symbols to download
            period: Data period
            interval: Data interval
            start: Start date for data download
            end: End date for data download
            save_to_cache: Whether to save data to cache
            use_parallel: Whether to use parallel processing
            **kwargs: Additional parameters for subclasses
            
        Returns:
            Dictionary mapping symbols to their DataFrames
        """
        if not symbols:
            return {}
        
        period = period or self.default_period
        interval = interval or self.default_interval
        
        # Create download function with fixed parameters
        def download_func(symbol: str) -> pd.DataFrame:
            return self.download_symbol_data(
                symbol, period, interval, start, end, save_to_cache, **kwargs
            )
        
        # Use parallel processor
        results = self.symbol_processor.download_symbols(
            symbols, download_func,
            operation_name=f"downloading {self.get_data_type_name()} data",
            use_parallel=use_parallel
        )
        
        # Filter out empty results
        valid_results = {
            symbol: data for symbol, data in results.items() 
            if data is not None and not data.empty
        }
        
        return valid_results
    
    def _post_process_data(
        self, 
        data: pd.DataFrame, 
        symbol: str, 
        period: str, 
        interval: str,
        **kwargs
    ) -> pd.DataFrame:
        """
        Post-process downloaded data. Override in subclasses for specific processing.
        
        Args:
            data: Raw data from yfinance
            symbol: Symbol that was downloaded
            period: Period used for download
            interval: Interval used for download
            **kwargs: Additional parameters
            
        Returns:
            Processed DataFrame
        """
        # Add symbol column
        data['Symbol'] = symbol
        
        # Reset index to make Date a column
        data = data.reset_index()
        
        # Ensure Date column is datetime
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'])
        elif 'Datetime' in data.columns:
            data['Date'] = pd.to_datetime(data['Datetime'])
            data = data.drop(columns=['Datetime'])
        
        return data
    
    def _save_to_cache(
        self, 
        data: pd.DataFrame, 
        symbol: str, 
        period: str, 
        interval: str
    ):
        """
        Save data to cache as parquet file.
        
        Args:
            data: Data to save
            symbol: Symbol identifier
            period: Period used for download
            interval: Interval used for download
        """
        try:
            data_type = self.get_data_type_name()
            cache_file = self.cache_dir / f"{symbol}_{period}_{interval}_{data_type}.parquet"
            
            # Add metadata
            data.attrs['symbol'] = symbol
            data.attrs['period'] = period
            data.attrs['interval'] = interval
            data.attrs['data_type'] = data_type
            data.attrs['download_time'] = datetime.now().isoformat()
            data.attrs['source'] = 'yfinance'
            
            data.to_parquet(cache_file, index=False)
            logger.debug(f"Saved {symbol} {data_type} data to cache: {cache_file}")
            
        except Exception as e:
            logger.error(f"Error saving {symbol} to cache: {e}")
    
    def load_from_cache(
        self, 
        symbol: str, 
        period: str = None, 
        interval: str = None
    ) -> Optional[pd.DataFrame]:
        """
        Load data from cache.
        
        Args:
            symbol: Symbol to load
            period: Period to load
            interval: Interval to load
            
        Returns:
            Cached DataFrame or None if not found
        """
        try:
            period = period or self.default_period
            interval = interval or self.default_interval
            data_type = self.get_data_type_name()
            
            cache_file = self.cache_dir / f"{symbol}_{period}_{interval}_{data_type}.parquet"
            
            if cache_file.exists():
                data = pd.read_parquet(cache_file)
                logger.debug(f"Loaded {symbol} {data_type} data from cache")
                return data
            
        except Exception as e:
            logger.error(f"Error loading {symbol} from cache: {e}")
            
        return None
    
    def get_available_symbols(self) -> List[str]:
        """
        Get list of symbols available in cache.
        
        Returns:
            List of symbols with cached data
        """
        symbols = set()
        data_type = self.get_data_type_name()
        
        pattern = f"*_{data_type}.parquet"
        for cache_file in self.cache_dir.glob(pattern):
            # Extract symbol from filename (format: SYMBOL_period_interval_datatype.parquet)
            parts = cache_file.stem.split("_")
            if len(parts) >= 4:  # symbol_period_interval_datatype
                symbol = parts[0]
                symbols.add(symbol)
        
        return sorted(list(symbols))
    
    def is_cache_fresh(
        self, 
        symbol: str, 
        period: str = None, 
        interval: str = None,
        max_age_hours: int = 24
    ) -> bool:
        """
        Check if cached data is fresh enough.
        
        Args:
            symbol: Symbol to check
            period: Period to check
            interval: Interval to check
            max_age_hours: Maximum age in hours
            
        Returns:
            True if cache is fresh, False otherwise
        """
        try:
            period = period or self.default_period
            interval = interval or self.default_interval
            data_type = self.get_data_type_name()
            
            cache_file = self.cache_dir / f"{symbol}_{period}_{interval}_{data_type}.parquet"
            
            if not cache_file.exists():
                return False
            
            # Check file modification time
            file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age_hours = (datetime.now() - file_time).total_seconds() / 3600
            
            return age_hours <= max_age_hours
            
        except Exception as e:
            logger.error(f"Error checking cache freshness for {symbol}: {e}")
            return False
    
    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear cached data.
        
        Args:
            symbol: Specific symbol to clear, or None to clear all
        """
        try:
            data_type = self.get_data_type_name()
            
            if symbol:
                pattern = f"{symbol}_*_{data_type}.parquet"
                files_removed = 0
                for cache_file in self.cache_dir.glob(pattern):
                    cache_file.unlink()
                    files_removed += 1
                logger.info(f"Cleared cache for {symbol}: {files_removed} files removed")
            else:
                pattern = f"*_{data_type}.parquet"
                files_removed = 0
                for cache_file in self.cache_dir.glob(pattern):
                    cache_file.unlink()
                    files_removed += 1
                logger.info(f"Cleared all {data_type} cache: {files_removed} files removed")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    @handle_data_errors(operation="getting symbol info")
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get symbol information and metadata from yfinance.
        
        Args:
            symbol: Symbol to get info for
            
        Returns:
            Dictionary with symbol information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Filter out None values and format key info
            filtered_info = {k: v for k, v in info.items() if v is not None}
            
            return filtered_info
            
        except Exception as e:
            logger.error(f"Error getting info for {symbol}: {e}")
            return {}