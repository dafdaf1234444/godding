"""
External data integration module for macroeconomic, sentiment, and options data.
Designed to be extensible for future data sources.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
from datetime import datetime, timedelta
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class ExternalDataManager:
    """
    Manager for external data sources including macroeconomic, sentiment, and options data.
    
    Features:
    - Macroeconomic indicators (GDP, inflation, interest rates, etc.)
    - Sentiment data (VIX, news sentiment, social media sentiment)
    - Options data (put/call ratios, implied volatility, etc.)
    - Currency and commodity data
    - Extensible architecture for new data sources
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize external data manager."""
        self.config = config or self._get_default_config()
        self.data_sources = {}
        self.cache_dir = Path("data/external")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for external data sources."""
        return {
            'macroeconomic': {
                'enabled': True,
                'indicators': [
                    'GDP', 'CPI', 'unemployment_rate', 'federal_funds_rate',
                    'treasury_yield_10y', 'treasury_yield_2y', 'dollar_index'
                ],
                'cache_duration_days': 1,  # Cache for 1 day
                'sources': {
                    'fred': {'api_key': None, 'base_url': 'https://api.stlouisfed.org/fred/series'},
                    'yahoo_finance': {'enabled': True}
                }
            },
            'sentiment': {
                'enabled': True,
                'indicators': ['VIX', 'put_call_ratio', 'high_low_index'],
                'cache_duration_days': 1
            },
            'options': {
                'enabled': False,  # Requires premium data access
                'indicators': ['implied_volatility', 'options_flow', 'gamma_exposure'],
                'cache_duration_days': 1
            },
            'currencies': {
                'enabled': True,
                'pairs': ['EURUSD', 'GBPUSD', 'JPYUSD', 'DXY'],
                'cache_duration_days': 1
            },
            'commodities': {
                'enabled': True,
                'symbols': ['GLD', 'USO', 'DBA'],  # Gold, Oil, Agriculture ETFs as proxies
                'cache_duration_days': 1
            }
        }
    
    def get_macroeconomic_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get macroeconomic indicators for the specified date range.
        
        Args:
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            DataFrame with macroeconomic indicators
        """
        logger.info("Fetching macroeconomic data")
        
        if not self.config['macroeconomic']['enabled']:
            return pd.DataFrame()
        
        macro_data = []
        indicators = self.config['macroeconomic']['indicators']
        
        # VIX as market fear indicator (available via yfinance)
        try:
            vix_data = self._get_yahoo_finance_data('^VIX', start_date, end_date)
            if not vix_data.empty:
                vix_data = vix_data.rename(columns={'Close': 'VIX'})
                macro_data.append(vix_data[['Date', 'VIX']])
        except Exception as e:
            logger.warning(f"Could not fetch VIX data: {e}")
        
        # Dollar Index (DXY)
        try:
            dxy_data = self._get_yahoo_finance_data('DX-Y.NYB', start_date, end_date)
            if not dxy_data.empty:
                dxy_data = dxy_data.rename(columns={'Close': 'DXY'})
                macro_data.append(dxy_data[['Date', 'DXY']])
        except Exception as e:
            logger.warning(f"Could not fetch DXY data: {e}")
        
        # Treasury yields (10-year)
        try:
            treasury_data = self._get_yahoo_finance_data('^TNX', start_date, end_date)
            if not treasury_data.empty:
                treasury_data = treasury_data.rename(columns={'Close': 'treasury_yield_10y'})
                macro_data.append(treasury_data[['Date', 'treasury_yield_10y']])
        except Exception as e:
            logger.warning(f"Could not fetch treasury yield data: {e}")
        
        # Combine all macro data
        if macro_data:
            combined_macro = macro_data[0]
            for data in macro_data[1:]:
                combined_macro = combined_macro.merge(data, on='Date', how='outer')
            
            # Forward fill missing values
            combined_macro = combined_macro.sort_values('Date')
            combined_macro = combined_macro.fillna(method='ffill')
            
            logger.info(f"Retrieved macroeconomic data: {list(combined_macro.columns)}")
            return combined_macro
        
        return pd.DataFrame()
    
    def get_sentiment_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get sentiment indicators for the specified date range.
        
        Args:
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            DataFrame with sentiment indicators
        """
        logger.info("Fetching sentiment data")
        
        if not self.config['sentiment']['enabled']:
            return pd.DataFrame()
        
        sentiment_data = []
        
        # VIX is already included in macro data, but we can add derived indicators
        try:
            vix_data = self._get_yahoo_finance_data('^VIX', start_date, end_date)
            if not vix_data.empty:
                # Calculate VIX percentiles as sentiment indicator
                vix_data['VIX_percentile'] = vix_data['Close'].rolling(window=252).rank(pct=True)
                vix_data['VIX_zscore'] = (vix_data['Close'] - vix_data['Close'].rolling(window=252).mean()) / vix_data['Close'].rolling(window=252).std()
                
                sentiment_data.append(vix_data[['Date', 'VIX_percentile', 'VIX_zscore']])
        except Exception as e:
            logger.warning(f"Could not calculate VIX sentiment indicators: {e}")
        
        # High-Low Index using SPY
        try:
            spy_data = self._get_yahoo_finance_data('SPY', start_date, end_date)
            if not spy_data.empty:
                # Calculate percentage of stocks near 52-week highs (simplified using SPY)
                spy_data['high_52w'] = spy_data['High'].rolling(window=252).max()
                spy_data['low_52w'] = spy_data['Low'].rolling(window=252).min()
                spy_data['high_low_index'] = (spy_data['Close'] - spy_data['low_52w']) / (spy_data['high_52w'] - spy_data['low_52w'])
                
                sentiment_data.append(spy_data[['Date', 'high_low_index']])
        except Exception as e:
            logger.warning(f"Could not calculate high-low index: {e}")
        
        # Combine sentiment data
        if sentiment_data:
            combined_sentiment = sentiment_data[0]
            for data in sentiment_data[1:]:
                combined_sentiment = combined_sentiment.merge(data, on='Date', how='outer')
            
            combined_sentiment = combined_sentiment.sort_values('Date')
            combined_sentiment = combined_sentiment.fillna(method='ffill')
            
            logger.info(f"Retrieved sentiment data: {list(combined_sentiment.columns)}")
            return combined_sentiment
        
        return pd.DataFrame()
    
    def get_currency_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get currency data for the specified date range.
        
        Args:
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            DataFrame with currency data
        """
        logger.info("Fetching currency data")
        
        if not self.config['currencies']['enabled']:
            return pd.DataFrame()
        
        currency_data = []
        
        # Currency pairs via Yahoo Finance
        currency_symbols = {
            'EURUSD': 'EURUSD=X',
            'GBPUSD': 'GBPUSD=X', 
            'JPYUSD': 'USDJPY=X',
            'DXY': 'DX-Y.NYB'
        }
        
        for currency_name, symbol in currency_symbols.items():
            try:
                data = self._get_yahoo_finance_data(symbol, start_date, end_date)
                if not data.empty:
                    data = data.rename(columns={'Close': f'{currency_name}_rate'})
                    currency_data.append(data[['Date', f'{currency_name}_rate']])
            except Exception as e:
                logger.warning(f"Could not fetch {currency_name} data: {e}")
        
        # Combine currency data
        if currency_data:
            combined_currencies = currency_data[0]
            for data in currency_data[1:]:
                combined_currencies = combined_currencies.merge(data, on='Date', how='outer')
            
            combined_currencies = combined_currencies.sort_values('Date')
            combined_currencies = combined_currencies.fillna(method='ffill')
            
            logger.info(f"Retrieved currency data: {list(combined_currencies.columns)}")
            return combined_currencies
        
        return pd.DataFrame()
    
    def get_commodity_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get commodity data for the specified date range.
        
        Args:
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            DataFrame with commodity data
        """
        logger.info("Fetching commodity data")
        
        if not self.config['commodities']['enabled']:
            return pd.DataFrame()
        
        commodity_data = []
        
        # Commodity ETFs as proxies
        commodity_symbols = {
            'Gold': 'GLD',
            'Oil': 'USO',
            'Agriculture': 'DBA'
        }
        
        for commodity_name, symbol in commodity_symbols.items():
            try:
                data = self._get_yahoo_finance_data(symbol, start_date, end_date)
                if not data.empty:
                    data = data.rename(columns={'Close': f'{commodity_name}_price'})
                    commodity_data.append(data[['Date', f'{commodity_name}_price']])
            except Exception as e:
                logger.warning(f"Could not fetch {commodity_name} data: {e}")
        
        # Combine commodity data
        if commodity_data:
            combined_commodities = commodity_data[0]
            for data in commodity_data[1:]:
                combined_commodities = combined_commodities.merge(data, on='Date', how='outer')
            
            combined_commodities = combined_commodities.sort_values('Date')
            combined_commodities = combined_commodities.fillna(method='ffill')
            
            logger.info(f"Retrieved commodity data: {list(combined_commodities.columns)}")
            return combined_commodities
        
        return pd.DataFrame()
    
    def _get_yahoo_finance_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get data from Yahoo Finance."""
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if not data.empty:
                data = data.reset_index()
                data = data.rename(columns={'Date': 'Date'})
                
                # Ensure Date column is datetime
                if 'Date' in data.columns:
                    data['Date'] = pd.to_datetime(data['Date'])
                
                return data
            
        except Exception as e:
            logger.warning(f"Error fetching Yahoo Finance data for {symbol}: {e}")
        
        return pd.DataFrame()
    
    def get_comprehensive_external_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get all available external data for the specified date range.
        
        Args:
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            Combined DataFrame with all external data
        """
        logger.info("Fetching comprehensive external data")
        
        all_data = []
        
        # Get all data types
        macro_data = self.get_macroeconomic_data(start_date, end_date)
        if not macro_data.empty:
            all_data.append(macro_data)
        
        sentiment_data = self.get_sentiment_data(start_date, end_date)
        if not sentiment_data.empty:
            all_data.append(sentiment_data)
        
        currency_data = self.get_currency_data(start_date, end_date)
        if not currency_data.empty:
            all_data.append(currency_data)
        
        commodity_data = self.get_commodity_data(start_date, end_date)
        if not commodity_data.empty:
            all_data.append(commodity_data)
        
        # Combine all external data
        if all_data:
            combined_external = all_data[0]
            for data in all_data[1:]:
                combined_external = combined_external.merge(data, on='Date', how='outer')
            
            combined_external = combined_external.sort_values('Date')
            combined_external = combined_external.fillna(method='ffill')
            
            logger.info(f"Retrieved comprehensive external data with {len(combined_external.columns)} features")
            return combined_external
        
        return pd.DataFrame()
    
    def add_external_features_to_stock_data(self, stock_data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Add external data features to stock data.
        
        Args:
            stock_data: Stock price data
            symbol: Stock symbol
            
        Returns:
            Stock data with external features added
        """
        if 'Date' not in stock_data.columns:
            logger.warning("Stock data must have 'Date' column")
            return stock_data
        
        # Get date range from stock data
        start_date = stock_data['Date'].min()
        end_date = stock_data['Date'].max()
        
        # Get external data
        external_data = self.get_comprehensive_external_data(start_date, end_date)
        
        if external_data.empty:
            logger.warning("No external data available")
            return stock_data
        
        # Merge with stock data
        enhanced_data = stock_data.merge(external_data, on='Date', how='left')
        
        # Forward fill external data (since it may not be available for all trading days)
        external_cols = [col for col in external_data.columns if col != 'Date']
        enhanced_data[external_cols] = enhanced_data[external_cols].fillna(method='ffill')
        
        logger.info(f"Added {len(external_cols)} external features to {symbol} stock data")
        return enhanced_data
    
    def get_available_features(self) -> Dict[str, List[str]]:
        """Get list of available external features by category."""
        features = {
            'macroeconomic': [],
            'sentiment': [],
            'currencies': [],
            'commodities': []
        }
        
        if self.config['macroeconomic']['enabled']:
            features['macroeconomic'] = ['VIX', 'DXY', 'treasury_yield_10y']
        
        if self.config['sentiment']['enabled']:
            features['sentiment'] = ['VIX_percentile', 'VIX_zscore', 'high_low_index']
        
        if self.config['currencies']['enabled']:
            features['currencies'] = ['EURUSD_rate', 'GBPUSD_rate', 'JPYUSD_rate', 'DXY_rate']
        
        if self.config['commodities']['enabled']:
            features['commodities'] = ['Gold_price', 'Oil_price', 'Agriculture_price']
        
        return features