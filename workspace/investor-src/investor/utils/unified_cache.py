"""
Unified caching utilities to eliminate duplicate caching functionality.
Provides standardized caching patterns for all data types.
"""
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class UnifiedCache:
    """
    Unified caching interface that consolidates all caching functionality.
    
    Supports multiple data formats (parquet, JSON, pickle) with automatic
    format detection and consistent metadata handling.
    """
    
    def __init__(
        self,
        cache_dir: Union[str, Path],
        default_format: str = "parquet",
        compression: Optional[str] = "snappy"
    ):
        """
        Initialize unified cache.
        
        Args:
            cache_dir: Base directory for cache files
            default_format: Default file format ('parquet', 'json', 'pickle')
            compression: Compression algorithm for parquet files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.default_format = default_format
        self.compression = compression
        
        # Format handlers
        self.format_handlers = {
            'parquet': {
                'save': self._save_parquet,
                'load': self._load_parquet,
                'extension': '.parquet'
            },
            'json': {
                'save': self._save_json,
                'load': self._load_json,
                'extension': '.json'
            },
            'pickle': {
                'save': self._save_pickle,
                'load': self._load_pickle,
                'extension': '.pkl'
            }
        }
    
    def save(
        self,
        data: Union[pd.DataFrame, Dict[str, Any], Any],
        key: str,
        metadata: Optional[Dict[str, Any]] = None,
        format_type: Optional[str] = None,
        expiry_hours: Optional[int] = None
    ) -> bool:
        """
        Save data to cache with metadata.
        
        Args:
            data: Data to save
            key: Cache key (becomes filename)
            metadata: Optional metadata to store with data
            format_type: File format override
            expiry_hours: Auto-expiry time in hours
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            format_type = format_type or self._detect_format(data)
            handler = self.format_handlers[format_type]
            
            # Add standard metadata
            full_metadata = {
                'cache_time': datetime.now().isoformat(),
                'format': format_type,
                'key': key
            }
            
            if expiry_hours:
                expiry_time = datetime.now() + timedelta(hours=expiry_hours)
                full_metadata['expires_at'] = expiry_time.isoformat()
            
            if metadata:
                full_metadata.update(metadata)
            
            # Generate filename
            filename = self._generate_filename(key, format_type)
            filepath = self.cache_dir / filename
            
            # Save using appropriate handler
            success = handler['save'](data, filepath, full_metadata)
            
            if success:
                logger.debug(f"Cached {key} as {format_type} format")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save cache for {key}: {e}")
            return False
    
    def load(
        self,
        key: str,
        format_type: Optional[str] = None,
        check_expiry: bool = True
    ) -> Optional[Union[pd.DataFrame, Dict[str, Any], Any]]:
        """
        Load data from cache.
        
        Args:
            key: Cache key
            format_type: File format hint
            check_expiry: Whether to check expiry time
            
        Returns:
            Cached data or None if not found/expired
        """
        try:
            # Find the cached file
            filepath = self._find_cache_file(key, format_type)
            if not filepath or not filepath.exists():
                return None
            
            # Detect format from file extension
            detected_format = self._detect_format_from_path(filepath)
            handler = self.format_handlers[detected_format]
            
            # Load data and metadata
            data, metadata = handler['load'](filepath)
            
            # Check expiry
            if check_expiry and self._is_expired(metadata):
                logger.debug(f"Cache for {key} has expired")
                return None
            
            logger.debug(f"Loaded {key} from {detected_format} cache")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load cache for {key}: {e}")
            return None
    
    def exists(self, key: str, format_type: Optional[str] = None) -> bool:
        """
        Check if cache entry exists.
        
        Args:
            key: Cache key
            format_type: File format hint
            
        Returns:
            True if cache entry exists
        """
        filepath = self._find_cache_file(key, format_type)
        return filepath is not None and filepath.exists()
    
    def is_fresh(
        self,
        key: str,
        max_age_hours: int = 24,
        format_type: Optional[str] = None
    ) -> bool:
        """
        Check if cache entry is fresh.
        
        Args:
            key: Cache key
            max_age_hours: Maximum age in hours
            format_type: File format hint
            
        Returns:
            True if cache is fresh enough
        """
        try:
            filepath = self._find_cache_file(key, format_type)
            if not filepath or not filepath.exists():
                return False
            
            # Check file modification time
            file_time = datetime.fromtimestamp(filepath.stat().st_mtime)
            age_hours = (datetime.now() - file_time).total_seconds() / 3600
            
            return age_hours <= max_age_hours
            
        except Exception as e:
            logger.error(f"Failed to check cache freshness for {key}: {e}")
            return False
    
    def delete(self, key: str, format_type: Optional[str] = None) -> bool:
        """
        Delete cache entry.
        
        Args:
            key: Cache key
            format_type: File format hint
            
        Returns:
            True if deleted successfully
        """
        try:
            filepath = self._find_cache_file(key, format_type)
            if filepath and filepath.exists():
                filepath.unlink()
                logger.debug(f"Deleted cache for {key}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete cache for {key}: {e}")
            return False
    
    def clear_all(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache entries matching pattern.
        
        Args:
            pattern: Glob pattern to match (None for all)
            
        Returns:
            Number of files deleted
        """
        try:
            pattern = pattern or "*"
            deleted_count = 0
            
            for filepath in self.cache_dir.glob(pattern):
                if filepath.is_file():
                    filepath.unlink()
                    deleted_count += 1
            
            logger.info(f"Cleared {deleted_count} cache files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache statistics and information.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            total_files = 0
            total_size = 0
            format_counts = {}
            
            for filepath in self.cache_dir.rglob("*"):
                if filepath.is_file():
                    total_files += 1
                    total_size += filepath.stat().st_size
                    
                    # Count by format
                    ext = filepath.suffix
                    format_counts[ext] = format_counts.get(ext, 0) + 1
            
            return {
                'cache_dir': str(self.cache_dir),
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'format_counts': format_counts
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {}
    
    def _detect_format(self, data: Any) -> str:
        """Detect appropriate format for data type."""
        if isinstance(data, pd.DataFrame):
            return 'parquet'
        elif isinstance(data, (dict, list)):
            return 'json'
        else:
            return 'pickle'
    
    def _detect_format_from_path(self, filepath: Path) -> str:
        """Detect format from file extension."""
        ext = filepath.suffix.lower()
        if ext == '.parquet':
            return 'parquet'
        elif ext == '.json':
            return 'json'
        elif ext in ['.pkl', '.pickle']:
            return 'pickle'
        else:
            return self.default_format
    
    def _generate_filename(self, key: str, format_type: str) -> str:
        """Generate filename for cache key."""
        extension = self.format_handlers[format_type]['extension']
        # Sanitize key for filename
        safe_key = "".join(c for c in key if c.isalnum() or c in "._-")
        return f"{safe_key}{extension}"
    
    def _find_cache_file(self, key: str, format_type: Optional[str] = None) -> Optional[Path]:
        """Find cache file for key."""
        if format_type:
            filename = self._generate_filename(key, format_type)
            filepath = self.cache_dir / filename
            return filepath if filepath.exists() else None
        
        # Try all formats
        for fmt in self.format_handlers:
            filename = self._generate_filename(key, fmt)
            filepath = self.cache_dir / filename
            if filepath.exists():
                return filepath
        
        return None
    
    def _is_expired(self, metadata: Dict[str, Any]) -> bool:
        """Check if cache entry has expired."""
        expires_at = metadata.get('expires_at')
        if not expires_at:
            return False
        
        try:
            expiry_time = datetime.fromisoformat(expires_at)
            return datetime.now() > expiry_time
        except Exception:
            return False
    
    def _save_parquet(self, data: pd.DataFrame, filepath: Path, metadata: Dict[str, Any]) -> bool:
        """Save DataFrame as parquet."""
        try:
            # Add metadata as DataFrame attributes
            for key, value in metadata.items():
                data.attrs[key] = value
            
            data.to_parquet(filepath, index=False, compression=self.compression)
            return True
        except Exception as e:
            logger.error(f"Failed to save parquet: {e}")
            return False
    
    def _load_parquet(self, filepath: Path) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """Load DataFrame from parquet."""
        data = pd.read_parquet(filepath)
        metadata = dict(data.attrs) if hasattr(data, 'attrs') else {}
        return data, metadata
    
    def _save_json(self, data: Union[Dict, List], filepath: Path, metadata: Dict[str, Any]) -> bool:
        """Save data as JSON."""
        try:
            # Wrap data with metadata
            wrapper = {
                'metadata': metadata,
                'data': data
            }
            
            with open(filepath, 'w') as f:
                json.dump(wrapper, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
            return False
    
    def _load_json(self, filepath: Path) -> tuple[Union[Dict, List], Dict[str, Any]]:
        """Load data from JSON."""
        with open(filepath, 'r') as f:
            wrapper = json.load(f)
        
        if isinstance(wrapper, dict) and 'metadata' in wrapper and 'data' in wrapper:
            return wrapper['data'], wrapper['metadata']
        else:
            # Legacy format without metadata wrapper
            return wrapper, {}
    
    def _save_pickle(self, data: Any, filepath: Path, metadata: Dict[str, Any]) -> bool:
        """Save data as pickle."""
        try:
            import pickle
            
            # Wrap data with metadata
            wrapper = {
                'metadata': metadata,
                'data': data
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(wrapper, f)
            return True
        except Exception as e:
            logger.error(f"Failed to save pickle: {e}")
            return False
    
    def _load_pickle(self, filepath: Path) -> tuple[Any, Dict[str, Any]]:
        """Load data from pickle."""
        import pickle
        
        with open(filepath, 'rb') as f:
            wrapper = pickle.load(f)
        
        if isinstance(wrapper, dict) and 'metadata' in wrapper and 'data' in wrapper:
            return wrapper['data'], wrapper['metadata']
        else:
            # Legacy format without metadata wrapper
            return wrapper, {}


# Global cache instances for common use cases
data_cache = UnifiedCache(Path.cwd() / "data" / "cache")
temp_cache = UnifiedCache(Path.cwd() / "data" / "temp")


def cached_function(
    cache_key: str,
    expiry_hours: int = 24,
    cache_instance: Optional[UnifiedCache] = None
):
    """
    Decorator for caching function results.
    
    Args:
        cache_key: Key for caching (can include {args} placeholders)
        expiry_hours: Cache expiry time in hours
        cache_instance: Cache instance to use
    """
    cache = cache_instance or data_cache
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key with arguments
            if '{args}' in cache_key:
                key = cache_key.format(args='_'.join(str(arg) for arg in args))
            else:
                key = cache_key
            
            # Try to load from cache
            result = cache.load(key)
            if result is not None:
                logger.debug(f"Cache hit for {key}")
                return result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {key}, executing function")
            result = func(*args, **kwargs)
            
            cache.save(result, key, expiry_hours=expiry_hours)
            return result
        
        return wrapper
    return decorator