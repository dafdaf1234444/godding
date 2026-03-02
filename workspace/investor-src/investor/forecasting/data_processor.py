"""
Data processing and feature engineering for forecasting with performance optimizations.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

from ..utils.temporal_validation import TemporalValidator, TemporalDataSplitter
from ..utils.performance import profile_performance

logger = logging.getLogger(__name__)




class ForecastingDataProcessor:
    """
    Process and prepare stock data for forecasting models.
    
    This class handles:
    - Data preparation for time series forecasting
    - Feature engineering for exogenous variables
    - Data splitting and validation
    - Missing value handling
    - Scaling and normalization
    """
    
    def __init__(self, target_column: str = 'Close', enable_temporal_validation: bool = True):
        """
        Initialize the data processor.
        
        Args:
            target_column: Column to forecast (default: 'Close')
            enable_temporal_validation: Enable strict temporal validation (default: True)
        """
        self.target_column = target_column
        self.scalers = {}
        self.feature_columns = []
        self.enable_temporal_validation = enable_temporal_validation
        
        # Initialize temporal validation
        if self.enable_temporal_validation:
            self.temporal_validator = TemporalValidator(strict_mode=False)  # Use warnings mode
            self.temporal_splitter = TemporalDataSplitter(self.temporal_validator)
        else:
            self.temporal_validator = None
            self.temporal_splitter = None
        
    @profile_performance
    def prepare_forecasting_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Prepare data for forecasting models with optimized processing.
        
        Args:
            data: Raw stock data
            symbol: Stock symbol
            
        Returns:
            Processed data ready for forecasting
        """
        logger.info(f"Preparing forecasting data for {symbol}")
        
        # Optimize memory usage by avoiding unnecessary copies
        df = data.copy()
        df.sort_values('Date', inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Optimize data types upfront
        df = self._optimize_dtypes(df)
        
        # Ensure Date is datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Basic cleaning
        df = self._clean_data(df)
        
        # Create target variable
        df['y'] = df[self.target_column]
        
        # Create unique_id for nixtla format
        df['unique_id'] = symbol
        
        # Rename Date to ds for nixtla format
        df.rename(columns={'Date': 'ds'}, inplace=True)
        
        # Create features (optimized vectorized approach)
        df = self._create_features_vectorized(df)
        
        # Handle missing values
        df = self._handle_missing_values(df)
        
        # Validate temporal integrity if enabled
        if self.enable_temporal_validation and self.temporal_validator:
            try:
                validation_result = self.temporal_validator.validate_temporal_integrity(df)
                if not validation_result['is_valid']:
                    logger.warning(f"Temporal validation issues for {symbol}: {validation_result['errors']}")
                if validation_result['warnings']:
                    logger.warning(f"Temporal validation warnings for {symbol}: {validation_result['warnings']}")
            except Exception as e:
                logger.warning(f"Temporal validation failed for {symbol}: {e}")
        
        logger.info(f"Prepared {len(df)} rows for {symbol}")
        return df
    
    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize data types for memory efficiency."""
        # Downcast numeric types
        for col in df.select_dtypes(include=['int64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')
        
        for col in df.select_dtypes(include=['float64']).columns:
            if col not in ['Date']:  # Keep Date as original type
                df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Convert low-cardinality strings to categorical
        for col in df.select_dtypes(include=['object']).columns:
            if col not in ['Date'] and df[col].nunique() / len(df) < 0.1:
                df[col] = df[col].astype('category')
        
        return df
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate data."""
        # Remove rows with missing target values
        df = df.dropna(subset=[self.target_column])
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['Date'], keep='last')
        
        # Sort by date
        df = df.sort_values('Date')
        
        # Check for reasonable price values using expanding window to avoid future leakage
        if self.target_column in df.columns:
            # Use expanding statistics to avoid future information leakage
            price_col = df[self.target_column]
            
            # Calculate expanding statistics
            expanding_mean = price_col.expanding(min_periods=30).mean()
            expanding_std = price_col.expanding(min_periods=30).std()
            
            # Remove extreme outliers (more than 5 standard deviations from expanding statistics)
            outlier_threshold = 5 * expanding_std
            outlier_mask = (
                (price_col >= expanding_mean - outlier_threshold) & 
                (price_col <= expanding_mean + outlier_threshold)
            )
            
            # Only apply outlier removal where we have sufficient history
            df = df[outlier_mask | (df.index < 30)]
        
        return df
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for forecasting."""
        logger.info("Creating features for forecasting")
        
        # Technical indicators
        df = self._create_technical_indicators(df)
        
        # Time-based features
        df = self._create_time_features(df)
        
        # Price-based features
        df = self._create_price_features(df)
        
        # Volume features
        df = self._create_volume_features(df)
        
        # Volatility features
        df = self._create_volatility_features(df)
        
        return df
    
    def integrate_earnings_features(self, df: pd.DataFrame, earnings_features: pd.DataFrame) -> pd.DataFrame:
        """
        Integrate earnings features with the main forecasting dataset.
        
        Args:
            df: Main forecasting dataset
            earnings_features: Earnings features DataFrame
            
        Returns:
            DataFrame with integrated earnings features
        """
        if earnings_features.empty:
            logger.warning("No earnings features to integrate")
            return df
        
        logger.info(f"Integrating earnings features: {len(earnings_features)} records")
        
        # Ensure both DataFrames have Date column
        if 'Date' not in df.columns or 'Date' not in earnings_features.columns:
            logger.warning("Date column missing, cannot integrate earnings features")
            return df
        
        # Prepare earnings features for integration
        earnings_prepared = self._prepare_earnings_features(earnings_features)
        
        # Merge with main dataset using temporal-aware join
        merged_df = self._merge_earnings_temporally(df, earnings_prepared)
        
        # Forward fill earnings features to create continuous time series
        merged_df = self._forward_fill_earnings_features(merged_df)
        
        # Create earnings-based derived features
        merged_df = self._create_earnings_derived_features(merged_df)
        
        logger.info(f"Integrated earnings features: {len(merged_df.columns)} total columns")
        return merged_df
    
    def _prepare_earnings_features(self, earnings_features: pd.DataFrame) -> pd.DataFrame:
        """Prepare earnings features for integration."""
        prepared = earnings_features.copy()
        
        # Ensure Date is datetime
        prepared['Date'] = pd.to_datetime(prepared['Date'])
        
        # Remove any future dates to prevent data leakage
        today = pd.Timestamp.now()
        prepared = prepared[prepared['Date'] <= today]
        
        # Sort by date
        prepared = prepared.sort_values('Date')
        
        # Handle missing values in earnings features
        earnings_columns = [col for col in prepared.columns if col not in ['Date', 'Symbol']]
        
        for col in earnings_columns:
            if prepared[col].dtype in ['float64', 'int64']:
                # For numerical features, use forward fill then backward fill
                prepared[col] = prepared[col].fillna(method='ffill').fillna(method='bfill')
                
                # If still missing, fill with median
                if prepared[col].isnull().any():
                    median_val = prepared[col].median()
                    prepared[col] = prepared[col].fillna(median_val)
        
        # Add earnings-specific temporal indicators
        prepared['has_earnings_data'] = 1
        
        # Create earnings announcement indicators
        if 'earnings_date' in prepared.columns:
            prepared['is_earnings_day'] = 1
        
        return prepared
    
    def _merge_earnings_temporally(self, df: pd.DataFrame, earnings_features: pd.DataFrame) -> pd.DataFrame:
        """Merge earnings features with main dataset using temporal-aware logic."""
        # Create a copy of the main dataset
        merged = df.copy()
        
        # Initialize earnings feature columns with NaN
        earnings_columns = [col for col in earnings_features.columns if col not in ['Date', 'Symbol']]
        for col in earnings_columns:
            merged[col] = np.nan
        
        # For each row in the main dataset, find the most recent earnings data
        for idx, row in merged.iterrows():
            current_date = row['Date']
            
            # Find the most recent earnings data up to this date
            recent_earnings = earnings_features[earnings_features['Date'] <= current_date]
            
            if not recent_earnings.empty:
                # Get the most recent earnings record
                latest_earnings = recent_earnings.iloc[-1]
                
                # Copy earnings features to the main dataset
                for col in earnings_columns:
                    if col in latest_earnings:
                        merged.at[idx, col] = latest_earnings[col]
        
        return merged
    
    def _forward_fill_earnings_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Forward fill earnings features to create continuous time series."""
        # Identify earnings feature columns
        earnings_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in 
                           ['eps', 'earnings', 'surprise', 'revenue', 'profit', 'roa', 'roe', 'debt', 'financial'])]
        
        # Forward fill earnings features
        for col in earnings_columns:
            if col in df.columns:
                df[col] = df[col].fillna(method='ffill')
        
        # Create indicator for data availability
        df['days_since_earnings'] = df.groupby('unique_id').apply(
            lambda x: (x['Date'] - x[x['has_earnings_data'] == 1]['Date'].shift(1)).dt.days
        ).reset_index(level=0, drop=True)
        
        return df
    
    def _create_earnings_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create derived features from earnings data."""
        # Earnings momentum features
        if 'eps_surprise' in df.columns:
            # Rolling earnings surprise trend
            df['eps_surprise_ma_3'] = df['eps_surprise'].rolling(window=3, min_periods=1).mean().shift(1)
            df['eps_surprise_trend'] = (df['eps_surprise'] - df['eps_surprise_ma_3']).shift(1)
        
        if 'earnings_beat' in df.columns:
            # Earnings beat consistency
            df['earnings_beat_ratio_4q'] = df['earnings_beat'].rolling(window=4, min_periods=1).mean().shift(1)
        
        # Financial health momentum
        if 'profit_margin' in df.columns:
            df['profit_margin_change'] = df['profit_margin'].diff().shift(1)
            df['profit_margin_ma_2'] = df['profit_margin'].rolling(window=2, min_periods=1).mean().shift(1)
        
        if 'roe' in df.columns:
            df['roe_change'] = df['roe'].diff().shift(1)
        
        # Growth momentum
        if 'revenue_yoy_growth' in df.columns:
            df['revenue_growth_acceleration'] = df['revenue_yoy_growth'].diff().shift(1)
        
        # Earnings event proximity features
        if 'days_since_earnings' in df.columns:
            # Create bins for days since earnings
            df['earnings_proximity'] = pd.cut(
                df['days_since_earnings'].fillna(365), 
                bins=[0, 7, 30, 90, 365, np.inf], 
                labels=['very_recent', 'recent', 'medium', 'old', 'very_old']
            ).astype(str)
            
            # One-hot encode proximity
            proximity_dummies = pd.get_dummies(df['earnings_proximity'], prefix='earnings_prox')
            df = pd.concat([df, proximity_dummies], axis=1)
        
        return df
    
    def _create_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create technical indicators as features."""
        # Moving averages (shift by 1 to avoid future leakage)
        for window in [5, 10, 20, 50]:
            df[f'sma_{window}'] = df['y'].rolling(window=window, min_periods=window).mean().shift(1)
            df[f'ema_{window}'] = df['y'].ewm(span=window, adjust=False).mean().shift(1)
        
        # RSI (shift by 1 to avoid future leakage)
        delta = df['y'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=14).mean()
        rs = gain / loss
        df['rsi'] = (100 - (100 / (1 + rs))).shift(1)
        
        # MACD (shift by 1 to avoid future leakage)
        exp1 = df['y'].ewm(span=12, adjust=False).mean()
        exp2 = df['y'].ewm(span=26, adjust=False).mean()
        df['macd'] = (exp1 - exp2).shift(1)
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean().shift(1)
        df['macd_histogram'] = (df['macd'] - df['macd_signal']).shift(1)
        
        # Bollinger Bands (shift by 1 to avoid future leakage)
        bb_window = 20
        df['bb_middle'] = df['y'].rolling(window=bb_window, min_periods=bb_window).mean().shift(1)
        bb_std = df['y'].rolling(window=bb_window, min_periods=bb_window).std().shift(1)
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = ((df['y'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower']))
        
        return df
    
    def _create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create time-based features."""
        # Day of week (0=Monday, 6=Sunday)
        df['day_of_week'] = df['ds'].dt.dayofweek
        
        # Month
        df['month'] = df['ds'].dt.month
        
        # Quarter
        df['quarter'] = df['ds'].dt.quarter
        
        # Year
        df['year'] = df['ds'].dt.year
        
        # Day of month
        df['day_of_month'] = df['ds'].dt.day
        
        # Week of year
        df['week_of_year'] = df['ds'].dt.isocalendar().week
        
        # Is beginning/end of month
        df['is_month_start'] = df['ds'].dt.is_month_start.astype(int)
        df['is_month_end'] = df['ds'].dt.is_month_end.astype(int)
        
        # Is quarter start/end
        df['is_quarter_start'] = df['ds'].dt.is_quarter_start.astype(int)
        df['is_quarter_end'] = df['ds'].dt.is_quarter_end.astype(int)
        
        return df
    
    def _create_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create price-based features."""
        # Price changes (use previous period data)
        df['price_change'] = df['y'].diff().shift(1)
        df['price_change_pct'] = df['y'].pct_change().shift(1)
        
        # Lagged prices
        for lag in [1, 2, 3, 5, 10]:
            df[f'price_lag_{lag}'] = df['y'].shift(lag)
        
        # Rolling statistics (shift by 1 to avoid future leakage)
        for window in [5, 10, 20]:
            df[f'price_mean_{window}'] = df['y'].rolling(window=window, min_periods=window).mean().shift(1)
            df[f'price_std_{window}'] = df['y'].rolling(window=window, min_periods=window).std().shift(1)
            df[f'price_min_{window}'] = df['y'].rolling(window=window, min_periods=window).min().shift(1)
            df[f'price_max_{window}'] = df['y'].rolling(window=window, min_periods=window).max().shift(1)
        
        # Price momentum (using previous periods only)
        df['momentum_5'] = (df['y'] / df['y'].shift(5) - 1).shift(1)
        df['momentum_10'] = (df['y'] / df['y'].shift(10) - 1).shift(1)
        df['momentum_20'] = (df['y'] / df['y'].shift(20) - 1).shift(1)
        
        return df
    
    def _create_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create volume-based features."""
        if 'Volume' not in df.columns:
            return df
        
        # Volume moving averages (shift by 1 to avoid future leakage)
        for window in [5, 10, 20]:
            df[f'volume_ma_{window}'] = df['Volume'].rolling(window=window, min_periods=window).mean().shift(1)
        
        # Volume ratio (shift by 1 to avoid future leakage)
        volume_ma_20 = df['Volume'].rolling(window=20, min_periods=20).mean().shift(1)
        df['volume_ratio'] = (df['Volume'] / volume_ma_20).shift(1)
        
        # Price-volume features (shift by 1 to avoid future leakage)
        df['price_volume'] = (df['y'] * df['Volume']).shift(1)
        
        # Volume momentum (shift by 1 to avoid future leakage)
        df['volume_change'] = df['Volume'].pct_change().shift(1)
        
        return df
    
    def _create_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create volatility features."""
        # Historical volatility (shift by 1 to avoid future leakage)
        returns = df['y'].pct_change()
        
        for window in [5, 10, 20]:
            df[f'volatility_{window}'] = returns.rolling(window=window, min_periods=window).std().shift(1)
        
        # Realized volatility (using high-low if available)
        if 'High' in df.columns and 'Low' in df.columns:
            df['high_low_ratio'] = (df['High'] / df['Low']).shift(1)
            df['daily_range'] = ((df['High'] - df['Low']) / df['y']).shift(1)
            
            for window in [5, 10]:
                df[f'avg_range_{window}'] = df['daily_range'].rolling(window=window, min_periods=window).mean().shift(1)
        
        return df
    
    @profile_performance
    def _create_features_vectorized(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create features using optimized vectorized operations.
        This is a faster, memory-efficient version of _create_features.
        """
        logger.info("Creating features using vectorized operations")
        
        prices = df['y']
        
        # Pre-compute common series to reuse
        price_changes = prices.pct_change()
        price_diffs = prices.diff()
        
        # 1. Moving Averages - Vectorized batch computation
        windows = [5, 10, 20, 50]
        sma_features = pd.concat([
            prices.rolling(window=w, min_periods=w).mean().shift(1).rename(f'sma_{w}')
            for w in windows
        ], axis=1)
        
        ema_features = pd.concat([
            prices.ewm(span=w, adjust=False).mean().shift(1).rename(f'ema_{w}')
            for w in windows
        ], axis=1)
        
        # 2. Technical Indicators - Optimized calculations
        # RSI calculation (vectorized)
        delta = price_diffs
        gain = delta.where(delta > 0, 0).rolling(window=14, min_periods=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).shift(1)
        
        # MACD calculation (vectorized)
        exp12 = prices.ewm(span=12, adjust=False).mean()
        exp26 = prices.ewm(span=26, adjust=False).mean()
        macd = (exp12 - exp26).shift(1)
        macd_signal = macd.ewm(span=9, adjust=False).mean().shift(1)
        macd_histogram = (macd - macd_signal).shift(1)
        
        # 3. Bollinger Bands (vectorized)
        bb_window = 20
        bb_middle = prices.rolling(window=bb_window, min_periods=bb_window).mean().shift(1)
        bb_std = prices.rolling(window=bb_window, min_periods=bb_window).std().shift(1)
        bb_upper = (bb_middle + 2 * bb_std)
        bb_lower = (bb_middle - 2 * bb_std)
        bb_position = ((prices - bb_lower) / (bb_upper - bb_lower)).shift(1)
        
        # 4. Price Features (vectorized)
        price_features = pd.DataFrame({
            'price_change': price_changes.shift(1),
            'price_change_abs': price_changes.abs().shift(1),
            'log_return': np.log(prices / prices.shift(1)).shift(1),
        })
        
        # Lagged features (vectorized)
        lag_features = pd.concat([
            price_changes.shift(i).rename(f'price_change_lag_{i}')
            for i in range(1, 6)
        ], axis=1)
        
        # Rolling statistics (vectorized)
        rolling_features = pd.concat([
            price_changes.rolling(window=w, min_periods=w).mean().shift(1).rename(f'price_change_ma_{w}')
            for w in [3, 5, 10]
        ] + [
            price_changes.rolling(window=w, min_periods=w).std().shift(1).rename(f'price_change_std_{w}')
            for w in [3, 5, 10]
        ], axis=1)
        
        # 5. Volume Features (if available)
        volume_features = pd.DataFrame()
        if 'Volume' in df.columns:
            volume = df['Volume']
            volume_features = pd.DataFrame({
                'volume_ma_20': volume.rolling(window=20, min_periods=20).mean().shift(1),
                'volume_ratio': (volume / volume.rolling(window=20, min_periods=20).mean()).shift(1),
                'price_volume': (prices * volume).shift(1),
            })
        
        # 6. Volatility Features (vectorized)
        volatility_windows = [5, 10, 20]
        volatility_features = pd.concat([
            price_changes.rolling(window=w, min_periods=w).std().shift(1).rename(f'volatility_{w}')
            for w in volatility_windows
        ], axis=1)
        
        # High-Low features (if available)
        if 'High' in df.columns and 'Low' in df.columns:
            high_low_features = pd.DataFrame({
                'high_low_ratio': (df['High'] / df['Low']).shift(1),
                'daily_range': ((df['High'] - df['Low']) / prices).shift(1),
            })
            
            # Average range features
            range_features = pd.concat([
                high_low_features['daily_range'].rolling(window=w, min_periods=w).mean().shift(1).rename(f'avg_range_{w}')
                for w in [5, 10]
            ], axis=1)
            
            volatility_features = pd.concat([volatility_features, high_low_features, range_features], axis=1)
        
        # 7. Time Features (vectorized)
        time_features = pd.DataFrame({
            'day_of_week': df['ds'].dt.dayofweek,
            'month': df['ds'].dt.month,
            'quarter': df['ds'].dt.quarter,
            'is_month_end': df['ds'].dt.is_month_end.astype(int),
            'is_quarter_end': df['ds'].dt.is_quarter_end.astype(int),
        })
        
        # Combine all features efficiently
        technical_features = pd.DataFrame({
            'rsi': rsi,
            'macd': macd,
            'macd_signal': macd_signal,
            'macd_histogram': macd_histogram,
            'bb_middle': bb_middle,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'bb_position': bb_position,
        })
        
        # Concatenate all feature groups in one operation
        feature_groups = [
            sma_features, ema_features, technical_features, price_features,
            lag_features, rolling_features, volatility_features, time_features
        ]
        
        if not volume_features.empty:
            feature_groups.append(volume_features)
        
        all_features = pd.concat(feature_groups, axis=1)
        
        # Combine with original dataframe
        df = pd.concat([df, all_features], axis=1)
        
        logger.info(f"Created {len(all_features.columns)} features using vectorized operations")
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in features."""
        # Forward fill for most features
        feature_cols = [col for col in df.columns if col not in ['ds', 'unique_id', 'y']]
        
        for col in feature_cols:
            if col in df.columns:
                # Forward fill then backward fill
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
        
        # Store feature columns for later use
        self.feature_columns = feature_cols
        
        return df
    
    def create_train_test_split(self, df: pd.DataFrame, test_size: int = 30, 
                              gap_days: int = 0) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Create train/test split for time series with temporal validation.
        
        Args:
            df: Processed data
            test_size: Number of days for test set
            gap_days: Days to skip between train and test (to simulate data lag)
            
        Returns:
            Tuple of (train_data, test_data)
        """
        # Use temporal splitter if available, otherwise use simple split
        if self.enable_temporal_validation and self.temporal_splitter:
            try:
                # Convert test_size from days to fraction
                test_fraction = test_size / len(df)
                train_data, test_data = self.temporal_splitter.temporal_train_test_split(
                    df, test_size=test_fraction, gap_days=gap_days
                )
                return train_data, test_data
            except Exception as e:
                logger.warning(f"Temporal split failed, using simple split: {e}")
        
        # Fallback to simple split
        split_idx = len(df) - test_size
        if gap_days > 0:
            # Apply gap between train and test
            train_data = df.iloc[:split_idx-gap_days].copy()
            test_data = df.iloc[split_idx:].copy()
        else:
            train_data = df.iloc[:split_idx].copy()
            test_data = df.iloc[split_idx:].copy()
        
        logger.info(f"Created train/test split: {len(train_data)} train, {len(test_data)} test")
        return train_data, test_data
    
    def prepare_multiple_stocks(self, stocks_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Prepare data for multiple stocks in nixtla format.
        
        Args:
            stocks_data: Dictionary of {symbol: dataframe}
            
        Returns:
            Combined dataframe in nixtla format
        """
        all_data = []
        
        for symbol, data in stocks_data.items():
            processed_data = self.prepare_forecasting_data(data, symbol)
            all_data.append(processed_data)
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Sort by unique_id and date
        combined_df = combined_df.sort_values(['unique_id', 'ds']).reset_index(drop=True)
        
        logger.info(f"Prepared combined data for {len(stocks_data)} stocks: {len(combined_df)} total rows")
        return combined_df
    
    def get_exogenous_features(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of exogenous features for forecasting.
        
        Args:
            df: Processed dataframe
            
        Returns:
            List of feature column names
        """
        # Exclude target and identifier columns
        exclude_cols = ['ds', 'unique_id', 'y', 'Date', self.target_column]
        exog_features = [col for col in df.columns if col not in exclude_cols]
        
        logger.info(f"Found {len(exog_features)} exogenous features")
        return exog_features
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate prepared data for forecasting.
        
        Args:
            df: Processed dataframe
            
        Returns:
            True if data is valid, False otherwise
        """
        required_cols = ['ds', 'unique_id', 'y']
        
        # Check required columns
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            return False
        
        # Check for missing values in required columns
        for col in required_cols:
            if df[col].isnull().any():
                logger.error(f"Missing values found in {col}")
                return False
        
        # Check date column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['ds']):
            logger.error("Date column 'ds' is not datetime type")
            return False
        
        # Check for minimum data points
        if len(df) < 50:
            logger.error(f"Insufficient data points: {len(df)} (minimum 50 required)")
            return False
        
        logger.info("Data validation passed")
        return True