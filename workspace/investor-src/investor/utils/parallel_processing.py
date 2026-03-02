"""
Parallel processing utilities for the investor analysis system.
Provides standardized parallel processing patterns to avoid code duplication.
"""
import concurrent.futures
import logging
from typing import Callable, Dict, List, Any, Optional, TypeVar, Generic
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


class ParallelProcessor(Generic[T, R]):
    """
    Utility class for standardized parallel processing operations.
    
    Handles common patterns like symbol processing, error collection,
    and fallback to sequential processing.
    """
    
    def __init__(
        self,
        max_workers: int = 10,
        sequential_threshold: int = 2,
        timeout_seconds: Optional[int] = None
    ):
        """
        Initialize parallel processor.
        
        Args:
            max_workers: Maximum number of parallel workers
            sequential_threshold: Use sequential processing below this item count
            timeout_seconds: Timeout for individual tasks (None for no timeout)
        """
        self.max_workers = max_workers
        self.sequential_threshold = sequential_threshold
        self.timeout_seconds = timeout_seconds
    
    def process_items(
        self,
        items: List[T],
        processor_func: Callable[[T], R],
        use_parallel: bool = True,
        operation_name: str = "processing",
        continue_on_error: bool = True
    ) -> Dict[T, R]:
        """
        Process a list of items either in parallel or sequentially.
        
        Args:
            items: List of items to process
            processor_func: Function to process each item
            use_parallel: Whether to use parallel processing
            operation_name: Name of operation for logging
            continue_on_error: Whether to continue processing other items on error
            
        Returns:
            Dictionary mapping items to their results
        """
        if not items:
            return {}
        
        if not use_parallel or len(items) <= self.sequential_threshold:
            return self._process_sequential(
                items, processor_func, operation_name, continue_on_error
            )
        
        return self._process_parallel(
            items, processor_func, operation_name, continue_on_error
        )
    
    def process_symbols(
        self,
        symbols: List[str],
        processor_func: Callable[[str], R],
        use_parallel: bool = True,
        continue_on_error: bool = True
    ) -> Dict[str, R]:
        """
        Convenience method for processing stock/crypto symbols.
        
        Args:
            symbols: List of symbols to process
            processor_func: Function to process each symbol
            use_parallel: Whether to use parallel processing
            continue_on_error: Whether to continue processing other symbols on error
            
        Returns:
            Dictionary mapping symbols to their results
        """
        return self.process_items(
            symbols, processor_func, use_parallel, 
            "symbol processing", continue_on_error
        )
    
    def _process_sequential(
        self,
        items: List[T],
        processor_func: Callable[[T], R],
        operation_name: str,
        continue_on_error: bool
    ) -> Dict[T, R]:
        """Process items sequentially."""
        logger.info(f"Processing {len(items)} items sequentially for {operation_name}")
        
        results = {}
        failed_items = []
        
        for item in items:
            try:
                result = processor_func(item)
                results[item] = result
                logger.debug(f"Processed {item} successfully")
                
            except Exception as e:
                logger.error(f"Error processing {item}: {e}")
                failed_items.append(item)
                
                if not continue_on_error:
                    raise
        
        if failed_items:
            logger.warning(f"Failed to process {len(failed_items)} items: {failed_items}")
        
        logger.info(f"Sequential {operation_name} completed: {len(results)} successful")
        return results
    
    def _process_parallel(
        self,
        items: List[T],
        processor_func: Callable[[T], R],
        operation_name: str,
        continue_on_error: bool
    ) -> Dict[T, R]:
        """Process items in parallel."""
        actual_workers = min(self.max_workers, len(items))
        logger.info(
            f"Processing {len(items)} items in parallel for {operation_name} "
            f"(max_workers={actual_workers})"
        )
        
        results = {}
        failed_items = []
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=actual_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(processor_func, item): item 
                for item in items
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(
                future_to_item, timeout=self.timeout_seconds
            ):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results[item] = result
                    logger.debug(f"Processed {item} successfully")
                    
                except Exception as e:
                    logger.error(f"Error processing {item}: {e}")
                    failed_items.append(item)
                    
                    if not continue_on_error:
                        # Cancel remaining futures and raise
                        for remaining_future in future_to_item:
                            remaining_future.cancel()
                        raise
        
        duration = time.time() - start_time
        
        if failed_items:
            logger.warning(f"Failed to process {len(failed_items)} items: {failed_items}")
        
        logger.info(
            f"Parallel {operation_name} completed in {duration:.2f}s: "
            f"{len(results)} successful, {len(failed_items)} failed"
        )
        
        return results
    
    def batch_process(
        self,
        items: List[T],
        processor_func: Callable[[List[T]], Dict[T, R]],
        batch_size: int = 50,
        use_parallel: bool = True,
        operation_name: str = "batch processing"
    ) -> Dict[T, R]:
        """
        Process items in batches (useful for API rate limiting).
        
        Args:
            items: List of items to process
            processor_func: Function that processes a batch of items
            batch_size: Number of items per batch
            use_parallel: Whether to process batches in parallel
            operation_name: Name of operation for logging
            
        Returns:
            Dictionary mapping items to their results
        """
        if not items:
            return {}
        
        # Create batches
        batches = [
            items[i:i + batch_size] 
            for i in range(0, len(items), batch_size)
        ]
        
        logger.info(
            f"Processing {len(items)} items in {len(batches)} batches "
            f"of size {batch_size} for {operation_name}"
        )
        
        # Process batches
        def process_batch(batch: List[T]) -> Dict[T, R]:
            return processor_func(batch)
        
        batch_results = self.process_items(
            batches, process_batch, use_parallel, 
            f"batch {operation_name}", continue_on_error=True
        )
        
        # Combine results from all batches
        combined_results = {}
        for batch, batch_result in batch_results.items():
            combined_results.update(batch_result)
        
        logger.info(f"Batch {operation_name} completed: {len(combined_results)} total results")
        return combined_results


class SymbolProcessor(ParallelProcessor[str, Any]):
    """
    Specialized parallel processor for stock/crypto symbols.
    
    Includes symbol-specific error handling and logging patterns.
    """
    
    def __init__(self, max_workers: int = 10, **kwargs):
        """Initialize symbol processor with symbol-specific defaults."""
        super().__init__(max_workers=max_workers, **kwargs)
    
    def download_symbols(
        self,
        symbols: List[str],
        download_func: Callable[[str], Any],
        operation_name: str = "downloading data",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Download data for multiple symbols with standardized logging.
        
        Args:
            symbols: List of symbols to download
            download_func: Function to download data for a single symbol
            operation_name: Description of the download operation
            **kwargs: Additional arguments passed to process_symbols
            
        Returns:
            Dictionary mapping symbols to their downloaded data
        """
        logger.info(f"Starting {operation_name} for {len(symbols)} symbols: {symbols}")
        
        results = self.process_symbols(
            symbols, download_func, 
            continue_on_error=True,
            **kwargs
        )
        
        successful_symbols = [symbol for symbol, data in results.items() if data is not None]
        failed_symbols = [symbol for symbol in symbols if symbol not in results]
        
        logger.info(
            f"Completed {operation_name}: {len(successful_symbols)} successful, "
            f"{len(failed_symbols)} failed"
        )
        
        if failed_symbols:
            logger.warning(f"Failed symbols: {failed_symbols}")
        
        return results


# Global instances for convenience
default_processor = ParallelProcessor()
symbol_processor = SymbolProcessor()


def parallel_map(
    items: List[T],
    func: Callable[[T], R],
    max_workers: int = 10,
    **kwargs
) -> Dict[T, R]:
    """
    Convenience function for simple parallel mapping.
    
    Args:
        items: Items to process
        func: Function to apply to each item
        max_workers: Maximum number of workers
        **kwargs: Additional arguments for ParallelProcessor
        
    Returns:
        Dictionary mapping items to results
    """
    processor = ParallelProcessor(max_workers=max_workers)
    return processor.process_items(items, func, **kwargs)


def parallel_download(
    symbols: List[str],
    download_func: Callable[[str], Any],
    max_workers: int = 10,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for parallel symbol downloading.
    
    Args:
        symbols: Symbols to download
        download_func: Download function for each symbol
        max_workers: Maximum number of workers
        **kwargs: Additional arguments for SymbolProcessor
        
    Returns:
        Dictionary mapping symbols to downloaded data
    """
    processor = SymbolProcessor(max_workers=max_workers)
    return processor.download_symbols(symbols, download_func, **kwargs)