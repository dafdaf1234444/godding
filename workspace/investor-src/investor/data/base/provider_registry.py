"""
Data provider registry for managing multiple data sources.
"""
from typing import Dict, List
import logging
import pandas as pd

from .interfaces import IDataProvider, DataRequest, DataResponse, DataProviderType, DataStatus
from .cache_manager import UnifiedCacheManager

logger = logging.getLogger(__name__)


class DataProviderRegistry:
    """Registry for managing multiple data providers."""
    
    def __init__(self, cache_manager: UnifiedCacheManager = None):
        """Initialize the provider registry."""
        self.providers: Dict[DataProviderType, IDataProvider] = {}
        self.symbol_routing: Dict[str, DataProviderType] = {}
        self.cache_manager = cache_manager
        self.fallback_providers: Dict[DataProviderType, List[DataProviderType]] = {}
        
    def register_provider(self, provider: IDataProvider, fallback_types: List[DataProviderType] = None):
        """
        Register a data provider.
        
        Args:
            provider: Data provider to register
            fallback_types: List of provider types to use as fallbacks
        """
        provider_type = provider.provider_type
        self.providers[provider_type] = provider
        
        if fallback_types:
            self.fallback_providers[provider_type] = fallback_types
        
        logger.info(f"Registered {provider_type.value} provider")
    
    def register_symbol_routing(self, symbol: str, provider_type: DataProviderType):
        """Register specific symbol routing to a provider type."""
        self.symbol_routing[symbol.upper()] = provider_type
    
    def auto_route_symbols(self, symbols: List[str]) -> Dict[DataProviderType, List[str]]:
        """
        Automatically route symbols to appropriate providers.
        
        Args:
            symbols: List of symbols to route
            
        Returns:
            Dictionary mapping provider types to their symbols
        """
        routing = {}
        
        for symbol in symbols:
            symbol_upper = symbol.upper()
            
            # Check explicit routing first
            if symbol_upper in self.symbol_routing:
                provider_type = self.symbol_routing[symbol_upper]
            else:
                # Auto-detect provider type based on symbol characteristics
                provider_type = self._detect_provider_type(symbol)
            
            if provider_type not in routing:
                routing[provider_type] = []
            routing[provider_type].append(symbol)
        
        return routing
    
    def download_data(self, request: DataRequest) -> DataResponse:
        """
        Download data using appropriate providers.
        
        Args:
            request: Data request specification
            
        Returns:
            Consolidated data response
        """
        # Route symbols to providers
        symbol_routing = self.auto_route_symbols(request.symbols)
        
        all_data = {}
        all_errors = []
        all_warnings = []
        successful_providers = []
        
        # Process each provider's symbols
        for provider_type, symbols in symbol_routing.items():
            if provider_type not in self.providers:
                error_msg = f"No provider registered for type {provider_type.value}"
                logger.error(error_msg)
                all_errors.append(error_msg)
                continue
            
            provider = self.providers[provider_type]
            provider_request = DataRequest(
                symbols=symbols,
                period=request.period,
                interval=request.interval,
                start=request.start,
                end=request.end,
                force_download=request.force_download,
                include_metadata=request.include_metadata
            )
            
            try:
                response = provider.download_data(provider_request)
                
                # Merge data
                all_data.update(response.data)
                
                # Collect errors and warnings
                if response.errors:
                    all_errors.extend(response.errors)
                if response.warnings:
                    all_warnings.extend(response.warnings)
                
                if response.data:
                    successful_providers.append(provider_type.value)
                    
                logger.info(f"Provider {provider_type.value} returned {len(response.data)} symbols")
                
            except Exception as e:
                error_msg = f"Error with provider {provider_type.value}: {str(e)}"
                logger.error(error_msg)
                all_errors.append(error_msg)
                
                # Try fallback providers
                if provider_type in self.fallback_providers:
                    fallback_data = self._try_fallback_providers(provider_type, symbols, provider_request)
                    all_data.update(fallback_data)
        
        # Determine overall status
        if all_data:
            status = DataStatus.LATEST
        elif all_errors:
            status = DataStatus.FAILED
        else:
            status = DataStatus.FAILED
        
        return DataResponse(
            data=all_data,
            metadata={
                'providers_used': successful_providers,
                'total_providers_attempted': len(symbol_routing),
                'symbol_routing': {pt.value: symbols for pt, symbols in symbol_routing.items()},
                'request_symbols': request.symbols,
                'successful_symbols': list(all_data.keys())
            },
            status=status,
            provider_type=DataProviderType.EXTERNAL,  # Mixed providers
            timestamp=list(all_data.values())[0].attrs.get('timestamp') if all_data else None,
            errors=all_errors if all_errors else None,
            warnings=all_warnings if all_warnings else None
        )
    
    def get_available_symbols(self, provider_type: DataProviderType = None) -> List[str]:
        """Get available symbols from providers."""
        if provider_type and provider_type in self.providers:
            return self.providers[provider_type].supported_symbols
        
        # Get symbols from all providers
        all_symbols = []
        for provider in self.providers.values():
            all_symbols.extend(provider.supported_symbols)
        
        return list(set(all_symbols))  # Remove duplicates
    
    def validate_symbols(self, symbols: List[str], provider_type: DataProviderType = None) -> Dict[str, bool]:
        """Validate symbols across providers."""
        validation_results = {}
        
        if provider_type and provider_type in self.providers:
            # Validate with specific provider
            provider = self.providers[provider_type]
            valid_symbols = provider.validate_symbols(symbols)
            for symbol in symbols:
                validation_results[symbol] = symbol in valid_symbols
        else:
            # Validate with appropriate providers
            symbol_routing = self.auto_route_symbols(symbols)
            
            for provider_type, provider_symbols in symbol_routing.items():
                if provider_type in self.providers:
                    provider = self.providers[provider_type]
                    valid_symbols = provider.validate_symbols(provider_symbols)
                    
                    for symbol in provider_symbols:
                        validation_results[symbol] = symbol in valid_symbols
                else:
                    # No provider available
                    for symbol in provider_symbols:
                        validation_results[symbol] = False
        
        return validation_results
    
    def get_provider_stats(self) -> Dict[str, Dict]:
        """Get statistics for all registered providers."""
        stats = {}
        
        for provider_type, provider in self.providers.items():
            stats[provider_type.value] = {
                'type': provider_type.value,
                'supported_symbols_count': len(provider.supported_symbols),
                'has_cache': self.cache_manager is not None
            }
        
        return stats
    
    def _detect_provider_type(self, symbol: str) -> DataProviderType:
        """Auto-detect provider type based on symbol characteristics."""
        symbol_upper = symbol.upper()
        
        # Crypto patterns
        crypto_patterns = ['-USD', '-EUR', '-GBP', '-BTC']
        crypto_symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'AAVE']
        
        if any(pattern in symbol_upper for pattern in crypto_patterns) or symbol_upper in crypto_symbols:
            return DataProviderType.CRYPTO
        
        # Sector ETF patterns
        sector_patterns = ['XL', 'SPY', 'QQQ', 'IWM', 'EEM', 'EFA', 'VTI', 'VEA', 'VWO']
        if any(symbol_upper.startswith(pattern) for pattern in sector_patterns):
            return DataProviderType.SECTOR
        
        # Macro/Index patterns
        macro_patterns = ['^', 'VIX', 'TNX', 'IRX', 'FVX', 'GLD', 'TLT', 'HYG']
        if symbol_upper.startswith('^') or symbol_upper in macro_patterns:
            return DataProviderType.MACRO
        
        # Currency patterns
        currency_patterns = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF']
        if any(f'{symbol_upper}=' in f'{curr}=' for curr in currency_patterns):
            return DataProviderType.CURRENCY
        
        # Default to stock
        return DataProviderType.STOCK
    
    def _try_fallback_providers(self, failed_provider_type: DataProviderType, 
                               symbols: List[str], request: DataRequest) -> Dict[str, pd.DataFrame]:
        """Try fallback providers when primary provider fails."""
        fallback_data = {}
        
        if failed_provider_type not in self.fallback_providers:
            return fallback_data
        
        for fallback_type in self.fallback_providers[failed_provider_type]:
            if fallback_type not in self.providers:
                continue
            
            try:
                logger.info(f"Trying fallback provider {fallback_type.value} for {len(symbols)} symbols")
                fallback_provider = self.providers[fallback_type]
                response = fallback_provider.download_data(request)
                
                if response.data:
                    fallback_data.update(response.data)
                    logger.info(f"Fallback provider {fallback_type.value} provided {len(response.data)} symbols")
                    break  # Stop on first successful fallback
                    
            except Exception as e:
                logger.error(f"Fallback provider {fallback_type.value} also failed: {str(e)}")
        
        return fallback_data