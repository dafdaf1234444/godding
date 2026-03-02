"""
Holiday effects analysis for market behavior.
Analyzes stock performance around holidays and seasonal patterns.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
from enum import Enum
import holidays

logger = logging.getLogger(__name__)


class MarketRegion(Enum):
    """Market regions for holiday calendars."""
    US = "US"
    UK = "UK"
    EU = "EU"
    ASIA = "ASIA"
    GLOBAL = "GLOBAL"


@dataclass
class HolidayEffect:
    """Holiday effect analysis result."""
    holiday_name: str
    holiday_date: datetime
    symbol: str
    pre_holiday_return: float
    post_holiday_return: float
    holiday_period_return: float
    volume_change_pre: float
    volume_change_post: float
    significance_score: float
    effect_type: str  # 'positive', 'negative', 'neutral'
    sample_size: int


@dataclass
class SeasonalPattern:
    """Seasonal trading pattern result."""
    period_name: str
    start_date: str  # MM-DD format
    end_date: str    # MM-DD format
    avg_return: float
    avg_volatility: float
    win_rate: float
    sample_size: int
    significance: float


class HolidayCalendarManager:
    """Manages holiday calendars for different market regions."""
    
    def __init__(self):
        """Initialize holiday calendar manager."""
        self.holiday_cache = {}
        self._init_market_specific_holidays()
    
    def _init_market_specific_holidays(self):
        """Initialize market-specific holidays."""
        # US market holidays (NYSE/NASDAQ)
        self.us_market_holidays = {
            'New Year\'s Day': lambda year: datetime(year, 1, 1),
            'Martin Luther King Jr. Day': lambda year: self._nth_weekday(year, 1, 2, 3),  # 3rd Monday in January
            'Presidents\' Day': lambda year: self._nth_weekday(year, 2, 2, 3),  # 3rd Monday in February
            'Good Friday': lambda year: self._easter_date(year) - timedelta(days=2),
            'Memorial Day': lambda year: self._last_weekday(year, 5, 0),  # Last Monday in May
            'Juneteenth': lambda year: datetime(year, 6, 19) if year >= 2021 else None,
            'Independence Day': lambda year: datetime(year, 7, 4),
            'Labor Day': lambda year: self._nth_weekday(year, 9, 0, 1),  # 1st Monday in September
            'Thanksgiving': lambda year: self._nth_weekday(year, 11, 3, 4),  # 4th Thursday in November
            'Christmas Day': lambda year: datetime(year, 12, 25)
        }
        
        # Trading effect holidays (not necessarily market closures)
        self.trading_effect_holidays = {
            'Halloween': lambda year: datetime(year, 10, 31),
            'Black Friday': lambda year: self._nth_weekday(year, 11, 3, 4) + timedelta(days=1),
            'Cyber Monday': lambda year: self._nth_weekday(year, 11, 3, 4) + timedelta(days=4),
            'Tax Day': lambda year: datetime(year, 4, 15),
            'Earnings Season Start': lambda year: datetime(year, 1, 15),  # Approximate
            'Q1 Earnings': lambda year: datetime(year, 4, 15),
            'Q2 Earnings': lambda year: datetime(year, 7, 15),
            'Q3 Earnings': lambda year: datetime(year, 10, 15)
        }
    
    def get_holidays_for_year(self, year: int, region: MarketRegion = MarketRegion.US) -> Dict[str, datetime]:
        """Get holidays for a specific year and region."""
        cache_key = f"{region.value}_{year}"
        
        if cache_key in self.holiday_cache:
            return self.holiday_cache[cache_key]
        
        year_holidays = {}
        
        if region == MarketRegion.US:
            # Market closure holidays
            for name, date_func in self.us_market_holidays.items():
                try:
                    holiday_date = date_func(year)
                    if holiday_date:
                        year_holidays[name] = holiday_date
                except Exception as e:
                    logger.warning(f"Error calculating {name} for {year}: {e}")
            
            # Trading effect holidays
            for name, date_func in self.trading_effect_holidays.items():
                try:
                    holiday_date = date_func(year)
                    if holiday_date:
                        year_holidays[name] = holiday_date
                except Exception as e:
                    logger.warning(f"Error calculating {name} for {year}: {e}")
        
        # Use holidays library for other regions
        elif region == MarketRegion.UK:
            uk_holidays = holidays.UK(years=year)
            year_holidays.update({name: date for date, name in uk_holidays.items()})
        elif region == MarketRegion.EU:
            # Use Germany as EU proxy
            eu_holidays = holidays.Germany(years=year)
            year_holidays.update({name: date for date, name in eu_holidays.items()})
        
        self.holiday_cache[cache_key] = year_holidays
        return year_holidays
    
    def get_holidays_for_period(self, start_year: int, end_year: int, 
                               region: MarketRegion = MarketRegion.US) -> Dict[str, List[datetime]]:
        """Get holidays for a period of years."""
        all_holidays = {}
        
        for year in range(start_year, end_year + 1):
            year_holidays = self.get_holidays_for_year(year, region)
            
            for name, date in year_holidays.items():
                if name not in all_holidays:
                    all_holidays[name] = []
                all_holidays[name].append(date)
        
        return all_holidays
    
    def is_trading_day(self, date: datetime, region: MarketRegion = MarketRegion.US) -> bool:
        """Check if a date is a trading day."""
        # Weekend check
        if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Holiday check
        year_holidays = self.get_holidays_for_year(date.year, region)
        holiday_dates = [h.date() for h in year_holidays.values() if h]
        
        return date.date() not in holiday_dates
    
    def _nth_weekday(self, year: int, month: int, weekday: int, n: int) -> datetime:
        """Get the nth weekday of a month (e.g., 3rd Monday)."""
        first_day = datetime(year, month, 1)
        first_weekday = first_day.weekday()
        
        days_to_add = (weekday - first_weekday) % 7
        target_date = first_day + timedelta(days=days_to_add + (n - 1) * 7)
        
        return target_date
    
    def _last_weekday(self, year: int, month: int, weekday: int) -> datetime:
        """Get the last weekday of a month."""
        # Start from the last day of the month and work backwards
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        days_to_subtract = (last_day.weekday() - weekday) % 7
        return last_day - timedelta(days=days_to_subtract)
    
    def _easter_date(self, year: int) -> datetime:
        """Calculate Easter date using the algorithm."""
        # Anonymous Gregorian algorithm
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        ell = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * ell) // 451
        month = (h + ell - 7 * m + 114) // 31
        day = ((h + ell - 7 * m + 114) % 31) + 1
        
        return datetime(year, month, day)


class HolidayEffectsAnalyzer:
    """Analyzes holiday effects on market behavior."""
    
    def __init__(self, region: MarketRegion = MarketRegion.US):
        """Initialize holiday effects analyzer."""
        self.region = region
        self.calendar_manager = HolidayCalendarManager()
        self.min_sample_size = 5  # Minimum years of data for analysis
    
    def analyze_holiday_effects(self, data: pd.DataFrame, symbol: str) -> List[HolidayEffect]:
        """
        Analyze holiday effects for a stock.
        
        Args:
            data: DataFrame with Date, Close, Volume columns
            symbol: Stock symbol
            
        Returns:
            List of holiday effects
        """
        if data.empty or 'Date' not in data.columns:
            logger.warning(f"Invalid data for holiday analysis: {symbol}")
            return []
        
        # Ensure Date column is datetime and handle timezone issues
        data = data.copy()
        data['Date'] = pd.to_datetime(data['Date'])
        
        # Convert timezone-aware to naive datetime for comparison
        if hasattr(data['Date'].dtype, 'tz') and data['Date'].dtype.tz is not None:
            data['Date'] = data['Date'].dt.tz_localize(None)
        
        data = data.sort_values('Date').reset_index(drop=True)
        
        # Calculate returns
        data['Return'] = data['Close'].pct_change()
        data['Volume_Change'] = data['Volume'].pct_change()
        
        # Get holiday dates for the data period
        start_year = data['Date'].min().year
        end_year = data['Date'].max().year
        
        holiday_effects = []
        all_holidays = self.calendar_manager.get_holidays_for_period(start_year, end_year, self.region)
        
        for holiday_name, holiday_dates in all_holidays.items():
            if len(holiday_dates) < self.min_sample_size:
                continue
            
            effect = self._analyze_single_holiday_effect(data, symbol, holiday_name, holiday_dates)
            if effect:
                holiday_effects.append(effect)
        
        return holiday_effects
    
    def _analyze_single_holiday_effect(self, data: pd.DataFrame, symbol: str, 
                                     holiday_name: str, holiday_dates: List[datetime]) -> Optional[HolidayEffect]:
        """Analyze effect of a single holiday."""
        pre_returns = []
        post_returns = []
        period_returns = []
        pre_volume_changes = []
        post_volume_changes = []
        
        for holiday_date in holiday_dates:
            # Find trading days around holiday
            pre_date = self._get_previous_trading_day(data, holiday_date)
            post_date = self._get_next_trading_day(data, holiday_date)
            
            if pre_date and post_date:
                # Get pre-holiday return (day before holiday)
                pre_idx = data[data['Date'].dt.date == pre_date.date()].index
                if len(pre_idx) > 0:
                    pre_returns.append(data.loc[pre_idx[0], 'Return'])
                    if not pd.isna(data.loc[pre_idx[0], 'Volume_Change']):
                        pre_volume_changes.append(data.loc[pre_idx[0], 'Volume_Change'])
                
                # Get post-holiday return (day after holiday)
                post_idx = data[data['Date'].dt.date == post_date.date()].index
                if len(post_idx) > 0:
                    post_returns.append(data.loc[post_idx[0], 'Return'])
                    if not pd.isna(data.loc[post_idx[0], 'Volume_Change']):
                        post_volume_changes.append(data.loc[post_idx[0], 'Volume_Change'])
                
                # Get holiday period return (pre to post)
                if len(pre_idx) > 0 and len(post_idx) > 0:
                    pre_price = data.loc[pre_idx[0], 'Close']
                    post_price = data.loc[post_idx[0], 'Close']
                    period_return = (post_price - pre_price) / pre_price
                    period_returns.append(period_return)
        
        if not pre_returns or not post_returns:
            return None
        
        # Calculate statistics
        avg_pre_return = np.mean(pre_returns)
        avg_post_return = np.mean(post_returns)
        avg_period_return = np.mean(period_returns) if period_returns else 0
        avg_pre_volume_change = np.mean(pre_volume_changes) if pre_volume_changes else 0
        avg_post_volume_change = np.mean(post_volume_changes) if post_volume_changes else 0
        
        # Calculate significance score (simplified t-test)
        significance_score = self._calculate_significance(pre_returns + post_returns)
        
        # Determine effect type
        effect_type = 'neutral'
        if avg_period_return > 0.005:  # 0.5% threshold
            effect_type = 'positive'
        elif avg_period_return < -0.005:
            effect_type = 'negative'
        
        return HolidayEffect(
            holiday_name=holiday_name,
            holiday_date=holiday_dates[0],  # Use first occurrence as representative
            symbol=symbol,
            pre_holiday_return=avg_pre_return,
            post_holiday_return=avg_post_return,
            holiday_period_return=avg_period_return,
            volume_change_pre=avg_pre_volume_change,
            volume_change_post=avg_post_volume_change,
            significance_score=significance_score,
            effect_type=effect_type,
            sample_size=len(pre_returns)
        )
    
    def analyze_seasonal_patterns(self, data: pd.DataFrame, symbol: str) -> List[SeasonalPattern]:
        """
        Analyze seasonal trading patterns.
        
        Args:
            data: DataFrame with Date, Close columns
            symbol: Stock symbol
            
        Returns:
            List of seasonal patterns
        """
        if data.empty or 'Date' not in data.columns:
            return []
        
        data = data.copy()
        data['Date'] = pd.to_datetime(data['Date'])
        
        # Convert timezone-aware to naive datetime for comparison
        if hasattr(data['Date'].dtype, 'tz') and data['Date'].dtype.tz is not None:
            data['Date'] = data['Date'].dt.tz_localize(None)
        
        data['Return'] = data['Close'].pct_change()
        
        # Define seasonal periods
        seasonal_periods = {
            'January Effect': ('01-01', '01-31'),
            'Sell in May': ('05-01', '05-31'),
            'Summer Rally': ('07-01', '08-31'),
            'September Decline': ('09-01', '09-30'),
            'October Volatility': ('10-01', '10-31'),
            'Santa Claus Rally': ('12-15', '12-31'),
            'Tax Loss Selling': ('12-01', '12-15'),
            'Q1 Earnings Season': ('01-15', '02-15'),
            'Q2 Earnings Season': ('04-15', '05-15'),
            'Q3 Earnings Season': ('07-15', '08-15'),
            'Q4 Earnings Season': ('10-15', '11-15')
        }
        
        patterns = []
        for period_name, (start_date, end_date) in seasonal_periods.items():
            pattern = self._analyze_seasonal_period(data, period_name, start_date, end_date)
            if pattern:
                patterns.append(pattern)
        
        return patterns
    
    def _analyze_seasonal_period(self, data: pd.DataFrame, period_name: str, 
                                start_date: str, end_date: str) -> Optional[SeasonalPattern]:
        """Analyze a specific seasonal period."""
        period_returns = []
        period_volatilities = []
        
        # Get unique years in data
        years = data['Date'].dt.year.unique()
        
        for year in years:
            # Create date range for this year
            try:
                period_start = datetime.strptime(f"{year}-{start_date}", "%Y-%m-%d")
                period_end = datetime.strptime(f"{year}-{end_date}", "%Y-%m-%d")
                
                # Get data for this period
                period_mask = (data['Date'] >= period_start) & (data['Date'] <= period_end)
                period_data = data[period_mask]
                
                if len(period_data) > 1:
                    # Calculate period return
                    start_price = period_data['Close'].iloc[0]
                    end_price = period_data['Close'].iloc[-1]
                    period_return = (end_price - start_price) / start_price
                    period_returns.append(period_return)
                    
                    # Calculate period volatility
                    period_vol = period_data['Return'].std()
                    if not pd.isna(period_vol):
                        period_volatilities.append(period_vol)
                
            except ValueError:
                continue
        
        if len(period_returns) < 3:  # Need at least 3 years of data
            return None
        
        # Calculate statistics
        avg_return = np.mean(period_returns)
        avg_volatility = np.mean(period_volatilities) if period_volatilities else 0
        win_rate = sum(1 for r in period_returns if r > 0) / len(period_returns)
        
        # Calculate significance (simplified)
        significance = abs(avg_return) / (np.std(period_returns) / np.sqrt(len(period_returns))) if len(period_returns) > 1 else 0
        
        return SeasonalPattern(
            period_name=period_name,
            start_date=start_date,
            end_date=end_date,
            avg_return=avg_return,
            avg_volatility=avg_volatility,
            win_rate=win_rate,
            sample_size=len(period_returns),
            significance=significance
        )
    
    def _get_previous_trading_day(self, data: pd.DataFrame, target_date: datetime) -> Optional[datetime]:
        """Get the previous trading day before target date."""
        candidate_date = target_date - timedelta(days=1)
        
        # Look back up to 5 days to find a trading day
        for _ in range(5):
            if self.calendar_manager.is_trading_day(candidate_date, self.region):
                # Check if we have data for this day
                if any(data['Date'].dt.date == candidate_date.date()):
                    return candidate_date
            candidate_date -= timedelta(days=1)
        
        return None
    
    def _get_next_trading_day(self, data: pd.DataFrame, target_date: datetime) -> Optional[datetime]:
        """Get the next trading day after target date."""
        candidate_date = target_date + timedelta(days=1)
        
        # Look forward up to 5 days to find a trading day
        for _ in range(5):
            if self.calendar_manager.is_trading_day(candidate_date, self.region):
                # Check if we have data for this day
                if any(data['Date'].dt.date == candidate_date.date()):
                    return candidate_date
            candidate_date += timedelta(days=1)
        
        return None
    
    def _calculate_significance(self, returns: List[float]) -> float:
        """Calculate significance score for returns."""
        if len(returns) < 2:
            return 0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0
        
        # Simplified t-statistic
        t_stat = abs(mean_return) / (std_return / np.sqrt(len(returns)))
        
        # Convert to 0-1 scale (simplified)
        return min(t_stat / 2.0, 1.0)
    
    def generate_holiday_report(self, holiday_effects: List[HolidayEffect], 
                               seasonal_patterns: List[SeasonalPattern]) -> Dict[str, Any]:
        """Generate a comprehensive holiday effects report."""
        report = {
            'summary': {
                'total_holidays_analyzed': len(holiday_effects),
                'significant_effects': len([h for h in holiday_effects if h.significance_score > 0.3]),
                'positive_effects': len([h for h in holiday_effects if h.effect_type == 'positive']),
                'negative_effects': len([h for h in holiday_effects if h.effect_type == 'negative']),
                'seasonal_patterns': len(seasonal_patterns)
            },
            'top_positive_effects': sorted(
                [h for h in holiday_effects if h.effect_type == 'positive'],
                key=lambda x: x.holiday_period_return,
                reverse=True
            )[:5],
            'top_negative_effects': sorted(
                [h for h in holiday_effects if h.effect_type == 'negative'],
                key=lambda x: x.holiday_period_return
            )[:5],
            'most_significant_effects': sorted(
                holiday_effects,
                key=lambda x: x.significance_score,
                reverse=True
            )[:10],
            'strongest_seasonal_patterns': sorted(
                seasonal_patterns,
                key=lambda x: x.significance,
                reverse=True
            )[:10],
            'volume_effects': {
                'holidays_with_volume_increase_pre': len([h for h in holiday_effects if h.volume_change_pre > 0.1]),
                'holidays_with_volume_decrease_post': len([h for h in holiday_effects if h.volume_change_post < -0.1])
            }
        }
        
        return report