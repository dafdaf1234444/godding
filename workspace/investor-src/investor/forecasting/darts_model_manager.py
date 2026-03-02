"""
Darts Model Manager for advanced time series forecasting.

This module provides a comprehensive interface for using Darts library models
with the investor forecasting system, including modern deep learning models
and classical statistical models.
"""
import pandas as pd
from typing import Dict, List, Optional, Any, Union
import logging
import pickle
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class DartsModelManager:
    """
    Advanced time series forecasting using Darts library.
    
    Supports:
    - Classical statistical models (ARIMA, ETS, etc.)
    - Modern deep learning models (TiDE, TSMixer, DLinear, NLinear)
    - Multivariate forecasting
    - Probabilistic predictions with confidence intervals
    - Global models trained on multiple time series
    - Covariate support (past and future)
    """
    
    def __init__(self, models_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Darts model manager.
        
        Args:
            models_config: Configuration for Darts models
        """
        self.models_config = models_config or self._get_default_config()
        self.fitted_models = {}
        self.model_performance = {}
        self.time_series_data = {}
        self.scalers = {}
        
        # Check Darts availability
        self.darts_available = self._check_darts_availability()
        if not self.darts_available:
            logger.warning("Darts library not available. Install with: uv add darts")
            return
            
        # Import Darts components
        self._import_darts_components()
        
    def _check_darts_availability(self) -> bool:
        """Check if Darts library is available."""
        try:
            import darts
            return True
        except ImportError:
            return False
    
    def _import_darts_components(self):
        """Import Darts components with error handling."""
        try:
            from darts import TimeSeries
            from darts.models import (
                ARIMA, ExponentialSmoothing, Theta, FourTheta,
                LinearRegressionModel, RandomForest, LightGBMModel,
                XGBModel, CatBoostModel
            )
            
            # Store commonly used classes
            self.TimeSeries = TimeSeries
            self.ARIMA = ARIMA
            self.ExponentialSmoothing = ExponentialSmoothing
            self.Theta = Theta
            self.FourTheta = FourTheta
            self.LinearRegressionModel = LinearRegressionModel
            self.RandomForest = RandomForest
            self.LightGBMModel = LightGBMModel
            self.XGBModel = XGBModel
            self.CatBoostModel = CatBoostModel
            
            # Try to import deep learning models
            try:
                from darts.models import (
                    TiDEModel, TSMixerModel, DLinearModel, NLinearModel,
                    NBEATSModel, NHiTSModel, TransformerModel, RNNModel
                )
                self.TiDEModel = TiDEModel
                self.TSMixerModel = TSMixerModel
                self.DLinearModel = DLinearModel
                self.NLinearModel = NLinearModel
                self.NBEATSModel = NBEATSModel
                self.NHiTSModel = NHiTSModel
                self.TransformerModel = TransformerModel
                self.RNNModel = RNNModel
                self.deep_learning_available = True
                logger.info("Deep learning models available")
            except ImportError as e:
                logger.warning(f"Some deep learning models not available: {e}")
                self.deep_learning_available = False
                
        except ImportError as e:
            logger.error(f"Error importing Darts components: {e}")
            self.darts_available = False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Darts models."""
        return {
            'statistical_models': {
                'arima': {'p': 1, 'q': 1, 'd': 1},
                'exponential_smoothing': {'trend': 'add', 'seasonal': 'add'},
                'theta': {'theta': 2},
                'four_theta': {'theta': 2}
            },
            'ml_models': {
                'linear_regression': {'lags': 14},
                'random_forest': {'lags': 14, 'n_estimators': 100},
                'lightgbm': {'lags': 14, 'n_estimators': 100},
                'xgboost': {'lags': 14, 'n_estimators': 100}
            },
            'deep_learning_models': {
                'tide': {
                    'input_chunk_length': 24,
                    'output_chunk_length': 1,
                    'num_encoder_layers': 1,
                    'num_decoder_layers': 1,
                    'decoder_output_dim': 4,
                    'hidden_size': 128,
                    'temporal_width_past': 4,
                    'temporal_width_future': 4,
                    'n_epochs': 50,
                    'batch_size': 32
                },
                'tsmixer': {
                    'input_chunk_length': 24,
                    'output_chunk_length': 1,
                    'hidden_size': 64,
                    'n_blocks': 2,
                    'n_epochs': 50,
                    'batch_size': 32
                },
                'dlinear': {
                    'input_chunk_length': 24,
                    'output_chunk_length': 1,
                    'n_epochs': 50,
                    'batch_size': 32
                },
                'nlinear': {
                    'input_chunk_length': 24,
                    'output_chunk_length': 1,
                    'n_epochs': 50,
                    'batch_size': 32
                }
            },
            'forecasting': {
                'train_test_split': 0.8,
                'validation_split': 0.2,
                'prediction_horizon': 21,
                'confidence_levels': [0.05, 0.95],  # 90% confidence interval
                'use_covariates': True,
                'multivariate_enabled': True
            }
        }
    
    def pandas_to_darts_timeseries(self, df: pd.DataFrame, 
                                   value_cols: Union[str, List[str]] = 'Close',
                                   time_col: str = 'Date',
                                   fill_missing_dates: bool = True) -> 'TimeSeries':
        """
        Convert pandas DataFrame to Darts TimeSeries.
        
        Args:
            df: Input DataFrame
            value_cols: Column(s) to use as values
            time_col: Column to use as time index
            fill_missing_dates: Whether to fill missing dates
            
        Returns:
            Darts TimeSeries object
        """
        if not self.darts_available:
            raise ImportError("Darts library not available")
            
        df_clean = df.copy()
        
        # Ensure time column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df_clean[time_col]):
            df_clean[time_col] = pd.to_datetime(df_clean[time_col])
        
        # Set time column as index
        df_clean = df_clean.set_index(time_col)
        
        # Handle single or multiple value columns
        if isinstance(value_cols, str):
            value_cols = [value_cols]
        
        # Select only the value columns
        df_values = df_clean[value_cols]
        
        # Fill missing dates if requested
        if fill_missing_dates:
            df_values = df_values.resample('D').interpolate(method='linear')
        
        # Remove any remaining NaN values
        df_values = df_values.dropna()
        
        # Create TimeSeries
        ts = self.TimeSeries.from_dataframe(df_values)
        
        logger.info(f"Created TimeSeries with {len(ts)} points and {ts.n_components} components")
        return ts
    
    def darts_to_pandas(self, ts: 'TimeSeries', 
                       symbol: str = 'UNKNOWN') -> pd.DataFrame:
        """
        Convert Darts TimeSeries back to pandas DataFrame.
        
        Args:
            ts: Darts TimeSeries object
            symbol: Symbol identifier for the data
            
        Returns:
            Pandas DataFrame in investor format
        """
        df = ts.to_dataframe()
        df.reset_index(inplace=True)
        
        # Rename columns to match investor format
        if df.shape[1] == 2:  # Single component
            df.columns = ['ds', 'y']
        else:  # Multiple components
            df.columns = ['ds'] + [f'component_{i}' for i in range(df.shape[1] - 1)]
        
        # Add symbol identifier
        df['unique_id'] = symbol
        
        # Reorder columns
        df = df[['unique_id', 'ds'] + [col for col in df.columns if col not in ['unique_id', 'ds']]]
        
        return df
    
    def initialize_models(self, model_types: List[str] = None) -> Dict[str, Any]:
        """
        Initialize Darts models.
        
        Args:
            model_types: List of model types to initialize
            
        Returns:
            Dictionary of initialized models
        """
        if not self.darts_available:
            return {}
        
        if model_types is None:
            model_types = ['arima', 'exponential_smoothing', 'theta', 'linear_regression', 'random_forest']
            if self.deep_learning_available:
                model_types.extend(['dlinear', 'nlinear'])
        
        models = {}
        
        # Statistical models
        if 'arima' in model_types:
            models['arima'] = self.ARIMA(**self.models_config['statistical_models']['arima'])
        
        if 'exponential_smoothing' in model_types:
            models['exponential_smoothing'] = self.ExponentialSmoothing(
                **self.models_config['statistical_models']['exponential_smoothing']
            )
        
        if 'theta' in model_types:
            models['theta'] = self.Theta(**self.models_config['statistical_models']['theta'])
        
        if 'four_theta' in model_types:
            models['four_theta'] = self.FourTheta(**self.models_config['statistical_models']['four_theta'])
        
        # ML models
        if 'linear_regression' in model_types:
            models['linear_regression'] = self.LinearRegressionModel(
                **self.models_config['ml_models']['linear_regression']
            )
        
        if 'random_forest' in model_types:
            models['random_forest'] = self.RandomForest(
                **self.models_config['ml_models']['random_forest']
            )
        
        # Try to initialize LightGBM if available
        if 'lightgbm' in model_types:
            try:
                models['lightgbm'] = self.LightGBMModel(
                    **self.models_config['ml_models']['lightgbm']
                )
            except Exception as e:
                logger.warning(f"Could not initialize LightGBM model: {e}")
        
        # Try to initialize XGBoost if available
        if 'xgboost' in model_types:
            try:
                models['xgboost'] = self.XGBModel(
                    **self.models_config['ml_models']['xgboost']
                )
            except Exception as e:
                logger.warning(f"Could not initialize XGBoost model: {e}")
        
        # Deep learning models
        if self.deep_learning_available:
            if 'tide' in model_types:
                try:
                    models['tide'] = self.TiDEModel(
                        **self.models_config['deep_learning_models']['tide']
                    )
                except Exception as e:
                    logger.warning(f"Could not initialize TiDE model: {e}")
            
            if 'tsmixer' in model_types:
                try:
                    models['tsmixer'] = self.TSMixerModel(
                        **self.models_config['deep_learning_models']['tsmixer']
                    )
                except Exception as e:
                    logger.warning(f"Could not initialize TSMixer model: {e}")
            
            if 'dlinear' in model_types:
                try:
                    models['dlinear'] = self.DLinearModel(
                        **self.models_config['deep_learning_models']['dlinear']
                    )
                except Exception as e:
                    logger.warning(f"Could not initialize DLinear model: {e}")
            
            if 'nlinear' in model_types:
                try:
                    models['nlinear'] = self.NLinearModel(
                        **self.models_config['deep_learning_models']['nlinear']
                    )
                except Exception as e:
                    logger.warning(f"Could not initialize NLinear model: {e}")
        
        logger.info(f"Initialized {len(models)} Darts models: {list(models.keys())}")
        return models
    
    def train_models(self, stocks_data: Dict[str, pd.DataFrame], 
                    model_types: List[str] = None,
                    value_cols: Union[str, List[str]] = 'Close') -> Dict[str, Any]:
        """
        Train Darts models on stock data.
        
        Args:
            stocks_data: Dictionary of {symbol: dataframe}
            model_types: List of model types to train
            value_cols: Column(s) to use for forecasting
            
        Returns:
            Dictionary of trained models
        """
        if not self.darts_available:
            logger.error("Darts library not available")
            return {}
        
        logger.info("Training Darts models")
        
        # Convert data to TimeSeries format
        time_series_dict = {}
        for symbol, df in stocks_data.items():
            try:
                ts = self.pandas_to_darts_timeseries(df, value_cols=value_cols)
                if len(ts) > 30:  # Minimum data requirement
                    time_series_dict[symbol] = ts
                else:
                    logger.warning(f"Insufficient data for {symbol}: {len(ts)} points")
            except Exception as e:
                logger.error(f"Error converting {symbol} to TimeSeries: {e}")
        
        if not time_series_dict:
            logger.error("No valid time series data for training")
            return {}
        
        self.time_series_data = time_series_dict
        
        # Initialize models
        models = self.initialize_models(model_types)
        if not models:
            return {}
        
        trained_models = {}
        
        # Train each model
        for model_name, model in models.items():
            logger.info(f"Training {model_name}")
            
            try:
                # Check if model supports global training (multiple series)
                model_supports_global = hasattr(model, 'supports_multivariate') and \
                                      hasattr(model, 'supports_past_covariates')
                
                if model_supports_global and len(time_series_dict) > 1:
                    # Train on all series (global model)
                    series_list = list(time_series_dict.values())
                    
                    # Split data for training
                    train_series = []
                    for ts in series_list:
                        split_point = int(len(ts) * self.models_config['forecasting']['train_test_split'])
                        train_ts = ts[:split_point]
                        if len(train_ts) > 10:  # Minimum training data
                            train_series.append(train_ts)
                    
                    if train_series:
                        model.fit(train_series)
                        trained_models[model_name] = model
                        logger.info(f"Trained global {model_name} on {len(train_series)} series")
                
                else:
                    # Train separate model for each series
                    model_instances = {}
                    
                    for symbol, ts in time_series_dict.items():
                        # Split data
                        split_point = int(len(ts) * self.models_config['forecasting']['train_test_split'])
                        train_ts = ts[:split_point]
                        
                        if len(train_ts) > 10:
                            # Create separate model instance for this symbol
                            symbol_model = self.initialize_models([model_name])[model_name]
                            symbol_model.fit(train_ts)
                            model_instances[symbol] = symbol_model
                    
                    if model_instances:
                        trained_models[model_name] = model_instances
                        logger.info(f"Trained {model_name} on {len(model_instances)} symbols")
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
        
        self.fitted_models = trained_models
        logger.info(f"Successfully trained {len(trained_models)} model types")
        
        return trained_models
    
    def predict(self, horizon: int = 21, 
               symbols: List[str] = None,
               include_confidence: bool = True) -> pd.DataFrame:
        """
        Generate predictions using trained Darts models.
        
        Args:
            horizon: Number of periods to forecast
            symbols: List of symbols to predict (None for all)
            include_confidence: Whether to include confidence intervals
            
        Returns:
            DataFrame with predictions
        """
        if not self.fitted_models:
            logger.error("No models trained. Call train_models() first.")
            return pd.DataFrame()
        
        logger.info(f"Generating Darts predictions for {horizon} periods")
        
        predictions = []
        symbols_to_predict = symbols or list(self.time_series_data.keys())
        
        for symbol in symbols_to_predict:
            if symbol not in self.time_series_data:
                continue
            
            ts = self.time_series_data[symbol]
            
            for model_name, model in self.fitted_models.items():
                try:
                    # Handle global vs individual models
                    if isinstance(model, dict):
                        # Individual models per symbol
                        if symbol not in model:
                            continue
                        symbol_model = model[symbol]
                    else:
                        # Global model
                        symbol_model = model
                    
                    # Generate prediction
                    if include_confidence:
                        # Try probabilistic prediction
                        try:
                            pred_ts = symbol_model.predict(
                                n=horizon,
                                series=ts,
                                num_samples=100  # For confidence intervals
                            )
                        except:
                            # Fallback to deterministic prediction
                            pred_ts = symbol_model.predict(n=horizon, series=ts)
                    else:
                        pred_ts = symbol_model.predict(n=horizon, series=ts)
                    
                    # Convert to DataFrame
                    pred_df = self.darts_to_pandas(pred_ts, symbol)
                    
                    # Rename prediction column
                    value_col = [col for col in pred_df.columns if col not in ['unique_id', 'ds']][0]
                    pred_df = pred_df.rename(columns={value_col: f'Darts_{model_name}'})
                    
                    # Add confidence intervals if available
                    if include_confidence and hasattr(pred_ts, 'quantile'):
                        try:
                            lower_bound = pred_ts.quantile(0.05)
                            upper_bound = pred_ts.quantile(0.95)
                            
                            lower_df = self.darts_to_pandas(lower_bound, symbol)
                            upper_df = self.darts_to_pandas(upper_bound, symbol)
                            
                            lower_col = [col for col in lower_df.columns if col not in ['unique_id', 'ds']][0]
                            upper_col = [col for col in upper_df.columns if col not in ['unique_id', 'ds']][0]
                            
                            pred_df[f'Darts_{model_name}-lo-90'] = lower_df[lower_col]
                            pred_df[f'Darts_{model_name}-hi-90'] = upper_df[upper_col]
                        except Exception as e:
                            logger.warning(f"Could not generate confidence intervals for {model_name}: {e}")
                    
                    predictions.append(pred_df)
                    
                except Exception as e:
                    logger.error(f"Error predicting with {model_name} for {symbol}: {e}")
        
        if predictions:
            # Combine all predictions
            combined_df = predictions[0]
            for pred_df in predictions[1:]:
                combined_df = combined_df.merge(
                    pred_df, on=['unique_id', 'ds'], how='outer'
                )
            
            logger.info(f"Generated {len(combined_df)} prediction rows")
            return combined_df
        
        return pd.DataFrame()
    
    def evaluate_models(self, metric: str = 'mae') -> pd.DataFrame:
        """
        Evaluate trained models using backtesting.
        
        Args:
            metric: Evaluation metric ('mae', 'mse', 'mape')
            
        Returns:
            DataFrame with evaluation results
        """
        if not self.fitted_models or not self.time_series_data:
            logger.error("No models or data available for evaluation")
            return pd.DataFrame()
        
        logger.info("Evaluating Darts models")
        
        from darts.metrics import mae, mse, mape
        
        metric_func = {
            'mae': mae,
            'mse': mse,
            'mape': mape
        }.get(metric, mae)
        
        evaluation_results = []
        
        for symbol, ts in self.time_series_data.items():
            # Split data
            split_point = int(len(ts) * self.models_config['forecasting']['train_test_split'])
            train_ts = ts[:split_point]
            test_ts = ts[split_point:]
            
            if len(test_ts) < 5:  # Need minimum test data
                continue
            
            for model_name, model in self.fitted_models.items():
                try:
                    # Get model for this symbol
                    if isinstance(model, dict):
                        if symbol not in model:
                            continue
                        symbol_model = model[symbol]
                    else:
                        symbol_model = model
                    
                    # Predict test period
                    pred_ts = symbol_model.predict(n=len(test_ts), series=train_ts)
                    
                    # Calculate metric
                    score = metric_func(test_ts, pred_ts)
                    
                    evaluation_results.append({
                        'symbol': symbol,
                        'model': f'Darts_{model_name}',
                        'metric': metric,
                        'score': score,
                        'test_length': len(test_ts)
                    })
                    
                except Exception as e:
                    logger.warning(f"Error evaluating {model_name} for {symbol}: {e}")
        
        if evaluation_results:
            eval_df = pd.DataFrame(evaluation_results)
            logger.info(f"Evaluated {len(eval_df)} model-symbol combinations")
            return eval_df
        
        return pd.DataFrame()
    
    def save_models(self, filepath: str) -> bool:
        """Save trained Darts models."""
        try:
            model_data = {
                'fitted_models': self.fitted_models,
                'time_series_data': self.time_series_data,
                'model_performance': self.model_performance,
                'models_config': self.models_config
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Darts models saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving Darts models: {e}")
            return False
    
    def load_models(self, filepath: str) -> bool:
        """Load trained Darts models."""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.fitted_models = model_data['fitted_models']
            self.time_series_data = model_data['time_series_data']
            self.model_performance = model_data['model_performance']
            self.models_config = model_data['models_config']
            
            logger.info(f"Darts models loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading Darts models: {e}")
            return False
    
    def get_model_summary(self) -> Dict[str, Any]:
        """Get summary of trained models."""
        summary = {
            'total_models': len(self.fitted_models),
            'model_types': list(self.fitted_models.keys()),
            'total_symbols': len(self.time_series_data),
            'symbols': list(self.time_series_data.keys()),
            'darts_available': self.darts_available,
            'deep_learning_available': getattr(self, 'deep_learning_available', False)
        }
        
        return summary