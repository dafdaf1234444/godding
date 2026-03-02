"""
Configuration management for the investor analysis system.
"""
import yaml
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, field, fields
import logging

logger = logging.getLogger(__name__)


@dataclass
class DataConfig:
    """Data configuration settings."""
    period: str = "2y"
    interval: str = "1d"
    symbols: Dict[str, Any] = field(default_factory=dict)
    cache_enabled: bool = True
    data_dir: str = "data"
    market_indicators: Dict[str, Any] = field(default_factory=dict)
    source: str = "yfinance"
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Validate configuration values."""
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        if self.period not in valid_periods:
            raise ValueError(f"Invalid period: {self.period}. Must be one of {valid_periods}")
        
        valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
        if self.interval not in valid_intervals:
            raise ValueError(f"Invalid interval: {self.interval}. Must be one of {valid_intervals}")


@dataclass
class AnalysisConfig:
    """Analysis configuration settings."""
    enable_forecasting: bool = True
    enable_anomaly_detection: bool = True
    enable_visualization: bool = True
    forecasting_horizon: int = 21
    confidence_intervals: list = field(default_factory=lambda: [0.80, 0.95])
    # Legacy config support
    forecasting: Dict[str, Any] = field(default_factory=dict)
    ml_models: Dict[str, Any] = field(default_factory=dict)
    anomaly_detection: Dict[str, Any] = field(default_factory=dict)
    technical_analysis: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.forecasting_horizon <= 0:
            raise ValueError("Forecasting horizon must be positive")


@dataclass
class OutputConfig:
    """Output configuration settings."""
    base_dir: str = "outputs"
    timestamp_format: str = "%Y%m%d_%H%M%S"
    enable_git_integration: bool = True
    max_old_runs: int = 5
    generate_html_report: bool = True
    # Legacy config support  
    keep_latest_only: bool = True
    max_runs_to_keep: int = 3


@dataclass
class SystemConfig:
    """System configuration settings."""
    name: str = "Investor Analysis System"
    version: str = "1.0.0"
    log_level: str = "INFO"
    environment: str = "production"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_output: bool = True
    file_output: bool = True
    max_log_files: int = 5


@dataclass
class InvestorConfig:
    """Main configuration class that combines all configuration sections."""
    data: DataConfig = field(default_factory=DataConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    
    @classmethod
    def from_yaml(cls, config_path: str) -> 'InvestorConfig':
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Config file {config_path} not found, using defaults")
            return cls()
        
        try:
            with open(config_file, 'r') as f:
                yaml_config = yaml.safe_load(f)
            
            # Extract configuration sections and filter out unknown fields
            def filter_known_fields(config_dict, dataclass_type):
                if not config_dict:
                    return {}
                known_fields = {f.name for f in fields(dataclass_type)}
                return {k: v for k, v in config_dict.items() if k in known_fields}
            
            data_config = DataConfig(**filter_known_fields(yaml_config.get('data', {}), DataConfig))
            analysis_config = AnalysisConfig(**filter_known_fields(yaml_config.get('analysis', {}), AnalysisConfig))
            output_config = OutputConfig(**filter_known_fields(yaml_config.get('output', {}), OutputConfig))
            system_config = SystemConfig(**filter_known_fields(yaml_config.get('system', {}), SystemConfig))
            
            return cls(
                data=data_config,
                analysis=analysis_config,
                output=output_config,
                system=system_config
            )
            
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            logger.info("Using default configuration")
            return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for backward compatibility."""
        return {
            'data': {
                'period': self.data.period,
                'interval': self.data.interval,
                'symbols': self.data.symbols,
                'cache_enabled': self.data.cache_enabled,
                'data_dir': self.data.data_dir
            },
            'analysis': {
                'enable_forecasting': self.analysis.enable_forecasting,
                'enable_anomaly_detection': self.analysis.enable_anomaly_detection,
                'enable_visualization': self.analysis.enable_visualization,
                'forecasting_horizon': self.analysis.forecasting_horizon,
                'confidence_intervals': self.analysis.confidence_intervals
            },
            'output': {
                'base_dir': self.output.base_dir,
                'timestamp_format': self.output.timestamp_format,
                'enable_git_integration': self.output.enable_git_integration,
                'max_old_runs': self.output.max_old_runs,
                'generate_html_report': self.output.generate_html_report
            },
            'system': {
                'name': self.system.name,
                'version': self.system.version,
                'log_level': self.system.log_level,
                'environment': self.system.environment
            }
        }