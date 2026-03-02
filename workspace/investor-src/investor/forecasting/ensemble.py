"""
Ensemble forecasting methods for combining multiple models.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

logger = logging.getLogger(__name__)


class EnsembleForecaster:
    """
    Ensemble methods for combining multiple forecasting models.
    
    This class provides:
    - Simple averaging
    - Weighted averaging
    - Stacking (meta-learning)
    - Dynamic weighting
    - Performance-based weighting
    """
    
    def __init__(self, method: str = 'simple_average'):
        """
        Initialize ensemble forecaster.
        
        Args:
            method: Ensemble method ('simple_average', 'weighted_average', 'stacking')
        """
        self.method = method
        self.weights = {}
        self.meta_model = None
        self.model_names = []
        
    def simple_average(self, predictions: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Simple average ensemble.
        
        Args:
            predictions: Dictionary of {model_name: predictions_df}
            
        Returns:
            Averaged predictions
        """
        logger.info("Creating simple average ensemble")
        
        if not predictions:
            logger.error("No predictions provided")
            return pd.DataFrame()
        
        try:
            # Get all prediction dataframes
            pred_dfs = list(predictions.values())
            
            # Find common columns (prediction columns)
            common_cols = set(pred_dfs[0].columns)
            for df in pred_dfs[1:]:
                common_cols = common_cols.intersection(set(df.columns))
            
            # Remove identifier columns
            id_cols = {'unique_id', 'ds'}
            pred_cols = [col for col in common_cols if col not in id_cols]
            
            # Start with first dataframe structure
            result = pred_dfs[0][['unique_id', 'ds']].copy()
            
            # Average predictions
            for col in pred_cols:
                if col in pred_dfs[0].columns:
                    col_values = []
                    for df in pred_dfs:
                        if col in df.columns:
                            col_values.append(df[col].values)
                    
                    if col_values:
                        result[col] = np.mean(col_values, axis=0)
            
            logger.info(f"Simple average ensemble created with {len(predictions)} models")
            return result
            
        except Exception as e:
            logger.error(f"Error creating simple average ensemble: {e}")
            return pd.DataFrame()
    
    def weighted_average(self, predictions: Dict[str, pd.DataFrame], weights: Dict[str, float]) -> pd.DataFrame:
        """
        Weighted average ensemble.
        
        Args:
            predictions: Dictionary of {model_name: predictions_df}
            weights: Dictionary of {model_name: weight}
            
        Returns:
            Weighted averaged predictions
        """
        logger.info("Creating weighted average ensemble")
        
        if not predictions or not weights:
            logger.error("No predictions or weights provided")
            return pd.DataFrame()
        
        try:
            # Normalize weights to sum to 1
            total_weight = sum(weights.values())
            normalized_weights = {k: v / total_weight for k, v in weights.items()}
            
            # Get all prediction dataframes
            pred_dfs = list(predictions.values())
            model_names = list(predictions.keys())
            
            # Find common columns
            common_cols = set(pred_dfs[0].columns)
            for df in pred_dfs[1:]:
                common_cols = common_cols.intersection(set(df.columns))
            
            # Remove identifier columns
            id_cols = {'unique_id', 'ds'}
            pred_cols = [col for col in common_cols if col not in id_cols]
            
            # Start with first dataframe structure
            result = pred_dfs[0][['unique_id', 'ds']].copy()
            
            # Weighted average predictions
            for col in pred_cols:
                if col in pred_dfs[0].columns:
                    weighted_sum = np.zeros(len(pred_dfs[0]))
                    
                    for i, (model_name, df) in enumerate(predictions.items()):
                        if col in df.columns and model_name in normalized_weights:
                            weight = normalized_weights[model_name]
                            weighted_sum += weight * df[col].values
                    
                    result[col] = weighted_sum
            
            logger.info(f"Weighted average ensemble created with weights: {normalized_weights}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating weighted average ensemble: {e}")
            return pd.DataFrame()
    
    def performance_weighted_average(self, 
                                   predictions: Dict[str, pd.DataFrame], 
                                   performance_scores: Dict[str, float]) -> pd.DataFrame:
        """
        Performance-based weighted average ensemble.
        
        Args:
            predictions: Dictionary of {model_name: predictions_df}
            performance_scores: Dictionary of {model_name: performance_score}
            
        Returns:
            Performance-weighted averaged predictions
        """
        logger.info("Creating performance-weighted average ensemble")
        
        try:
            # Convert performance scores to weights (inverse of error)
            # Lower error = higher weight
            weights = {}
            for model_name, score in performance_scores.items():
                if model_name in predictions:
                    # Use inverse of score as weight (assuming score is an error metric)
                    weights[model_name] = 1.0 / (score + 1e-8)  # Add small epsilon to avoid division by zero
            
            return self.weighted_average(predictions, weights)
            
        except Exception as e:
            logger.error(f"Error creating performance-weighted ensemble: {e}")
            return pd.DataFrame()
    
    def stacking_ensemble(self, 
                         base_predictions: Dict[str, pd.DataFrame], 
                         actuals: pd.DataFrame,
                         meta_model: Optional[Any] = None) -> pd.DataFrame:
        """
        Stacking ensemble using meta-learning.
        
        Args:
            base_predictions: Dictionary of {model_name: predictions_df}
            actuals: Actual values for training meta-model
            meta_model: Meta-model to use (default: LinearRegression)
            
        Returns:
            Stacked predictions
        """
        logger.info("Creating stacking ensemble")
        
        if not base_predictions:
            logger.error("No base predictions provided")
            return pd.DataFrame()
        
        try:
            if meta_model is None:
                meta_model = LinearRegression()
            
            # Prepare training data for meta-model
            X_meta = []
            y_meta = []
            
            # Get prediction columns
            pred_dfs = list(base_predictions.values())
            model_names = list(base_predictions.keys())
            
            # Find common prediction columns
            common_cols = set(pred_dfs[0].columns)
            for df in pred_dfs[1:]:
                common_cols = common_cols.intersection(set(df.columns))
            
            id_cols = {'unique_id', 'ds'}
            pred_cols = [col for col in common_cols if col not in id_cols]
            
            # For each prediction point, create features from all models
            for i in range(len(pred_dfs[0])):
                row_features = []
                
                for model_name, df in base_predictions.items():
                    for col in pred_cols:
                        if col in df.columns:
                            row_features.append(df[col].iloc[i])
                
                if row_features:
                    X_meta.append(row_features)
                    
                    # Get corresponding actual value
                    if i < len(actuals):
                        y_meta.append(actuals['y'].iloc[i])
            
            # Train meta-model
            if X_meta and y_meta:
                X_meta = np.array(X_meta)
                y_meta = np.array(y_meta)
                
                meta_model.fit(X_meta, y_meta)
                self.meta_model = meta_model
                
                # Make predictions with meta-model
                meta_predictions = meta_model.predict(X_meta)
                
                # Create result dataframe
                result = pred_dfs[0][['unique_id', 'ds']].copy()
                result['stacked_prediction'] = meta_predictions
                
                logger.info(f"Stacking ensemble created with {len(base_predictions)} base models")
                return result
            
            else:
                logger.error("No valid training data for meta-model")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error creating stacking ensemble: {e}")
            return pd.DataFrame()
    
    def dynamic_weighting(self, 
                         predictions: Dict[str, pd.DataFrame], 
                         recent_performance: Dict[str, List[float]],
                         window_size: int = 10) -> pd.DataFrame:
        """
        Dynamic weighting based on recent performance.
        
        Args:
            predictions: Dictionary of {model_name: predictions_df}
            recent_performance: Dictionary of {model_name: [recent_errors]}
            window_size: Size of window for calculating recent performance
            
        Returns:
            Dynamically weighted predictions
        """
        logger.info("Creating dynamic weighted ensemble")
        
        try:
            # Calculate recent average performance for each model
            recent_avg_performance = {}
            
            for model_name, errors in recent_performance.items():
                if model_name in predictions:
                    # Take last window_size errors
                    recent_errors = errors[-window_size:] if len(errors) >= window_size else errors
                    if recent_errors:
                        recent_avg_performance[model_name] = np.mean(recent_errors)
            
            # Use performance-based weighting
            return self.performance_weighted_average(predictions, recent_avg_performance)
            
        except Exception as e:
            logger.error(f"Error creating dynamic weighted ensemble: {e}")
            return pd.DataFrame()
    
    def create_ensemble(self, 
                       predictions: Dict[str, pd.DataFrame], 
                       method: Optional[str] = None,
                       **kwargs) -> pd.DataFrame:
        """
        Create ensemble using specified method.
        
        Args:
            predictions: Dictionary of {model_name: predictions_df}
            method: Ensemble method to use (overrides instance method)
            **kwargs: Additional arguments for specific methods
            
        Returns:
            Ensemble predictions
        """
        method = method or self.method
        
        if method == 'simple_average':
            return self.simple_average(predictions)
        
        elif method == 'weighted_average':
            weights = kwargs.get('weights', {})
            return self.weighted_average(predictions, weights)
        
        elif method == 'performance_weighted':
            performance_scores = kwargs.get('performance_scores', {})
            return self.performance_weighted_average(predictions, performance_scores)
        
        elif method == 'stacking':
            actuals = kwargs.get('actuals', pd.DataFrame())
            meta_model = kwargs.get('meta_model', None)
            return self.stacking_ensemble(predictions, actuals, meta_model)
        
        elif method == 'dynamic_weighting':
            recent_performance = kwargs.get('recent_performance', {})
            window_size = kwargs.get('window_size', 10)
            return self.dynamic_weighting(predictions, recent_performance, window_size)
        
        else:
            logger.error(f"Unknown ensemble method: {method}")
            return pd.DataFrame()
    
    def evaluate_ensemble(self, 
                         ensemble_predictions: pd.DataFrame, 
                         actuals: pd.DataFrame) -> Dict[str, float]:
        """
        Evaluate ensemble performance.
        
        Args:
            ensemble_predictions: Ensemble predictions
            actuals: Actual values
            
        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("Evaluating ensemble performance")
        
        try:
            # Find prediction column
            pred_cols = [col for col in ensemble_predictions.columns 
                        if col not in ['unique_id', 'ds']]
            
            if not pred_cols:
                logger.error("No prediction columns found")
                return {}
            
            # Use first prediction column
            pred_col = pred_cols[0]
            
            # Calculate metrics
            y_true = actuals['y'].values
            y_pred = ensemble_predictions[pred_col].values
            
            # Ensure same length
            min_len = min(len(y_true), len(y_pred))
            y_true = y_true[:min_len]
            y_pred = y_pred[:min_len]
            
            metrics = {
                'mae': mean_absolute_error(y_true, y_pred),
                'mse': mean_squared_error(y_true, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
                'mape': np.mean(np.abs((y_true - y_pred) / y_true)) * 100,
            }
            
            logger.info(f"Ensemble evaluation completed: MAE={metrics['mae']:.4f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating ensemble: {e}")
            return {}
    
    def generate_ensemble_forecast(self, processed_data: pd.DataFrame, horizon: int = 21) -> pd.DataFrame:
        """
        Generate ensemble forecasts from processed data.
        
        Args:
            processed_data: Processed time series data
            horizon: Forecast horizon in days
            
        Returns:
            Ensemble forecast dataframe
        """
        try:
            logger.info(f"Generating ensemble forecast with horizon {horizon}")
            
            # For now, return a simple forecast based on trend analysis
            # This is a placeholder implementation until full forecasting models are integrated
            if processed_data.empty:
                return pd.DataFrame()
            
            # Get the last value and calculate simple trend
            # Try different possible column names for price data
            price_col = None
            for col_name in ['Close', 'close', 'y', 'target']:
                if col_name in processed_data.columns:
                    price_col = col_name
                    break
            
            if price_col is None:
                logger.error(f"No price column found in data. Available columns: {list(processed_data.columns)}")
                return pd.DataFrame()
            
            # Use 'ds' column for date if available, otherwise use index
            if 'ds' in processed_data.columns:
                last_date = processed_data['ds'].iloc[-1]
            else:
                last_date = processed_data.index[-1]
            
            last_value = processed_data[price_col].iloc[-1]
            
            # Calculate simple moving average trend
            if len(processed_data) >= 20:
                recent_trend = processed_data[price_col].tail(20).pct_change().mean()
            else:
                recent_trend = 0.0
            
            # Generate forecast dates
            forecast_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=horizon,
                freq='D'
            )
            
            # Generate simple forecasts
            forecasts = []
            current_value = last_value
            
            for i, date in enumerate(forecast_dates):
                # Apply trend with some dampening
                damping_factor = 0.95 ** i  # Trend dampens over time
                forecast_value = current_value * (1 + recent_trend * damping_factor)
                
                forecasts.append({
                    'unique_id': 'forecast',
                    'ds': date,
                    'forecast': forecast_value,
                    'lower': forecast_value * 0.95,  # Simple confidence interval
                    'upper': forecast_value * 1.05
                })
                
                current_value = forecast_value
            
            result_df = pd.DataFrame(forecasts)
            logger.info(f"Generated {len(result_df)} forecast points")
            return result_df
            
        except Exception as e:
            logger.error(f"Error generating ensemble forecast: {e}")
            return pd.DataFrame()

    def get_ensemble_summary(self) -> Dict[str, Any]:
        """
        Get summary of ensemble configuration.
        
        Returns:
            Dictionary with ensemble summary
        """
        summary = {
            'method': self.method,
            'weights': self.weights,
            'meta_model': str(type(self.meta_model).__name__) if self.meta_model else None,
            'model_names': self.model_names
        }
        
        return summary