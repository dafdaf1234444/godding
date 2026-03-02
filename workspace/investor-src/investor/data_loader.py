"""
Data loading functionality for the investor library.
"""
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List
import logging
from datetime import datetime

from .data.stock_data import StockDataDownloader
from .data.storage import ParquetStorage

logger = logging.getLogger(__name__)


class DataLoader:
    """Main data loading interface."""
    
    def __init__(self, config_manager):
        """Initialize data loader with config manager."""
        self.config = config_manager
        self.downloader = StockDataDownloader()
        self.storage = ParquetStorage()
        self.base_dir = Path.cwd()
        
    def load_stock_data(self, symbol: str, period: str = "2y") -> pd.DataFrame:
        """Load stock data for a single symbol."""
        try:
            # First try to load from storage
            data = self.storage.load_stock_data(symbol)
            
            if data.empty:
                logger.info(f"No cached data for {symbol}, downloading...")
                data = self.downloader.download_stock_data(symbol, period=period)
                
                if not data.empty:
                    metadata = {
                        'symbol': symbol,
                        'period': period,
                        'download_time': datetime.now().isoformat()
                    }
                    self.storage.save_stock_data(data, symbol, metadata)
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {e}")
            return pd.DataFrame()
    
    def load_group_data(self, group_name: str) -> Dict[str, pd.DataFrame]:
        """Load data for a group of stocks."""
        try:
            # Load config
            config_file = self.base_dir / "config" / "data_sources.yaml"
            if not config_file.exists():
                logger.error(f"Config file not found: {config_file}")
                return {}
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Get symbols for group
            groups = config.get('stock_groups', {})
            if group_name not in groups:
                logger.error(f"Group {group_name} not found in config")
                return {}
            
            symbols = groups[group_name].get('symbols', [])
            
            # Load data for each symbol
            group_data = {}
            for symbol in symbols:
                data = self.load_stock_data(symbol)
                if not data.empty:
                    group_data[symbol] = data
            
            return group_data
            
        except Exception as e:
            logger.error(f"Error loading group data for {group_name}: {e}")
            return {}
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols."""
        try:
            return self.storage.get_available_symbols()
        except Exception as e:
            logger.error(f"Error getting available symbols: {e}")
            return []
    
    def get_available_groups(self) -> List[str]:
        """Get list of available groups."""
        try:
            config_file = self.base_dir / "config" / "data_sources.yaml"
            if not config_file.exists():
                return []
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            return list(config.get('stock_groups', {}).keys())
            
        except Exception as e:
            logger.error(f"Error getting available groups: {e}")
            return []