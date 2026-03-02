"""
Configuration management for the investor library.
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Configuration manager for the investor library."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize config manager."""
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load default config
        self.config = self._load_default_config()
        
        # Load user config if exists
        user_config_file = self.config_dir / "data_sources.yaml"
        if user_config_file.exists():
            try:
                with open(user_config_file, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self.config.update(user_config)
            except Exception as e:
                logger.error(f"Error loading user config: {e}")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            'stock_groups': {
                'tech_stocks': {
                    'symbols': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
                    'description': 'Major technology stocks'
                },
                'sp500_sample': {
                    'symbols': ['SPY', 'VOO', 'IVV'],
                    'description': 'S&P 500 ETFs'
                }
            },
            'analysis_settings': {
                'moving_averages': [20, 50, 200],
                'rsi_period': 14,
                'macd_settings': {
                    'fast': 12,
                    'slow': 26,
                    'signal': 9
                },
                'bollinger_bands': {
                    'period': 20,
                    'std_dev': 2
                }
            },
            'forecasting_settings': {
                'default_horizon': 21,
                'confidence_levels': [80, 95],
                'cross_validation': {
                    'n_windows': 5,
                    'step_size': 5
                }
            }
        }
    
    def get_stock_groups(self) -> Dict[str, Dict[str, Any]]:
        """Get stock groups configuration."""
        return self.config.get('stock_groups', {})
    
    def get_group_symbols(self, group_name: str) -> list:
        """Get symbols for a specific group."""
        groups = self.get_stock_groups()
        if group_name in groups:
            return groups[group_name].get('symbols', [])
        return []
    
    def get_analysis_settings(self) -> Dict[str, Any]:
        """Get analysis settings."""
        return self.config.get('analysis_settings', {})
    
    def get_forecasting_settings(self) -> Dict[str, Any]:
        """Get forecasting settings."""
        return self.config.get('forecasting_settings', {})
    
    def get_config(self) -> Dict[str, Any]:
        """Get full configuration."""
        return self.config
    
    def save_config(self, config_file: Optional[str] = None):
        """Save configuration to file."""
        if config_file is None:
            config_file = self.config_dir / "data_sources.yaml"
        
        try:
            with open(config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def add_stock_group(self, group_name: str, symbols: list, description: str = ""):
        """Add a new stock group."""
        if 'stock_groups' not in self.config:
            self.config['stock_groups'] = {}
        
        self.config['stock_groups'][group_name] = {
            'symbols': symbols,
            'description': description
        }
        
        logger.info(f"Added stock group: {group_name}")
    
    def remove_stock_group(self, group_name: str):
        """Remove a stock group."""
        if 'stock_groups' in self.config and group_name in self.config['stock_groups']:
            del self.config['stock_groups'][group_name]
            logger.info(f"Removed stock group: {group_name}")
    
    def update_analysis_settings(self, settings: Dict[str, Any]):
        """Update analysis settings."""
        if 'analysis_settings' not in self.config:
            self.config['analysis_settings'] = {}
        
        self.config['analysis_settings'].update(settings)
        logger.info("Updated analysis settings")
    
    def update_forecasting_settings(self, settings: Dict[str, Any]):
        """Update forecasting settings."""
        if 'forecasting_settings' not in self.config:
            self.config['forecasting_settings'] = {}
        
        self.config['forecasting_settings'].update(settings)
        logger.info("Updated forecasting settings")