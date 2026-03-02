"""
Clean logging system for forecasting operations.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import json


class ForecastLogger:
    """Clean logger for forecasting operations."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session log file
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = self.log_dir / f"forecast_session_{self.session_id}.log"
        
        # Session tracking
        self.session_data = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'operations': [],
            'status': 'running'
        }
        
        # Set up clean logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up clean logging configuration."""
        # Create custom formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(formatter)
        
        # Console handler (clean)
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Get logger
        self.logger = logging.getLogger('forecast_session')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Suppress other loggers
        logging.getLogger('investor.forecasting').setLevel(logging.WARNING)
        logging.getLogger('investor.data').setLevel(logging.WARNING)
        logging.getLogger('statsforecast').setLevel(logging.WARNING)
        
    def log_operation(self, operation: str, details: Dict[str, Any] = None, status: str = 'success'):
        """Log a forecasting operation."""
        timestamp = datetime.now().isoformat()
        
        operation_data = {
            'timestamp': timestamp,
            'operation': operation,
            'status': status,
            'details': details or {}
        }
        
        self.session_data['operations'].append(operation_data)
        
        # Log to file and console
        if status == 'success':
            self.logger.info(f"✅ {operation}")
        elif status == 'warning':
            self.logger.warning(f"⚠️  {operation}")
        elif status == 'error':
            self.logger.error(f"❌ {operation}")
        else:
            self.logger.info(f"ℹ️  {operation}")
        
        # Add details if provided
        if details:
            for key, value in details.items():
                self.logger.info(f"   {key}: {value}")
    
    def log_start(self, symbols: List[str], horizon: int, ensemble_method: str):
        """Log the start of a forecasting session."""
        self.log_operation(
            "Starting forecasting session",
            {
                'symbols': symbols,
                'horizon': f"{horizon} days",
                'ensemble_method': ensemble_method,
                'models': ['AutoARIMA', 'AutoETS', 'AutoCES', 'MSTL', 'Theta']
            }
        )
    
    def log_data_loading(self, loaded_count: int, total_count: int):
        """Log data loading results."""
        if loaded_count == total_count:
            self.log_operation(
                "Data loading completed",
                {'loaded_stocks': loaded_count, 'total_requested': total_count}
            )
        else:
            self.log_operation(
                "Data loading partially completed",
                {'loaded_stocks': loaded_count, 'total_requested': total_count,
                 'missing': total_count - loaded_count},
                'warning'
            )
    
    def log_data_preparation(self, total_rows: int, features_count: int):
        """Log data preparation results."""
        self.log_operation(
            "Data preparation completed",
            {'total_rows': total_rows, 'features_engineered': features_count}
        )
    
    def log_model_training(self, duration_seconds: float):
        """Log model training completion."""
        self.log_operation(
            "Model training completed",
            {'duration': f"{duration_seconds:.1f}s", 'models_trained': 5}
        )
    
    def log_predictions(self, predictions_count: int, horizon: int):
        """Log prediction generation."""
        self.log_operation(
            "Predictions generated",
            {'predictions_count': predictions_count, 'horizon': f"{horizon} days"}
        )
    
    def log_ensemble(self, method: str, models_combined: int):
        """Log ensemble creation."""
        self.log_operation(
            "Ensemble predictions created",
            {'method': method, 'models_combined': models_combined}
        )
    
    def log_charts(self, charts_created: int):
        """Log chart generation."""
        self.log_operation(
            "Charts generated",
            {'charts_created': charts_created}
        )
    
    def log_report(self, report_path: str):
        """Log report generation."""
        self.log_operation(
            "Report generated",
            {'report_path': str(report_path)}
        )
    
    def log_completion(self, total_duration: float, stocks_count: int):
        """Log session completion."""
        self.session_data['status'] = 'completed'
        self.session_data['end_time'] = datetime.now().isoformat()
        self.session_data['total_duration'] = f"{total_duration:.1f}s"
        
        self.log_operation(
            "Forecasting session completed",
            {
                'total_duration': f"{total_duration:.1f}s",
                'stocks_processed': stocks_count,
                'operations_completed': len(self.session_data['operations'])
            }
        )
        
        # Save session summary
        self._save_session_summary()
    
    def log_error(self, error_msg: str, details: Dict[str, Any] = None):
        """Log an error."""
        self.session_data['status'] = 'error'
        self.log_operation(f"Error: {error_msg}", details, 'error')
        self._save_session_summary()
    
    def _save_session_summary(self):
        """Save session summary to JSON file."""
        try:
            summary_file = self.log_dir / f"session_summary_{self.session_id}.json"
            with open(summary_file, 'w') as f:
                json.dump(self.session_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save session summary: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get current session summary."""
        return self.session_data.copy()
    
    def print_quick_stats(self, predictions_data: Dict[str, Any]):
        """Print quick statistics at the end."""
        self.logger.info("\n" + "="*50)
        self.logger.info("📊 FORECASTING RESULTS")
        self.logger.info("="*50)
        
        if predictions_data:
            for symbol, stats in predictions_data.items():
                self.logger.info(f"📈 {symbol}: ${stats['avg_price']:.2f} avg | ${stats['final_price']:.2f} final")
        
        self.logger.info("📁 Results saved to: outputs/forecasting/")
        self.logger.info(f"📋 Session log: {self.log_file}")
        self.logger.info("="*50 + "\n")