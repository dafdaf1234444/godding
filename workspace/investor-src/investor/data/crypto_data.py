"""
Cryptocurrency data downloader using yfinance and other sources.
Handles 24/7 trading characteristics and crypto-specific features.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path
import concurrent.futures
import time
from functools import wraps

from ..utils.performance import profile_performance

logger = logging.getLogger(__name__)




class CryptoDataDownloader:
    """Downloads cryptocurrency data using yfinance and other sources."""
    
    # Common cryptocurrency symbols for yfinance
    CRYPTO_SYMBOLS = {
        'BTC': 'BTC-USD',
        'ETH': 'ETH-USD',
        'ADA': 'ADA-USD',
        'SOL': 'SOL-USD',
        'DOT': 'DOT-USD',
        'AVAX': 'AVAX-USD',
        'MATIC': 'MATIC-USD',
        'LINK': 'LINK-USD',
        'UNI': 'UNI-USD',
        'AAVE': 'AAVE-USD',
        'ALGO': 'ALGO-USD',
        'XRP': 'XRP-USD',
        'LTC': 'LTC-USD',
        'BCH': 'BCH-USD',
        'DOGE': 'DOGE-USD'
    }
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the crypto data downloader.
        
        Args:
            cache_dir: Directory to cache downloaded data
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / "data" / "crypto"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def download_crypto_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        save_to_cache: bool = True
    ) -> pd.DataFrame:
        """
        Download cryptocurrency data for a given symbol.
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH', 'BTC-USD')
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            start: Start date for data download
            end: End date for data download
            save_to_cache: Whether to save data to cache
            
        Returns:
            DataFrame with crypto data (Open, High, Low, Close, Volume)
        """
        try:
            # Convert crypto symbol to yfinance format if needed
            yahoo_symbol = self._get_yahoo_symbol(symbol)
            
            ticker = yf.Ticker(yahoo_symbol)
            
            # Download data
            if start and end:
                data = ticker.history(start=start, end=end, interval=interval)
            else:
                data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No data found for crypto symbol {symbol} ({yahoo_symbol})")
                return pd.DataFrame()
            
            # Add crypto-specific columns
            data['Symbol'] = symbol
            data['YahooSymbol'] = yahoo_symbol
            data['AssetType'] = 'crypto'
            
            # Reset index to make Date a column
            data = data.reset_index()
            
            # Add crypto-specific features
            data = self._add_crypto_features(data)
            
            if save_to_cache:
                self._save_to_cache(data, symbol, period, interval)
            
            logger.info(f"Downloaded {len(data)} rows for crypto {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error downloading crypto data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _get_yahoo_symbol(self, symbol: str) -> str:
        """Convert crypto symbol to yfinance format."""
        # If already in yfinance format, return as is
        if '-USD' in symbol or '-EUR' in symbol or '-GBP' in symbol:
            return symbol
        
        # Check if it's a known crypto symbol
        if symbol.upper() in self.CRYPTO_SYMBOLS:
            return self.CRYPTO_SYMBOLS[symbol.upper()]
        
        # Default to USD pair
        return f"{symbol.upper()}-USD"
    
    def _add_crypto_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add cryptocurrency-specific features to the data."""
        if data.empty:
            return data
        
        # Calculate volatility (more important for crypto)
        data['Volatility'] = data['Close'].pct_change().rolling(window=24).std()
        
        # Calculate trading intensity (volume relative to price)
        data['Trading_Intensity'] = data['Volume'] / data['Close']
        
        # Add 24/7 trading flag (always True for crypto)
        data['Is_24_7_Trading'] = True
        
        # Calculate price momentum
        data['Price_Momentum_1d'] = data['Close'].pct_change(1)
        data['Price_Momentum_7d'] = data['Close'].pct_change(7)
        data['Price_Momentum_30d'] = data['Close'].pct_change(30)
        
        # Calculate moving averages (important for crypto trends)
        data['MA_7'] = data['Close'].rolling(window=7).mean()
        data['MA_30'] = data['Close'].rolling(window=30).mean()
        data['MA_200'] = data['Close'].rolling(window=200).mean()
        
        return data
    
    @profile_performance
    def download_multiple_cryptos(
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
        Download cryptocurrency data for multiple symbols with parallel processing.
        
        Args:
            symbols: List of crypto symbols
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
        """Download crypto symbols sequentially (fallback method)."""
        results = {}
        
        for symbol in symbols:
            logger.info(f"Downloading crypto data for {symbol}")
            data = self.download_crypto_data(
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
        """Download crypto symbols in parallel for improved performance."""
        results = {}
        
        def download_single(symbol: str) -> tuple[str, pd.DataFrame]:
            """Download data for a single crypto symbol."""
            data = self.download_crypto_data(
                symbol=symbol,
                period=period,
                interval=interval,
                start=start,
                end=end,
                save_to_cache=save_to_cache
            )
            return symbol, data
        
        logger.info(f"Downloading crypto data for {len(symbols)} symbols in parallel (max_workers={max_workers})")
        
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
                    logger.info(f"Completed crypto download for {symbol_result}: {len(data)} rows")
                except Exception as e:
                    logger.error(f"Error downloading crypto {symbol}: {e}")
                    results[symbol] = pd.DataFrame()  # Return empty DataFrame on error
        
        logger.info(f"Parallel crypto download completed for {len(results)} symbols")
        return results
    
    def get_crypto_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get cryptocurrency information and metadata.
        
        Args:
            symbol: Crypto symbol
            
        Returns:
            Dictionary with crypto information
        """
        try:
            yahoo_symbol = self._get_yahoo_symbol(symbol)
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            # Filter out None values and add crypto-specific info
            filtered_info = {k: v for k, v in info.items() if v is not None}
            
            # Add crypto-specific metadata
            filtered_info['is_cryptocurrency'] = True
            filtered_info['trades_24_7'] = True
            filtered_info['original_symbol'] = symbol
            filtered_info['yahoo_symbol'] = yahoo_symbol
            
            return filtered_info
            
        except Exception as e:
            logger.error(f"Error getting crypto info for {symbol}: {str(e)}")
            return {}
    
    def _save_to_cache(self, data: pd.DataFrame, symbol: str, period: str, interval: str):
        """Save crypto data to cache as parquet file."""
        try:
            cache_file = self.cache_dir / f"{symbol}_{period}_{interval}.parquet"
            
            # Add metadata
            data.attrs['symbol'] = symbol
            data.attrs['period'] = period
            data.attrs['interval'] = interval
            data.attrs['download_time'] = datetime.now().isoformat()
            data.attrs['asset_type'] = 'crypto'
            
            data.to_parquet(cache_file, index=False)
            logger.info(f"Saved {symbol} crypto data to cache: {cache_file}")
            
        except Exception as e:
            logger.error(f"Error saving crypto data to cache: {str(e)}")
    
    def load_from_cache(self, symbol: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        """Load crypto data from cache."""
        try:
            cache_file = self.cache_dir / f"{symbol}_{period}_{interval}.parquet"
            
            if cache_file.exists():
                data = pd.read_parquet(cache_file)
                logger.info(f"Loaded {symbol} crypto data from cache")
                return data
            
        except Exception as e:
            logger.error(f"Error loading crypto data from cache: {str(e)}")
            
        return None
    
    def get_available_symbols(self) -> List[str]:
        """Get list of crypto symbols available in cache."""
        symbols = set()
        
        for cache_file in self.cache_dir.glob("*.parquet"):
            # Extract symbol from filename (format: SYMBOL_period_interval.parquet)
            symbol = cache_file.stem.split("_")[0]
            symbols.add(symbol)
            
        return sorted(list(symbols))
    
    def get_popular_cryptos(self) -> List[str]:
        """Get list of popular cryptocurrency symbols."""
        return list(self.CRYPTO_SYMBOLS.keys())
    
    def is_crypto_symbol(self, symbol: str) -> bool:
        """Check if a symbol is a cryptocurrency."""
        # Check if it's in our known crypto symbols
        if symbol.upper() in self.CRYPTO_SYMBOLS:
            return True
        
        # Check if it's already in yfinance crypto format
        if any(suffix in symbol.upper() for suffix in ['-USD', '-EUR', '-GBP', '-BTC']):
            return True
        
        return False
    
    def validate_crypto_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate cryptocurrency data for quality and completeness.
        
        Args:
            data: DataFrame with crypto data
            
        Returns:
            Dictionary with validation results
        """
        if data.empty:
            return {'valid': False, 'error': 'Empty data'}
        
        validation_results = {
            'valid': True,
            'total_rows': len(data),
            'date_range': None,
            'missing_values': {},
            'data_gaps': [],
            'warnings': []
        }
        
        try:
            # Check date range
            if 'Date' in data.columns:
                date_col = pd.to_datetime(data['Date'])
                validation_results['date_range'] = {
                    'start': date_col.min().isoformat(),
                    'end': date_col.max().isoformat()
                }
                
                # Check for data gaps (crypto should have 24/7 data)
                expected_days = (date_col.max() - date_col.min()).days
                actual_days = len(data)
                
                if expected_days > actual_days * 1.1:  # Allow 10% tolerance
                    validation_results['warnings'].append(
                        f"Potential data gaps: expected ~{expected_days} days, got {actual_days}"
                    )
            
            # Check for missing values
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if col in data.columns:
                    missing_count = data[col].isna().sum()
                    if missing_count > 0:
                        validation_results['missing_values'][col] = missing_count
            
            # Check for zero volumes (unusual for major cryptos)
            if 'Volume' in data.columns:
                zero_volume_count = (data['Volume'] == 0).sum()
                if zero_volume_count > 0:
                    validation_results['warnings'].append(
                        f"Found {zero_volume_count} rows with zero volume"
                    )
            
            # Check for extreme price movements (>50% in a day)
            if 'Close' in data.columns and len(data) > 1:
                price_changes = data['Close'].pct_change().abs()
                extreme_moves = (price_changes > 0.5).sum()
                if extreme_moves > 0:
                    validation_results['warnings'].append(
                        f"Found {extreme_moves} extreme price movements (>50%)"
                    )
            
        except Exception as e:
            validation_results['valid'] = False
            validation_results['error'] = str(e)
        
        return validation_results