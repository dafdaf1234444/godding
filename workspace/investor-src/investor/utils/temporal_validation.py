"""
Temporal data validation utilities to prevent future data leakage.
Critical for maintaining the integrity of historical analysis and backtesting.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class TemporalValidator:
    """
    Ensures strict temporal validation to prevent future data leakage.
    
    This class provides:
    - Point-in-time data access controls
    - Future data contamination checks
    - Temporal ordering validation
    - Look-ahead bias detection
    - Data lag management for real-time analysis
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize temporal validator.
        
        Args:
            strict_mode: If True, raises errors on violations. If False, logs warnings.
        """
        self.strict_mode = strict_mode
        self.validation_errors = []
        self.warnings = []
        
    def validate_temporal_integrity(self, data: pd.DataFrame, 
                                  analysis_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Perform comprehensive temporal validation on dataset.
        
        Args:
            data: DataFrame with datetime index or Date column
            analysis_date: Simulated "current" date for backtesting validation
            
        Returns:
            Validation results dictionary
        """
        logger.info("Performing temporal integrity validation")
        
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'checks_performed': []
        }
        
        # Ensure datetime index or Date column
        df = self._ensure_datetime_index(data)
        
        # Check 1: Future data contamination
        future_check = self._check_future_data_contamination(df, analysis_date)
        results['checks_performed'].append('future_data_contamination')
        if not future_check['is_valid']:
            results['is_valid'] = False
            results['errors'].extend(future_check['errors'])
        
        # Check 2: Temporal ordering
        ordering_check = self._check_temporal_ordering(df)
        results['checks_performed'].append('temporal_ordering')
        if not ordering_check['is_valid']:
            results['is_valid'] = False
            results['errors'].extend(ordering_check['errors'])
        
        # Check 3: Look-ahead bias in features
        if len(df.columns) > 1:  # Has features beyond just date/price
            lookahead_check = self._check_lookahead_bias(df)
            results['checks_performed'].append('lookahead_bias')
            if not lookahead_check['is_valid']:
                results['is_valid'] = False
                results['errors'].extend(lookahead_check['errors'])
            results['warnings'].extend(lookahead_check['warnings'])
        
        # Check 4: Data availability gaps
        gaps_check = self._check_data_gaps(df)
        results['checks_performed'].append('data_gaps')
        results['warnings'].extend(gaps_check['warnings'])
        
        # Check 5: Weekend/holiday data integrity
        weekday_check = self._check_weekday_data_integrity(df)
        results['checks_performed'].append('weekday_integrity')
        results['warnings'].extend(weekday_check['warnings'])
        
        # Log results
        if results['is_valid']:
            logger.info(f"Temporal validation passed. Checks: {len(results['checks_performed'])}")
        else:
            error_msg = f"Temporal validation failed with {len(results['errors'])} errors"
            if self.strict_mode:
                logger.error(error_msg)
                raise ValueError(f"Temporal validation failed: {results['errors']}")
            else:
                logger.warning(error_msg)
        
        if results['warnings']:
            logger.warning(f"Temporal validation warnings: {len(results['warnings'])}")
        
        return results
    
    def _ensure_datetime_index(self, data: pd.DataFrame) -> pd.DataFrame:
        """Ensure DataFrame has proper datetime index."""
        df = data.copy()
        
        if 'Date' in df.columns and not isinstance(df.index, pd.DatetimeIndex):
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
        elif not isinstance(df.index, pd.DatetimeIndex):
            if 'ds' in df.columns:  # nixtla format
                df['ds'] = pd.to_datetime(df['ds'])
                df = df.set_index('ds')
            else:
                # Try to convert index to datetime
                try:
                    df.index = pd.to_datetime(df.index)
                except:
                    raise ValueError("DataFrame must have datetime index or Date/ds column")
        
        return df
    
    def _check_future_data_contamination(self, df: pd.DataFrame, 
                                       analysis_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Check for future data contamination."""
        if analysis_date is None:
            analysis_date = datetime.now()
        
        # Convert to datetime if needed
        if isinstance(analysis_date, str):
            analysis_date = pd.to_datetime(analysis_date)
        
        # Handle timezone comparison - convert analysis_date to match df index timezone
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            if isinstance(analysis_date, datetime) and analysis_date.tzinfo is None:
                # Make analysis_date timezone naive for comparison
                analysis_date = pd.to_datetime(analysis_date).tz_localize(None)
                df_index = df.index.tz_localize(None)
                future_data = df[df_index > analysis_date]
            else:
                # Both are timezone aware, compare directly
                future_data = df[df.index > analysis_date]
        else:
            # Neither has timezone info
            future_data = df[df.index > analysis_date]
        
        result = {
            'is_valid': True,
            'errors': [],
            'future_data_count': len(future_data)
        }
        
        if len(future_data) > 0:
            result['is_valid'] = False
            result['errors'].append(
                f"Found {len(future_data)} data points from the future "
                f"(after {analysis_date.strftime('%Y-%m-%d')})"
            )
        
        return result
    
    def _check_temporal_ordering(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check that data is properly temporally ordered."""
        result = {
            'is_valid': True,
            'errors': []
        }
        
        # Check for duplicate dates
        duplicate_dates = df.index.duplicated()
        if duplicate_dates.any():
            dup_count = duplicate_dates.sum()
            result['errors'].append(f"Found {dup_count} duplicate dates")
            result['is_valid'] = False
        
        # Check for proper ordering
        if not df.index.is_monotonic_increasing:
            result['errors'].append("Data is not in chronological order")
            result['is_valid'] = False
        
        return result
    
    def _check_lookahead_bias(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for potential look-ahead bias in features."""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check for suspicious feature patterns that might indicate look-ahead bias
        for col in df.columns:
            if col in ['Close', 'Open', 'High', 'Low', 'Volume', 'y']:
                continue
                
            # Check if feature has future perfect correlation with target
            if 'Close' in df.columns:
                try:
                    # Calculate rolling correlation to avoid using future data
                    rolling_corr = df[col].rolling(window=20, min_periods=10).corr(
                        df['Close'].rolling(window=20, min_periods=10)
                    )
                    
                    # Check for suspiciously high correlations (> 0.95)
                    high_corr_periods = (rolling_corr.abs() > 0.95).sum()
                    if high_corr_periods > len(df) * 0.1:  # More than 10% of periods
                        result['warnings'].append(
                            f"Feature '{col}' has suspiciously high correlation with target "
                            f"({high_corr_periods} periods with |corr| > 0.95)"
                        )
                except:
                    pass  # Skip if correlation calculation fails
            
            # Check for features that are perfectly shifted versions of the target
            if 'Close' in df.columns:
                try:
                    for shift in [1, 2, 3, 5]:  # Check various shifts
                        shifted_corr = df[col].corr(df['Close'].shift(-shift))
                        if abs(shifted_corr) > 0.98:
                            result['errors'].append(
                                f"Feature '{col}' appears to be future target shifted by {shift} periods "
                                f"(correlation: {shifted_corr:.4f})"
                            )
                            result['is_valid'] = False
                except:
                    pass
        
        return result
    
    def _check_data_gaps(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for unusual data gaps."""
        result = {
            'warnings': []
        }
        
        # Calculate time differences
        time_diffs = df.index.to_series().diff()
        
        # Identify large gaps (more than 7 days for daily data)
        large_gaps = time_diffs[time_diffs > timedelta(days=7)]
        
        if len(large_gaps) > 0:
            result['warnings'].append(
                f"Found {len(large_gaps)} large data gaps (>7 days). "
                f"Largest gap: {large_gaps.max()}"
            )
        
        # Check for weekend data (suspicious for stock data)
        weekend_data = df[df.index.weekday >= 5]  # Saturday=5, Sunday=6
        if len(weekend_data) > len(df) * 0.05:  # More than 5% weekend data
            result['warnings'].append(
                f"Found {len(weekend_data)} weekend data points "
                f"({len(weekend_data)/len(df)*100:.1f}% of data)"
            )
        
        return result
    
    def _check_weekday_data_integrity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check weekday data patterns for stock market data."""
        result = {
            'warnings': []
        }
        
        # Check for missing weekdays (Mon-Fri)
        weekday_counts = df.groupby(df.index.weekday).size()
        
        # Expected weekdays (0=Monday, 4=Friday)
        expected_weekdays = set(range(5))
        actual_weekdays = set(weekday_counts.index)
        
        missing_weekdays = expected_weekdays - actual_weekdays
        if missing_weekdays:
            weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            missing_names = [weekday_names[i] for i in missing_weekdays]
            result['warnings'].append(
                f"Missing data for weekdays: {', '.join(missing_names)}"
            )
        
        return result
    
    def create_point_in_time_dataset(self, data: pd.DataFrame, 
                                   as_of_date: datetime,
                                   lookback_days: Optional[int] = None) -> pd.DataFrame:
        """
        Create a point-in-time dataset that would have been available as of a specific date.
        
        Args:
            data: Full dataset
            as_of_date: Date to simulate "current" time
            lookback_days: Optional limit on how far back to include data
            
        Returns:
            Dataset that would have been available as of the specified date
        """
        df = self._ensure_datetime_index(data)
        
        # Filter to data available as of the specified date
        pit_data = df[df.index <= as_of_date].copy()
        
        # Apply lookback window if specified
        if lookback_days is not None:
            start_date = as_of_date - timedelta(days=lookback_days)
            pit_data = pit_data[pit_data.index >= start_date]
        
        # Validate the resulting dataset
        validation_result = self.validate_temporal_integrity(pit_data, as_of_date)
        
        if not validation_result['is_valid']:
            logger.warning(f"Point-in-time dataset validation failed: {validation_result['errors']}")
        
        logger.info(f"Created point-in-time dataset with {len(pit_data)} records as of {as_of_date}")
        return pit_data
    
    def detect_data_snooping(self, train_data: pd.DataFrame, 
                           test_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect potential data snooping between training and test sets.
        
        Args:
            train_data: Training dataset
            test_data: Test dataset
            
        Returns:
            Detection results
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        train_df = self._ensure_datetime_index(train_data)
        test_df = self._ensure_datetime_index(test_data)
        
        # Check 1: No overlap in dates
        train_dates = set(train_df.index.date)
        test_dates = set(test_df.index.date)
        overlap = train_dates.intersection(test_dates)
        
        if overlap:
            result['is_valid'] = False
            result['errors'].append(
                f"Found {len(overlap)} overlapping dates between train and test sets"
            )
        
        # Check 2: Test data is after training data
        if len(train_df) > 0 and len(test_df) > 0:
            latest_train = train_df.index.max()
            earliest_test = test_df.index.min()
            
            if earliest_test <= latest_train:
                result['warnings'].append(
                    f"Test data starts ({earliest_test.date()}) before training data ends "
                    f"({latest_train.date()}). Consider temporal splitting."
                )
        
        # Check 3: Reasonable gap between train and test
        if len(train_df) > 0 and len(test_df) > 0:
            gap = earliest_test - latest_train
            if gap < timedelta(days=1):
                result['warnings'].append(
                    f"Very small gap ({gap}) between training and test data. "
                    f"Consider adding buffer period."
                )
        
        return result


class TemporalDataSplitter:
    """
    Temporal data splitting utilities for time series analysis.
    Ensures proper temporal ordering in train/validation/test splits.
    """
    
    def __init__(self, validator: Optional[TemporalValidator] = None):
        """Initialize with optional validator."""
        self.validator = validator or TemporalValidator()
    
    def temporal_train_test_split(self, data: pd.DataFrame, 
                                test_size: float = 0.2,
                                gap_days: int = 0) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data temporally (chronologically) into train and test sets.
        
        Args:
            data: DataFrame with datetime index
            test_size: Fraction of data to use for testing
            gap_days: Days to skip between train and test (to simulate data lag)
            
        Returns:
            Tuple of (train_data, test_data)
        """
        df = self.validator._ensure_datetime_index(data)
        
        # Calculate split point
        split_idx = int(len(df) * (1 - test_size))
        split_date = df.index[split_idx]
        
        # Apply gap if specified
        if gap_days > 0:
            gap_end_date = split_date + timedelta(days=gap_days)
            train_data = df[df.index < split_date]
            test_data = df[df.index >= gap_end_date]
        else:
            train_data = df.iloc[:split_idx]
            test_data = df.iloc[split_idx:]
        
        # Validate the split
        snooping_result = self.validator.detect_data_snooping(train_data, test_data)
        if not snooping_result['is_valid']:
            logger.warning(f"Data splitting validation failed: {snooping_result['errors']}")
        
        logger.info(f"Temporal split: {len(train_data)} train, {len(test_data)} test")
        return train_data, test_data
    
    def walk_forward_split(self, data: pd.DataFrame, 
                          initial_train_size: int,
                          test_size: int,
                          step_size: int = 1) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Create walk-forward splits for time series cross-validation.
        
        Args:
            data: DataFrame with datetime index
            initial_train_size: Initial training window size
            test_size: Test window size
            step_size: Number of periods to step forward each iteration
            
        Returns:
            List of (train_data, test_data) tuples
        """
        df = self.validator._ensure_datetime_index(data)
        splits = []
        
        start_idx = 0
        while start_idx + initial_train_size + test_size <= len(df):
            train_end_idx = start_idx + initial_train_size
            test_end_idx = train_end_idx + test_size
            
            train_data = df.iloc[start_idx:train_end_idx]
            test_data = df.iloc[train_end_idx:test_end_idx]
            
            splits.append((train_data, test_data))
            start_idx += step_size
        
        logger.info(f"Created {len(splits)} walk-forward splits")
        return splits