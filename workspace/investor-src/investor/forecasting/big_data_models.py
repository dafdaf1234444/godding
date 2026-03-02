"""
Big Data ML Models for comprehensive financial forecasting.
Designed to handle large datasets with macro, stock, and indicator data.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class BigDataMLForecaster:
    """
    Comprehensive ML forecasting system for large financial datasets.
    
    Supports:
    - CatBoost for categorical features and robustness
    - TabNet for attention-based deep learning on tabular data
    - NGBoost for uncertainty quantification
    - Multi-target regression for multiple asset forecasting
    - Feature selection and engineering for big datasets
    - Distributed training capabilities
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize big data ML forecaster."""
        self.config = config or self._get_default_config()
        self.models = {}
        self.scalers = {}
        self.feature_selectors = {}
        self.feature_importance = {}
        self.performance_metrics = {}
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for big data models."""
        return {
            'models': {
                'catboost': {
                    'iterations': 1000,
                    'learning_rate': 0.03,
                    'depth': 8,
                    'l2_leaf_reg': 3,
                    'random_seed': 42,
                    'verbose': False,
                    'allow_writing_files': False
                },
                'lightgbm': {
                    'objective': 'regression',
                    'num_leaves': 64,
                    'learning_rate': 0.05,
                    'feature_fraction': 0.8,
                    'bagging_fraction': 0.8,
                    'bagging_freq': 5,
                    'verbose': -1,
                    'random_state': 42,
                    'n_estimators': 1000
                },
                'tabnet': {
                    'n_d': 32,
                    'n_a': 32,
                    'n_steps': 5,
                    'gamma': 1.3,
                    'lambda_sparse': 1e-3,
                    'optimizer_fn': 'adam',
                    'optimizer_params': {'lr': 2e-2},
                    'max_epochs': 100,
                    'patience': 20,
                    'batch_size': 256
                },
                'ngboost': {
                    'n_estimators': 500,
                    'learning_rate': 0.01,
                    'minibatch_frac': 1.0,
                    'verbose': False,
                    'random_state': 42
                }
            },
            'feature_selection': {
                'max_features': 200,
                'importance_threshold': 0.001,
                'correlation_threshold': 0.95
            },
            'training': {
                'test_size': 0.2,
                'cv_folds': 5,
                'early_stopping_rounds': 50
            }
        }
    
    def prepare_big_dataset(self, 
                           stock_data: Dict[str, pd.DataFrame],
                           macro_data: Optional[pd.DataFrame] = None,
                           sentiment_data: Optional[pd.DataFrame] = None,
                           additional_features: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Prepare comprehensive dataset for big data ML.
        
        Args:
            stock_data: Dictionary of stock dataframes
            macro_data: Macroeconomic indicators
            sentiment_data: Sentiment indicators
            additional_features: Any additional feature data
            
        Returns:
            Comprehensive dataset ready for ML
        """
        logger.info("Preparing big dataset for ML")
        
        # Start with stock data
        all_stock_data = []
        for symbol, data in stock_data.items():
            stock_df = data.copy()
            stock_df['symbol'] = symbol
            
            # Create target variable (next day return)
            stock_df['target_1d'] = stock_df['Close'].shift(-1)
            stock_df['target_5d'] = stock_df['Close'].shift(-5)
            stock_df['target_21d'] = stock_df['Close'].shift(-21)
            
            # Returns
            stock_df['return_1d'] = stock_df['Close'].pct_change()
            stock_df['return_5d'] = stock_df['Close'].pct_change(5)
            stock_df['return_21d'] = stock_df['Close'].pct_change(21)
            
            # Advanced technical indicators
            stock_df = self._add_advanced_technical_features(stock_df)
            
            # Cross-asset features (will be added later)
            all_stock_data.append(stock_df)
        
        # Combine all stock data
        combined_data = pd.concat(all_stock_data, ignore_index=True)
        combined_data = combined_data.sort_values(['Date', 'symbol']).reset_index(drop=True)
        
        # Add cross-asset features
        combined_data = self._add_cross_asset_features(combined_data)
        
        # Add macroeconomic data
        if macro_data is not None:
            combined_data = self._merge_external_data(combined_data, macro_data, 'macro')\n        \n        # Add sentiment data
        if sentiment_data is not None:
            combined_data = self._merge_external_data(combined_data, sentiment_data, 'sentiment')
        
        # Add additional features
        if additional_features is not None:
            combined_data = self._merge_external_data(combined_data, additional_features, 'additional')
        
        # Feature engineering
        combined_data = self._create_interaction_features(combined_data)
        combined_data = self._create_time_features(combined_data)
        
        logger.info(f"Prepared big dataset: {len(combined_data)} rows, {len(combined_data.columns)} features")
        return combined_data
    
    def _add_advanced_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive technical indicators."""
        # Existing basic features
        df['sma_5'] = df['Close'].rolling(5).mean().shift(1)
        df['sma_21'] = df['Close'].rolling(21).mean().shift(1)
        df['sma_50'] = df['Close'].rolling(50).mean().shift(1)
        df['sma_200'] = df['Close'].rolling(200).mean().shift(1)
        
        # Advanced moving averages
        df['ema_12'] = df['Close'].ewm(span=12).mean().shift(1)
        df['ema_26'] = df['Close'].ewm(span=26).mean().shift(1)
        df['wma_21'] = df['Close'].rolling(21).apply(lambda x: np.dot(x, np.arange(1, len(x)+1)) / np.arange(1, len(x)+1).sum()).shift(1)
        
        # Momentum indicators
        df['rsi_14'] = self._calculate_rsi(df['Close'], 14).shift(1)
        df['rsi_7'] = self._calculate_rsi(df['Close'], 7).shift(1)
        df['stoch_k'] = self._calculate_stochastic(df, 14).shift(1)
        
        # MACD family
        df['macd'] = (df['ema_12'] - df['ema_26']).shift(1)
        df['macd_signal'] = df['macd'].ewm(span=9).mean().shift(1)
        df['macd_histogram'] = (df['macd'] - df['macd_signal']).shift(1)
        
        # Bollinger Bands
        bb_std = df['Close'].rolling(20).std()
        df['bb_upper'] = (df['sma_21'] + 2 * bb_std).shift(1)
        df['bb_lower'] = (df['sma_21'] - 2 * bb_std).shift(1)
        df['bb_width'] = ((df['bb_upper'] - df['bb_lower']) / df['sma_21']).shift(1)
        df['bb_position'] = ((df['Close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])).shift(1)
        
        # Volume indicators
        if 'Volume' in df.columns:
            df['volume_sma_21'] = df['Volume'].rolling(21).mean().shift(1)
            df['volume_ratio'] = (df['Volume'] / df['volume_sma_21']).shift(1)
            df['price_volume'] = (df['Close'] * df['Volume']).shift(1)
            df['obv'] = self._calculate_obv(df).shift(1)
        
        # Volatility indicators
        df['atr_14'] = self._calculate_atr(df, 14).shift(1)
        df['volatility_21'] = df['return_1d'].rolling(21).std().shift(1)
        df['volatility_ratio'] = (df['volatility_21'] / df['volatility_21'].rolling(63).mean()).shift(1)
        
        # Price action features
        if 'High' in df.columns and 'Low' in df.columns:
            df['daily_range'] = ((df['High'] - df['Low']) / df['Close']).shift(1)
            df['gap'] = ((df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)).shift(1)
            df['intraday_return'] = ((df['Close'] - df['Open']) / df['Open']).shift(1)
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_stochastic(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate Stochastic %K."""
        if 'High' not in df.columns or 'Low' not in df.columns:
            return pd.Series(index=df.index, dtype=float)
        
        lowest_low = df['Low'].rolling(window=window).min()
        highest_high = df['High'].rolling(window=window).max()
        return 100 * (df['Close'] - lowest_low) / (highest_high - lowest_low)
    
    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume."""
        if 'Volume' not in df.columns:
            return pd.Series(index=df.index, dtype=float)
        
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = df['Volume'].iloc[0]
        
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['Volume'].iloc[i]
            elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['Volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    def _calculate_atr(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        if 'High' not in df.columns or 'Low' not in df.columns:
            return pd.Series(index=df.index, dtype=float)
        
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=window).mean()
    
    def _add_cross_asset_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add cross-asset correlation and momentum features."""
        # Market-wide features
        market_data = df.groupby('Date').agg({
            'Close': ['mean', 'std', 'min', 'max'],
            'Volume': 'sum',
            'return_1d': ['mean', 'std']
        }).reset_index()
        
        market_data.columns = ['Date', 'market_price_mean', 'market_price_std', 'market_price_min', 'market_price_max',
                              'market_volume_total', 'market_return_mean', 'market_return_std']
        
        # Add market momentum
        market_data['market_momentum_5d'] = market_data['market_return_mean'].rolling(5).mean()
        market_data['market_momentum_21d'] = market_data['market_return_mean'].rolling(21).mean()
        
        # Merge back
        df = df.merge(market_data, on='Date', how='left')
        
        # Relative performance
        df['relative_performance'] = df['return_1d'] - df['market_return_mean']
        df['relative_volume'] = df['Volume'] / df['market_volume_total']
        
        return df
    
    def _merge_external_data(self, df: pd.DataFrame, external_data: pd.DataFrame, prefix: str) -> pd.DataFrame:
        """Merge external data with proper prefix."""
        external_data_copy = external_data.copy()
        
        # Add prefix to columns except Date
        rename_dict = {col: f'{prefix}_{col}' for col in external_data_copy.columns if col != 'Date'}
        external_data_copy = external_data_copy.rename(columns=rename_dict)
        
        # Merge
        merged = df.merge(external_data_copy, on='Date', how='left')
        
        # Forward fill external data
        external_cols = [col for col in merged.columns if col.startswith(f'{prefix}_')]
        merged[external_cols] = merged[external_cols].fillna(method='ffill')
        
        return merged
    
    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features between key variables."""
        # Volume-Price interactions
        if 'Volume' in df.columns:
            df['volume_price_momentum'] = df['volume_ratio'] * df['return_1d']
            df['volume_volatility'] = df['volume_ratio'] * df['volatility_21']
        
        # Technical indicator interactions
        df['rsi_bb_signal'] = df['rsi_14'] * df['bb_position']
        df['macd_rsi_signal'] = df['macd'] * df['rsi_14']
        
        # Market relative interactions
        df['beta_proxy'] = df['relative_performance'] / df['market_return_std']
        
        return df
    
    def _create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create comprehensive time-based features."""
        df['day_of_week'] = df['Date'].dt.dayofweek
        df['month'] = df['Date'].dt.month
        df['quarter'] = df['Date'].dt.quarter
        df['day_of_month'] = df['Date'].dt.day
        df['week_of_year'] = df['Date'].dt.isocalendar().week
        
        # Market timing features
        df['is_month_end'] = df['Date'].dt.is_month_end.astype(int)
        df['is_quarter_end'] = df['Date'].dt.is_quarter_end.astype(int)
        df['days_to_month_end'] = (df['Date'].dt.days_in_month - df['Date'].dt.day)
        
        # Cyclical encoding
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        return df
    
    def initialize_models(self) -> Dict[str, Any]:
        """Initialize big data ML models."""
        models = {}
        
        # CatBoost
        try:
            from catboost import CatBoostRegressor
            models['catboost'] = CatBoostRegressor(**self.config['models']['catboost'])
            logger.info("Initialized CatBoost")
        except ImportError:
            logger.warning("CatBoost not available")
        
        # LightGBM
        try:
            import lightgbm as lgb
            models['lightgbm'] = lgb.LGBMRegressor(**self.config['models']['lightgbm'])
            logger.info("Initialized LightGBM")
        except ImportError:
            logger.warning("LightGBM not available")
        
        # TabNet (requires pytorch-tabnet)
        try:
            from pytorch_tabnet.tab_model import TabNetRegressor
            models['tabnet'] = TabNetRegressor(**self.config['models']['tabnet'])
            logger.info("Initialized TabNet")
        except ImportError:
            logger.warning("TabNet not available")
        
        # NGBoost
        try:
            from ngboost import NGBRegressor
            from ngboost.distns import Normal
            from ngboost.scores import MLE
            from sklearn.tree import DecisionTreeRegressor
            
            models['ngboost'] = NGBRegressor(
                Base=DecisionTreeRegressor(criterion='friedman_mse', max_depth=3),
                Dist=Normal,
                Score=MLE(),
                **self.config['models']['ngboost']
            )
            logger.info("Initialized NGBoost")
        except ImportError:
            logger.warning("NGBoost not available")
        
        return models
    
    def feature_selection(self, X: pd.DataFrame, y: pd.Series) -> List[str]:
        """Perform feature selection for big datasets."""
        logger.info(f"Starting feature selection from {len(X.columns)} features")
        
        # Remove features with too many missing values
        missing_threshold = 0.3
        valid_features = X.columns[X.isnull().mean() < missing_threshold].tolist()
        X_valid = X[valid_features]
        
        # Remove highly correlated features
        corr_matrix = X_valid.corr().abs()
        upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        high_corr_features = [column for column in upper_triangle.columns if any(upper_triangle[column] > self.config['feature_selection']['correlation_threshold'])]
        X_valid = X_valid.drop(columns=high_corr_features)
        
        # Feature importance using LightGBM
        try:
            import lightgbm as lgb
            
            # Fill missing values for feature selection
            X_filled = X_valid.fillna(0)
            
            model = lgb.LGBMRegressor(n_estimators=100, random_state=42, verbose=-1)
            model.fit(X_filled, y)
            
            # Get feature importance
            importance_df = pd.DataFrame({
                'feature': X_filled.columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            # Select top features
            max_features = min(self.config['feature_selection']['max_features'], len(importance_df))
            selected_features = importance_df.head(max_features)['feature'].tolist()
            
            logger.info(f"Selected {len(selected_features)} features after selection")
            return selected_features
            
        except Exception as e:
            logger.warning(f"Feature selection failed: {e}, using all valid features")
            return X_valid.columns.tolist()
    
    def train_models(self, df: pd.DataFrame, target_col: str = 'target_1d') -> Dict[str, Any]:
        """Train big data ML models."""
        logger.info("Training big data ML models")
        
        # Prepare data
        exclude_cols = ['Date', 'symbol'] + [col for col in df.columns if col.startswith('target_')]
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Remove rows with missing targets
        valid_data = df.dropna(subset=[target_col])
        
        if len(valid_data) < 100:
            logger.error("Insufficient valid data for training")
            return {}
        
        X = valid_data[feature_cols]
        y = valid_data[target_col]
        
        # Feature selection
        selected_features = self.feature_selection(X, y)
        X_selected = X[selected_features].fillna(0)
        
        # Scale features
        scaler = RobustScaler()
        X_scaled = pd.DataFrame(
            scaler.fit_transform(X_selected),
            columns=X_selected.columns,
            index=X_selected.index
        )
        self.scalers[target_col] = scaler
        
        # Initialize models
        models = self.initialize_models()
        
        # Time series split
        tscv = TimeSeriesSplit(n_splits=self.config['training']['cv_folds'])
        
        trained_models = {}
        
        for model_name, model in models.items():
            logger.info(f"Training {model_name}")
            
            try:
                # Cross-validation
                cv_scores = []
                for train_idx, val_idx in tscv.split(X_scaled):
                    X_train, X_val = X_scaled.iloc[train_idx], X_scaled.iloc[val_idx]
                    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                    
                    # Handle categorical features for CatBoost
                    if model_name == 'catboost':
                        cat_features = [i for i, col in enumerate(X_scaled.columns) 
                                      if col in ['symbol', 'day_of_week', 'month', 'quarter']]
                        model.fit(X_train, y_train, cat_features=cat_features, verbose=False)
                    else:
                        model.fit(X_train, y_train)
                    
                    y_pred = model.predict(X_val)
                    mae = mean_absolute_error(y_val, y_pred)
                    cv_scores.append(mae)
                
                # Train on full dataset
                if model_name == 'catboost':
                    cat_features = [i for i, col in enumerate(X_scaled.columns) 
                                  if col in ['symbol', 'day_of_week', 'month', 'quarter']]
                    model.fit(X_scaled, y, cat_features=cat_features, verbose=False)
                else:
                    model.fit(X_scaled, y)
                
                trained_models[model_name] = model
                
                # Store performance
                self.performance_metrics[model_name] = {
                    'cv_mae_mean': np.mean(cv_scores),
                    'cv_mae_std': np.std(cv_scores),
                    'target': target_col
                }
                
                # Store feature importance
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[model_name] = pd.DataFrame({
                        'feature': X_scaled.columns,
                        'importance': model.feature_importances_
                    }).sort_values('importance', ascending=False)
                
                logger.info(f"Trained {model_name} - CV MAE: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
        
        self.models[target_col] = trained_models
        logger.info(f"Successfully trained {len(trained_models)} big data models")
        
        return trained_models
    
    def predict(self, df: pd.DataFrame, target_col: str = 'target_1d', horizon: int = 21) -> pd.DataFrame:
        """Make predictions with big data models."""
        logger.info(f"Making predictions for {horizon} days")
        
        if target_col not in self.models or not self.models[target_col]:
            logger.error(f"No trained models for {target_col}")
            return pd.DataFrame()
        
        # Get latest data for each symbol
        latest_data = df.groupby('symbol').tail(1).copy()
        
        predictions = []
        
        for _, row in latest_data.iterrows():
            symbol = row['symbol']
            base_date = row['Date']
            
            symbol_predictions = []
            
            for day in range(1, horizon + 1):
                pred_date = base_date + timedelta(days=day)
                
                # Prepare features (this is simplified - in practice you'd need to update features)
                exclude_cols = ['Date', 'symbol'] + [col for col in df.columns if col.startswith('target_')]
                feature_cols = [col for col in df.columns if col not in exclude_cols]
                
                # Use latest row features (in practice, you'd update these)
                features = row[feature_cols].fillna(0)
                
                # Scale features
                if target_col in self.scalers:
                    features_scaled = self.scalers[target_col].transform([features])
                else:
                    features_scaled = [features]
                
                pred_row = {
                    'unique_id': symbol,
                    'ds': pred_date
                }
                
                # Get predictions from each model
                for model_name, model in self.models[target_col].items():
                    try:
                        pred = model.predict(features_scaled)[0]
                        pred_row[f'BigML_{model_name}'] = pred
                    except Exception as e:
                        logger.warning(f"Prediction failed for {model_name}: {e}")
                        pred_row[f'BigML_{model_name}'] = np.nan
                
                symbol_predictions.append(pred_row)
            
            predictions.extend(symbol_predictions)
        
        if predictions:
            predictions_df = pd.DataFrame(predictions)
            logger.info(f"Generated big data ML predictions: {len(predictions_df)} rows")
            return predictions_df
        
        return pd.DataFrame()
    
    def get_model_summary(self) -> Dict[str, Any]:
        """Get comprehensive model summary."""
        summary = {
            'trained_targets': list(self.models.keys()),
            'model_performance': self.performance_metrics,
            'feature_importance': {name: df.head(10).to_dict() for name, df in self.feature_importance.items()},
            'total_models': sum(len(models) for models in self.models.values())
        }
        
        return summary