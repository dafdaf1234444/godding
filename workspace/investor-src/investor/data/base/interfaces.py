"""
Base interfaces for data providers in the investor analysis system.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class DataProviderType(Enum):
    """Types of data providers."""
    STOCK = "stock"
    CRYPTO = "crypto"
    MACRO = "macro"
    SECTOR = "sector"
    CURRENCY = "currency"
    EXTERNAL = "external"


class DataStatus(Enum):
    """Status of downloaded data."""
    LATEST = "latest"
    HISTORICAL = "historical"
    ARCHIVED = "archived"
    FAILED = "failed"


@dataclass
class DataRequest:
    """Data request specification."""
    symbols: List[str]
    period: str = "1y"
    interval: str = "1d"
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    force_download: bool = False
    include_metadata: bool = True


@dataclass
class DataResponse:
    """Data response with metadata."""
    data: Dict[str, pd.DataFrame]
    metadata: Dict[str, Any]
    status: DataStatus
    provider_type: DataProviderType
    timestamp: datetime
    errors: List[str] = None
    warnings: List[str] = None


@dataclass
class ValidationResult:
    """Data validation result."""
    valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None


class IDataProvider(ABC):
    """Base interface for all data providers."""
    
    @property
    @abstractmethod
    def provider_type(self) -> DataProviderType:
        """Get the type of this data provider."""
        pass
    
    @property
    @abstractmethod
    def supported_symbols(self) -> List[str]:
        """Get list of supported symbols for this provider."""
        pass
    
    @abstractmethod
    def download_data(self, request: DataRequest) -> DataResponse:
        """
        Download data for the specified request.
        
        Args:
            request: Data request specification
            
        Returns:
            DataResponse with downloaded data and metadata
        """
        pass
    
    @abstractmethod
    def validate_symbols(self, symbols: List[str]) -> List[str]:
        """
        Validate and filter supported symbols.
        
        Args:
            symbols: List of symbols to validate
            
        Returns:
            List of supported symbols
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: pd.DataFrame, symbol: str) -> ValidationResult:
        """
        Validate downloaded data quality.
        
        Args:
            data: Downloaded data
            symbol: Symbol being validated
            
        Returns:
            Validation result
        """
        pass
    
    def get_cache_key(self, symbol: str, period: str, interval: str) -> str:
        """Generate cache key for data."""
        return f"{self.provider_type.value}_{symbol}_{period}_{interval}"


class ICacheManager(ABC):
    """Interface for cache management."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[pd.DataFrame]:
        """Get data from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, data: pd.DataFrame, metadata: Dict[str, Any] = None) -> bool:
        """Store data in cache."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    def is_fresh(self, key: str, max_age_hours: int = 24) -> bool:
        """Check if cached data is fresh."""
        pass
    
    @abstractmethod
    def invalidate(self, key: str) -> bool:
        """Invalidate cached data."""
        pass
    
    @abstractmethod
    def cleanup(self, max_age_days: int = 30) -> int:
        """Clean up old cache entries."""
        pass


class IDataQualityValidator(ABC):
    """Interface for data quality validation."""
    
    @abstractmethod
    def validate_temporal_integrity(self, data: pd.DataFrame) -> ValidationResult:
        """Validate temporal data integrity."""
        pass
    
    @abstractmethod
    def validate_price_ranges(self, data: pd.DataFrame, symbol: str) -> ValidationResult:
        """Validate price data ranges."""
        pass
    
    @abstractmethod
    def validate_volume_patterns(self, data: pd.DataFrame) -> ValidationResult:
        """Validate volume data patterns."""
        pass
    
    @abstractmethod
    def validate_completeness(self, data: pd.DataFrame, expected_periods: int = None) -> ValidationResult:
        """Validate data completeness."""
        pass


class IDataTransformer(ABC):
    """Interface for data transformation."""
    
    @abstractmethod
    def transform(self, data: pd.DataFrame, symbol: str, metadata: Dict[str, Any]) -> pd.DataFrame:
        """Transform raw data into standardized format."""
        pass
    
    @abstractmethod
    def add_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add derived features to data."""
        pass
    
    @abstractmethod
    def normalize_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and types."""
        pass