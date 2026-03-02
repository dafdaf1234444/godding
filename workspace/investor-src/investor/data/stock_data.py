"""
Stock data downloader using yfinance with parallel processing optimization.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
import logging
from pathlib import Path
import concurrent.futures
import time
from functools import wraps

from ..utils.performance import profile_performance

logger = logging.getLogger(__name__)




class StockDataDownloader:
    """Downloads stock data using yfinance."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the stock data downloader.
        
        Args:
            cache_dir: Directory to cache downloaded data
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / "data" / "stocks"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def download_stock_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        save_to_cache: bool = True
    ) -> pd.DataFrame:
        """
        Download stock data for a given symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'GOOGL')
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            start: Start date for data download
            end: End date for data download
            save_to_cache: Whether to save data to cache
            
        Returns:
            DataFrame with stock data (Open, High, Low, Close, Volume, Adj Close)
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Download data
            if start and end:
                data = ticker.history(start=start, end=end, interval=interval)
            else:
                data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No data found for symbol {symbol}")
                return pd.DataFrame()
            
            # Add symbol column
            data['Symbol'] = symbol
            
            # Reset index to make Date a column
            data = data.reset_index()
            
            if save_to_cache:
                self._save_to_cache(data, symbol, period, interval)
            
            logger.info(f"Downloaded {len(data)} rows for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error downloading data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    @profile_performance
    def download_multiple_stocks(
        self,
        symbols: List[str],
        period: str = "1y",
        interval: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        save_to_cache: bool = True,
        max_workers: int = 10,
        use_parallel: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Download stock data for multiple symbols with parallel processing.
        
        Args:
            symbols: List of stock symbols
            period: Data period
            interval: Data interval
            start: Start date for data download
            end: End date for data download
            save_to_cache: Whether to save data to cache
            max_workers: Maximum number of parallel workers
            use_parallel: Whether to use parallel processing
            
        Returns:
            Dictionary mapping symbols to their DataFrames
        """
        if not use_parallel or len(symbols) <= 2:
            # Use sequential processing for small batches
            return self._download_sequential(symbols, period, interval, start, end, save_to_cache)
        
        # Use parallel processing for better performance
        return self._download_parallel(symbols, period, interval, start, end, save_to_cache, max_workers)
    
    def _download_sequential(
        self,
        symbols: List[str],
        period: str,
        interval: str,
        start: Optional[datetime],
        end: Optional[datetime],
        save_to_cache: bool
    ) -> Dict[str, pd.DataFrame]:
        """Download symbols sequentially (fallback method)."""
        results = {}
        
        for symbol in symbols:
            logger.info(f"Downloading data for {symbol}")
            data = self.download_stock_data(
                symbol=symbol,
                period=period,
                interval=interval,
                start=start,
                end=end,
                save_to_cache=save_to_cache
            )
            results[symbol] = data
            
        return results
    
    def _download_parallel(
        self,
        symbols: List[str],
        period: str,
        interval: str,
        start: Optional[datetime],
        end: Optional[datetime],
        save_to_cache: bool,
        max_workers: int
    ) -> Dict[str, pd.DataFrame]:
        """Download symbols in parallel for improved performance."""
        results = {}
        
        def download_single(symbol: str) -> tuple[str, pd.DataFrame]:
            """Download data for a single symbol."""
            data = self.download_stock_data(
                symbol=symbol,
                period=period,
                interval=interval,
                start=start,
                end=end,
                save_to_cache=save_to_cache
            )
            return symbol, data
        
        logger.info(f"Downloading data for {len(symbols)} symbols in parallel (max_workers={max_workers})")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_symbol = {
                executor.submit(download_single, symbol): symbol 
                for symbol in symbols
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    symbol_result, data = future.result()
                    results[symbol_result] = data
                    logger.info(f"Completed download for {symbol_result}: {len(data)} rows")
                except Exception as e:
                    logger.error(f"Error downloading {symbol}: {e}")
                    results[symbol] = pd.DataFrame()  # Return empty DataFrame on error
        
        logger.info(f"Parallel download completed for {len(results)} symbols")
        return results
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock information and metadata.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with stock information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Filter out None values and format key info
            filtered_info = {k: v for k, v in info.items() if v is not None}
            
            return filtered_info
            
        except Exception as e:
            logger.error(f"Error getting info for {symbol}: {str(e)}")
            return {}
    
    def _save_to_cache(self, data: pd.DataFrame, symbol: str, period: str, interval: str):
        """Save data to cache as parquet file."""
        try:
            cache_file = self.cache_dir / f"{symbol}_{period}_{interval}.parquet"
            
            # Add metadata
            data.attrs['symbol'] = symbol
            data.attrs['period'] = period
            data.attrs['interval'] = interval
            data.attrs['download_time'] = datetime.now().isoformat()
            
            data.to_parquet(cache_file, index=False)
            logger.info(f"Saved {symbol} data to cache: {cache_file}")
            
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")
    
    def load_from_cache(self, symbol: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        """Load data from cache."""
        try:
            cache_file = self.cache_dir / f"{symbol}_{period}_{interval}.parquet"
            
            if cache_file.exists():
                data = pd.read_parquet(cache_file)
                logger.info(f"Loaded {symbol} data from cache")
                return data
            
        except Exception as e:
            logger.error(f"Error loading from cache: {str(e)}")
            
        return None
    
    def get_available_symbols(self) -> List[str]:
        """Get list of symbols available in cache."""
        symbols = set()
        
        for cache_file in self.cache_dir.glob("*.parquet"):
            # Extract symbol from filename (format: SYMBOL_period_interval.parquet)
            symbol = cache_file.stem.split("_")[0]
            symbols.add(symbol)
            
        return sorted(list(symbols))