"""
Investor - Investment library for data download, analysis, and portfolio management.
"""
from .data.stock_data import StockDataDownloader
from .utils.logging import setup_logging
from .utils.date_utils import parse_date, get_business_days_ago

__version__ = "0.1.0"
__all__ = [
    "StockDataDownloader",
    "setup_logging",
    "parse_date",
    "get_business_days_ago",
]