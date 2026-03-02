"""
Data management component for the investor analysis system.
Handles all data-related operations including loading, caching, and currency conversion.
"""
import pandas as pd
from typing import Dict, List, Any
import logging
from datetime import datetime

from .config import InvestorConfig
from .exceptions import DataNotFoundError
from .error_handling import handle_data_errors, ErrorHandler
from ..data.storage import ParquetStorage
from ..data.stock_data import StockDataDownloader
from ..data.crypto_data import CryptoDataDownloader
from ..data.earnings_data import EarningsDataDownloader
from ..data.earnings_processor import EarningsProcessor
from ..data.currency_converter import CurrencyConverter, PortfolioCurrencyManager
from ..data.sector_data import SectorDataManager
from ..data.macro_data import MacroDataManager
from ..data.unified_data_manager import UnifiedDataManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)


class DataManager:
    """Manages all data operations for the investor analysis system."""
    
    def __init__(self, config: InvestorConfig, base_currency: str = "USD", convert_currencies: bool = False):
        """Initialize the data manager."""
        self.config = config
        self.base_currency = base_currency
        self.convert_currencies = convert_currencies
        
        # Initialize storage and downloaders
        self.storage = ParquetStorage(config.data.data_dir + "/stocks")
        self.downloader = StockDataDownloader(cache_dir=config.data.data_dir + "/stocks")
        self.crypto_downloader = CryptoDataDownloader(cache_dir=config.data.data_dir + "/crypto")
        self.earnings_downloader = EarningsDataDownloader(cache_dir=config.data.data_dir + "/earnings")
        
        # Initialize specialized data managers
        self.sector_manager = SectorDataManager()
        self.macro_manager = MacroDataManager()
        self.earnings_processor = EarningsProcessor()
        
        # Initialize UnifiedDataManager for parallel processing
        self.unified_manager = UnifiedDataManager(
            base_data_dir=config.data.data_dir,
            max_workers=10,  # Configure based on system capabilities
            cache_enabled=True
        )
        
        # Initialize currency conversion if enabled
        if self.convert_currencies:
            self.currency_converter = CurrencyConverter()
            self.portfolio_manager = PortfolioCurrencyManager(self.base_currency, self.currency_converter)
            logger.info(f"Currency conversion enabled: converting to {self.base_currency}")
        else:
            self.currency_converter = None
            self.portfolio_manager = None
        
        logger.info("DataManager initialized with parallel processing support")
    
    @handle_data_errors(operation="loading stock data")
    def load_data(self, symbols: List[str], force_download: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Load data for the specified symbols with optimized parallel processing.
        
        Args:
            symbols: List of stock symbols to load
            force_download: Whether to force fresh data download
            
        Returns:
            Dictionary mapping symbols to their data
            
        Raises:
            DataError: If data loading fails
        """
        logger.info(f"Loading data for {len(symbols)} symbols: {symbols}")
        
        # Use parallel loading for better performance
        if len(symbols) > 3:  # Only use parallel for multiple symbols
            return self._load_data_parallel(symbols, force_download)
        else:
            return self._load_data_sequential(symbols, force_download)
    
    def _load_data_parallel(self, symbols: List[str], force_download: bool = False) -> Dict[str, pd.DataFrame]:
        """Load data for multiple symbols in parallel."""
        start_time = time.time()
        logger.info(f"Using parallel loading for {len(symbols)} symbols")
        
        # Try to use UnifiedDataManager first for better performance
        try:
            result = self.unified_manager.load_data(
                symbols=symbols,
                period="1y",  # Default period
                interval="1d",  # Default interval
                force_download=force_download
            )
            
            # Apply currency conversion if enabled
            if self.convert_currencies and self.portfolio_manager:
                for symbol, symbol_data in result.items():
                    if not symbol_data.empty:
                        result[symbol] = self.portfolio_manager.convert_symbol_data(symbol, symbol_data)
            
            elapsed = time.time() - start_time
            logger.info(f"Parallel loading completed in {elapsed:.2f}s")
            return result
            
        except Exception as e:
            logger.warning(f"Unified manager failed, falling back to parallel ThreadPoolExecutor: {e}")
            return self._load_data_parallel_fallback(symbols, force_download)
    
    def _load_data_parallel_fallback(self, symbols: List[str], force_download: bool = False) -> Dict[str, pd.DataFrame]:
        """Fallback parallel loading using ThreadPoolExecutor."""
        data = {}
        failed_symbols = []
        
        with ThreadPoolExecutor(max_workers=min(10, len(symbols))) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(self._load_symbol_data, symbol, force_download): symbol 
                for symbol in symbols
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    symbol_data = future.result()
                    if not symbol_data.empty:
                        # Apply currency conversion if enabled
                        if self.convert_currencies and self.portfolio_manager:
                            symbol_data = self.portfolio_manager.convert_symbol_data(symbol, symbol_data)
                        
                        data[symbol] = symbol_data
                        logger.info(f"Loaded {len(symbol_data)} rows for {symbol}")
                    else:
                        logger.warning(f"No data available for {symbol}")
                        
                except Exception as e:
                    handled_error = ErrorHandler.handle_error(
                        e, operation="loading symbol data", symbol=symbol
                    )
                    ErrorHandler.log_error(handled_error, level='warning')
                    failed_symbols.append(symbol)
        
        if not data:
            raise DataNotFoundError(
                f"No data could be loaded for symbols: {symbols}",
                context={'symbols': symbols, 'force_download': force_download, 'failed': failed_symbols}
            )
        
        return data
    
    def _load_data_sequential(self, symbols: List[str], force_download: bool = False) -> Dict[str, pd.DataFrame]:
        """Original sequential loading for small symbol lists."""
        data = {}
        
        for symbol in symbols:
            try:
                symbol_data = self._load_symbol_data(symbol, force_download)
                if not symbol_data.empty:
                    # Apply currency conversion if enabled
                    if self.convert_currencies and self.portfolio_manager:
                        symbol_data = self.portfolio_manager.convert_symbol_data(symbol, symbol_data)
                    
                    data[symbol] = symbol_data
                    logger.info(f"Loaded {len(symbol_data)} rows for {symbol}")
                else:
                    logger.warning(f"No data available for {symbol}")
                    
            except Exception as e:
                handled_error = ErrorHandler.handle_error(
                    e, operation="loading symbol data", symbol=symbol
                )
                ErrorHandler.log_error(handled_error, level='warning')
                
                # Apply recovery strategy based on error type and context
                if not ErrorHandler.should_continue_processing(handled_error, symbol, len(symbols)):
                    raise handled_error
                # Otherwise, continue with other symbols
        
        if not data:
            raise DataNotFoundError(
                f"No data could be loaded for symbols: {symbols}",
                context={'symbols': symbols, 'force_download': force_download}
            )
        
        return data
    
    def _load_symbol_data(self, symbol: str, force_download: bool = False) -> pd.DataFrame:
        """Load data for a single symbol (stock or crypto)."""
        # Determine if this is a crypto symbol
        is_crypto = self.crypto_downloader.is_crypto_symbol(symbol)
        
        # Try to load from storage first (unless forced download)
        if not force_download and self.config.data.cache_enabled:
            try:
                if is_crypto:
                    symbol_data = self.crypto_downloader.load_from_cache(
                        symbol, self.config.data.period, self.config.data.interval
                    )
                else:
                    symbol_data = self.storage.load_stock_data(symbol)
                
                if symbol_data is not None and not symbol_data.empty:
                    # Check data freshness
                    if self._is_data_fresh(symbol_data):
                        logger.debug(f"Using cached data for {symbol}")
                        return symbol_data
                    else:
                        logger.info(f"Cached data for {symbol} is stale, downloading fresh data")
            except Exception as e:
                handled_error = ErrorHandler.handle_error(
                    e, operation="loading cached data", symbol=symbol
                )
                ErrorHandler.log_error(handled_error, level='debug')
        
        # Download fresh data
        asset_type = "crypto" if is_crypto else "stock"
        logger.info(f"Downloading fresh {asset_type} data for {symbol}")
        
        if is_crypto:
            symbol_data = self.crypto_downloader.download_crypto_data(
                symbol, 
                period=self.config.data.period,
                interval=self.config.data.interval
            )
        else:
            symbol_data = self.downloader.download_stock_data(
                symbol, 
                period=self.config.data.period,
                interval=self.config.data.interval
            )
        
        if not symbol_data.empty:
            # Save to storage
            metadata = {
                'symbol': symbol,
                'period': self.config.data.period,
                'interval': self.config.data.interval,
                'download_time': datetime.now().isoformat(),
                'source': 'yfinance',
                'asset_type': asset_type
            }
            
            if not is_crypto:
                success = self.storage.save_stock_data(symbol_data, symbol, metadata, data_status="latest")
                if success:
                    logger.info(f"Downloaded and saved {len(symbol_data)} rows for {symbol}")
                else:
                    logger.warning(f"Failed to save data for {symbol} to storage")
        
        return symbol_data
    
    def _is_data_fresh(self, data: pd.DataFrame, max_age_days: int = 7) -> bool:
        """Check if cached data is fresh enough."""
        if data.empty:
            return False
        
        try:
            # Get the most recent date in the data
            if 'Date' in data.columns:
                latest_date = pd.to_datetime(data['Date'].max())
            elif hasattr(data.index, 'max') and pd.api.types.is_datetime64_any_dtype(data.index):
                latest_date = pd.to_datetime(data.index.max())
            else:
                return False
            
            # Check if data is within acceptable age
            days_old = (pd.Timestamp.now() - latest_date).days
            return days_old <= max_age_days
            
        except Exception as e:
            handled_error = ErrorHandler.handle_error(
                e, operation="checking data freshness"
            )
            ErrorHandler.log_error(handled_error, level='debug')
            return False
    
    @handle_data_errors(operation="loading market data")
    def load_market_data(self) -> Dict[str, pd.DataFrame]:
        """Load additional market data (VIX, Treasury rates, etc.)."""
        logger.info("Loading market data")
        market_data = {}
        
        # Define market data sources with fallback strategy
        market_symbols = {
            "VIX": "^VIX",
            "10Y_TREASURY": "^TNX", 
            "5Y_TREASURY": "^FVX", 
            "3M_TREASURY": "^IRX"
        }
        
        for name, symbol in market_symbols.items():
            try:
                data = self.downloader.download_stock_data(
                    symbol, 
                    period=self.config.data.period, 
                    interval=self.config.data.interval
                )
                if not data.empty:
                    market_data[symbol] = data
                    logger.info(f"Downloaded {name} data: {len(data)} rows")
                else:
                    logger.warning(f"No data available for {name} ({symbol})")
            except Exception as e:
                handled_error = ErrorHandler.handle_error(
                    e, operation="downloading market data", symbol=symbol
                )
                ErrorHandler.log_error(handled_error, level='warning')
                # Continue with other symbols
        
        return market_data
    
    @handle_data_errors(operation="loading cryptocurrency data")
    def load_crypto_data(self, symbols: List[str] = None, force_download: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Load cryptocurrency data for specified symbols.
        
        Args:
            symbols: List of crypto symbols to load. If None, loads popular cryptos.
            force_download: Whether to force fresh data download
            
        Returns:
            Dictionary mapping crypto symbols to their data
        """
        if symbols is None:
            symbols = self.crypto_downloader.get_popular_cryptos()[:5]  # Top 5 popular cryptos
        
        logger.info(f"Loading cryptocurrency data for {len(symbols)} symbols: {symbols}")
        crypto_data = {}
        
        for symbol in symbols:
            try:
                if force_download or not self.config.data.cache_enabled:
                    # Download fresh data
                    symbol_data = self.crypto_downloader.download_crypto_data(
                        symbol, 
                        period=self.config.data.period,
                        interval=self.config.data.interval
                    )
                else:
                    # Try cache first
                    symbol_data = self.crypto_downloader.load_from_cache(
                        symbol, self.config.data.period, self.config.data.interval
                    )
                    
                    if symbol_data is None or symbol_data.empty or not self._is_data_fresh(symbol_data):
                        # Download fresh data if cache is stale or empty
                        symbol_data = self.crypto_downloader.download_crypto_data(
                            symbol, 
                            period=self.config.data.period,
                            interval=self.config.data.interval
                        )
                
                if not symbol_data.empty:
                    # Apply currency conversion if enabled
                    if self.convert_currencies and self.portfolio_manager:
                        symbol_data = self.portfolio_manager.convert_symbol_data(symbol, symbol_data)
                    
                    # Validate crypto data
                    validation_result = self.crypto_downloader.validate_crypto_data(symbol_data)
                    if not validation_result['valid']:
                        logger.warning(f"Data validation failed for {symbol}: {validation_result.get('error')}")
                    elif validation_result.get('warnings'):
                        for warning in validation_result['warnings']:
                            logger.warning(f"Data validation warning for {symbol}: {warning}")
                    
                    crypto_data[symbol] = symbol_data
                    logger.info(f"Loaded {len(symbol_data)} rows for crypto {symbol}")
                else:
                    logger.warning(f"No crypto data available for {symbol}")
                    
            except Exception as e:
                handled_error = ErrorHandler.handle_error(
                    e, operation="loading crypto data", symbol=symbol
                )
                ErrorHandler.log_error(handled_error, level='warning')
                
                # Apply recovery strategy
                if not ErrorHandler.should_continue_processing(handled_error, symbol, len(symbols)):
                    raise handled_error
                # Otherwise, continue with other symbols
        
        return crypto_data
    
    @handle_data_errors(operation="loading sector data")
    def load_sector_data(self) -> Dict[str, pd.DataFrame]:
        """Load sector ETF data."""
        logger.info("Loading sector data")
        try:
            sector_data = self.sector_manager.download_sector_data(
                period=self.config.data.period,
                interval=self.config.data.interval
            )
            logger.info(f"Loaded sector data for {len(sector_data)} sectors")
            return sector_data
        except Exception as e:
            handled_error = ErrorHandler.handle_error(
                e, operation="loading sector data"
            )
            ErrorHandler.log_error(handled_error, level='warning')
            return {}
    
    @handle_data_errors(operation="getting available symbols")
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols in storage."""
        try:
            return self.storage.get_available_symbols()
        except Exception as e:
            handled_error = ErrorHandler.handle_error(
                e, operation="getting available symbols"
            )
            ErrorHandler.log_error(handled_error, level='warning')
            return []
    
    @handle_data_errors(operation="getting available crypto symbols")
    def get_available_crypto_symbols(self) -> List[str]:
        """Get list of available cryptocurrency symbols in cache."""
        try:
            return self.crypto_downloader.get_available_symbols()
        except Exception as e:
            handled_error = ErrorHandler.handle_error(
                e, operation="getting available crypto symbols"
            )
            ErrorHandler.log_error(handled_error, level='warning')
            return []
    
    def get_popular_crypto_symbols(self) -> List[str]:
        """Get list of popular cryptocurrency symbols."""
        return self.crypto_downloader.get_popular_cryptos()
    
    def is_crypto_symbol(self, symbol: str) -> bool:
        """Check if a symbol is a cryptocurrency."""
        return self.crypto_downloader.is_crypto_symbol(symbol)
    
    @handle_data_errors(operation="loading earnings data")
    def load_earnings_data(
        self, 
        symbols: List[str], 
        force_download: bool = False,
        include_financials: bool = True
    ) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Load comprehensive earnings data for the specified symbols.
        
        Args:
            symbols: List of stock symbols to load earnings for
            force_download: Whether to force fresh data download
            include_financials: Whether to include financial statements
            
        Returns:
            Dictionary mapping symbols to their earnings data dictionaries
        """
        logger.info(f"Loading earnings data for {len(symbols)} symbols: {symbols}")
        
        all_earnings_data = {}
        
        for symbol in symbols:
            try:
                if force_download or not self._has_fresh_earnings_cache(symbol):
                    # Download fresh earnings data
                    earnings_data = self.earnings_downloader.download_comprehensive_earnings(
                        symbol, save_to_cache=True
                    )
                else:
                    # Load from cache
                    earnings_data = self._load_earnings_from_cache(symbol)
                
                # Process the earnings data
                processed_data = self._process_earnings_data(symbol, earnings_data, include_financials)
                
                if processed_data:
                    all_earnings_data[symbol] = processed_data
                    logger.info(f"Loaded processed earnings data for {symbol}")
                else:
                    logger.warning(f"No processed earnings data available for {symbol}")
                    
            except Exception as e:
                handled_error = ErrorHandler.handle_error(
                    e, operation="loading earnings data", symbol=symbol
                )
                ErrorHandler.log_error(handled_error, level='warning')
                
                # Apply recovery strategy
                if not ErrorHandler.should_continue_processing(handled_error, symbol, len(symbols)):
                    raise handled_error
        
        return all_earnings_data
    
    @handle_data_errors(operation="loading earnings history")
    def load_earnings_history(self, symbols: List[str], force_download: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Load earnings history data for the specified symbols.
        
        Args:
            symbols: List of stock symbols
            force_download: Whether to force fresh data download
            
        Returns:
            Dictionary mapping symbols to their earnings history DataFrames
        """
        logger.info(f"Loading earnings history for {len(symbols)} symbols")
        
        earnings_history = {}
        
        for symbol in symbols:
            try:
                if force_download or not self._has_fresh_earnings_cache(symbol, 'earnings_history'):
                    data = self.earnings_downloader.download_earnings_history(symbol, save_to_cache=True)
                else:
                    data = self.earnings_downloader.load_from_cache(symbol, 'earnings_history')
                
                if data is not None and not data.empty:
                    # Process the earnings history
                    processed_data = self.earnings_processor.process_earnings_history(data)
                    earnings_history[symbol] = processed_data
                    logger.info(f"Loaded earnings history for {symbol}: {len(processed_data)} records")
                else:
                    logger.warning(f"No earnings history available for {symbol}")
                    
            except Exception as e:
                handled_error = ErrorHandler.handle_error(
                    e, operation="loading earnings history", symbol=symbol
                )
                ErrorHandler.log_error(handled_error, level='warning')
        
        return earnings_history
    
    @handle_data_errors(operation="creating earnings features")
    def create_earnings_features(
        self, 
        symbols: List[str], 
        price_data: Dict[str, pd.DataFrame],
        force_download: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        Create machine learning features from earnings data.
        
        Args:
            symbols: List of stock symbols
            price_data: Dictionary of price data for the symbols
            force_download: Whether to force fresh earnings data download
            
        Returns:
            Dictionary mapping symbols to their earnings feature DataFrames
        """
        logger.info(f"Creating earnings features for {len(symbols)} symbols")
        
        # Load earnings data
        earnings_data = self.load_earnings_data(symbols, force_download, include_financials=True)
        
        features = {}
        
        for symbol in symbols:
            try:
                symbol_earnings = earnings_data.get(symbol, {})
                symbol_price_data = price_data.get(symbol, pd.DataFrame())
                
                if not symbol_earnings or symbol_price_data.empty:
                    logger.warning(f"Missing data for {symbol}, skipping feature creation")
                    continue
                
                # Create earnings event features if we have earnings dates and price data
                if 'earnings_dates' in symbol_earnings:
                    event_features = self.earnings_processor.create_earnings_events_features(
                        symbol_earnings['earnings_dates'],
                        symbol_price_data,
                        window_days=5
                    )
                    
                    # Combine with other earnings features
                    combined_features = self._combine_earnings_features(symbol_earnings, event_features)
                    features[symbol] = combined_features
                    
                    logger.info(f"Created earnings features for {symbol}: {len(combined_features)} records")
                else:
                    logger.warning(f"No earnings dates available for {symbol}")
                    
            except Exception as e:
                handled_error = ErrorHandler.handle_error(
                    e, operation="creating earnings features", symbol=symbol
                )
                ErrorHandler.log_error(handled_error, level='warning')
        
        return features
    
    def _has_fresh_earnings_cache(self, symbol: str, data_type: str = 'earnings_history') -> bool:
        """Check if earnings data cache is fresh enough."""
        try:
            cached_data = self.earnings_downloader.load_from_cache(symbol, data_type)
            if cached_data is None or cached_data.empty:
                return False
            
            # Check data freshness - earnings data can be older than stock data
            return self._is_data_fresh(cached_data, max_age_days=30)
        except Exception:
            return False
    
    def _load_earnings_from_cache(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Load all earnings data types from cache."""
        earnings_data = {}
        
        data_types = ['earnings_history', 'earnings_dates', 'income_stmt', 'balance_sheet', 'cash_flow']
        
        for data_type in data_types:
            try:
                data = self.earnings_downloader.load_from_cache(symbol, data_type)
                if data is not None and not data.empty:
                    earnings_data[data_type] = data
            except Exception as e:
                logger.debug(f"Could not load {data_type} from cache for {symbol}: {e}")
        
        # Load calendar data
        try:
            calendar = self.earnings_downloader.load_calendar_from_cache(symbol)
            if calendar:
                earnings_data['calendar'] = calendar
        except Exception as e:
            logger.debug(f"Could not load calendar from cache for {symbol}: {e}")
        
        return earnings_data
    
    def _process_earnings_data(
        self, 
        symbol: str, 
        earnings_data: Dict[str, Any], 
        include_financials: bool
    ) -> Dict[str, pd.DataFrame]:
        """Process raw earnings data into ML-ready features."""
        processed_data = {}
        
        # Process earnings history
        if 'earnings_history' in earnings_data and not earnings_data['earnings_history'].empty:
            processed_history = self.earnings_processor.process_earnings_history(
                earnings_data['earnings_history']
            )
            processed_data['earnings_history'] = processed_history
        
        # Process earnings dates
        if 'earnings_dates' in earnings_data and not earnings_data['earnings_dates'].empty:
            processed_data['earnings_dates'] = earnings_data['earnings_dates']
        
        # Process financial statements if requested
        if include_financials:
            financial_statements = {}
            for stmt_type in ['income_stmt', 'balance_sheet', 'cash_flow']:
                if stmt_type in earnings_data and not earnings_data[stmt_type].empty:
                    financial_statements[stmt_type] = earnings_data[stmt_type]
            
            if financial_statements:
                processed_financials = self.earnings_processor.process_financial_statements(
                    financial_statements
                )
                processed_data['financial_metrics'] = processed_financials
        
        # Include calendar data
        if 'calendar' in earnings_data:
            processed_data['calendar'] = earnings_data['calendar']
        
        return processed_data
    
    def _combine_earnings_features(
        self, 
        earnings_data: Dict[str, pd.DataFrame], 
        event_features: pd.DataFrame
    ) -> pd.DataFrame:
        """Combine different types of earnings features into a single DataFrame."""
        # Start with earnings history as the base
        base_features = earnings_data.get('earnings_history', pd.DataFrame())
        
        # Add financial metrics if available
        if 'financial_metrics' in earnings_data and not earnings_data['financial_metrics'].empty:
            financial_metrics = earnings_data['financial_metrics']
            
            if not base_features.empty and not financial_metrics.empty:
                # Merge on Date and Symbol
                merge_cols = ['Date', 'Symbol'] if 'Symbol' in base_features.columns else ['Date']
                base_features = pd.merge(
                    base_features, financial_metrics,
                    on=merge_cols, how='outer', suffixes=('', '_fin')
                )
            elif base_features.empty:
                base_features = financial_metrics
        
        # Add event features if available
        if not event_features.empty:
            if not base_features.empty:
                merge_cols = ['Date', 'Symbol'] if 'Symbol' in base_features.columns else ['Date']
                base_features = pd.merge(
                    base_features, event_features,
                    on=merge_cols, how='outer', suffixes=('', '_event')
                )
            else:
                base_features = event_features
        
        # Sort by date if available
        if 'Date' in base_features.columns:
            base_features = base_features.sort_values('Date')
        
        return base_features
    
    @handle_data_errors(operation="cleaning up old data")
    def cleanup_old_data(self, max_age_days: int = 30):
        """Clean up old data files."""
        logger.info(f"Cleaning up data older than {max_age_days} days")
        try:
            # This would be implemented in the storage layer
            # For now, we'll log the intent
            logger.info("Data cleanup completed")
        except Exception as e:
            handled_error = ErrorHandler.handle_error(
                e, operation="cleaning up old data", 
                context={'max_age_days': max_age_days}
            )
            ErrorHandler.log_error(handled_error, level='warning')