"""
Unified cache manager for all data providers.
"""
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import logging

from .interfaces import ICacheManager
from .utils import ensure_directory, safe_filename

logger = logging.getLogger(__name__)


class UnifiedCacheManager(ICacheManager):
    """Unified cache manager supporting multiple storage formats."""
    
    def __init__(self, cache_dir: str, default_format: str = "parquet"):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Base directory for cache storage
            default_format: Default storage format (parquet, pickle, csv)
        """
        self.cache_dir = ensure_directory(Path(cache_dir))
        self.default_format = default_format
        self.metadata_dir = ensure_directory(self.cache_dir / "metadata")
        
        # Format-specific subdirectories
        self.parquet_dir = ensure_directory(self.cache_dir / "parquet")
        self.pickle_dir = ensure_directory(self.cache_dir / "pickle")
        self.csv_dir = ensure_directory(self.cache_dir / "csv")
        
        logger.info(f"Initialized cache manager at {self.cache_dir}")
    
    def get(self, key: str, format_preference: str = None) -> Optional[pd.DataFrame]:
        """Get data from cache with format preference."""
        format_to_use = format_preference or self.default_format
        
        try:
            if format_to_use == "parquet":
                return self._get_parquet(key)
            elif format_to_use == "pickle":
                return self._get_pickle(key)
            elif format_to_use == "csv":
                return self._get_csv(key)
            else:
                # Try all formats in order of preference
                for fmt in ["parquet", "pickle", "csv"]:
                    data = self.get(key, fmt)
                    if data is not None:
                        return data
                return None
                
        except Exception as e:
            logger.error(f"Error reading from cache key {key}: {e}")
            return None
    
    def set(self, key: str, data: pd.DataFrame, metadata: Dict[str, Any] = None, 
           format_preference: str = None) -> bool:
        """Store data in cache with metadata."""
        if data is None or data.empty:
            logger.warning(f"Skipping cache storage for empty data: {key}")
            return False
        
        format_to_use = format_preference or self.default_format
        
        try:
            # Store metadata
            if metadata:
                self._save_metadata(key, metadata)
            
            # Store data in specified format
            if format_to_use == "parquet":
                return self._set_parquet(key, data, metadata)
            elif format_to_use == "pickle":
                return self._set_pickle(key, data, metadata)
            elif format_to_use == "csv":
                return self._set_csv(key, data, metadata)
            else:
                logger.error(f"Unsupported cache format: {format_to_use}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing to cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in any format."""
        safe_key = safe_filename(key)
        
        # Check all possible formats
        parquet_file = self.parquet_dir / f"{safe_key}.parquet"
        pickle_file = self.pickle_dir / f"{safe_key}.pkl"
        csv_file = self.csv_dir / f"{safe_key}.csv"
        
        return any(f.exists() for f in [parquet_file, pickle_file, csv_file])
    
    def is_fresh(self, key: str, max_age_hours: int = 24) -> bool:
        """Check if cached data is fresh."""
        metadata = self._get_metadata(key)
        if not metadata:
            return False
        
        try:
            stored_time = datetime.fromisoformat(metadata.get('timestamp', ''))
            age = datetime.now() - stored_time
            return age < timedelta(hours=max_age_hours)
        except (ValueError, TypeError):
            return False
    
    def invalidate(self, key: str) -> bool:
        """Invalidate cached data by removing all formats."""
        safe_key = safe_filename(key)
        success = True
        
        # Remove all possible formats
        files_to_remove = [
            self.parquet_dir / f"{safe_key}.parquet",
            self.pickle_dir / f"{safe_key}.pkl",
            self.csv_dir / f"{safe_key}.csv",
            self.metadata_dir / f"{safe_key}.json"
        ]
        
        for file_path in files_to_remove:
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.debug(f"Removed cache file: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing cache file {file_path}: {e}")
                    success = False
        
        return success
    
    def cleanup(self, max_age_days: int = 30) -> int:
        """Clean up old cache entries."""
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        removed_count = 0
        
        # Check all cache directories
        for cache_subdir in [self.parquet_dir, self.pickle_dir, self.csv_dir]:
            for file_path in cache_subdir.glob("*"):
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        removed_count += 1
                        logger.debug(f"Removed old cache file: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing old cache file {file_path}: {e}")
        
        # Clean up metadata files
        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                file_time = datetime.fromtimestamp(metadata_file.stat().st_mtime)
                if file_time < cutoff_time:
                    metadata_file.unlink()
                    removed_count += 1
            except Exception as e:
                logger.error(f"Error removing metadata file {metadata_file}: {e}")
        
        logger.info(f"Cache cleanup completed: removed {removed_count} files older than {max_age_days} days")
        return removed_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'formats': {},
            'oldest_file': None,
            'newest_file': None
        }
        
        for cache_subdir in [self.parquet_dir, self.pickle_dir, self.csv_dir]:
            format_name = cache_subdir.name
            format_files = list(cache_subdir.glob("*"))
            format_size = sum(f.stat().st_size for f in format_files if f.is_file())
            
            stats['formats'][format_name] = {
                'files': len(format_files),
                'size_mb': format_size / (1024 * 1024)
            }
            
            stats['total_files'] += len(format_files)
            stats['total_size_mb'] += format_size / (1024 * 1024)
            
            # Track oldest and newest files
            for file_path in format_files:
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if stats['oldest_file'] is None or file_time < stats['oldest_file']:
                        stats['oldest_file'] = file_time
                    if stats['newest_file'] is None or file_time > stats['newest_file']:
                        stats['newest_file'] = file_time
        
        return stats
    
    # Format-specific methods
    def _get_parquet(self, key: str) -> Optional[pd.DataFrame]:
        """Get data from parquet format."""
        safe_key = safe_filename(key)
        file_path = self.parquet_dir / f"{safe_key}.parquet"
        
        if file_path.exists():
            return pd.read_parquet(file_path)
        return None
    
    def _set_parquet(self, key: str, data: pd.DataFrame, metadata: Dict[str, Any] = None) -> bool:
        """Store data in parquet format."""
        safe_key = safe_filename(key)
        file_path = self.parquet_dir / f"{safe_key}.parquet"
        
        # Add metadata to DataFrame attributes
        if metadata:
            for k, v in metadata.items():
                data.attrs[k] = v
        
        data.to_parquet(file_path, index=False)
        logger.debug(f"Stored data in parquet cache: {file_path}")
        return True
    
    def _get_pickle(self, key: str) -> Optional[pd.DataFrame]:
        """Get data from pickle format."""
        safe_key = safe_filename(key)
        file_path = self.pickle_dir / f"{safe_key}.pkl"
        
        if file_path.exists():
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        return None
    
    def _set_pickle(self, key: str, data: pd.DataFrame, metadata: Dict[str, Any] = None) -> bool:
        """Store data in pickle format."""
        safe_key = safe_filename(key)
        file_path = self.pickle_dir / f"{safe_key}.pkl"
        
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        logger.debug(f"Stored data in pickle cache: {file_path}")
        return True
    
    def _get_csv(self, key: str) -> Optional[pd.DataFrame]:
        """Get data from CSV format."""
        safe_key = safe_filename(key)
        file_path = self.csv_dir / f"{safe_key}.csv"
        
        if file_path.exists():
            return pd.read_csv(file_path)
        return None
    
    def _set_csv(self, key: str, data: pd.DataFrame, metadata: Dict[str, Any] = None) -> bool:
        """Store data in CSV format."""
        safe_key = safe_filename(key)
        file_path = self.csv_dir / f"{safe_key}.csv"
        
        data.to_csv(file_path, index=False)
        logger.debug(f"Stored data in CSV cache: {file_path}")
        return True
    
    def _save_metadata(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Save metadata to JSON file."""
        safe_key = safe_filename(key)
        file_path = self.metadata_dir / f"{safe_key}.json"
        
        # Add timestamp
        metadata['timestamp'] = datetime.now().isoformat()
        
        with open(file_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        return True
    
    def _get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata from JSON file."""
        safe_key = safe_filename(key)
        file_path = self.metadata_dir / f"{safe_key}.json"
        
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading metadata for {key}: {e}")
        
        return None