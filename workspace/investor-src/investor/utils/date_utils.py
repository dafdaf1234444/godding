"""
Date utilities for the investor library.
"""
from datetime import datetime, timedelta
from typing import Union
import pandas as pd


def parse_date(date_str: Union[str, datetime]) -> datetime:
    """
    Parse a date string or datetime object into a datetime.
    
    Args:
        date_str: Date string or datetime object
        
    Returns:
        Parsed datetime object
    """
    if isinstance(date_str, datetime):
        return date_str
    
    if isinstance(date_str, str):
        try:
            return pd.to_datetime(date_str).to_pydatetime()
        except Exception:
            raise ValueError(f"Unable to parse date: {date_str}")
    
    raise ValueError(f"Invalid date type: {type(date_str)}")


def get_business_days_ago(days: int) -> datetime:
    """
    Get a date that is a certain number of business days ago.
    
    Args:
        days: Number of business days ago
        
    Returns:
        Date that is 'days' business days ago
    """
    today = datetime.now()
    business_days = 0
    current_date = today
    
    while business_days < days:
        current_date -= timedelta(days=1)
        # Monday is 0, Sunday is 6
        if current_date.weekday() < 5:  # Monday to Friday
            business_days += 1
    
    return current_date


def get_market_calendar_range(
    start_date: datetime,
    end_date: datetime,
    market: str = "NYSE"
) -> pd.DatetimeIndex:
    """
    Get trading days between two dates for a specific market.
    
    Args:
        start_date: Start date
        end_date: End date
        market: Market identifier (NYSE, NASDAQ, etc.)
        
    Returns:
        DatetimeIndex of trading days
    """
    # For now, just return business days
    # TODO: Implement proper market calendar support
    return pd.bdate_range(start=start_date, end=end_date)


def format_period_to_dates(period: str) -> tuple[datetime, datetime]:
    """
    Convert yfinance period string to start and end dates.
    
    Args:
        period: Period string (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = datetime.now()
    
    if period == "1d":
        start_date = end_date - timedelta(days=1)
    elif period == "5d":
        start_date = end_date - timedelta(days=5)
    elif period == "1mo":
        start_date = end_date - timedelta(days=30)
    elif period == "3mo":
        start_date = end_date - timedelta(days=90)
    elif period == "6mo":
        start_date = end_date - timedelta(days=180)
    elif period == "1y":
        start_date = end_date - timedelta(days=365)
    elif period == "2y":
        start_date = end_date - timedelta(days=730)
    elif period == "5y":
        start_date = end_date - timedelta(days=1825)
    elif period == "10y":
        start_date = end_date - timedelta(days=3650)
    elif period == "ytd":
        start_date = datetime(end_date.year, 1, 1)
    elif period == "max":
        start_date = datetime(1900, 1, 1)
    else:
        raise ValueError(f"Invalid period: {period}")
    
    return start_date, end_date