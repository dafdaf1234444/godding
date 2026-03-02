"""
Macroeconomic data management for enhanced financial analysis.
Integrates interest rates, inflation, GDP, and other macro indicators.
"""
import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class MacroDataManager:
    """Manage macroeconomic data integration with financial analysis."""
    
    def __init__(self, data_dir: str = "data/macro", fred_api_key: Optional[str] = None):
        """
        Initialize macro data manager.
        
        Args:
            data_dir: Directory to store macro data
            fred_api_key: FRED API key for accessing Federal Reserve data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to get FRED API key from environment if not provided
        self.fred_api_key = fred_api_key or os.getenv('FRED_API_KEY')
        self.base_url = "https://api.stlouisfed.org/fred"
        
        # Common FRED series IDs for key indicators
        self.fred_series = {
            'fed_funds_rate': 'FEDFUNDS',
            'us_10yr_treasury': 'GS10',
            'us_2yr_treasury': 'GS2', 
            'us_3m_treasury': 'GS3M',
            'cpi_inflation': 'CPIAUCSL',
            'core_cpi': 'CPILFESL',
            'ppi_inflation': 'PPIACO',  # Producer Price Index - All Commodities
            'core_ppi': 'PPIFIS',       # Producer Price Index - Final Demand less Foods and Energy
            'pce_inflation': 'PCEPI',   # Personal Consumption Expenditures Price Index
            'core_pce': 'PCEPILFE',     # Core PCE (Fed's preferred inflation measure)
            'unemployment_rate': 'UNRATE',
            'gdp_growth': 'GDP',
            'real_gdp': 'GDPC1',
            'vix_index': 'VIXCLS',
            'dxy_dollar_index': 'DEXUSEU',  # USD/EUR exchange rate
            'oil_prices': 'DCOILWTICO',
            'gold_prices': 'GOLDAMGBD228NLBM',
            'consumer_sentiment': 'UMCSENT',  # University of Michigan Consumer Sentiment
            'housing_starts': 'HOUST',       # Housing Starts
            'industrial_production': 'INDPRO' # Industrial Production Index
        }
        
        # Yahoo Finance fallback symbols (more reliable for recent data)
        self.yfinance_symbols = {
            'vix': '^VIX',
            'us_10yr_treasury': '^TNX',
            'us_5yr_treasury': '^FVX', 
            'us_3m_treasury': '^IRX',
            'dollar_index': 'DX-Y.NYB',
            'oil': 'CL=F',
            'gold': 'GC=F',
            'sp500': '^GSPC',
            'nasdaq': '^IXIC'
        }
    
    def download_fred_data(self, series_id: str, start_date: str, end_date: str,
                          frequency: str = 'daily') -> pd.DataFrame:
        """
        Download data from FRED API.
        
        Args:
            series_id: FRED series identifier
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            frequency: Data frequency (daily, weekly, monthly, quarterly, annual)
            
        Returns:
            DataFrame with date index and values
        """
        if not self.fred_api_key:
            logger.error("FRED API key not provided")
            return pd.DataFrame()
        
        try:
            params = {
                'series_id': series_id,
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'observation_start': start_date,
                'observation_end': end_date,
                'frequency': frequency.lower()[0] if frequency != 'daily' else 'd',
                'sort_order': 'asc'
            }
            
            url = f"{self.base_url}/series/observations"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get('observations', [])
            
            if not observations:
                logger.warning(f"No data returned for series {series_id}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(observations)
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            # Set date as index and clean data
            df = df.set_index('date')[['value']].dropna()
            df.columns = [series_id]
            
            logger.info(f"Downloaded {len(df)} observations for {series_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error downloading FRED data for {series_id}: {e}")
            return pd.DataFrame()
    
    def download_yfinance_fallback(self, symbol: str, period: str = '2y') -> pd.DataFrame:
        """
        Download macro data using yfinance as fallback.
        
        Args:
            symbol: Yahoo Finance symbol
            period: Data period (1y, 2y, 5y, max)
            
        Returns:
            DataFrame with date index and close prices
        """
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if not data.empty:
                # Return just the Close price with proper naming
                df = pd.DataFrame(data['Close'])
                df.columns = [symbol]
                logger.info(f"Downloaded {len(df)} observations for {symbol} via yfinance")
                return df
            else:
                logger.warning(f"No data returned for {symbol} via yfinance")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error downloading yfinance data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_essential_market_data(self, period: str = '2y') -> Dict[str, pd.DataFrame]:
        """
        Get essential market data using yfinance (reliable and free).
        Focus on high-signal indicators only.
        
        Args:
            period: Data period (1y, 2y, 5y, max)
            
        Returns:
            Dictionary with market data
        """
        market_data = {}
        
        # Essential indicators for quant analysis
        essential_symbols = {
            'VIX': '^VIX',           # Volatility regime
            '10Y_Treasury': '^TNX',   # Interest rate level
            '5Y_Treasury': '^FVX',    # For yield curve slope
            '3M_Treasury': '^IRX',    # Short rate
            'Dollar_Index': 'DX-Y.NYB',  # USD strength
            'Oil': 'CL=F',           # Commodity proxy
            'Gold': 'GC=F'           # Safe haven
        }
        
        for name, symbol in essential_symbols.items():
            try:
                data = self.download_yfinance_fallback(symbol, period)
                if not data.empty:
                    market_data[name] = data
                    
                    # Calculate additional indicators
                    if name in ['10Y_Treasury', '5Y_Treasury', '3M_Treasury']:
                        # Convert to percentage if needed and add regime indicators
                        prices = data.iloc[:, 0]
                        market_data[f'{name}_regime'] = self._classify_rate_regime(prices)
                
                time.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"Failed to download {name} ({symbol}): {e}")
        
        # Calculate yield curve slope if we have the data
        if '10Y_Treasury' in market_data and '5Y_Treasury' in market_data:
            try:
                tnx = market_data['10Y_Treasury'].iloc[:, 0]
                fvx = market_data['5Y_Treasury'].iloc[:, 0]
                
                # Align dates and calculate spread
                common_idx = tnx.index.intersection(fvx.index)
                if len(common_idx) > 0:
                    spread = tnx.loc[common_idx] - fvx.loc[common_idx]
                    market_data['Yield_Curve_Slope'] = pd.DataFrame(spread, columns=['10Y-5Y'])
                    
                    # Add inversion indicator
                    inversion = (spread < 0).astype(int)
                    market_data['Yield_Curve_Inverted'] = pd.DataFrame(inversion, columns=['Inverted'])
                    
            except Exception as e:
                logger.warning(f"Error calculating yield curve slope: {e}")
        
        logger.info(f"Downloaded {len(market_data)} essential market indicators")
        return market_data
    
    def _classify_rate_regime(self, rates: pd.Series) -> pd.DataFrame:
        """Classify interest rate regime (rising/falling/stable)."""
        try:
            # Calculate 30-day rate change
            rate_change = rates.diff(periods=30)
            
            # Classify regime
            regime = pd.cut(rate_change, 
                          bins=[-float('inf'), -0.1, 0.1, float('inf')],
                          labels=['falling', 'stable', 'rising'])
            
            return pd.DataFrame(regime, columns=['Rate_Regime'])
        except:
            return pd.DataFrame()
    
    def get_interest_rates_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get comprehensive interest rates data.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DataFrame with various interest rates
        """
        rates_data = []
        rate_series = {
            'fed_funds_rate': self.fred_series['fed_funds_rate'],
            'us_10yr_treasury': self.fred_series['us_10yr_treasury'],
            'us_2yr_treasury': self.fred_series['us_2yr_treasury'],
            'us_3m_treasury': self.fred_series['us_3m_treasury']
        }
        
        for rate_name, series_id in rate_series.items():
            df = self.download_fred_data(series_id, start_date, end_date, 'daily')
            if not df.empty:
                df.columns = [rate_name]
                rates_data.append(df)
            
            # Rate limiting for API calls
            time.sleep(0.5)
        
        if rates_data:
            combined_rates = pd.concat(rates_data, axis=1, sort=True)
            
            # Forward fill missing values (weekends/holidays)
            combined_rates = combined_rates.ffill()
            
            # Save to cache
            cache_file = self.data_dir / f"interest_rates_{start_date}_{end_date}.parquet"
            combined_rates.to_parquet(cache_file)
            
            return combined_rates
        
        return pd.DataFrame()
    
    def get_inflation_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get comprehensive inflation indicators data including CPI, PPI, and PCE.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DataFrame with inflation indicators and year-over-year changes
        """
        inflation_data = []
        inflation_series = {
            'cpi_inflation': self.fred_series['cpi_inflation'],
            'core_cpi': self.fred_series['core_cpi'],
            'ppi_inflation': self.fred_series['ppi_inflation'],
            'core_ppi': self.fred_series['core_ppi'],
            'pce_inflation': self.fred_series['pce_inflation'],
            'core_pce': self.fred_series['core_pce']
        }
        
        for indicator, series_id in inflation_series.items():
            try:
                df = self.download_fred_data(series_id, start_date, end_date, 'monthly')
                if not df.empty:
                    df.columns = [indicator]
                    
                    # Calculate year-over-year changes for inflation rates
                    df[f'{indicator}_yoy'] = df[indicator].pct_change(12) * 100
                    
                    # Calculate month-over-month changes
                    df[f'{indicator}_mom'] = df[indicator].pct_change(1) * 100
                    
                    inflation_data.append(df)
                    logger.info(f"Downloaded {indicator} data: {len(df)} records")
                
                time.sleep(0.5)  # Rate limiting for API calls
                
            except Exception as e:
                logger.warning(f"Could not download {indicator} data: {e}")
        
        if inflation_data:
            combined_inflation = pd.concat(inflation_data, axis=1, sort=True)
            
            # Save to cache
            cache_file = self.data_dir / f"inflation_data_{start_date}_{end_date}.parquet"
            combined_inflation.to_parquet(cache_file)
            
            return combined_inflation
        
        return pd.DataFrame()
    
    def get_economic_indicators(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Get broader economic indicators."""
        economic_data = []
        economic_series = {
            'unemployment_rate': self.fred_series['unemployment_rate'],
            'vix_index': self.fred_series['vix_index'],
            'oil_prices': self.fred_series['oil_prices'],
            'gold_prices': self.fred_series['gold_prices']
        }
        
        for indicator, series_id in economic_series.items():
            frequency = 'monthly' if indicator == 'unemployment_rate' else 'daily'
            df = self.download_fred_data(series_id, start_date, end_date, frequency)
            
            if not df.empty:
                df.columns = [indicator]
                economic_data.append(df)
            
            time.sleep(0.5)
        
        if economic_data:
            combined_economic = pd.concat(economic_data, axis=1, sort=True)
            
            # Forward fill for alignment with daily stock data
            combined_economic = combined_economic.fillna(method='ffill')
            
            # Save to cache
            cache_file = self.data_dir / f"economic_indicators_{start_date}_{end_date}.parquet"
            combined_economic.to_parquet(cache_file)
            
            return combined_economic
        
        return pd.DataFrame()
    
    def load_cached_data(self, data_type: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Load cached macro data if available."""
        cache_file = self.data_dir / f"{data_type}_{start_date}_{end_date}.parquet"
        
        if cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)
                logger.info(f"Loaded cached {data_type} data from {cache_file}")
                return df
            except Exception as e:
                logger.warning(f"Error loading cached data: {e}")
        
        return None
    
    def get_yield_curve_data(self, date: str) -> Dict[str, float]:
        """
        Get yield curve data for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            Dictionary with maturity -> yield mapping
        """
        yield_series = {
            '3M': 'GS3M',
            '6M': 'GS6M', 
            '1Y': 'GS1',
            '2Y': 'GS2',
            '3Y': 'GS3',
            '5Y': 'GS5',
            '7Y': 'GS7',
            '10Y': 'GS10',
            '20Y': 'GS20',
            '30Y': 'GS30'
        }
        
        yield_curve = {}
        
        for maturity, series_id in yield_series.items():
            df = self.download_fred_data(series_id, date, date, 'daily')
            if not df.empty and len(df) > 0:
                yield_curve[maturity] = df.iloc[0, 0]
            time.sleep(0.3)
        
        return yield_curve
    
    def calculate_regime_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate regime indicators from macro data."""
        regime_data = data.copy()
        
        # Yield curve slope (10Y - 2Y spread)
        if 'us_10yr_treasury' in data.columns and 'us_2yr_treasury' in data.columns:
            regime_data['yield_curve_slope'] = data['us_10yr_treasury'] - data['us_2yr_treasury']
            regime_data['inverted_yield_curve'] = (regime_data['yield_curve_slope'] < 0).astype(int)
        
        # Interest rate regime (rising/falling/stable)
        if 'fed_funds_rate' in data.columns:
            fed_rate_change = data['fed_funds_rate'].diff(periods=30)  # 30-day change
            regime_data['rate_regime'] = pd.cut(fed_rate_change, 
                                              bins=[-float('inf'), -0.1, 0.1, float('inf')],
                                              labels=['falling', 'stable', 'rising'])
        
        # Volatility regime
        if 'vix_index' in data.columns:
            vix_ma = data['vix_index'].rolling(window=20).mean()
            regime_data['volatility_regime'] = pd.cut(vix_ma,
                                                    bins=[0, 20, 30, float('inf')],
                                                    labels=['low', 'moderate', 'high'])
        
        return regime_data
    
    def validate_temporal_integrity(self, data: pd.DataFrame, 
                                  reference_date: datetime) -> bool:
        """
        Validate that macro data doesn't contain future information.
        
        Args:
            data: Macro data DataFrame
            reference_date: Reference date for validation
            
        Returns:
            True if data integrity is maintained
        """
        try:
            if data.empty:
                return True
            
            latest_data_date = data.index.max()
            
            # Allow for some lag in data publication (max 7 days)
            max_allowed_date = reference_date + timedelta(days=7)
            
            if latest_data_date <= max_allowed_date:
                return True
            else:
                logger.error(f"Temporal integrity violation: data contains future information. "
                           f"Latest data: {latest_data_date}, Reference: {reference_date}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating temporal integrity: {e}")
            return False