"""
Cryptocurrency data provider using the unified architecture.
"""
import pandas as pd
from typing import List, Dict
import logging

from ..base.interfaces import DataProviderType
from ..base.yfinance_provider import YFinanceDataProvider
from ..base.cache_manager import UnifiedCacheManager

logger = logging.getLogger(__name__)


def create_crypto_provider(cache_dir: str = None, max_workers: int = 10) -> YFinanceDataProvider:
    """Create a cryptocurrency data provider with unified architecture."""
    
    # Create cache manager
    cache_manager = UnifiedCacheManager(cache_dir) if cache_dir else None
    
    def crypto_symbol_transformer(symbol: str) -> str:
        """Transform crypto symbols for yfinance."""
        symbol = symbol.upper().strip()
        
        # If already in yfinance format, return as is
        if '-USD' in symbol or '-EUR' in symbol or '-GBP' in symbol:
            return symbol
        
        # Check if it's a known crypto symbol
        crypto_mappings = CryptoSymbolMappings.get_symbol_mappings()
        if symbol in crypto_mappings:
            return crypto_mappings[symbol]
        
        # Default to USD pair
        return f"{symbol}-USD"
    
    def crypto_data_transformer(data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Add cryptocurrency-specific features to data."""
        if data.empty:
            return data
        
        data = data.copy()
        
        # Add crypto-specific metadata
        data['AssetType'] = 'crypto'
        data['YahooSymbol'] = crypto_symbol_transformer(symbol)
        data['Is_24_7_Trading'] = True
        
        if 'Close' in data.columns and 'Volume' in data.columns:
            # Calculate crypto-specific volatility (more important for crypto)
            if len(data) >= 24:  # 24-hour rolling for crypto
                data['Volatility'] = data['Close'].pct_change().rolling(window=24).std()
            
            # Calculate trading intensity (volume relative to price)
            data['Trading_Intensity'] = data['Volume'] / data['Close']
            
            # Calculate price momentum for different timeframes
            data['Price_Momentum_1d'] = data['Close'].pct_change(1)
            if len(data) >= 7:
                data['Price_Momentum_7d'] = data['Close'].pct_change(7)
            if len(data) >= 30:
                data['Price_Momentum_30d'] = data['Close'].pct_change(30)
            
            # Calculate moving averages (important for crypto trends)
            if len(data) >= 7:
                data['MA_7'] = data['Close'].rolling(window=7).mean()
            if len(data) >= 30:
                data['MA_30'] = data['Close'].rolling(window=30).mean()
            if len(data) >= 200:
                data['MA_200'] = data['Close'].rolling(window=200).mean()
        
        return data
    
    return YFinanceDataProvider(
        provider_type=DataProviderType.CRYPTO,
        cache_manager=cache_manager,
        symbol_transformer=crypto_symbol_transformer,
        data_transformer=crypto_data_transformer,
        max_workers=max_workers
    )


class CryptoSymbolMappings:
    """Helper class for cryptocurrency symbol mappings."""
    
    @classmethod
    def get_symbol_mappings(cls) -> Dict[str, str]:
        """Get mapping of crypto symbols to yfinance format."""
        return {
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
            'DOGE': 'DOGE-USD',
            'SHIB': 'SHIB-USD',
            'ATOM': 'ATOM-USD',
            'FTM': 'FTM-USD',
            'NEAR': 'NEAR-USD',
            'SAND': 'SAND-USD'
        }
    
    @classmethod
    def get_popular_cryptos(cls) -> List[str]:
        """Get list of popular cryptocurrency symbols."""
        return list(cls.get_symbol_mappings().keys())
    
    @classmethod
    def is_crypto_symbol(cls, symbol: str) -> bool:
        """Check if a symbol is a cryptocurrency."""
        symbol = symbol.upper().strip()
        
        # Check if it's in our known crypto symbols
        if symbol in cls.get_symbol_mappings():
            return True
        
        # Check if it's already in yfinance crypto format
        crypto_suffixes = ['-USD', '-EUR', '-GBP', '-BTC']
        if any(suffix in symbol for suffix in crypto_suffixes):
            return True
        
        return False
    
    @classmethod
    def validate_crypto_data(cls, data: pd.DataFrame, symbol: str) -> Dict[str, any]:
        """
        Validate cryptocurrency data for quality and completeness.
        
        Args:
            data: DataFrame with crypto data
            symbol: Crypto symbol being validated
            
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
            
            # Check for extreme price movements (>50% in a day - common for crypto)
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
    
    @classmethod
    def get_crypto_categories(cls) -> Dict[str, List[str]]:
        """Get cryptocurrencies grouped by category."""
        return {
            'large_cap': ['BTC', 'ETH', 'ADA', 'SOL', 'DOT'],
            'defi': ['UNI', 'AAVE', 'LINK', 'MATIC'],
            'layer1': ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'ATOM', 'NEAR'],
            'layer2': ['MATIC', 'FTM'],
            'meme': ['DOGE', 'SHIB'],
            'metaverse': ['SAND'],
            'payments': ['XRP', 'LTC', 'BCH'],
            'algorithms': ['ALGO']
        }