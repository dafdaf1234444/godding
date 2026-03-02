"""
Analysis orchestrator for the investor analysis system.
Main coordinator that manages the entire analysis pipeline using specialized managers.
"""
import time
from typing import Dict, List, Any
import logging
from datetime import datetime

from .config import InvestorConfig
from .data_manager import DataManager
from .analysis_manager import AnalysisManager
from .visualization_manager import VisualizationManager
from .output_manager import OutputManager

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    Main orchestrator for the investor analysis system.
    Coordinates data loading, analysis, visualization, and output management.
    """
    
    def __init__(self, config_path: str = "config/main_config.yaml", 
                 base_currency: str = "USD", convert_currencies: bool = False):
        """Initialize the analysis orchestrator."""
        # Load configuration
        self.config = InvestorConfig.from_yaml(config_path)
        self.timestamp = datetime.now().strftime(self.config.output.timestamp_format)
        
        # Initialize specialized managers
        self.data_manager = DataManager(self.config, base_currency, convert_currencies)
        self.analysis_manager = AnalysisManager(self.config)
        self.visualization_manager = VisualizationManager(self.config)
        self.output_manager = OutputManager(self.config, self.timestamp)
        
        # Set up logging after output manager is created
        self._setup_logging()
        
        logger.info(f"Initialized {self.config.system.name} v{self.config.system.version}")
        logger.info(f"Configuration: {self.config.system.environment} environment")
    
    def _setup_logging(self):
        """Set up logging configuration."""
        log_level = getattr(logging, self.config.system.log_level.upper(), logging.INFO)
        
        # Create logger
        self.logger = logging.getLogger("InvestorSystem")
        self.logger.setLevel(log_level)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            # Formatter
            formatter = logging.Formatter(self.config.system.log_format)
            
            # Console handler
            if self.config.system.console_output:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(log_level)
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)
            
            # File handler
            if self.config.system.file_output:
                # Create logs directory if it doesn't exist
                log_dir = self.output_manager.run_dir / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                
                # Create log file path
                log_file = log_dir / f"analysis_{self.timestamp}.log"
                
                # Add rotating file handler
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    log_file, 
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=self.config.system.max_log_files
                )
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
                
                logger.info(f"Logging to file: {log_file}")
    
    def run_full_analysis(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Run complete analysis pipeline.
        
        Args:
            symbols: List of stock symbols to analyze
            
        Returns:
            Dictionary containing analysis results and metadata
        """
        start_time = time.time()
        
        try:
            self.logger.info("Starting comprehensive investment analysis...")
            self.logger.info(f"Symbols: {symbols}")
            
            # Setup output directories
            output_dir = self.output_manager.setup_output_directories()
            
            # Phase 1: Data Loading
            self.logger.info("Loading data...")
            data = self._load_all_data(symbols)
            
            # Phase 2: Analysis
            investment_signals = []
            predictions = {}
            
            if self.config.analysis.enable_anomaly_detection:
                self.logger.info("Running anomaly detection...")
                investment_signals = self.analysis_manager.run_anomaly_detection(data)
            
            if self.config.analysis.enable_forecasting:
                self.logger.info("Running forecasting...")
                predictions = self.analysis_manager.run_forecasting(data)
            
            # Holiday Effects Analysis (enabled by default)
            holiday_analysis = {}
            enable_holiday_effects = getattr(self.config.analysis, 'enable_holiday_effects', True)
            self.logger.info(f"Holiday effects analysis enabled: {enable_holiday_effects}")
            if enable_holiday_effects:
                self.logger.info("Running holiday effects analysis...")
                holiday_analysis = self.analysis_manager.run_holiday_effects_analysis(data)
            
            # Phase 3: Visualization
            visualizations = {}
            if self.config.analysis.enable_visualization:
                self.logger.info("Creating visualizations...")
                visualizations = self.visualization_manager.create_visualizations(
                    data, predictions, investment_signals, output_dir
                )
            
            # Phase 4: Output Management
            self.logger.info("Saving results...")
            saved_files = self.output_manager.save_analysis_results(
                data, predictions, investment_signals, visualizations, holiday_analysis
            )
            
            # Generate report
            if self.config.output.generate_html_report:
                analysis_duration = time.time() - start_time
                report_path = self.output_manager.generate_html_report(
                    data, predictions, investment_signals, visualizations, analysis_duration
                )
                if report_path:
                    saved_files['html_report'] = report_path
            
            # Git workflow
            if self.config.output.enable_git_integration:
                self.logger.info("Managing git workflow...")
                self.output_manager.manage_git_workflow()
            
            # Calculate final metrics
            end_time = time.time()
            duration = end_time - start_time
            
            # Create performance summary
            performance_summary = self.visualization_manager.create_performance_summary(
                data, predictions, investment_signals
            )
            
            # Validate results
            validation_results = self.analysis_manager.validate_analysis_results(
                predictions, investment_signals
            )
            
            # Prepare final results
            results = {
                'success': True,
                'symbols': symbols,
                'signals_count': len(investment_signals),
                'predictions_count': len(predictions),
                'holiday_analysis': holiday_analysis,
                'visualizations_count': len(visualizations),
                'duration': duration,
                'output_dir': str(output_dir),
                'saved_files': saved_files,
                'performance_summary': performance_summary,
                'validation_results': validation_results,
                'timestamp': self.timestamp
            }
            
            self.logger.info(f"Analysis completed successfully in {duration:.1f}s")
            self.logger.info(f"Generated {len(investment_signals)} signals, {len(predictions)} forecasts")
            self.logger.info(f"Results saved to: {output_dir}")
            
            return results
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Analysis failed after {duration:.1f}s: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                'success': False,
                'error': str(e),
                'symbols': symbols,
                'duration': duration,
                'timestamp': self.timestamp
            }
    
    def _load_all_data(self, symbols: List[str], include_market_data: bool = True, include_crypto: bool = True) -> Dict[str, Any]:
        """Load all required data for analysis."""
        # Load primary symbol data (stocks and cryptos)
        data = self.data_manager.load_data(symbols)
        
        # Only load additional market data if requested (default: True for full analysis)
        if include_market_data:
            # Load additional market data
            market_data = self.data_manager.load_market_data()
            data.update(market_data)
        
        # Load cryptocurrency data if requested and if we have crypto symbols
        if include_crypto:
            crypto_symbols = [s for s in symbols if self.data_manager.is_crypto_symbol(s)]
            if crypto_symbols:
                self.logger.info(f"Loading additional crypto data for {len(crypto_symbols)} symbols")
                crypto_data = self.data_manager.load_crypto_data(crypto_symbols)
                # Merge with existing data, crypto takes precedence
                data.update(crypto_data)
            
            # Load sector data for context
            sector_data = self.data_manager.load_sector_data()
            data.update(sector_data)
        
        self.logger.info(f"Loaded data for {len(data)} symbols total")
        return data
    
    def run_quick_analysis(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Run a quick analysis with reduced functionality for faster execution.
        
        Args:
            symbols: List of stock symbols to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        # Temporarily disable some features for speed
        original_forecasting = self.config.analysis.enable_forecasting
        original_visualization = self.config.analysis.enable_visualization
        
        try:
            # Disable forecasting for quick run
            self.config.analysis.enable_forecasting = False
            # Keep basic visualization
            self.config.analysis.enable_visualization = True
            
            self.logger.info("Running quick analysis mode...")
            
            # For quick analysis, use symbol-only data loading
            start_time = time.time()
            
            try:
                # Setup output directories
                output_dir = self.output_manager.setup_output_directories()
                
                # Load only requested symbols data (no market/sector data for speed)
                self.logger.info("Loading symbol data only...")
                data = self._load_all_data(symbols, include_market_data=False)
                
                # Phase 2: Analysis (limited for quick mode)
                investment_signals = []
                predictions = {}
                
                if self.config.analysis.enable_anomaly_detection:
                    self.logger.info("Running anomaly detection...")
                    investment_signals = self.analysis_manager.run_anomaly_detection(data)
                
                # Holiday Effects Analysis (quick and valuable)
                holiday_analysis = {}
                enable_holiday_effects = getattr(self.config.analysis, 'enable_holiday_effects', True)
                self.logger.info(f"Holiday effects analysis enabled: {enable_holiday_effects}")
                if enable_holiday_effects:
                    self.logger.info("Running holiday effects analysis...")
                    holiday_analysis = self.analysis_manager.run_holiday_effects_analysis(data)
                
                # Phase 3: Basic Visualization
                visualizations = {}
                if self.config.analysis.enable_visualization:
                    self.logger.info("Creating basic visualizations...")
                    visualizations = self.visualization_manager.create_visualizations(
                        data, predictions, investment_signals, output_dir
                    )
                
                # Phase 4: Output Management
                self.logger.info("Saving results...")
                saved_files = self.output_manager.save_analysis_results(
                    data, predictions, investment_signals, visualizations, holiday_analysis
                )
                
                # Git workflow
                if self.config.output.enable_git_integration:
                    self.logger.info("Managing git workflow...")
                    self.output_manager.manage_git_workflow()
                
                # Calculate final metrics
                end_time = time.time()
                duration = end_time - start_time
                
                results = {
                    'success': True,
                    'symbols': symbols,
                    'signals_count': len(investment_signals),
                    'predictions_count': len(predictions),
                    'holiday_analysis': holiday_analysis,
                    'visualizations_count': len(visualizations),
                    'duration': duration,
                    'output_dir': str(output_dir),
                    'saved_files': saved_files,
                    'timestamp': self.timestamp
                }
                
                self.logger.info(f"Quick analysis completed successfully in {duration:.1f}s")
                self.logger.info(f"Generated {len(investment_signals)} signals for {len(symbols)} symbols")
                self.logger.info(f"Results saved to: {output_dir}")
                
                return results
                
            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"Quick analysis failed after {duration:.1f}s: {str(e)}"
                self.logger.error(error_msg)
                
                return {
                    'success': False,
                    'error': str(e),
                    'symbols': symbols,
                    'duration': duration,
                    'timestamp': self.timestamp
                }
            
        finally:
            # Restore original settings
            self.config.analysis.enable_forecasting = original_forecasting
            self.config.analysis.enable_visualization = original_visualization
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and configuration."""
        return {
            'system_name': self.config.system.name,
            'version': self.config.system.version,
            'environment': self.config.system.environment,
            'config': self.config.to_dict(),
            'available_symbols': self.data_manager.get_available_symbols()[:10],  # First 10
            'managers_initialized': {
                'data_manager': self.data_manager is not None,
                'analysis_manager': self.analysis_manager is not None,
                'visualization_manager': self.visualization_manager is not None,
                'output_manager': self.output_manager is not None
            }
        }
    
    def cleanup_old_data(self, max_age_days: int = 30):
        """Clean up old data and output files."""
        self.logger.info("Cleaning up old data...")
        self.data_manager.cleanup_old_data(max_age_days)
        # Additional cleanup could be added here
        self.logger.info("Cleanup completed")


def create_orchestrator(config_path: str = "config/main_config.yaml", 
                       base_currency: str = "USD", 
                       convert_currencies: bool = False) -> AnalysisOrchestrator:
    """
    Factory function to create an AnalysisOrchestrator instance.
    
    Args:
        config_path: Path to configuration file
        base_currency: Base currency for conversions
        convert_currencies: Whether to enable currency conversion
        
    Returns:
        Configured AnalysisOrchestrator instance
    """
    return AnalysisOrchestrator(config_path, base_currency, convert_currencies)