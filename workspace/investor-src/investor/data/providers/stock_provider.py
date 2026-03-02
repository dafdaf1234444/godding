"""
Stock data provider using the unified architecture.
"""
import pandas as pd
from typing import List
import logging

from ..base.interfaces import DataProviderType
from ..base.yfinance_provider import YFinanceDataProvider
from ..base.cache_manager import UnifiedCacheManager

logger = logging.getLogger(__name__)


def create_stock_provider(cache_dir: str = None, max_workers: int = 10) -> YFinanceDataProvider:
    """Create a stock data provider with unified architecture."""
    
    # Create cache manager
    cache_manager = UnifiedCacheManager(cache_dir) if cache_dir else None
    
    def stock_symbol_transformer(symbol: str) -> str:
        """Transform stock symbols for yfinance (minimal transformation needed)."""
        # Most stock symbols work directly with yfinance
        return symbol.upper()
    
    def stock_data_transformer(data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Add stock-specific features to data."""
        if data.empty:
            return data
        
        data = data.copy()
        
        # Add asset type
        data['AssetType'] = 'stock'
        
        # Add basic technical indicators commonly used for stocks
        if 'Close' in data.columns and len(data) > 1:
            # Simple moving averages
            if len(data) >= 20:
                data['SMA_20'] = data['Close'].rolling(window=20).mean()
            if len(data) >= 50:
                data['SMA_50'] = data['Close'].rolling(window=50).mean()
            
            # Daily returns
            data['Daily_Return'] = data['Close'].pct_change()
            
            # Volatility (20-day rolling)
            if len(data) >= 20:
                data['Volatility_20d'] = data['Daily_Return'].rolling(window=20).std()
        
        # Add trading day indicator (excludes weekends)
        if 'Date' in data.columns:
            dates = pd.to_datetime(data['Date'])
            data['Is_Trading_Day'] = ~dates.dt.weekday.isin([5, 6])  # Not Saturday or Sunday
        
        return data
    
    return YFinanceDataProvider(
        provider_type=DataProviderType.STOCK,
        cache_manager=cache_manager,
        symbol_transformer=stock_symbol_transformer,
        data_transformer=stock_data_transformer,
        max_workers=max_workers
    )


class StockSymbolValidator:
    """Helper class for stock symbol validation."""
    
    COMMON_STOCK_PATTERNS = [
        # US stocks are typically 1-4 letters
        r'^[A-Z]{1,4}$',
        # Some stocks have dots or dashes
        r'^[A-Z]{1,4}[-\.][A-Z]$',
        # Some have numbers
        r'^[A-Z]{1,4}[0-9]$'
    ]
    
    KNOWN_EXCHANGES = [
        'NASDAQ', 'NYSE', 'TSX', 'LSE', 'ASX'
    ]
    
    @classmethod
    def is_likely_stock_symbol(cls, symbol: str) -> bool:
        """Check if symbol is likely a stock symbol."""
        import re
        
        symbol = symbol.upper().strip()
        
        # Check against common patterns
        for pattern in cls.COMMON_STOCK_PATTERNS:
            if re.match(pattern, symbol):
                return True
        
        # Additional heuristics
        if len(symbol) <= 5 and symbol.isalpha():
            return True
        
        return False
    
    @classmethod
    def get_popular_stocks(cls) -> List[str]:
        """Get list of popular stock symbols."""
        return [
            # Tech giants
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA',
            # Traditional blue chips
            'JNJ', 'WMT', 'JPM', 'V', 'PG', 'UNH', 'HD', 'MA',
            # Other popular stocks
            'DIS', 'NFLX', 'CRM', 'ADBE', 'PYPL', 'INTC', 'AMD',
            'BABA', 'TSM', 'ASML', 'TM', 'NVO', 'RHHBY'
        ]