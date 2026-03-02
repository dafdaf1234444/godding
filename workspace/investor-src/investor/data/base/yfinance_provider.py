"""
Unified yfinance data provider for all asset types.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Callable
import logging

from .interfaces import IDataProvider, DataRequest, DataResponse, DataProviderType, DataStatus, ValidationResult
from .utils import ParallelDataFetcher, DataNormalizer, DataValidator, profile_performance
from .cache_manager import UnifiedCacheManager

logger = logging.getLogger(__name__)


class YFinanceDataProvider(IDataProvider):
    """Unified yfinance data provider for stocks, crypto, ETFs, and indices."""
    
    def __init__(self, 
                 provider_type: DataProviderType,
                 cache_manager: UnifiedCacheManager = None,
                 symbol_transformer: Callable[[str], str] = None,
                 data_transformer: Callable[[pd.DataFrame, str], pd.DataFrame] = None,
                 max_workers: int = 10):
        """
        Initialize yfinance data provider.
        
        Args:
            provider_type: Type of data this provider handles
            cache_manager: Cache manager instance
            symbol_transformer: Function to transform symbols for yfinance
            data_transformer: Function to add provider-specific features
            max_workers: Maximum workers for parallel processing
        """
        self._provider_type = provider_type
        self.cache_manager = cache_manager
        self.symbol_transformer = symbol_transformer or (lambda x: x)
        self.data_transformer = data_transformer or (lambda data, symbol: data)
        self.parallel_fetcher = ParallelDataFetcher(max_workers)
        
    @property
    def provider_type(self) -> DataProviderType:
        """Get the type of this data provider."""
        return self._provider_type
    
    @property
    def supported_symbols(self) -> List[str]:
        """Get list of supported symbols (dynamic for yfinance)."""
        # yfinance supports a wide range of symbols, return empty list to indicate dynamic support
        return []
    
    @profile_performance
    def download_data(self, request: DataRequest) -> DataResponse:
        """Download data for the specified request."""
        start_time = datetime.now()
        errors = []
        warnings = []
        data = {}
        
        # Validate symbols
        valid_symbols = self.validate_symbols(request.symbols)
        if not valid_symbols:
            return DataResponse(
                data={},
                metadata={'error': 'No valid symbols found'},
                status=DataStatus.FAILED,
                provider_type=self.provider_type,
                timestamp=start_time,
                errors=['No valid symbols provided']
            )
        
        # Check cache first if not forcing download
        if not request.force_download and self.cache_manager:
            cached_data, cache_errors = self._load_from_cache(valid_symbols, request)
            data.update(cached_data)
            errors.extend(cache_errors)
            
            # Remove cached symbols from download list
            valid_symbols = [s for s in valid_symbols if s not in data]
        
        # Download remaining symbols
        if valid_symbols:
            downloaded_data, download_errors = self._download_symbols(valid_symbols, request)
            data.update(downloaded_data)
            errors.extend(download_errors)
            
            # Cache downloaded data
            if self.cache_manager:
                self._save_to_cache(downloaded_data, request)
        
        # Determine overall status
        status = DataStatus.LATEST if data else DataStatus.FAILED
        if errors:
            warnings.extend(errors)  # Treat errors as warnings if we have some data
        
        return DataResponse(
            data=data,
            metadata={
                'download_time': datetime.now().isoformat(),
                'provider': 'yfinance',
                'request_symbols': request.symbols,
                'successful_symbols': list(data.keys()),
                'cache_hits': len(request.symbols) - len(valid_symbols) if not request.force_download else 0
            },
            status=status,
            provider_type=self.provider_type,
            timestamp=start_time,
            errors=errors if not data else None,
            warnings=warnings if warnings else None
        )
    
    def validate_symbols(self, symbols: List[str]) -> List[str]:
        """Validate and filter supported symbols."""
        # For yfinance, we accept most symbols and let yfinance validate
        # Symbol transformer can handle provider-specific formatting
        return [s for s in symbols if s and isinstance(s, str)]
    
    def validate_data(self, data: pd.DataFrame, symbol: str) -> ValidationResult:
        """Validate downloaded data quality."""
        if data is None or data.empty:
            return ValidationResult(
                valid=False,
                errors=[f"No data found for symbol {symbol}"]
            )
        
        errors = []
        warnings = []
        
        # Basic DataFrame validation
        if not DataValidator.is_valid_dataframe(data, ['Close']):
            errors.append("Invalid DataFrame structure")
        
        # Price data validation
        price_issues = DataValidator.validate_price_data(data)
        warnings.extend(price_issues)
        
        # Date validation
        if 'Date' in data.columns:
            date_issues = DataValidator.validate_date_range(data)
            warnings.extend(date_issues)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors if errors else None,
            warnings=warnings if warnings else None,
            metadata={
                'rows': len(data),
                'columns': list(data.columns),
                'date_range': self._get_date_range(data)
            }
        )
    
    def _download_symbols(self, symbols: List[str], request: DataRequest) -> tuple[Dict[str, pd.DataFrame], List[str]]:
        """Download data for multiple symbols."""
        errors = []
        
        def download_single(symbol: str) -> pd.DataFrame:
            """Download data for a single symbol."""
            try:
                # Transform symbol for yfinance if needed
                yf_symbol = self.symbol_transformer(symbol)
                
                # Create ticker and download data
                ticker = yf.Ticker(yf_symbol)
                
                if request.start and request.end:
                    data = ticker.history(start=request.start, end=request.end, interval=request.interval)
                else:
                    data = ticker.history(period=request.period, interval=request.interval)
                
                if data.empty:
                    logger.warning(f"No data found for symbol {symbol} ({yf_symbol})")
                    return pd.DataFrame()
                
                # Normalize data
                data = DataNormalizer.reset_index_to_column(data)
                data = DataNormalizer.normalize_dates(data)
                data = DataNormalizer.normalize_numeric_columns(data)
                data = DataNormalizer.add_symbol_column(data, symbol)
                
                # Apply provider-specific transformations
                data = self.data_transformer(data, symbol)
                
                logger.info(f"Downloaded {len(data)} rows for {symbol}")
                return data
                
            except Exception as e:
                error_msg = f"Error downloading data for {symbol}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                return pd.DataFrame()
        
        # Use parallel fetcher
        results = self.parallel_fetcher.fetch_parallel(
            symbols, 
            download_single,
            use_parallel=len(symbols) > 2
        )
        
        # Filter out empty results
        data = {symbol: df for symbol, df in results.items() if df is not None and not df.empty}
        
        return data, errors
    
    def _load_from_cache(self, symbols: List[str], request: DataRequest) -> tuple[Dict[str, pd.DataFrame], List[str]]:
        """Load data from cache for symbols."""
        cached_data = {}
        errors = []
        
        for symbol in symbols:
            try:
                cache_key = self.get_cache_key(symbol, request.period, request.interval)
                
                if self.cache_manager.exists(cache_key) and self.cache_manager.is_fresh(cache_key, max_age_hours=24):
                    data = self.cache_manager.get(cache_key)
                    if data is not None and not data.empty:
                        cached_data[symbol] = data
                        logger.debug(f"Loaded {symbol} from cache")
                    
            except Exception as e:
                error_msg = f"Error loading {symbol} from cache: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        return cached_data, errors
    
    def _save_to_cache(self, data: Dict[str, pd.DataFrame], request: DataRequest) -> None:
        """Save downloaded data to cache."""
        if not self.cache_manager:
            return
        
        for symbol, df in data.items():
            if df is not None and not df.empty:
                try:
                    cache_key = self.get_cache_key(symbol, request.period, request.interval)
                    metadata = {
                        'symbol': symbol,
                        'period': request.period,
                        'interval': request.interval,
                        'provider_type': self.provider_type.value,
                        'download_time': datetime.now().isoformat(),
                        'rows': len(df),
                        'columns': list(df.columns)
                    }
                    
                    self.cache_manager.set(cache_key, df, metadata)
                    logger.debug(f"Cached data for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Error caching data for {symbol}: {str(e)}")
    
    def _get_date_range(self, data: pd.DataFrame) -> Optional[Dict[str, str]]:
        """Get date range from data."""
        if data.empty or 'Date' not in data.columns:
            return None
        
        try:
            dates = pd.to_datetime(data['Date'])
            return {
                'start': dates.min().isoformat(),
                'end': dates.max().isoformat()
            }
        except Exception:
            return None