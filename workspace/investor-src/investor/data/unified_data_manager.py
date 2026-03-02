"""
Unified data manager using the redesigned architecture.
Replaces the existing DataManager with a cleaner, more efficient design.
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from pathlib import Path

from .base.interfaces import DataRequest, DataProviderType
from .base.provider_registry import DataProviderRegistry
from .base.cache_manager import UnifiedCacheManager
from .providers.stock_provider import create_stock_provider
from .providers.crypto_provider import create_crypto_provider, CryptoSymbolMappings

# Import existing providers for fallback
from .macro_data import MacroDataManager
from .sector_data import SectorDataManager

logger = logging.getLogger(__name__)


class UnifiedDataManager:
    """
    Unified data manager using the redesigned architecture.
    Provides a clean interface for all data operations.
    """
    
    def __init__(self, 
                 base_data_dir: str = "data",
                 max_workers: int = 10,
                 cache_enabled: bool = True):
        """
        Initialize the unified data manager.
        
        Args:
            base_data_dir: Base directory for data storage
            max_workers: Maximum workers for parallel processing
            cache_enabled: Whether to enable caching
        """
        self.base_data_dir = Path(base_data_dir)
        self.max_workers = max_workers
        self.cache_enabled = cache_enabled
        
        # Create cache manager
        if cache_enabled:
            cache_dir = self.base_data_dir / "cache"
            self.cache_manager = UnifiedCacheManager(str(cache_dir))
        else:
            self.cache_manager = None
        
        # Create provider registry
        self.provider_registry = DataProviderRegistry(self.cache_manager)
        
        # Initialize providers
        self._initialize_providers()
        
        # Legacy support for existing managers
        self.sector_manager = SectorDataManager()
        self.macro_manager = MacroDataManager()
        
        logger.info("Initialized UnifiedDataManager with redesigned architecture")
    
    def _initialize_providers(self):
        """Initialize and register data providers."""
        
        # Stock provider
        stock_cache_dir = str(self.base_data_dir / "stocks") if self.cache_enabled else None
        stock_provider = create_stock_provider(stock_cache_dir, self.max_workers)
        self.provider_registry.register_provider(
            stock_provider,
            fallback_types=[DataProviderType.EXTERNAL]  # Fallback to external for stocks
        )
        
        # Crypto provider
        crypto_cache_dir = str(self.base_data_dir / "crypto") if self.cache_enabled else None
        crypto_provider = create_crypto_provider(crypto_cache_dir, self.max_workers)
        self.provider_registry.register_provider(
            crypto_provider,
            fallback_types=[DataProviderType.STOCK]  # Fallback to stock provider for crypto
        )
        
        # Register symbol routing for better auto-detection
        self._register_symbol_routing()
        
        logger.info("Registered all data providers")
    
    def _register_symbol_routing(self):
        """Register explicit symbol routing for better performance."""
        
        # Register popular crypto symbols
        crypto_symbols = CryptoSymbolMappings.get_popular_cryptos()
        for symbol in crypto_symbols:
            self.provider_registry.register_symbol_routing(symbol, DataProviderType.CRYPTO)
        
        # Register common macro symbols
        macro_symbols = ['VIX', '^TNX', '^IRX', '^FVX', 'GLD', 'TLT', 'HYG']
        for symbol in macro_symbols:
            self.provider_registry.register_symbol_routing(symbol, DataProviderType.MACRO)
        
        # Register sector ETF symbols
        sector_symbols = ['SPY', 'QQQ', 'IWM', 'XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLB', 'XLC', 'XLRE', 'XLU']
        for symbol in sector_symbols:
            self.provider_registry.register_symbol_routing(symbol, DataProviderType.SECTOR)
    
    def load_data(self, 
                  symbols: List[str], 
                  period: str = "1y",
                  interval: str = "1d",
                  force_download: bool = False,
                  start: Optional[datetime] = None,
                  end: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Load data for specified symbols using the unified architecture.
        
        Args:
            symbols: List of symbols to load
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            force_download: Whether to force fresh download
            start: Start date for data download
            end: End date for data download
            
        Returns:
            Dictionary mapping symbols to their DataFrames
        """
        logger.info(f"Loading data for {len(symbols)} symbols: {symbols}")
        
        # Create data request
        request = DataRequest(
            symbols=symbols,
            period=period,
            interval=interval,
            start=start,
            end=end,
            force_download=force_download,
            include_metadata=True
        )
        
        # Download data using provider registry
        response = self.provider_registry.download_data(request)
        
        # Log results
        if response.errors:
            logger.warning(f"Errors occurred: {response.errors}")
        if response.warnings:
            logger.info(f"Warnings: {response.warnings}")
        
        successful_symbols = list(response.data.keys())
        logger.info(f"Successfully loaded data for {len(successful_symbols)} symbols")
        
        return response.data
    
    def load_market_data(self, period: str = "1y", interval: str = "1d") -> Dict[str, Any]:
        """Load market data (VIX, Treasury rates, etc.) using legacy manager."""
        logger.info("Loading market data using legacy macro manager")
        
        try:
            # Use existing macro manager for market data
            market_data = {}
            
            # Load VIX and treasury data
            vix_data = self.macro_manager.download_vix_data(period=period, interval=interval)
            if not vix_data.empty:
                market_data['^VIX'] = vix_data
            
            treasury_data = self.macro_manager.download_treasury_data(period=period, interval=interval)
            market_data.update(treasury_data)
            
            logger.info(f"Loaded market data for {len(market_data)} indicators")
            return market_data
            
        except Exception as e:
            logger.error(f"Error loading market data: {e}")
            return {}
    
    def load_sector_data(self, period: str = "1y", interval: str = "1d") -> Dict[str, Any]:
        """Load sector ETF data using legacy manager."""
        logger.info("Loading sector data using legacy sector manager")
        
        try:
            sector_data = self.sector_manager.download_sector_data(period=period, interval=interval)
            logger.info(f"Loaded sector data for {len(sector_data)} sectors")
            return sector_data
            
        except Exception as e:
            logger.error(f"Error loading sector data: {e}")
            return {}
    
    def load_crypto_data(self, 
                        symbols: List[str] = None, 
                        period: str = "1y",
                        interval: str = "1d",
                        force_download: bool = False) -> Dict[str, Any]:
        """
        Load cryptocurrency data for specified symbols.
        
        Args:
            symbols: List of crypto symbols. If None, loads popular cryptos.
            period: Data period
            interval: Data interval  
            force_download: Whether to force fresh download
            
        Returns:
            Dictionary mapping crypto symbols to their DataFrames
        """
        if symbols is None:
            symbols = CryptoSymbolMappings.get_popular_cryptos()[:5]  # Top 5 popular cryptos
        
        logger.info(f"Loading cryptocurrency data for {len(symbols)} symbols: {symbols}")
        
        # Use the unified load_data method which will route to crypto provider
        return self.load_data(symbols, period, interval, force_download)
    
    def validate_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        """Validate symbols across all providers."""
        return self.provider_registry.validate_symbols(symbols)
    
    def get_available_symbols(self, provider_type: DataProviderType = None) -> List[str]:
        """Get available symbols from providers."""
        return self.provider_registry.get_available_symbols(provider_type)
    
    def get_available_crypto_symbols(self) -> List[str]:
        """Get available cryptocurrency symbols."""
        return CryptoSymbolMappings.get_popular_cryptos()
    
    def is_crypto_symbol(self, symbol: str) -> bool:
        """Check if a symbol is a cryptocurrency."""
        return CryptoSymbolMappings.is_crypto_symbol(symbol)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.cache_manager:
            return self.cache_manager.get_cache_stats()
        return {'cache_enabled': False}
    
    def cleanup_cache(self, max_age_days: int = 30) -> int:
        """Clean up old cache entries."""
        if self.cache_manager:
            return self.cache_manager.cleanup(max_age_days)
        return 0
    
    def get_provider_stats(self) -> Dict[str, Dict]:
        """Get statistics for all registered providers."""
        stats = self.provider_registry.get_provider_stats()
        stats['cache_stats'] = self.get_cache_stats()
        stats['legacy_managers'] = {
            'sector_manager': 'SectorDataManager',
            'macro_manager': 'MacroDataManager'
        }
        return stats
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            'providers': self.get_provider_stats(),
            'cache': self.get_cache_stats(),
            'base_data_dir': str(self.base_data_dir),
            'cache_enabled': self.cache_enabled,
            'max_workers': self.max_workers
        }