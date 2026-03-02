"""
Data storage utilities for efficient data management with performance optimizations.
"""
import pandas as pd
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
from abc import ABC, abstractmethod
import time
from functools import wraps
import concurrent.futures

logger = logging.getLogger(__name__)


def profile_performance(func):
    """Decorator to profile function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        if hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__
            logger.info(f"{class_name}.{func.__name__} completed in {duration:.2f}s")
        else:
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
        
        return result
    return wrapper


class DataStorage(ABC):
    """Abstract base class for data storage implementations."""
    
    @abstractmethod
    def save_stock_data(self, data: pd.DataFrame, symbol: str, metadata: Dict[str, Any], 
                       data_status: str = "latest") -> bool:
        """Save stock data with metadata and classification."""
        pass
    
    @abstractmethod
    def load_stock_data(self, symbol: str, start_date: Optional[datetime] = None, 
                       end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Load stock data for a symbol."""
        pass
    
    @abstractmethod
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols."""
        pass
    
    @abstractmethod
    def delete_symbol_data(self, symbol: str) -> bool:
        """Delete all data for a symbol."""
        pass
    
    def batch_save_stock_data(self, stocks_data: Dict[str, pd.DataFrame], 
                            metadata: Dict[str, Dict[str, Any]], 
                            data_status: str = "latest") -> Dict[str, bool]:
        """
        Save multiple stocks data in batch for better performance.
        Default implementation uses individual saves, can be overridden for optimization.
        
        Args:
            stocks_data: Dictionary mapping symbols to their DataFrames
            metadata: Dictionary mapping symbols to their metadata
            data_status: Data classification (latest, historical, archived)
            
        Returns:
            Dictionary mapping symbols to success/failure status
        """
        results = {}
        for symbol, data in stocks_data.items():
            symbol_metadata = metadata.get(symbol, {})
            results[symbol] = self.save_stock_data(data, symbol, symbol_metadata, data_status)
        return results
    
    def batch_load_stock_data(self, symbols: List[str], 
                            start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None) -> Dict[str, pd.DataFrame]:
        """
        Load multiple stocks data in batch for better performance.
        Default implementation uses individual loads, can be overridden for optimization.
        
        Args:
            symbols: List of stock symbols to load
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Dictionary mapping symbols to their DataFrames
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.load_stock_data(symbol, start_date, end_date)
        return results


class ParquetStorage(DataStorage):
    """Parquet file-based storage for stock data."""
    
    def __init__(self, data_dir: str = "data/stocks"):
        """
        Initialize parquet storage.
        
        Args:
            data_dir: Directory to store parquet files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create metadata directory
        self.metadata_dir = self.data_dir / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def save_stock_data(self, data: pd.DataFrame, symbol: str, metadata: Dict[str, Any], 
                       data_status: str = "latest") -> bool:
        """
        Save stock data as parquet file with classification and intelligent compression.
        
        Args:
            data: Stock data DataFrame
            symbol: Stock symbol
            metadata: Metadata dictionary
            data_status: Data classification (latest, historical, archived)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add data classification to metadata
            metadata = metadata.copy()
            metadata['data_status'] = data_status
            metadata['saved_at'] = datetime.now().isoformat()
            metadata['data_freshness'] = self._calculate_data_freshness(data)
            
            # Determine compression strategy based on data status and size
            compression_config = self._get_compression_config(data, data_status)
            
            # Create status-specific directory
            status_dir = self.data_dir / data_status
            status_dir.mkdir(parents=True, exist_ok=True)
            
            # Save main data with optimized compression
            data_file = status_dir / f"{symbol}.parquet"
            self._save_with_compression(data, data_file, compression_config)
            
            # Archive old versions if needed
            if data_status == "latest":
                self._archive_previous_version(symbol)
            
            # Save metadata
            metadata_df = pd.DataFrame([metadata])
            metadata_file = self.metadata_dir / f"{symbol}_metadata.parquet"
            metadata_df.to_parquet(metadata_file, index=False, compression='snappy')
            
            logger.info(f"Saved {symbol} data to parquet: {data_file} (status: {data_status}, compression: {compression_config['compression']})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving {symbol} to parquet: {str(e)}")
            return False
    
    def _get_compression_config(self, data: pd.DataFrame, data_status: str) -> Dict[str, Any]:
        """Determine optimal compression configuration based on data characteristics."""
        data_size_mb = data.memory_usage(deep=True).sum() / (1024 * 1024)
        
        # Compression strategy based on data status and size
        if data_status == "archived":
            # Maximum compression for archived data
            return {
                'compression': 'gzip',
                'compression_level': 9,
                'row_group_size': 50000  # Larger row groups for better compression
            }
        elif data_status == "historical":
            # Balanced compression for historical data
            return {
                'compression': 'brotli',
                'compression_level': 6,
                'row_group_size': 100000
            }
        elif data_size_mb > 50:
            # Use stronger compression for large datasets
            return {
                'compression': 'brotli',
                'compression_level': 4,
                'row_group_size': 200000
            }
        else:
            # Fast compression for latest/small data
            return {
                'compression': 'snappy',
                'compression_level': None,
                'row_group_size': 500000
            }
    
    def _save_with_compression(self, data: pd.DataFrame, file_path: Path, config: Dict[str, Any]) -> None:
        """Save data with specific compression configuration."""
        try:
            # Optimize data types before saving
            optimized_data = self._optimize_data_types(data)
            
            # Save with compression settings
            kwargs = {
                'index': False,
                'compression': config['compression'],
                'row_group_size': config['row_group_size']
            }
            
            # Add compression level if available
            if config['compression_level'] is not None:
                kwargs['compression_level'] = config['compression_level']
            
            optimized_data.to_parquet(file_path, **kwargs)
            
            # Log compression statistics
            original_size = data.memory_usage(deep=True).sum()
            compressed_size = file_path.stat().st_size
            compression_ratio = original_size / compressed_size if compressed_size > 0 else 1
            
            logger.debug(f"Compression ratio: {compression_ratio:.2f}x, size: {compressed_size / (1024*1024):.2f} MB")
            
        except Exception as e:
            logger.error(f"Error during compression save: {e}")
            # Fallback to basic save
            data.to_parquet(file_path, index=False, compression='snappy')
    
    def _optimize_data_types(self, data: pd.DataFrame) -> pd.DataFrame:
        """Optimize data types for better compression."""
        optimized = data.copy()
        
        try:
            # Optimize numeric columns
            for col in optimized.select_dtypes(include=['float64']).columns:
                if optimized[col].notna().all():
                    # Try to downcast float64 to float32 if no precision loss
                    optimized[col] = pd.to_numeric(optimized[col], downcast='float')
            
            for col in optimized.select_dtypes(include=['int64']).columns:
                optimized[col] = pd.to_numeric(optimized[col], downcast='integer')
            
            # Optimize object columns (strings)
            for col in optimized.select_dtypes(include=['object']).columns:
                if col != 'Date':  # Don't convert Date column
                    unique_count = optimized[col].nunique()
                    total_count = len(optimized[col])
                    
                    # Convert to category if low cardinality
                    if unique_count / total_count < 0.5:
                        optimized[col] = optimized[col].astype('category')
            
            return optimized
            
        except Exception as e:
            logger.warning(f"Error optimizing data types: {e}")
            return data
    
    def _archive_previous_version(self, symbol: str) -> None:
        """Archive the previous version of the data before saving new latest version."""
        try:
            current_latest = self.data_dir / "latest" / f"{symbol}.parquet"
            if current_latest.exists():
                # Create timestamped archive
                archive_dir = self.data_dir / "archived"
                archive_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_path = archive_dir / f"{symbol}_{timestamp}.parquet"
                
                # Move to archive with high compression
                if current_latest.exists():
                    data = pd.read_parquet(current_latest)
                    archive_config = self._get_compression_config(data, "archived")
                    self._save_with_compression(data, archive_path, archive_config)
                    
                    logger.info(f"Archived previous version: {archive_path}")
                    
        except Exception as e:
            logger.warning(f"Could not archive previous version for {symbol}: {e}")
    
    def _calculate_data_freshness(self, data: pd.DataFrame) -> str:
        """Calculate data freshness based on most recent data point."""
        try:
            if 'Date' in data.columns:
                latest_date = pd.to_datetime(data['Date']).max()
                days_old = (datetime.now() - latest_date).days
                
                if days_old <= 1:
                    return "fresh"
                elif days_old <= 7:
                    return "recent"
                elif days_old <= 30:
                    return "moderate"
                else:
                    return "stale"
            return "unknown"
        except Exception:
            return "unknown"
    
    def load_stock_data(self, symbol: str, start_date: Optional[datetime] = None, 
                       end_date: Optional[datetime] = None, data_status: str = "latest") -> pd.DataFrame:
        """
        Load stock data from parquet file with status-aware loading.
        
        Args:
            symbol: Stock symbol
            start_date: Optional start date filter
            end_date: Optional end date filter
            data_status: Data status to load (latest, historical, archived)
            
        Returns:
            Stock data DataFrame
        """
        try:
            # Try status-specific directory first
            data_file = self.data_dir / data_status / f"{symbol}.parquet"
            
            # Fallback to legacy location if not found
            if not data_file.exists():
                data_file = self.data_dir / f"{symbol}.parquet"
            
            if not data_file.exists():
                logger.warning(f"No data file found for {symbol} (status: {data_status})")
                return pd.DataFrame()
            
            data = pd.read_parquet(data_file)
            
            # Apply date filters if provided
            if start_date or end_date:
                if 'Date' in data.columns:
                    data['Date'] = pd.to_datetime(data['Date'])
                    
                    if start_date:
                        data = data[data['Date'] >= start_date]
                    if end_date:
                        data = data[data['Date'] <= end_date]
            
            logger.info(f"Loaded {len(data)} rows for {symbol} (status: {data_status})")
            return data
            
        except Exception as e:
            logger.error(f"Error loading {symbol} from parquet: {str(e)}")
            return pd.DataFrame()
    
    def get_available_symbols(self, data_status: str = "latest") -> List[str]:
        """Get list of available symbols in storage for specific status."""
        symbols = set()
        
        # Check status-specific directory
        status_dir = self.data_dir / data_status
        if status_dir.exists():
            for file_path in status_dir.glob("*.parquet"):
                symbol = file_path.stem
                symbols.add(symbol)
        
        # Also check legacy location for backwards compatibility
        for file_path in self.data_dir.glob("*.parquet"):
            symbol = file_path.stem
            symbols.add(symbol)
        
        return sorted(list(symbols))
    
    def delete_symbol_data(self, symbol: str) -> bool:
        """Delete all data for a symbol across all status directories."""
        try:
            deleted = False
            
            # Delete from all status directories (latest, historical, archived)
            for status_dir in self.data_dir.iterdir():
                if status_dir.is_dir() and status_dir.name != "metadata":
                    data_file = status_dir / f"{symbol}.parquet"
                    if data_file.exists():
                        data_file.unlink()
                        deleted = True
                        logger.debug(f"Deleted {symbol} from {status_dir.name}")
            
            # Delete from legacy location (direct in data_dir)
            legacy_data_file = self.data_dir / f"{symbol}.parquet"
            if legacy_data_file.exists():
                legacy_data_file.unlink()
                deleted = True
                logger.debug(f"Deleted legacy {symbol} file")
            
            # Delete metadata
            metadata_file = self.metadata_dir / f"{symbol}_metadata.parquet"
            if metadata_file.exists():
                metadata_file.unlink()
                deleted = True
                logger.debug(f"Deleted {symbol} metadata")
            
            # Delete from archived directory if it exists
            archived_dir = self.data_dir / "archived"
            if archived_dir.exists():
                for archived_file in archived_dir.glob(f"{symbol}_*.parquet"):
                    archived_file.unlink()
                    deleted = True
                    logger.debug(f"Deleted archived file: {archived_file.name}")
            
            if deleted:
                logger.info(f"Deleted all data for {symbol}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting data for {symbol}: {str(e)}")
            return False
    
    def get_metadata(self, symbol: str) -> Dict[str, Any]:
        """Get metadata for a symbol."""
        try:
            metadata_file = self.metadata_dir / f"{symbol}_metadata.parquet"
            
            if not metadata_file.exists():
                return {}
            
            metadata_df = pd.read_parquet(metadata_file)
            return metadata_df.iloc[0].to_dict() if len(metadata_df) > 0 else {}
            
        except Exception as e:
            logger.error(f"Error loading metadata for {symbol}: {str(e)}")
            return {}
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics for all stored data."""
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'by_status': {},
            'by_compression': {},
            'largest_files': []
        }
        
        try:
            all_files = []
            
            # Collect all parquet files
            for parquet_file in self.data_dir.rglob("*.parquet"):
                if parquet_file.is_file():
                    size_mb = parquet_file.stat().st_size / (1024 * 1024)
                    status = parquet_file.parent.name if parquet_file.parent != self.data_dir else "legacy"
                    
                    file_info = {
                        'file': parquet_file.name,
                        'status': status,
                        'size_mb': size_mb,
                        'path': str(parquet_file)
                    }
                    all_files.append(file_info)
                    
                    # Update totals
                    stats['total_files'] += 1
                    stats['total_size_mb'] += size_mb
                    
                    # Update by status
                    if status not in stats['by_status']:
                        stats['by_status'][status] = {'count': 0, 'size_mb': 0}
                    stats['by_status'][status]['count'] += 1
                    stats['by_status'][status]['size_mb'] += size_mb
            
            # Sort by size and get largest files
            all_files.sort(key=lambda x: x['size_mb'], reverse=True)
            stats['largest_files'] = all_files[:10]
            
            logger.info(f"Storage stats: {stats['total_files']} files, {stats['total_size_mb']:.2f} MB total")
            
        except Exception as e:
            logger.error(f"Error calculating compression stats: {e}")
        
        return stats
    
    def cleanup_old_archives(self, symbol: str, keep_versions: int = 5) -> bool:
        """Clean up old archived versions, keeping only the most recent ones."""
        try:
            archive_dir = self.data_dir / "archived"
            if not archive_dir.exists():
                return True
            
            # Find all archive files for this symbol
            pattern = f"{symbol}_*.parquet"
            archive_files = list(archive_dir.glob(pattern))
            
            if len(archive_files) <= keep_versions:
                return True
            
            # Sort by timestamp (newest first)
            archive_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Delete old versions
            files_to_delete = archive_files[keep_versions:]
            deleted_count = 0
            
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Could not delete {file_path}: {e}")
            
            logger.info(f"Cleaned up {deleted_count} old archive files for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up archives for {symbol}: {e}")
            return False
    
    def get_data_versions(self, symbol: str) -> List[Dict[str, Any]]:
        """Get all available versions of data for a symbol."""
        versions = []
        
        try:
            # Check latest version
            latest_file = self.data_dir / "latest" / f"{symbol}.parquet"
            if latest_file.exists():
                versions.append({
                    'status': 'latest',
                    'file_path': str(latest_file),
                    'size_mb': latest_file.stat().st_size / (1024 * 1024),
                    'modified': datetime.fromtimestamp(latest_file.stat().st_mtime),
                    'is_current': True
                })
            
            # Check historical version
            historical_file = self.data_dir / "historical" / f"{symbol}.parquet"
            if historical_file.exists():
                versions.append({
                    'status': 'historical',
                    'file_path': str(historical_file),
                    'size_mb': historical_file.stat().st_size / (1024 * 1024),
                    'modified': datetime.fromtimestamp(historical_file.stat().st_mtime),
                    'is_current': False
                })
            
            # Check archived versions
            archive_dir = self.data_dir / "archived"
            if archive_dir.exists():
                pattern = f"{symbol}_*.parquet"
                for archive_file in archive_dir.glob(pattern):
                    # Extract timestamp from filename
                    timestamp_str = archive_file.stem.replace(f"{symbol}_", "")
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    except:
                        timestamp = datetime.fromtimestamp(archive_file.stat().st_mtime)
                    
                    versions.append({
                        'status': 'archived',
                        'file_path': str(archive_file),
                        'size_mb': archive_file.stat().st_size / (1024 * 1024),
                        'modified': timestamp,
                        'is_current': False
                    })
            
            # Sort by modification time (newest first)
            versions.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting data versions for {symbol}: {e}")
        
        return versions
    
    def restore_from_archive(self, symbol: str, archive_timestamp: str) -> bool:
        """Restore data from a specific archived version."""
        try:
            archive_file = self.data_dir / "archived" / f"{symbol}_{archive_timestamp}.parquet"
            
            if not archive_file.exists():
                logger.error(f"Archive file not found: {archive_file}")
                return False
            
            # Load archived data
            data = pd.read_parquet(archive_file)
            
            # Create basic metadata
            metadata = {
                'restored_from': archive_timestamp,
                'restored_at': datetime.now().isoformat(),
                'source': 'archive_restore'
            }
            
            # Save as latest
            return self.save_stock_data(data, symbol, metadata, "latest")
            
        except Exception as e:
            logger.error(f"Error restoring {symbol} from archive {archive_timestamp}: {e}")
            return False
    
    def apply_archival_policies(self, policy_config: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        Apply automated archival policies to manage storage.
        
        Args:
            policy_config: Optional configuration for archival policies
            
        Returns:
            Statistics about archival actions taken
        """
        if policy_config is None:
            policy_config = {
                'max_archive_versions': 10,
                'archive_age_days': 30,
                'cleanup_age_days': 90,
                'max_total_size_gb': 5.0
            }
        
        stats = {
            'files_archived': 0,
            'files_deleted': 0,
            'space_freed_mb': 0,
            'errors': 0
        }
        
        try:
            # Get all symbols
            symbols = self.get_available_symbols()
            
            for symbol in symbols:
                try:
                    # Clean up old archives for this symbol
                    if self.cleanup_old_archives(symbol, policy_config['max_archive_versions']):
                        stats['files_deleted'] += 1
                    
                    # Archive old historical data if it exists
                    historical_file = self.data_dir / "historical" / f"{symbol}.parquet"
                    if historical_file.exists():
                        age_days = (datetime.now() - datetime.fromtimestamp(historical_file.stat().st_mtime)).days
                        
                        if age_days > policy_config['archive_age_days']:
                            # Move to archived with timestamp
                            data = pd.read_parquet(historical_file)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            archive_config = self._get_compression_config(data, "archived")
                            
                            archive_dir = self.data_dir / "archived"
                            archive_dir.mkdir(parents=True, exist_ok=True)
                            archive_path = archive_dir / f"{symbol}_historical_{timestamp}.parquet"
                            
                            self._save_with_compression(data, archive_path, archive_config)
                            
                            # Calculate space freed
                            original_size = historical_file.stat().st_size
                            new_size = archive_path.stat().st_size
                            stats['space_freed_mb'] += (original_size - new_size) / (1024 * 1024)
                            
                            # Remove original historical file
                            historical_file.unlink()
                            stats['files_archived'] += 1
                            
                            logger.info(f"Archived historical data for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Error applying archival policy to {symbol}: {e}")
                    stats['errors'] += 1
            
            # Check total storage size and apply global cleanup if needed
            storage_stats = self.get_compression_stats()
            total_size_gb = storage_stats['total_size_mb'] / 1024
            
            if total_size_gb > policy_config['max_total_size_gb']:
                logger.warning(f"Storage exceeds limit ({total_size_gb:.2f} GB > {policy_config['max_total_size_gb']} GB)")
                cleanup_stats = self._emergency_cleanup(policy_config)
                stats['files_deleted'] += cleanup_stats['files_deleted']
                stats['space_freed_mb'] += cleanup_stats['space_freed_mb']
            
            logger.info(f"Archival policy applied: {stats}")
            
        except Exception as e:
            logger.error(f"Error applying archival policies: {e}")
            stats['errors'] += 1
        
        return stats
    
    def _emergency_cleanup(self, policy_config: Dict[str, Any]) -> Dict[str, int]:
        """Emergency cleanup when storage exceeds limits."""
        cleanup_stats = {'files_deleted': 0, 'space_freed_mb': 0}
        
        try:
            # Get all archived files sorted by age (oldest first)
            archive_dir = self.data_dir / "archived"
            if not archive_dir.exists():
                return cleanup_stats
            
            archive_files = []
            for archive_file in archive_dir.glob("*.parquet"):
                archive_files.append({
                    'path': archive_file,
                    'size_mb': archive_file.stat().st_size / (1024 * 1024),
                    'age_days': (datetime.now() - datetime.fromtimestamp(archive_file.stat().st_mtime)).days
                })
            
            # Sort by age (oldest first)
            archive_files.sort(key=lambda x: x['age_days'], reverse=True)
            
            # Delete oldest files until we're under the limit
            target_reduction_mb = (self.get_compression_stats()['total_size_mb'] / 1024 - policy_config['max_total_size_gb']) * 1024
            deleted_mb = 0
            
            for file_info in archive_files:
                if deleted_mb >= target_reduction_mb:
                    break
                
                # Delete files older than cleanup threshold
                if file_info['age_days'] > policy_config['cleanup_age_days']:
                    try:
                        file_info['path'].unlink()
                        deleted_mb += file_info['size_mb']
                        cleanup_stats['files_deleted'] += 1
                        cleanup_stats['space_freed_mb'] += file_info['size_mb']
                        
                        logger.info(f"Emergency cleanup: deleted {file_info['path'].name}")
                        
                    except Exception as e:
                        logger.error(f"Could not delete {file_info['path']}: {e}")
            
        except Exception as e:
            logger.error(f"Error during emergency cleanup: {e}")
        
        return cleanup_stats
    
    def schedule_archival_task(self, interval_hours: int = 24) -> bool:
        """
        Set up scheduled archival task (placeholder for cron/scheduler integration).
        
        Args:
            interval_hours: Hours between archival runs
            
        Returns:
            True if successful
        """
        logger.info(f"Archival task scheduled every {interval_hours} hours")
        logger.info("Note: Actual scheduling requires external cron/scheduler setup")
        
        # This would typically integrate with a job scheduler
        # For now, just log the configuration
        return True
    
    @profile_performance
    def batch_save_stock_data(self, stocks_data: Dict[str, pd.DataFrame], 
                            metadata: Dict[str, Dict[str, Any]], 
                            data_status: str = "latest") -> Dict[str, bool]:
        """
        Optimized batch save operation for ParquetStorage.
        Uses parallel I/O and optimized compression strategies.
        """
        logger.info(f"Starting optimized batch save for {len(stocks_data)} symbols")
        results = {}
        
        if len(stocks_data) <= 2:
            # Use sequential for small batches
            return super().batch_save_stock_data(stocks_data, metadata, data_status)
        
        def save_single(symbol_and_data):
            symbol, data = symbol_and_data
            symbol_metadata = metadata.get(symbol, {})
            return symbol, self.save_stock_data(data, symbol, symbol_metadata, data_status)
        
        # Use parallel processing for better I/O performance
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {
                executor.submit(save_single, (symbol, data)): symbol 
                for symbol, data in stocks_data.items()
            }
            
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result_symbol, success = future.result()
                    results[result_symbol] = success
                except Exception as e:
                    logger.error(f"Error in batch save for {symbol}: {e}")
                    results[symbol] = False
        
        success_count = sum(results.values())
        logger.info(f"Batch save completed: {success_count}/{len(stocks_data)} successful")
        return results
    
    @profile_performance 
    def batch_load_stock_data(self, symbols: List[str], 
                            start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None) -> Dict[str, pd.DataFrame]:
        """
        Optimized batch load operation for ParquetStorage.
        Uses parallel I/O for better performance.
        """
        logger.info(f"Starting optimized batch load for {len(symbols)} symbols")
        results = {}
        
        if len(symbols) <= 2:
            # Use sequential for small batches
            return super().batch_load_stock_data(symbols, start_date, end_date)
        
        def load_single(symbol):
            return symbol, self.load_stock_data(symbol, start_date, end_date)
        
        # Use parallel processing for better I/O performance
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {
                executor.submit(load_single, symbol): symbol 
                for symbol in symbols
            }
            
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result_symbol, data = future.result()
                    results[result_symbol] = data
                except Exception as e:
                    logger.error(f"Error in batch load for {symbol}: {e}")
                    results[symbol] = pd.DataFrame()
        
        loaded_count = sum(1 for df in results.values() if not df.empty)
        logger.info(f"Batch load completed: {loaded_count}/{len(symbols)} loaded successfully")
        return results


class SQLiteStorage(DataStorage):
    """SQLite database storage for stock data."""
    
    def __init__(self, db_path: str = "data/stocks.db"):
        """
        Initialize SQLite storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Create stock_data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    adj_close REAL,
                    volume INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date)
                )
            """)
            
            # Create metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_metadata (
                    symbol TEXT PRIMARY KEY,
                    metadata TEXT,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol_date ON stock_data(symbol, date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON stock_data(symbol)")
            
            conn.commit()
    
    def save_stock_data(self, data: pd.DataFrame, symbol: str, metadata: Dict[str, Any]) -> bool:
        """
        Save stock data to SQLite database.
        
        Args:
            data: Stock data DataFrame
            symbol: Stock symbol
            metadata: Metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Prepare data for insertion
                data_copy = data.copy()
                data_copy['symbol'] = symbol
                
                # Rename columns to match database schema
                column_mapping = {
                    'Date': 'date',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Adj Close': 'adj_close',
                    'Volume': 'volume'
                }
                
                data_copy = data_copy.rename(columns=column_mapping)
                
                # Select only columns that exist in the database
                db_columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
                data_copy = data_copy[[col for col in db_columns if col in data_copy.columns]]
                
                # Insert data (replace if exists)
                data_copy.to_sql('stock_data', conn, if_exists='append', index=False)
                
                # Save metadata
                import json
                metadata_json = json.dumps(metadata)
                conn.execute(
                    "INSERT OR REPLACE INTO stock_metadata (symbol, metadata) VALUES (?, ?)",
                    (symbol, metadata_json)
                )
                
                conn.commit()
                logger.info(f"Saved {len(data_copy)} rows for {symbol} to SQLite")
                return True
                
        except Exception as e:
            logger.error(f"Error saving {symbol} to SQLite: {str(e)}")
            return False
    
    def load_stock_data(self, symbol: str, start_date: Optional[datetime] = None, 
                       end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Load stock data from SQLite database.
        
        Args:
            symbol: Stock symbol
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Stock data DataFrame
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM stock_data WHERE symbol = ?"
                params = [symbol]
                
                if start_date:
                    query += " AND date >= ?"
                    params.append(start_date.strftime('%Y-%m-%d'))
                
                if end_date:
                    query += " AND date <= ?"
                    params.append(end_date.strftime('%Y-%m-%d'))
                
                query += " ORDER BY date"
                
                data = pd.read_sql_query(query, conn, params=params)
                
                if not data.empty:
                    # Convert date column to datetime
                    data['date'] = pd.to_datetime(data['date'])
                    
                    # Rename columns back to standard format
                    column_mapping = {
                        'date': 'Date',
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'adj_close': 'Adj Close',
                        'volume': 'Volume'
                    }
                    data = data.rename(columns=column_mapping)
                    
                    # Remove database-specific columns
                    data = data.drop(columns=['id', 'symbol', 'created_at'], errors='ignore')
                
                logger.info(f"Loaded {len(data)} rows for {symbol} from SQLite")
                return data
                
        except Exception as e:
            logger.error(f"Error loading {symbol} from SQLite: {str(e)}")
            return pd.DataFrame()
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT DISTINCT symbol FROM stock_data ORDER BY symbol")
                symbols = [row[0] for row in cursor.fetchall()]
                return symbols
                
        except Exception as e:
            logger.error(f"Error getting available symbols: {str(e)}")
            return []
    
    def delete_symbol_data(self, symbol: str) -> bool:
        """Delete all data for a symbol."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM stock_data WHERE symbol = ?", (symbol,))
                conn.execute("DELETE FROM stock_metadata WHERE symbol = ?", (symbol,))
                conn.commit()
                
                deleted_rows = cursor.rowcount
                if deleted_rows > 0:
                    logger.info(f"Deleted {deleted_rows} rows for {symbol}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error deleting data for {symbol}: {str(e)}")
            return False