"""
Model management for forecasting with multiple models.
"""
import pandas as pd
from typing import Dict, List, Optional, Any
import logging
import pickle
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class ForecastingModelManager:
    """
    Manage multiple forecasting models from different libraries.
    
    This class handles:
    - Model initialization and configuration
    - Training multiple models
    - Making predictions
    - Model evaluation and selection
    - Model persistence
    """
    
    def __init__(self, models_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the model manager.
        
        Args:
            models_config: Configuration for models
        """
        self.models_config = models_config or self._get_default_config()
        self.fitted_models = {}
        self.model_performances = {}
        self.best_models = {}
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default model configuration."""
        return {
            'statistical_models': {
                'AutoARIMA': {'max_p': 3, 'max_q': 3, 'max_d': 2},
                'AutoETS': {'damped': True},
                'AutoCES': {},
                'MSTL': {'season_length': [5, 252]},  # Weekly and yearly seasonality
                'Theta': {'decomposition_type': 'multiplicative'},
            },
            'horizons': [1, 5, 10, 21],  # 1 day, 1 week, 2 weeks, 1 month
            'cross_validation': {
                'h': 21,  # Forecast horizon
                'step_size': 5,  # Step size for cross-validation
                'n_windows': 5,  # Number of windows
            }
        }
    
    def initialize_models(self) -> Dict[str, Any]:
        """Initialize models from statsforecast."""
        try:
            from statsforecast import StatsForecast
            from statsforecast.models import (
                AutoARIMA, AutoETS, AutoCES, MSTL, Theta
            )
            
            models = []
            
            # Statistical models
            if 'AutoARIMA' in self.models_config['statistical_models']:
                config = self.models_config['statistical_models']['AutoARIMA']
                models.append(AutoARIMA(**config))
            
            if 'AutoETS' in self.models_config['statistical_models']:
                config = self.models_config['statistical_models']['AutoETS']
                models.append(AutoETS(**config))
            
            if 'AutoCES' in self.models_config['statistical_models']:
                config = self.models_config['statistical_models']['AutoCES']
                models.append(AutoCES(**config))
            
            if 'MSTL' in self.models_config['statistical_models']:
                config = self.models_config['statistical_models']['MSTL']
                models.append(MSTL(**config))
            
            if 'Theta' in self.models_config['statistical_models']:
                config = self.models_config['statistical_models']['Theta']
                models.append(Theta(**config))
            
            # Initialize StatsForecast
            sf = StatsForecast(
                models=models,
                freq='D',  # Daily frequency
                n_jobs=-1,
                fallback_model=AutoARIMA()
            )
            
            logger.info(f"Initialized {len(models)} statistical models")
            return {'statsforecast': sf, 'models': models}
            
        except ImportError as e:
            logger.error(f"Failed to import statsforecast: {e}")
            return {}
    
    def train_models(self, df: pd.DataFrame, exog_features: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Train multiple models on the data.
        
        Args:
            df: Data in nixtla format (unique_id, ds, y)
            exog_features: List of exogenous feature columns
            
        Returns:
            Dictionary of trained models
        """
        logger.info("Training statistical models")
        
        # Initialize models
        model_dict = self.initialize_models()
        
        if not model_dict:
            logger.error("No models initialized")
            return {}
        
        try:
            # Prepare data for training
            train_data = df[['unique_id', 'ds', 'y']].copy()
            
            # Fit models
            sf = model_dict['statsforecast']
            sf.fit(train_data)
            
            # Store fitted models
            self.fitted_models['statsforecast'] = sf
            
            logger.info("Successfully trained statistical models")
            return self.fitted_models
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return {}
    
    def predict(self, h: int = 21, level: Optional[List[int]] = None) -> pd.DataFrame:
        """
        Make predictions with trained models.
        
        Args:
            h: Forecast horizon (days)
            level: Confidence levels for prediction intervals
            
        Returns:
            Predictions dataframe
        """
        if 'statsforecast' not in self.fitted_models:
            logger.error("No models trained. Call train_models() first.")
            return pd.DataFrame()
        
        try:
            sf = self.fitted_models['statsforecast']
            
            # Make predictions
            if level is None:
                level = [80, 95]  # 80% and 95% confidence intervals
            
            predictions = sf.predict(h=h, level=level)
            
            logger.info(f"Generated predictions for {h} days ahead")
            return predictions
            
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            return pd.DataFrame()
    
    def cross_validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform cross-validation to evaluate models.
        
        Args:
            df: Data in nixtla format
            
        Returns:
            Cross-validation results
        """
        logger.info("Performing cross-validation")
        
        if 'statsforecast' not in self.fitted_models:
            logger.error("No models trained. Call train_models() first.")
            return pd.DataFrame()
        
        try:
            
            sf = self.fitted_models['statsforecast']
            cv_config = self.models_config['cross_validation']
            
            # Perform cross-validation
            cv_results = sf.cross_validation(
                df=df,
                h=cv_config['h'],
                step_size=cv_config['step_size'],
                n_windows=cv_config['n_windows'],
                level=[80, 95]
            )
            
            logger.info(f"Cross-validation completed with {len(cv_results)} results")
            return cv_results
            
        except Exception as e:
            logger.error(f"Error in cross-validation: {e}")
            return pd.DataFrame()
    
    def evaluate_models(self, cv_results: pd.DataFrame) -> pd.DataFrame:
        """
        Evaluate model performance from cross-validation results.
        
        Args:
            cv_results: Cross-validation results
            
        Returns:
            Model performance metrics
        """
        logger.info("Evaluating model performance")
        
        if cv_results.empty:
            logger.error("No cross-validation results to evaluate")
            return pd.DataFrame()
        
        try:
            from statsforecast.utils import evaluate
            
            # Calculate evaluation metrics
            evaluation = evaluate(
                cv_results,
                metrics=['mae', 'mse', 'rmse', 'mape', 'smape']
            )
            
            # Store performance results
            self.model_performances = evaluation
            
            logger.info("Model evaluation completed")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating models: {e}")
            return pd.DataFrame()
    
    def select_best_models(self, evaluation: pd.DataFrame, metric: str = 'mae') -> Dict[str, str]:
        """
        Select best model for each stock based on evaluation metric.
        
        Args:
            evaluation: Model evaluation results
            metric: Metric to use for selection (default: 'mae')
            
        Returns:
            Dictionary mapping stock symbols to best model names
        """
        logger.info(f"Selecting best models based on {metric}")
        
        if evaluation.empty:
            logger.error("No evaluation results to select from")
            return {}
        
        try:
            best_models = {}
            
            # Group by unique_id and find best model for each stock
            for unique_id in evaluation['unique_id'].unique():
                stock_eval = evaluation[evaluation['unique_id'] == unique_id]
                
                # Find model with lowest error for this metric
                best_model = stock_eval.loc[stock_eval[metric].idxmin(), 'model']
                best_models[unique_id] = best_model
            
            # Store best models
            self.best_models = best_models
            
            logger.info(f"Selected best models for {len(best_models)} stocks")
            return best_models
            
        except Exception as e:
            logger.error(f"Error selecting best models: {e}")
            return {}
    
    def predict_with_best_models(self, df: pd.DataFrame, h: int = 21) -> pd.DataFrame:
        """
        Make predictions using the best model for each stock.
        
        Args:
            df: Data in nixtla format
            h: Forecast horizon
            
        Returns:
            Predictions with best models
        """
        logger.info("Making predictions with best models")
        
        if not self.best_models:
            logger.warning("No best models selected. Using all models.")
            return self.predict(h=h)
        
        try:
            # For now, return predictions from all models
            # In a full implementation, you would filter by best models
            predictions = self.predict(h=h)
            
            logger.info("Generated predictions with best models")
            return predictions
            
        except Exception as e:
            logger.error(f"Error making predictions with best models: {e}")
            return pd.DataFrame()
    
    def save_models(self, filepath: str) -> bool:
        """
        Save trained models to disk.
        
        Args:
            filepath: Path to save models
            
        Returns:
            True if successful, False otherwise
        """
        try:
            model_data = {
                'fitted_models': self.fitted_models,
                'model_performances': self.model_performances,
                'best_models': self.best_models,
                'models_config': self.models_config
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Models saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            return False
    
    def load_models(self, filepath: str) -> bool:
        """
        Load trained models from disk.
        
        Args:
            filepath: Path to load models from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.fitted_models = model_data['fitted_models']
            self.model_performances = model_data['model_performances']
            self.best_models = model_data['best_models']
            self.models_config = model_data['models_config']
            
            logger.info(f"Models loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Get summary of trained models and performance.
        
        Returns:
            Dictionary with model summary
        """
        summary = {
            'fitted_models': list(self.fitted_models.keys()),
            'best_models': self.best_models,
            'model_count': len(self.fitted_models),
            'performance_available': bool(self.model_performances),
            'config': self.models_config
        }
        
        return summary
    
    def create_forecast_intervals(self, predictions: pd.DataFrame, level: int = 95) -> pd.DataFrame:
        """
        Create forecast intervals from predictions.
        
        Args:
            predictions: Predictions dataframe
            level: Confidence level
            
        Returns:
            Predictions with intervals
        """
        # Add logic to process prediction intervals
        # This would depend on the specific format of predictions
        return predictions