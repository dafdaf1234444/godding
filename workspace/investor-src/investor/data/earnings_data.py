"""
Earnings data downloader using yfinance.
Provides comprehensive earnings data for machine learning models.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import logging
from pathlib import Path
import concurrent.futures
import time
from functools import wraps

from ..utils.performance import profile_performance

logger = logging.getLogger(__name__)




class EarningsDataDownloader:
    """Downloads earnings data using yfinance."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the earnings data downloader.
        
        Args:
            cache_dir: Directory to cache downloaded data
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / "data" / "earnings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def download_earnings_history(
        self,
        symbol: str,
        save_to_cache: bool = True
    ) -> pd.DataFrame:
        """
        Download earnings history for a given symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'GOOGL')
            save_to_cache: Whether to save data to cache
            
        Returns:
            DataFrame with earnings history (epsActual, epsEstimate, epsDifference, surprisePercent)
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Download earnings history
            earnings_history = ticker.get_earnings_history()
            
            if earnings_history is None or earnings_history.empty:
                logger.warning(f"No earnings history found for symbol {symbol}")
                return pd.DataFrame()
            
            # Add symbol column
            earnings_history['Symbol'] = symbol
            
            # Reset index to make quarter a column
            earnings_history = earnings_history.reset_index()
            
            # Convert quarter to datetime if it's not already
            if 'quarter' in earnings_history.columns:
                earnings_history['quarter'] = pd.to_datetime(earnings_history['quarter'])
                earnings_history = earnings_history.rename(columns={'quarter': 'Date'})
            
            if save_to_cache:
                self._save_to_cache(earnings_history, symbol, "earnings_history")
            
            logger.info(f"Downloaded earnings history for {symbol}: {len(earnings_history)} records")
            return earnings_history
            
        except Exception as e:
            logger.error(f"Error downloading earnings history for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def download_earnings_dates(
        self,
        symbol: str,
        save_to_cache: bool = True
    ) -> pd.DataFrame:
        """
        Download earnings dates and estimates for a given symbol.
        
        Args:
            symbol: Stock symbol
            save_to_cache: Whether to save data to cache
            
        Returns:
            DataFrame with earnings dates and estimates
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Download earnings dates
            earnings_dates = ticker.get_earnings_dates()
            
            if earnings_dates is None or earnings_dates.empty:
                logger.warning(f"No earnings dates found for symbol {symbol}")
                return pd.DataFrame()
            
            # Add symbol column
            earnings_dates['Symbol'] = symbol
            
            # Reset index to make earnings date a column
            earnings_dates = earnings_dates.reset_index()
            earnings_dates = earnings_dates.rename(columns={'Earnings Date': 'Date'})
            
            # Convert to datetime if it's not already
            earnings_dates['Date'] = pd.to_datetime(earnings_dates['Date'])
            
            if save_to_cache:
                self._save_to_cache(earnings_dates, symbol, "earnings_dates")
            
            logger.info(f"Downloaded earnings dates for {symbol}: {len(earnings_dates)} records")
            return earnings_dates
            
        except Exception as e:
            logger.error(f"Error downloading earnings dates for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def download_financial_statements(
        self,
        symbol: str,
        save_to_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Download quarterly financial statements for a given symbol.
        
        Args:
            symbol: Stock symbol
            save_to_cache: Whether to save data to cache
            
        Returns:
            Dictionary with financial statements (income_stmt, balance_sheet, cash_flow)
        """
        try:
            ticker = yf.Ticker(symbol)
            financial_data = {}
            
            # Download quarterly financial statements
            statements = {
                'income_stmt': ticker.quarterly_income_stmt,
                'balance_sheet': ticker.quarterly_balance_sheet,
                'cash_flow': ticker.quarterly_cash_flow
            }
            
            for stmt_type, stmt_data in statements.items():
                if stmt_data is not None and not stmt_data.empty:
                    # Transpose so dates are rows and metrics are columns
                    stmt_df = stmt_data.T
                    stmt_df['Symbol'] = symbol
                    stmt_df = stmt_df.reset_index()
                    stmt_df = stmt_df.rename(columns={'index': 'Date'})
                    
                    # Convert to datetime
                    stmt_df['Date'] = pd.to_datetime(stmt_df['Date'])
                    
                    financial_data[stmt_type] = stmt_df
                    
                    if save_to_cache:
                        self._save_to_cache(stmt_df, symbol, stmt_type)
                    
                    logger.info(f"Downloaded {stmt_type} for {symbol}: {len(stmt_df)} records")
                else:
                    logger.warning(f"No {stmt_type} data found for {symbol}")
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Error downloading financial statements for {symbol}: {str(e)}")
            return {}
    
    def download_earnings_calendar(
        self,
        symbol: str,
        save_to_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Download earnings calendar information for a given symbol.
        
        Args:
            symbol: Stock symbol
            save_to_cache: Whether to save data to cache
            
        Returns:
            Dictionary with calendar information
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Download earnings calendar
            calendar = ticker.get_calendar()
            
            if calendar is None or not calendar:
                logger.warning(f"No earnings calendar found for symbol {symbol}")
                return {}
            
            # Add symbol to calendar data
            calendar['Symbol'] = symbol
            
            if save_to_cache:
                self._save_calendar_to_cache(calendar, symbol)
            
            logger.info(f"Downloaded earnings calendar for {symbol}")
            return calendar
            
        except Exception as e:
            logger.error(f"Error downloading earnings calendar for {symbol}: {str(e)}")
            return {}
    
    @profile_performance
    def download_comprehensive_earnings(
        self,
        symbol: str,
        save_to_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Download all earnings-related data for a symbol.
        
        Args:
            symbol: Stock symbol
            save_to_cache: Whether to save data to cache
            
        Returns:
            Dictionary with all earnings data types
        """
        logger.info(f"Downloading comprehensive earnings data for {symbol}")
        
        earnings_data = {
            'earnings_history': self.download_earnings_history(symbol, save_to_cache),
            'earnings_dates': self.download_earnings_dates(symbol, save_to_cache),
            'calendar': self.download_earnings_calendar(symbol, save_to_cache)
        }
        
        # Download financial statements
        financial_statements = self.download_financial_statements(symbol, save_to_cache)
        earnings_data.update(financial_statements)
        
        return earnings_data
    
    @profile_performance
    def download_multiple_symbols(
        self,
        symbols: List[str],
        save_to_cache: bool = True,
        max_workers: int = 10,
        use_parallel: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Download earnings data for multiple symbols with parallel processing.
        
        Args:
            symbols: List of stock symbols
            save_to_cache: Whether to save data to cache
            max_workers: Maximum number of parallel workers
            use_parallel: Whether to use parallel processing
            
        Returns:
            Dictionary mapping symbols to their earnings data
        """
        if not use_parallel or len(symbols) <= 2:
            return self._download_sequential(symbols, save_to_cache)
        
        return self._download_parallel(symbols, save_to_cache, max_workers)
    
    def _download_sequential(
        self,
        symbols: List[str],
        save_to_cache: bool
    ) -> Dict[str, Dict[str, Any]]:
        """Download earnings data sequentially."""
        results = {}
        
        for symbol in symbols:
            logger.info(f"Downloading earnings data for {symbol}")
            earnings_data = self.download_comprehensive_earnings(symbol, save_to_cache)
            results[symbol] = earnings_data
            
        return results
    
    def _download_parallel(
        self,
        symbols: List[str],
        save_to_cache: bool,
        max_workers: int
    ) -> Dict[str, Dict[str, Any]]:
        """Download earnings data in parallel."""
        results = {}
        
        def download_single(symbol: str) -> Tuple[str, Dict[str, Any]]:
            """Download earnings data for a single symbol."""
            earnings_data = self.download_comprehensive_earnings(symbol, save_to_cache)
            return symbol, earnings_data
        
        logger.info(f"Downloading earnings data for {len(symbols)} symbols in parallel (max_workers={max_workers})")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(download_single, symbol): symbol 
                for symbol in symbols
            }
            
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    symbol_result, earnings_data = future.result()
                    results[symbol_result] = earnings_data
                    logger.info(f"Completed earnings download for {symbol_result}")
                except Exception as e:
                    logger.error(f"Error downloading earnings for {symbol}: {e}")
                    results[symbol] = {}
        
        logger.info(f"Parallel earnings download completed for {len(results)} symbols")
        return results
    
    def _save_to_cache(self, data: pd.DataFrame, symbol: str, data_type: str):
        """Save DataFrame to cache as parquet file."""
        try:
            cache_file = self.cache_dir / f"{symbol}_{data_type}.parquet"
            
            # Add metadata
            data.attrs['symbol'] = symbol
            data.attrs['data_type'] = data_type
            data.attrs['download_time'] = datetime.now().isoformat()
            
            data.to_parquet(cache_file, index=False)
            logger.debug(f"Saved {symbol} {data_type} to cache: {cache_file}")
            
        except Exception as e:
            logger.error(f"Error saving {data_type} to cache: {str(e)}")
    
    def _save_calendar_to_cache(self, calendar: Dict[str, Any], symbol: str):
        """Save calendar data to cache as JSON."""
        try:
            import json
            cache_file = self.cache_dir / f"{symbol}_calendar.json"
            
            # Convert datetime objects to strings for JSON serialization
            calendar_serializable = {}
            for key, value in calendar.items():
                if hasattr(value, 'isoformat'):
                    calendar_serializable[key] = value.isoformat()
                elif isinstance(value, list):
                    calendar_serializable[key] = [
                        item.isoformat() if hasattr(item, 'isoformat') else item 
                        for item in value
                    ]
                else:
                    calendar_serializable[key] = value
            
            calendar_serializable['download_time'] = datetime.now().isoformat()
            
            with open(cache_file, 'w') as f:
                json.dump(calendar_serializable, f, indent=2)
            
            logger.debug(f"Saved {symbol} calendar to cache: {cache_file}")
            
        except Exception as e:
            logger.error(f"Error saving calendar to cache: {str(e)}")
    
    def load_from_cache(self, symbol: str, data_type: str) -> Optional[pd.DataFrame]:
        """Load earnings data from cache."""
        try:
            cache_file = self.cache_dir / f"{symbol}_{data_type}.parquet"
            
            if cache_file.exists():
                data = pd.read_parquet(cache_file)
                logger.debug(f"Loaded {symbol} {data_type} from cache")
                return data
            
        except Exception as e:
            logger.error(f"Error loading {data_type} from cache: {str(e)}")
            
        return None
    
    def load_calendar_from_cache(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Load calendar data from cache."""
        try:
            import json
            cache_file = self.cache_dir / f"{symbol}_calendar.json"
            
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    calendar = json.load(f)
                logger.debug(f"Loaded {symbol} calendar from cache")
                return calendar
            
        except Exception as e:
            logger.error(f"Error loading calendar from cache: {str(e)}")
            
        return None
    
    def get_available_symbols(self) -> List[str]:
        """Get list of symbols available in cache."""
        symbols = set()
        
        for cache_file in self.cache_dir.glob("*.parquet"):
            # Extract symbol from filename
            symbol = cache_file.stem.split("_")[0]
            symbols.add(symbol)
            
        return sorted(list(symbols))
    
    def validate_earnings_data(self, data: pd.DataFrame, data_type: str) -> Dict[str, Any]:
        """
        Validate earnings data quality and completeness.
        
        Args:
            data: DataFrame to validate
            data_type: Type of earnings data
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        if data.empty:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Empty {data_type} data")
            return validation_result
        
        # Common validations
        if 'Date' in data.columns:
            if data['Date'].isnull().any():
                validation_result['warnings'].append("Missing dates found")
            
            # Check for future dates (potential data leakage)
            future_dates = data['Date'] > pd.Timestamp.now()
            if future_dates.any():
                validation_result['warnings'].append(f"Found {future_dates.sum()} future dates")
        
        # Data type specific validations
        if data_type == 'earnings_history':
            required_cols = ['epsActual', 'epsEstimate']
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required columns: {missing_cols}")
            
            # Check for reasonable EPS values
            if 'epsActual' in data.columns:
                extreme_eps = (data['epsActual'].abs() > 100)
                if extreme_eps.any():
                    validation_result['warnings'].append(f"Found {extreme_eps.sum()} extreme EPS values (>100)")
        
        elif data_type == 'earnings_dates':
            if 'EPS Estimate' in data.columns:
                missing_estimates = data['EPS Estimate'].isnull().sum()
                if missing_estimates > 0:
                    validation_result['warnings'].append(f"Missing EPS estimates: {missing_estimates}")
        
        return validation_result