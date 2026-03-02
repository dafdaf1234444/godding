"""
Analysis management component for the investor analysis system.
Handles forecasting, anomaly detection, and investment signal generation.
"""
import pandas as pd
from typing import Dict, List, Any
import logging

from .config import InvestorConfig
from .exceptions import AnalysisError, ForecastingError, AnomalyDetectionError
from .error_handling import ErrorHandler
from ..forecasting.data_processor import ForecastingDataProcessor
from ..forecasting.model_manager import ForecastingModelManager
from ..forecasting.ensemble import EnsembleForecaster
from ..forecasting.investment_anomaly_detector import InvestmentAnomalyDetector
from ..data.events import EventDataManager
from ..analysis.holiday_effects import HolidayEffectsAnalyzer, MarketRegion
from ..analysis.options_analysis import OptionsAnalysisManager

logger = logging.getLogger(__name__)


class AnalysisManager:
    """Manages all analysis operations including forecasting and anomaly detection."""
    
    def __init__(self, config: InvestorConfig):
        """Initialize the analysis manager."""
        self.config = config
        
        # Initialize analysis components
        self.data_processor = None
        self.model_manager = None
        self.ensemble_manager = None
        self.anomaly_detector = None
        self.events_manager = EventDataManager()
        self.holiday_analyzer = HolidayEffectsAnalyzer(MarketRegion.US)
        self.options_analyzer = OptionsAnalysisManager(config)
        
        logger.info("AnalysisManager initialized")
    
    def run_anomaly_detection(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """
        Run comprehensive anomaly detection on the provided data.
        
        Args:
            data: Dictionary mapping symbols to their data
            
        Returns:
            List of investment signals/anomalies detected
            
        Raises:
            AnomalyDetectionError: If anomaly detection fails
        """
        if not self.config.analysis.enable_anomaly_detection:
            logger.info("Anomaly detection disabled in configuration")
            return []
        
        logger.info("Running comprehensive anomaly detection...")
        
        try:
            # Get relevant events for context
            symbols = list(data.keys())
            events_data = self._get_relevant_events(symbols, data)
            logger.info(f"Found {len(events_data)} relevant events for anomaly detection")
            
            # Initialize anomaly detector if not already done
            if self.anomaly_detector is None:
                self.anomaly_detector = InvestmentAnomalyDetector(
                    events_data=events_data, 
                    enable_temporal_validation=True
                )
            
            # Run investment anomaly detection
            logger.info("Running investment anomaly detection...")
            
            # Convert data to the format expected by anomaly detector
            if isinstance(data, dict):
                # Create combined data with symbol column
                all_data = []
                for symbol, stock_data in data.items():
                    if not stock_data.empty:
                        stock_data_copy = stock_data.copy()
                        stock_data_copy['symbol'] = symbol
                        all_data.append(stock_data_copy)
                if all_data:
                    combined_data = pd.concat(all_data, ignore_index=True)
                else:
                    combined_data = pd.DataFrame()
            else:
                combined_data = data
            
            investment_signals = self.anomaly_detector.detect_investment_anomalies(combined_data)
            
            logger.info(f"Anomaly detection completed. Generated {len(investment_signals)} investment signals")
            return investment_signals
            
        except Exception as e:
            raise AnomalyDetectionError(
                f"Anomaly detection failed: {e}",
                context={'enabled': self.config.analysis.enable_anomaly_detection, 'symbol_count': len(data)}
            )
    
    def run_forecasting(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Run forecasting analysis on the provided data.
        
        Args:
            data: Dictionary mapping symbols to their data
            
        Returns:
            Dictionary mapping symbols to their forecast data
            
        Raises:
            ForecastingError: If forecasting fails
        """
        if not self.config.analysis.enable_forecasting:
            logger.info("Forecasting disabled in configuration")
            return {}
        
        logger.info("Running forecasting analysis...")
        
        try:
            # Initialize components if needed
            if self.data_processor is None:
                self.data_processor = ForecastingDataProcessor()
            if self.model_manager is None:
                self.model_manager = ForecastingModelManager()
            if self.ensemble_manager is None:
                self.ensemble_manager = EnsembleForecaster()
            
            predictions = {}
            
            for symbol, symbol_data in data.items():
                try:
                    logger.info(f"Processing forecasting for {symbol}")
                    
                    # Prepare data for forecasting
                    processed_data = self.data_processor.prepare_forecasting_data(symbol_data, symbol)
                    
                    if processed_data.empty:
                        logger.warning(f"No processed data available for {symbol}")
                        continue
                    
                    # Generate predictions using ensemble
                    symbol_predictions = self.ensemble_manager.generate_ensemble_forecast(
                        processed_data, 
                        horizon=self.config.analysis.forecasting_horizon
                    )
                    
                    if not symbol_predictions.empty:
                        predictions[symbol] = symbol_predictions
                        logger.info(f"Generated forecasts for {symbol}: {len(symbol_predictions)} predictions")
                    else:
                        logger.warning(f"No predictions generated for {symbol}")
                        
                except Exception as e:
                    handled_error = ErrorHandler.handle_error(
                        e, operation="forecasting symbol", symbol=symbol
                    )
                    ErrorHandler.log_error(handled_error, level='warning')
                    # Continue with other symbols
            
            # Save trained models after successful forecasting
            if self.model_manager and hasattr(self.model_manager, 'save_models'):
                from pathlib import Path
                from datetime import datetime
                
                models_dir = Path(self.config.output.base_dir) / "forecasting" / "models"
                models_dir.mkdir(parents=True, exist_ok=True)
                model_path = models_dir / f"models_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                
                if self.model_manager.save_models(str(model_path)):
                    logger.info(f"Saved forecasting models to {model_path}")
                else:
                    logger.warning(f"Failed to save forecasting models to {model_path}")
            
            logger.info(f"Forecasting completed for {len(predictions)} symbols")
            return predictions
            
        except Exception as e:
            raise ForecastingError(
                f"Forecasting failed: {e}",
                context={'enabled': self.config.analysis.enable_forecasting, 'symbol_count': len(data)}
            )
    
    def _get_relevant_events(self, symbols: List[str], data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Get events relevant to the analysis period and symbols."""
        try:
            # Determine date range from data
            start_date = None
            end_date = None
            
            for symbol_data in data.values():
                if not symbol_data.empty:
                    if 'Date' in symbol_data.columns:
                        dates = pd.to_datetime(symbol_data['Date'])
                    elif hasattr(symbol_data.index, 'min') and pd.api.types.is_datetime64_any_dtype(symbol_data.index):
                        dates = symbol_data.index
                    else:
                        continue
                    
                    data_start = dates.min().date()
                    data_end = dates.max().date()
                    
                    if start_date is None or data_start < start_date:
                        start_date = data_start
                    if end_date is None or data_end > end_date:
                        end_date = data_end
            
            if start_date and end_date:
                return self.events_manager.get_events_for_symbols(symbols, start_date, end_date)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            handled_error = ErrorHandler.handle_error(
                e, operation="getting relevant events", 
                context={'symbols': symbols}
            )
            ErrorHandler.log_error(handled_error, level='warning')
            return pd.DataFrame()
    
    def calculate_confidence_intervals(self, predictions: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
        """Calculate confidence intervals for predictions."""
        logger.info("Calculating confidence intervals")
        
        confidence_stats = {}
        
        for symbol, pred_data in predictions.items():
            try:
                stats = {}
                
                # Calculate confidence intervals for configured levels
                for confidence_level in self.config.analysis.confidence_intervals:
                    if 'forecast' in pred_data.columns:
                        forecast_values = pred_data['forecast'].dropna()
                        if len(forecast_values) > 0:
                            std_dev = forecast_values.std()
                            mean_forecast = forecast_values.mean()
                            
                            # Simple confidence interval calculation
                            # In a real implementation, you'd use more sophisticated methods
                            margin = std_dev * (confidence_level + 1) / 2
                            
                            stats[f'ci_{int(confidence_level*100)}'] = {
                                'lower': mean_forecast - margin,
                                'upper': mean_forecast + margin,
                                'mean': mean_forecast,
                                'std': std_dev
                            }
                
                confidence_stats[symbol] = stats
                
            except Exception as e:
                handled_error = ErrorHandler.handle_error(
                    e, operation="calculating confidence intervals", symbol=symbol
                )
                ErrorHandler.log_error(handled_error, level='warning')
        
        return confidence_stats
    
    def validate_analysis_results(self, predictions: Dict[str, pd.DataFrame], 
                                signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate analysis results for quality and consistency."""
        logger.info("Validating analysis results")
        
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            # Validate predictions
            for symbol, pred_data in predictions.items():
                if pred_data.empty:
                    validation_results['warnings'].append(f"Empty predictions for {symbol}")
                elif 'forecast' in pred_data.columns:
                    forecast_values = pred_data['forecast'].dropna()
                    if len(forecast_values) == 0:
                        validation_results['warnings'].append(f"No valid forecasts for {symbol}")
                    elif forecast_values.isna().all():
                        validation_results['errors'].append(f"All forecasts are NaN for {symbol}")
                        validation_results['is_valid'] = False
            
            # Validate signals
            if not signals:
                validation_results['warnings'].append("No investment signals generated")
            else:
                signal_types = []
                for signal in signals:
                    # Handle both dict and AnomalySignal objects
                    if hasattr(signal, 'signal'):
                        signal_types.append(signal.signal)
                    elif hasattr(signal, 'anomaly_type'):
                        signal_types.append(signal.anomaly_type)
                    elif isinstance(signal, dict):
                        signal_types.append(signal.get('signal_type', 'unknown'))
                    else:
                        signal_types.append('unknown')
                
                unique_types = set(signal_types)
                validation_results['statistics']['signal_types'] = dict(zip(unique_types, [signal_types.count(t) for t in unique_types]))
                validation_results['statistics']['total_signals'] = len(signals)
            
        except Exception as e:
            handled_error = ErrorHandler.handle_error(
                e, operation="validating analysis results"
            )
            ErrorHandler.log_error(handled_error, level='warning')
            validation_results['errors'].append(f"Validation error: {e}")
            validation_results['is_valid'] = False
        
        return validation_results
    
    def run_holiday_effects_analysis(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Run holiday effects analysis on the provided data.
        
        Args:
            data: Dictionary mapping symbols to their data
            
        Returns:
            Dictionary containing holiday effects and seasonal patterns for each symbol
            
        Raises:
            AnalysisError: If holiday effects analysis fails
        """
        logger.info("Running holiday effects analysis...")
        
        try:
            results = {
                'holiday_effects': {},
                'seasonal_patterns': {},
                'reports': {}
            }
            
            for symbol, symbol_data in data.items():
                try:
                    logger.info(f"Analyzing holiday effects for {symbol}")
                    
                    # Analyze holiday effects
                    holiday_effects = self.holiday_analyzer.analyze_holiday_effects(symbol_data, symbol)
                    results['holiday_effects'][symbol] = holiday_effects
                    
                    # Analyze seasonal patterns
                    seasonal_patterns = self.holiday_analyzer.analyze_seasonal_patterns(symbol_data, symbol)
                    results['seasonal_patterns'][symbol] = seasonal_patterns
                    
                    # Generate comprehensive report
                    report = self.holiday_analyzer.generate_holiday_report(holiday_effects, seasonal_patterns)
                    results['reports'][symbol] = report
                    
                    logger.info(f"Holiday analysis completed for {symbol}: "
                              f"{len(holiday_effects)} holiday effects, "
                              f"{len(seasonal_patterns)} seasonal patterns")
                    
                except Exception as e:
                    handled_error = ErrorHandler.handle_error(
                        e, operation="holiday effects analysis", symbol=symbol
                    )
                    ErrorHandler.log_error(handled_error, level='warning')
                    # Continue with other symbols
            
            # Calculate summary statistics
            total_holiday_effects = sum(len(effects) for effects in results['holiday_effects'].values())
            total_seasonal_patterns = sum(len(patterns) for patterns in results['seasonal_patterns'].values())
            
            logger.info(f"Holiday effects analysis completed for {len(data)} symbols: "
                       f"{total_holiday_effects} total holiday effects, "
                       f"{total_seasonal_patterns} total seasonal patterns")
            
            return results
            
        except Exception as e:
            raise AnalysisError(
                f"Holiday effects analysis failed: {e}",
                context={'symbol_count': len(data)}
            )
    
    def run_options_analysis(self, symbols: List[str], output_dir: str) -> Dict[str, Any]:
        """
        Run comprehensive options analysis for the provided symbols.
        
        Args:
            symbols: List of symbols to analyze options for
            output_dir: Directory to save analysis outputs
            
        Returns:
            Dictionary containing options analysis results
            
        Raises:
            AnalysisError: If options analysis fails
        """
        if not self.config.analysis.get('enable_options_analysis', True):
            logger.info("Options analysis disabled in configuration")
            return {}
        
        logger.info(f"Running options analysis for {len(symbols)} symbols...")
        
        try:
            # Run comprehensive options analysis
            results = self.options_analyzer.analyze_options_for_symbols(symbols, output_dir)
            
            # Log summary statistics
            options_signals = results.get('options_signals', [])
            portfolio_greeks = results.get('portfolio_greeks', {})
            visualizations = results.get('visualizations', {})
            
            logger.info(f"Options analysis completed: "
                       f"{len(options_signals)} signals generated, "
                       f"{len(visualizations)} symbols visualized, "
                       f"Portfolio P/C ratio: {portfolio_greeks.get('portfolio_pc_ratio', 'N/A')}")
            
            return results
            
        except Exception as e:
            raise AnalysisError(
                f"Options analysis failed: {e}",
                context={'symbols': symbols, 'output_dir': output_dir}
            )