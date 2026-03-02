"""
Currency conversion utilities for international stock analysis.
Provides real-time and historical currency conversion using multiple data sources.
"""
import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path
import requests
import json
from dataclasses import dataclass

from .storage import ParquetStorage

logger = logging.getLogger(__name__)


@dataclass
class CurrencyRate:
    """Currency exchange rate with metadata."""
    from_currency: str
    to_currency: str
    rate: float
    date: datetime
    source: str
    bid: Optional[float] = None
    ask: Optional[float] = None


class CurrencyConverter:
    """
    Multi-source currency converter for international stock analysis.
    
    Features:
    - Real-time currency rates from multiple sources
    - Historical currency data for backtesting
    - Automatic rate caching and updates
    - Support for major currency pairs
    - Point-in-time conversion for historical analysis
    """
    
    def __init__(self, data_dir: str = "data/currencies", cache_hours: int = 1):
        """
        Initialize currency converter.
        
        Args:
            data_dir: Directory to store currency data
            cache_hours: Hours to cache currency rates
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.storage = ParquetStorage(str(self.data_dir))
        self.cache_hours = cache_hours
        
        # Major currency pairs and their sources
        self.major_pairs = {
            'EUR': 'EURUSD=X',
            'GBP': 'GBPUSD=X', 
            'JPY': 'JPY=X',
            'CHF': 'CHF=X',
            'CAD': 'CAD=X',
            'AUD': 'AUD=X',
            'NZD': 'NZD=X',
            'CNY': 'CNY=X',
            'HKD': 'HKD=X',
            'SGD': 'SGD=X',
            'KRW': 'KRW=X',
            'TWD': 'TWD=X',
            'INR': 'INR=X',
            'BRL': 'BRL=X',
            'MXN': 'MXN=X'
        }
        
        # Stock exchange default currencies
        self.exchange_currencies = {
            'NYSE': 'USD',
            'NASDAQ': 'USD',
            'LSE': 'GBP',
            'XETRA': 'EUR',
            'FRA': 'EUR',
            'AMS': 'EUR',
            'EPA': 'EUR',
            'BME': 'EUR',
            'TSE': 'JPY',
            'HKEX': 'HKD',
            'SSE': 'CNY',
            'SZSE': 'CNY',
            'KRX': 'KRW',
            'ASX': 'AUD',
            'TSX': 'CAD',
            'BSE': 'INR',
            'NSE': 'INR'
        }
        
        # Symbol suffix to exchange mapping
        self.suffix_to_exchange = {
            '.L': 'LSE',
            '.DE': 'XETRA', 
            '.PA': 'EPA',
            '.AS': 'AMS',
            '.MC': 'BME',
            '.T': 'TSE',
            '.HK': 'HKEX',
            '.SS': 'SSE',
            '.SZ': 'SZSE',
            '.KS': 'KRX',
            '.AX': 'ASX',
            '.TO': 'TSX',
            '.BO': 'BSE',
            '.NS': 'NSE'
        }
        
    def get_symbol_currency(self, symbol: str) -> str:
        """
        Determine the currency for a stock symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'ASML.AS', '7974.T')
            
        Returns:
            Currency code (e.g., 'USD', 'EUR', 'JPY')
        """
        # Check for suffix indicating exchange
        for suffix, exchange in self.suffix_to_exchange.items():
            if symbol.endswith(suffix):
                return self.exchange_currencies.get(exchange, 'USD')
        
        # Special cases for indices
        if symbol.startswith('^'):
            index_currencies = {
                '^GSPC': 'USD',  # S&P 500
                '^DJI': 'USD',   # Dow Jones
                '^IXIC': 'USD',  # NASDAQ
                '^FTSE': 'GBP',  # FTSE 100
                '^GDAXI': 'EUR', # DAX
                '^FCHI': 'EUR',  # CAC 40
                '^STOXX50E': 'EUR', # Euro Stoxx 50
                '^N225': 'JPY',  # Nikkei 225
                '^HSI': 'HKD',   # Hang Seng
                '^STI': 'SGD',   # Straits Times
                '^TWII': 'TWD',  # Taiwan Weighted
                '^KS11': 'KRW'   # KOSPI
            }
            return index_currencies.get(symbol, 'USD')
        
        # Default to USD for unknown symbols
        return 'USD'
    
    def get_current_rate(self, from_currency: str, to_currency: str = 'USD') -> Optional[CurrencyRate]:
        """
        Get current exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Current exchange rate or None if not available
        """
        if from_currency == to_currency:
            return CurrencyRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=1.0,
                date=datetime.now(),
                source='identity'
            )
        
        # Check cache first
        cached_rate = self._get_cached_rate(from_currency, to_currency)
        if cached_rate:
            return cached_rate
        
        # Try to fetch from yfinance
        rate = self._fetch_rate_yfinance(from_currency, to_currency)
        if rate:
            self._cache_rate(rate)
            return rate
        
        # Try alternative sources if available
        rate = self._fetch_rate_alternative(from_currency, to_currency)
        if rate:
            self._cache_rate(rate)
            return rate
        
        logger.warning(f"Could not fetch rate for {from_currency}/{to_currency}")
        return None
    
    def get_historical_rates(self, from_currency: str, to_currency: str = 'USD', 
                           start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """
        Get historical exchange rates between two currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            DataFrame with historical rates
        """
        if from_currency == to_currency:
            # Create identity rates
            if start_date is None:
                start_date = datetime.now() - timedelta(days=365)
            if end_date is None:
                end_date = datetime.now()
                
            dates = pd.date_range(start_date, end_date, freq='D')
            return pd.DataFrame({
                'Date': dates,
                'Rate': 1.0,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'source': 'identity'
            })
        
        # Try to load from cache/storage
        symbol = self._get_currency_symbol(from_currency, to_currency)
        try:
            cached_data = self.storage.load_stock_data(symbol)
            if not cached_data.empty:
                # Filter by date range if specified
                if start_date:
                    cached_data = cached_data[cached_data['Date'] >= start_date]
                if end_date:
                    cached_data = cached_data[cached_data['Date'] <= end_date]
                
                if not cached_data.empty:
                    return cached_data[['Date', 'Close']].rename(columns={'Close': 'Rate'})
        except:
            pass
        
        # Fetch fresh data
        return self._fetch_historical_rates(from_currency, to_currency, start_date, end_date)
    
    def convert_price(self, price: float, from_currency: str, to_currency: str = 'USD', 
                     date: Optional[datetime] = None) -> Optional[float]:
        """
        Convert a price from one currency to another.
        
        Args:
            price: Price to convert
            from_currency: Source currency
            to_currency: Target currency
            date: Optional date for historical conversion
            
        Returns:
            Converted price or None if conversion failed
        """
        if from_currency == to_currency:
            return price
        
        if date:
            # Historical conversion
            rates = self.get_historical_rates(from_currency, to_currency)
            if rates.empty:
                return None
            
            # Find closest date
            rates['Date'] = pd.to_datetime(rates['Date'])
            closest_idx = (rates['Date'] - date).abs().idxmin()
            rate = rates.loc[closest_idx, 'Rate']
        else:
            # Current conversion
            rate_obj = self.get_current_rate(from_currency, to_currency)
            if not rate_obj:
                return None
            rate = rate_obj.rate
        
        return price * rate
    
    def convert_dataframe(self, df: pd.DataFrame, price_columns: List[str], 
                         from_currency: str, to_currency: str = 'USD') -> pd.DataFrame:
        """
        Convert price columns in a DataFrame to target currency.
        
        Args:
            df: DataFrame with price data
            price_columns: List of columns to convert
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            DataFrame with converted prices
        """
        if from_currency == to_currency:
            return df.copy()
        
        df_converted = df.copy()
        
        # Get historical rates
        start_date = df['Date'].min() if 'Date' in df.columns else None
        end_date = df['Date'].max() if 'Date' in df.columns else None
        
        rates_df = self.get_historical_rates(from_currency, to_currency, start_date, end_date)
        
        if rates_df.empty:
            logger.warning(f"No rates available for {from_currency}/{to_currency}")
            return df_converted
        
        # Merge rates with data (handle timezone issues)
        rates_df['Date'] = pd.to_datetime(rates_df['Date']).dt.tz_localize(None)
        df_converted['Date'] = pd.to_datetime(df_converted['Date']).dt.tz_localize(None)
        
        merged = df_converted.merge(rates_df[['Date', 'Rate']], on='Date', how='left')
        
        # Forward fill missing rates
        merged['Rate'] = merged['Rate'].ffill()
        
        # Convert price columns
        for col in price_columns:
            if col in merged.columns:
                merged[col] = merged[col] * merged['Rate']
        
        # Add currency metadata
        merged['original_currency'] = from_currency
        merged['converted_currency'] = to_currency
        
        return merged.drop('Rate', axis=1)
    
    def _get_currency_symbol(self, from_currency: str, to_currency: str) -> str:
        """Get the yfinance symbol for a currency pair."""
        if to_currency == 'USD':
            return self.major_pairs.get(from_currency, f"{from_currency}USD=X")
        elif from_currency == 'USD':
            # Invert the pair
            return self.major_pairs.get(to_currency, f"USD{to_currency}=X")
        else:
            # Cross currency pair
            return f"{from_currency}{to_currency}=X"
    
    def _fetch_rate_yfinance(self, from_currency: str, to_currency: str) -> Optional[CurrencyRate]:
        """Fetch current rate using yfinance."""
        try:
            symbol = self._get_currency_symbol(from_currency, to_currency)
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', interval='1m')
            
            if data.empty:
                return None
            
            latest_rate = data['Close'].iloc[-1]
            latest_time = data.index[-1].to_pydatetime()
            
            # Handle inverted pairs
            if to_currency != 'USD' and from_currency == 'USD':
                latest_rate = 1.0 / latest_rate
            
            return CurrencyRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=latest_rate,
                date=latest_time,
                source='yfinance'
            )
            
        except Exception as e:
            logger.debug(f"yfinance rate fetch failed for {from_currency}/{to_currency}: {e}")
            return None
    
    def _fetch_rate_alternative(self, from_currency: str, to_currency: str) -> Optional[CurrencyRate]:
        """Fetch rate from alternative sources."""
        # For now, just return None. Can be extended with additional APIs
        # like exchangerate-api.com, fixer.io, etc.
        return None
    
    def _fetch_historical_rates(self, from_currency: str, to_currency: str,
                              start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """Fetch historical rates and cache them."""
        try:
            symbol = self._get_currency_symbol(from_currency, to_currency)
            
            # Default to 2 years of data
            if start_date is None:
                start_date = datetime.now() - timedelta(days=730)
            if end_date is None:
                end_date = datetime.now()
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                return pd.DataFrame()
            
            # Prepare data for storage
            rates_df = data.reset_index()
            rates_df = rates_df[['Date', 'Close']].copy()
            rates_df.columns = ['Date', 'Rate']
            
            # Handle inverted pairs
            if to_currency != 'USD' and from_currency == 'USD':
                rates_df['Rate'] = 1.0 / rates_df['Rate']
            
            # Add metadata
            rates_df['from_currency'] = from_currency
            rates_df['to_currency'] = to_currency
            rates_df['source'] = 'yfinance'
            
            # Cache the data
            metadata = {
                'symbol': symbol,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'source': 'yfinance',
                'last_updated': datetime.now().isoformat(),
                'data_type': 'currency_rates'
            }
            
            # Save to storage
            self.storage.save_stock_data(rates_df, symbol, metadata, "latest")
            
            return rates_df
            
        except Exception as e:
            logger.error(f"Failed to fetch historical rates for {from_currency}/{to_currency}: {e}")
            return pd.DataFrame()
    
    def _get_cached_rate(self, from_currency: str, to_currency: str) -> Optional[CurrencyRate]:
        """Get cached current rate if still valid."""
        try:
            symbol = self._get_currency_symbol(from_currency, to_currency)
            cached_data = self.storage.load_stock_data(symbol)
            
            if cached_data.empty:
                return None
            
            # Check if cache is still valid
            latest_date = pd.to_datetime(cached_data['Date']).max()
            age_hours = (datetime.now() - latest_date).total_seconds() / 3600
            
            if age_hours > self.cache_hours:
                return None
            
            latest_rate = cached_data.loc[cached_data['Date'].idxmax(), 'Rate']
            
            return CurrencyRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=latest_rate,
                date=latest_date,
                source='cache'
            )
            
        except Exception as e:
            logger.debug(f"Cache lookup failed for {from_currency}/{to_currency}: {e}")
            return None
    
    def _cache_rate(self, rate: CurrencyRate) -> None:
        """Cache a single rate."""
        try:
            symbol = self._get_currency_symbol(rate.from_currency, rate.to_currency)
            
            # Create single-row DataFrame
            rate_df = pd.DataFrame([{
                'Date': rate.date,
                'Rate': rate.rate,
                'from_currency': rate.from_currency,
                'to_currency': rate.to_currency,
                'source': rate.source
            }])
            
            metadata = {
                'symbol': symbol,
                'from_currency': rate.from_currency,
                'to_currency': rate.to_currency,
                'source': rate.source,
                'last_updated': datetime.now().isoformat(),
                'data_type': 'currency_rates'
            }
            
            # Append to existing data or create new
            try:
                existing = self.storage.load_stock_data(symbol)
                if not existing.empty:
                    # Remove duplicates and append
                    existing['Date'] = pd.to_datetime(existing['Date'])
                    rate_df['Date'] = pd.to_datetime(rate_df['Date'])
                    
                    combined = pd.concat([existing, rate_df]).drop_duplicates(subset=['Date'])
                    combined = combined.sort_values('Date')
                    rate_df = combined
            except:
                pass
            
            self.storage.save_stock_data(rate_df, symbol, metadata, "latest")
            
        except Exception as e:
            logger.debug(f"Failed to cache rate: {e}")
    
    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies."""
        return list(self.major_pairs.keys()) + ['USD']
    
    def get_conversion_summary(self, symbols: List[str], target_currency: str = 'USD') -> pd.DataFrame:
        """
        Get currency conversion summary for a list of symbols.
        
        Args:
            symbols: List of stock symbols
            target_currency: Target currency for conversion
            
        Returns:
            DataFrame with conversion information
        """
        summary_data = []
        
        for symbol in symbols:
            original_currency = self.get_symbol_currency(symbol)
            current_rate = self.get_current_rate(original_currency, target_currency)
            
            summary_data.append({
                'symbol': symbol,
                'original_currency': original_currency,
                'target_currency': target_currency,
                'current_rate': current_rate.rate if current_rate else None,
                'rate_date': current_rate.date if current_rate else None,
                'needs_conversion': original_currency != target_currency
            })
        
        return pd.DataFrame(summary_data)


class PortfolioCurrencyManager:
    """
    Manage currency conversions for portfolio analysis.
    Handles multi-currency portfolios and provides unified currency reporting.
    """
    
    def __init__(self, base_currency: str = 'USD', converter: CurrencyConverter = None):
        """
        Initialize portfolio currency manager.
        
        Args:
            base_currency: Base currency for portfolio reporting
            converter: Currency converter instance
        """
        self.base_currency = base_currency
        self.converter = converter or CurrencyConverter()
        self.converted_cache = {}
        
    def normalize_portfolio_data(self, portfolio_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Convert all portfolio data to base currency.
        
        Args:
            portfolio_data: Dictionary of {symbol: dataframe}
            
        Returns:
            Dictionary with currency-normalized data
        """
        normalized = {}
        
        for symbol, df in portfolio_data.items():
            original_currency = self.converter.get_symbol_currency(symbol)
            
            if original_currency == self.base_currency:
                normalized[symbol] = df.copy()
            else:
                # Convert price columns
                price_columns = ['Open', 'High', 'Low', 'Close', 'Adj Close']
                available_price_columns = [col for col in price_columns if col in df.columns]
                
                if available_price_columns:
                    converted_df = self.converter.convert_dataframe(
                        df, available_price_columns, original_currency, self.base_currency
                    )
                    normalized[symbol] = converted_df
                    
                    logger.info(f"Converted {symbol} from {original_currency} to {self.base_currency}")
                else:
                    normalized[symbol] = df.copy()
                    logger.warning(f"No price columns found for {symbol} conversion")
        
        return normalized
    
    def get_portfolio_summary(self, symbols: List[str]) -> pd.DataFrame:
        """Get portfolio currency summary."""
        return self.converter.get_conversion_summary(symbols, self.base_currency)