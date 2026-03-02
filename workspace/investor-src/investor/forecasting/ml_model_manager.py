"""
Machine Learning Model Manager for multivariate forecasting.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
import pickle
from datetime import timedelta
import warnings
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler, LabelEncoder

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MLForecastingModelManager:
    """
    Machine Learning Model Manager for multivariate forecasting.
    
    Supports:
    - LightGBM for gradient boosting
    - XGBoost for ensemble learning
    - Random Forest for bagging
    - Linear models for baseline
    - Neural networks for deep learning
    - Multivariate time series forecasting
    - Cross-stock feature engineering
    """
    
    def __init__(self, models_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ML model manager.
        
        Args:
            models_config: Configuration for ML models
        """
        self.models_config = models_config or self._get_default_config()
        self.fitted_models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.feature_importance = {}
        self.model_performance = {}
        self.multivariate_data = pd.DataFrame()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default ML model configuration."""
        return {
            'ml_models': {
                'lightgbm': {
                    'objective': 'regression',
                    'num_leaves': 31,
                    'learning_rate': 0.05,
                    'feature_fraction': 0.9,
                    'bagging_fraction': 0.8,
                    'bagging_freq': 5,
                    'verbose': -1,
                    'random_state': 42
                },
                'xgboost': {
                    'objective': 'reg:squarederror',
                    'n_estimators': 100,
                    'max_depth': 6,
                    'learning_rate': 0.05,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,
                    'random_state': 42
                },
                'random_forest': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'min_samples_split': 5,
                    'min_samples_leaf': 2,
                    'random_state': 42
                },
                'linear_models': {
                    'ridge_alpha': 1.0,
                    'lasso_alpha': 0.1,
                    'elastic_net_alpha': 0.1,
                    'elastic_net_l1_ratio': 0.5
                }
            },
            'forecasting': {
                'lookback_days': 60,
                'forecast_horizon': 21,
                'cross_validation_folds': 5,
                'feature_selection_threshold': 0.01,
                'multivariate_enabled': True
            }
        }
    
    def prepare_multivariate_data(self, stocks_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Prepare multivariate dataset with cross-stock features.
        
        Args:
            stocks_data: Dictionary of {symbol: dataframe}
            
        Returns:
            Combined multivariate dataframe
        """
        logger.info("Preparing multivariate dataset")
        
        all_data = []
        
        # Process each stock individually first
        for symbol, data in stocks_data.items():
            stock_data = data.copy()
            stock_data['symbol'] = symbol
            stock_data['target'] = stock_data['Close'].shift(-1)  # Next day's price
            
            # Add symbol-specific features
            stock_data = self._add_stock_specific_features(stock_data, symbol)
            
            all_data.append(stock_data)
        
        # Combine all stocks
        combined_data = pd.concat(all_data, ignore_index=True)
        combined_data = combined_data.sort_values(['Date', 'symbol']).reset_index(drop=True)
        
        # Add cross-stock features
        combined_data = self._add_cross_stock_features(combined_data)
        
        # Add market features
        combined_data = self._add_market_features(combined_data)
        
        self.multivariate_data = combined_data
        logger.info(f"Prepared multivariate dataset with {len(combined_data)} rows and {len(combined_data.columns)} features")
        
        return combined_data
    
    def _add_stock_specific_features(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Add features specific to individual stocks - NO LOOKAHEAD BIAS."""
        df = data.copy()
        
        # Price features (using past data only)
        df['price_change'] = df['Close'].diff()
        df['price_change_pct'] = df['Close'].pct_change()
        df['log_return'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Rolling statistics (using past data only)
        for window in [5, 10, 20, 50]:
            df[f'sma_{window}'] = df['Close'].shift(1).rolling(window=window).mean()
            df[f'std_{window}'] = df['Close'].shift(1).rolling(window=window).std()
            df[f'rsi_{window}'] = self._calculate_rsi(df['Close'].shift(1), window)
        
        # Volume features
        if 'Volume' in df.columns:
            df['volume_change'] = df['Volume'].pct_change()
            df['volume_ma_5'] = df['Volume'].shift(1).rolling(window=5).mean()
            df['volume_ratio'] = df['Volume'] / df['volume_ma_5']
            df['price_volume'] = df['Close'] * df['Volume']
        
        # Volatility features (using past data only)
        for window in [5, 10, 20]:
            df[f'volatility_{window}'] = df['log_return'].shift(1).rolling(window=window).std()
        
        # High-Low features
        if 'High' in df.columns and 'Low' in df.columns:
            df['daily_range'] = (df['High'] - df['Low']) / df['Close']
            df['daily_range_ma'] = df['daily_range'].shift(1).rolling(window=10).mean()
        
        # Momentum features (using past data only)
        for lag in [1, 3, 5, 10, 20]:
            df[f'momentum_{lag}'] = df['Close'] / df['Close'].shift(lag) - 1
        
        # Time features
        df['day_of_week'] = df['Date'].dt.dayofweek
        df['month'] = df['Date'].dt.month
        df['quarter'] = df['Date'].dt.quarter
        df['is_month_end'] = df['Date'].dt.is_month_end.astype(int)
        df['is_quarter_end'] = df['Date'].dt.is_quarter_end.astype(int)
        
        return df
    
    def _add_cross_stock_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add cross-stock correlation and relative performance features."""
        df = data.copy()
        
        # For each date, calculate cross-stock features
        for date in df['Date'].unique():
            date_mask = df['Date'] == date
            date_data = df[date_mask].copy()
            
            if len(date_data) > 1:  # Need multiple stocks
                # Cross-stock correlations (using past 20 days)
                for symbol in date_data['symbol'].unique():
                    symbol_data = df[(df['symbol'] == symbol) & (df['Date'] <= date)].tail(20)
                    other_symbols_data = df[(df['symbol'] != symbol) & (df['Date'] <= date)]
                    
                    if len(symbol_data) > 10 and len(other_symbols_data) > 10:
                        # Calculate average correlation with other stocks
                        correlations = []
                        for other_symbol in other_symbols_data['symbol'].unique():
                            other_data = other_symbols_data[other_symbols_data['symbol'] == other_symbol].tail(20)
                            if len(other_data) > 10:
                                corr = symbol_data['Close'].corr(other_data['Close'])
                                if not np.isnan(corr):
                                    correlations.append(corr)
                        
                        avg_correlation = np.mean(correlations) if correlations else 0
                        df.loc[(df['Date'] == date) & (df['symbol'] == symbol), 'avg_cross_correlation'] = avg_correlation
                
                # Market relative performance
                market_avg_return = date_data['price_change_pct'].mean()
                df.loc[date_mask, 'relative_to_market'] = date_data['price_change_pct'] - market_avg_return
                
                # Sector momentum (simplified - treat all as same sector for now)
                market_momentum = date_data['momentum_5'].mean()
                df.loc[date_mask, 'market_momentum'] = market_momentum
        
        return df
    
    def _add_market_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add market-wide features."""
        df = data.copy()
        
        # Market-wide features calculated daily
        daily_stats = df.groupby('Date').agg({
            'Close': ['mean', 'std', 'min', 'max'],
            'Volume': 'sum',
            'price_change_pct': ['mean', 'std']
        }).reset_index()
        
        daily_stats.columns = ['Date', 'market_price_mean', 'market_price_std', 'market_price_min', 'market_price_max',
                              'market_volume_total', 'market_return_mean', 'market_return_std']
        
        # Add market volatility
        daily_stats['market_volatility'] = daily_stats['market_return_std']
        
        # Merge back to main dataset
        df = df.merge(daily_stats, on='Date', how='left')
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def initialize_ml_models(self) -> Dict[str, Any]:
        """Initialize machine learning models."""
        models = {}
        
        try:
            # LightGBM
            import lightgbm as lgb
            lgb_config = self.models_config['ml_models']['lightgbm']
            models['lightgbm'] = lgb.LGBMRegressor(**lgb_config)
            
        except ImportError:
            logger.warning("LightGBM not available")
        
        try:
            # XGBoost
            import xgboost as xgb
            xgb_config = self.models_config['ml_models']['xgboost']
            models['xgboost'] = xgb.XGBRegressor(**xgb_config)
            
        except ImportError:
            logger.warning("XGBoost not available")
        
        # Scikit-learn models (always available)
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.linear_model import Ridge, Lasso, ElasticNet
        
        rf_config = self.models_config['ml_models']['random_forest']
        models['random_forest'] = RandomForestRegressor(**rf_config)
        
        linear_config = self.models_config['ml_models']['linear_models']
        models['ridge'] = Ridge(alpha=linear_config['ridge_alpha'])
        models['lasso'] = Lasso(alpha=linear_config['lasso_alpha'])
        models['elastic_net'] = ElasticNet(alpha=linear_config['elastic_net_alpha'], 
                                          l1_ratio=linear_config['elastic_net_l1_ratio'])
        
        logger.info(f"Initialized {len(models)} ML models: {list(models.keys())}")
        return models
    
    def prepare_features_and_targets(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """Prepare features and targets for ML training."""
        df = data.copy()
        
        # Remove rows with missing targets
        df = df.dropna(subset=['target'])
        
        # Define feature columns (exclude metadata and target, but include symbol for encoding)
        exclude_cols = ['Date', 'target', 'Close', 'Open', 'High', 'Low', 'Volume', 'Adj Close']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Handle categorical features including symbol
        categorical_cols = ['day_of_week', 'month', 'quarter', 'symbol']
        for col in categorical_cols:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[col] = self.label_encoders[col].fit_transform(df[col].fillna(-1))
                else:
                    # Handle unseen categories
                    unique_vals = df[col].fillna(-1).unique()
                    known_classes = set(self.label_encoders[col].classes_)
                    unknown_mask = ~pd.Series(unique_vals).isin(known_classes)
                    
                    if unknown_mask.any():
                        # Add unknown categories to the encoder
                        new_classes = np.concatenate([self.label_encoders[col].classes_, unique_vals[unknown_mask]])
                        self.label_encoders[col].classes_ = new_classes
                    
                    df[col] = self.label_encoders[col].transform(df[col].fillna(-1))
        
        # Prepare features and targets
        X = df[feature_cols].fillna(0)  # Fill remaining NaN with 0
        y = df['target']
        
        # Scale features
        if 'feature_scaler' not in self.scalers:
            self.scalers['feature_scaler'] = StandardScaler()
            X_scaled = pd.DataFrame(
                self.scalers['feature_scaler'].fit_transform(X),
                columns=X.columns,
                index=X.index
            )
        else:
            X_scaled = pd.DataFrame(
                self.scalers['feature_scaler'].transform(X),
                columns=X.columns,
                index=X.index
            )
        
        logger.info(f"Prepared features: {len(feature_cols)} features, {len(X_scaled)} samples")
        return X_scaled, y, feature_cols
    
    def train_ml_models(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Train machine learning models."""
        logger.info("Training ML models")
        
        # Prepare data
        X, y, feature_cols = self.prepare_features_and_targets(data)
        
        if len(X) < 100:
            logger.warning("Insufficient data for ML training")
            return {}
        
        # Initialize models
        models = self.initialize_ml_models()
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=self.models_config['forecasting']['cross_validation_folds'])
        
        trained_models = {}
        
        for model_name, model in models.items():
            logger.info(f"Training {model_name}")
            
            try:
                # Cross-validation scores
                cv_scores = []
                
                for train_idx, val_idx in tscv.split(X):
                    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                    
                    # Train model
                    model.fit(X_train, y_train)
                    
                    # Validate
                    y_pred = model.predict(X_val)
                    mae = mean_absolute_error(y_val, y_pred)
                    cv_scores.append(mae)
                
                # Train on full data
                model.fit(X, y)
                
                # Store model and performance
                trained_models[model_name] = model
                self.model_performance[model_name] = {
                    'cv_mae_mean': np.mean(cv_scores),
                    'cv_mae_std': np.std(cv_scores),
                    'cv_scores': cv_scores
                }
                
                # Store feature importance if available
                if hasattr(model, 'feature_importances_'):
                    importance_df = pd.DataFrame({
                        'feature': feature_cols,
                        'importance': model.feature_importances_
                    }).sort_values('importance', ascending=False)
                    self.feature_importance[model_name] = importance_df
                
                logger.info(f"Trained {model_name} - CV MAE: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
        
        self.fitted_models.update(trained_models)
        logger.info(f"Successfully trained {len(trained_models)} ML models")
        
        return trained_models
    
    def predict_ml_models(self, data: pd.DataFrame, horizon: int = 21) -> pd.DataFrame:
        """Make predictions with trained ML models."""
        logger.info(f"Making ML predictions for {horizon} days")
        
        if not self.fitted_models:
            logger.error("No models trained. Call train_ml_models() first.")
            return pd.DataFrame()
        
        predictions = []
        
        # Get unique symbols
        symbols = data['symbol'].unique()
        
        for symbol in symbols:
            symbol_data = data[data['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values('Date').reset_index(drop=True)
            
            # Get the latest complete row for this symbol
            latest_row = symbol_data.dropna(subset=['target']).iloc[-1:].copy()
            
            if latest_row.empty:
                continue
            
            symbol_predictions = []
            
            for day in range(horizon):
                # Prepare features for this prediction
                X, _, feature_cols = self.prepare_features_and_targets(pd.concat([symbol_data, latest_row]))
                
                if X.empty:
                    continue
                
                latest_features = X.iloc[-1:].copy()
                
                pred_row = {
                    'unique_id': symbol,
                    'ds': latest_row['Date'].iloc[0] + timedelta(days=day + 1)
                }
                
                # Make predictions with each model
                for model_name, model in self.fitted_models.items():
                    try:
                        pred = model.predict(latest_features)[0]
                        pred_row[f'ML_{model_name}'] = pred
                    except Exception as e:
                        logger.warning(f"Error predicting with {model_name}: {e}")
                        pred_row[f'ML_{model_name}'] = np.nan
                
                symbol_predictions.append(pred_row)
                
                # Update latest_row for next iteration (recursive prediction)
                latest_row = latest_row.copy()
                latest_row['Close'] = pred_row.get('ML_lightgbm', latest_row['Close'].iloc[0])
                latest_row['Date'] = pred_row['ds']
            
            predictions.extend(symbol_predictions)
        
        if predictions:
            predictions_df = pd.DataFrame(predictions)
            logger.info(f"Generated ML predictions: {len(predictions_df)} rows")
            return predictions_df
        
        return pd.DataFrame()
    
    def get_feature_importance_summary(self) -> pd.DataFrame:
        """Get feature importance summary across all models."""
        if not self.feature_importance:
            return pd.DataFrame()
        
        # Combine feature importance from all models
        all_importance = []
        
        for model_name, importance_df in self.feature_importance.items():
            importance_df = importance_df.copy()
            importance_df['model'] = model_name
            all_importance.append(importance_df)
        
        combined = pd.concat(all_importance, ignore_index=True)
        
        # Calculate average importance across models
        avg_importance = combined.groupby('feature')['importance'].agg(['mean', 'std', 'count']).reset_index()
        avg_importance = avg_importance.sort_values('mean', ascending=False)
        
        return avg_importance
    
    def save_ml_models(self, filepath: str) -> bool:
        """Save trained ML models."""
        try:
            model_data = {
                'fitted_models': self.fitted_models,
                'scalers': self.scalers,
                'label_encoders': self.label_encoders,
                'feature_importance': self.feature_importance,
                'model_performance': self.model_performance,
                'models_config': self.models_config
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"ML models saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving ML models: {e}")
            return False
    
    def load_ml_models(self, filepath: str) -> bool:
        """Load trained ML models."""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.fitted_models = model_data['fitted_models']
            self.scalers = model_data['scalers']
            self.label_encoders = model_data['label_encoders']
            self.feature_importance = model_data['feature_importance']
            self.model_performance = model_data['model_performance']
            self.models_config = model_data['models_config']
            
            logger.info(f"ML models loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
            return False