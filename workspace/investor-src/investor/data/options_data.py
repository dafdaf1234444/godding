"""
Options data downloader and processor for financial options data.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass

from .base.interfaces import IDataProvider, DataRequest, DataResponse, DataProviderType, DataStatus, ValidationResult
from .base.cache_manager import UnifiedCacheManager

logger = logging.getLogger(__name__)


@dataclass
class OptionsRequest:
    """Options-specific data request."""
    symbol: str
    expiration_dates: Optional[List[str]] = None  # If None, get all available
    include_greeks: bool = True
    include_volume: bool = True
    include_open_interest: bool = True


@dataclass
class OptionsContract:
    """Options contract data structure."""
    symbol: str
    strike: float
    expiration: str
    option_type: str  # 'call' or 'put'
    last_price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    implied_volatility: float
    in_the_money: bool
    last_trade_date: Optional[datetime] = None
    
    
@dataclass
class OptionsChain:
    """Complete options chain for a symbol."""
    symbol: str
    underlying_price: float
    expiration_dates: List[str]
    calls: Dict[str, List[OptionsContract]]  # expiration -> contracts
    puts: Dict[str, List[OptionsContract]]   # expiration -> contracts
    download_time: datetime


class OptionsDataProvider(IDataProvider):
    """Provider for options data using yfinance."""
    
    def __init__(self, cache_manager: UnifiedCacheManager = None):
        """Initialize options data provider."""
        self.cache_manager = cache_manager
        
    @property
    def provider_type(self) -> DataProviderType:
        """Get the type of this data provider."""
        return DataProviderType.EXTERNAL  # Options are external derivative data
    
    @property
    def supported_symbols(self) -> List[str]:
        """Get list of supported symbols (dynamic for options)."""
        return []  # Dynamic support based on yfinance capabilities
    
    def download_data(self, request: DataRequest) -> DataResponse:
        """Download options data for the specified symbols."""
        start_time = datetime.now()
        errors = []
        data = {}
        
        valid_symbols = self.validate_symbols(request.symbols)
        if not valid_symbols:
            return DataResponse(
                data={},
                metadata={'error': 'No valid symbols found'},
                status=DataStatus.FAILED,
                provider_type=self.provider_type,
                timestamp=start_time,
                errors=['No valid symbols provided']
            )
        
        for symbol in valid_symbols:
            try:
                options_chain = self._download_options_chain(symbol)
                if options_chain:
                    data[symbol] = self._convert_chain_to_dataframe(options_chain)
                else:
                    errors.append(f"No options data found for {symbol}")
                    
            except Exception as e:
                error_msg = f"Error downloading options for {symbol}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        status = DataStatus.LATEST if data else DataStatus.FAILED
        
        return DataResponse(
            data=data,
            metadata={
                'download_time': datetime.now().isoformat(),
                'provider': 'yfinance_options',
                'data_type': 'options_chain',
                'successful_symbols': list(data.keys())
            },
            status=status,
            provider_type=self.provider_type,
            timestamp=start_time,
            errors=errors if errors else None
        )
    
    def validate_symbols(self, symbols: List[str]) -> List[str]:
        """Validate symbols for options data availability."""
        valid_symbols = []
        
        for symbol in symbols:
            if not symbol or not isinstance(symbol, str):
                continue
                
            try:
                # Quick check if symbol has options
                ticker = yf.Ticker(symbol)
                if hasattr(ticker, 'options') and ticker.options:
                    valid_symbols.append(symbol.upper())
                else:
                    logger.warning(f"No options found for symbol {symbol}")
                    
            except Exception as e:
                logger.warning(f"Cannot validate options for {symbol}: {str(e)}")
                
        return valid_symbols
    
    def validate_data(self, data: pd.DataFrame, symbol: str) -> ValidationResult:
        """Validate options data quality."""
        if data is None or data.empty:
            return ValidationResult(
                valid=False,
                errors=[f"No options data found for symbol {symbol}"]
            )
        
        errors = []
        warnings = []
        
        # Check required columns
        required_columns = ['strike', 'expiration', 'option_type', 'last_price', 'implied_volatility']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        # Check data types and ranges
        if 'strike' in data.columns:
            if data['strike'].dtype not in [np.float64, np.int64]:
                warnings.append("Strike prices should be numeric")
            if (data['strike'] <= 0).any():
                warnings.append("Found non-positive strike prices")
        
        if 'implied_volatility' in data.columns:
            iv_data = data['implied_volatility'].dropna()
            if len(iv_data) > 0:
                if (iv_data < 0).any() or (iv_data > 10).any():
                    warnings.append("Implied volatility values outside reasonable range (0-10)")
        
        if 'last_price' in data.columns:
            if (data['last_price'] < 0).any():
                warnings.append("Found negative option prices")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors if errors else None,
            warnings=warnings if warnings else None,
            metadata={
                'rows': len(data),
                'columns': list(data.columns),
                'option_types': data['option_type'].unique().tolist() if 'option_type' in data.columns else [],
                'expiration_dates': data['expiration'].unique().tolist() if 'expiration' in data.columns else []
            }
        )
    
    def _download_options_chain(self, symbol: str) -> Optional[OptionsChain]:
        """Download complete options chain for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current price
            info = ticker.info
            current_price = info.get('regularMarketPrice', info.get('previousClose', 0))
            
            if not current_price:
                # Fallback: get recent price from history
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    logger.warning(f"Cannot determine current price for {symbol}")
                    return None
            
            # Get expiration dates
            expiration_dates = ticker.options
            if not expiration_dates:
                logger.warning(f"No options expiration dates found for {symbol}")
                return None
            
            calls = {}
            puts = {}
            
            for exp_date in expiration_dates:
                try:
                    option_chain = ticker.option_chain(exp_date)
                    
                    # Process calls
                    if not option_chain.calls.empty:
                        calls[exp_date] = self._process_options_data(
                            option_chain.calls, symbol, exp_date, 'call', current_price
                        )
                    
                    # Process puts
                    if not option_chain.puts.empty:
                        puts[exp_date] = self._process_options_data(
                            option_chain.puts, symbol, exp_date, 'put', current_price
                        )
                        
                except Exception as e:
                    logger.warning(f"Error processing expiration {exp_date} for {symbol}: {str(e)}")
                    continue
            
            return OptionsChain(
                symbol=symbol,
                underlying_price=current_price,
                expiration_dates=list(expiration_dates),
                calls=calls,
                puts=puts,
                download_time=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error downloading options chain for {symbol}: {str(e)}")
            return None
    
    def _process_options_data(self, options_df: pd.DataFrame, symbol: str, expiration: str, 
                            option_type: str, underlying_price: float) -> List[OptionsContract]:
        """Process raw options data into OptionsContract objects."""
        contracts = []
        
        for _, row in options_df.iterrows():
            try:
                contract = OptionsContract(
                    symbol=symbol,
                    strike=float(row.get('strike', 0)),
                    expiration=expiration,
                    option_type=option_type,
                    last_price=float(row.get('lastPrice', 0)),
                    bid=float(row.get('bid', 0)),
                    ask=float(row.get('ask', 0)),
                    volume=int(row.get('volume', 0)) if pd.notna(row.get('volume', 0)) else 0,
                    open_interest=int(row.get('openInterest', 0)) if pd.notna(row.get('openInterest', 0)) else 0,
                    implied_volatility=float(row.get('impliedVolatility', 0)) if pd.notna(row.get('impliedVolatility', 0)) else 0,
                    in_the_money=bool(row.get('inTheMoney', False)),
                    last_trade_date=pd.to_datetime(row.get('lastTradeDate')) if pd.notna(row.get('lastTradeDate')) else None
                )
                contracts.append(contract)
                
            except Exception as e:
                logger.warning(f"Error processing options contract: {str(e)}")
                continue
        
        return contracts
    
    def _convert_chain_to_dataframe(self, options_chain: OptionsChain) -> pd.DataFrame:
        """Convert OptionsChain to pandas DataFrame."""
        all_contracts = []
        
        # Add all calls
        for exp_date, contracts in options_chain.calls.items():
            for contract in contracts:
                all_contracts.append({
                    'symbol': contract.symbol,
                    'underlying_price': options_chain.underlying_price,
                    'strike': contract.strike,
                    'expiration': contract.expiration,
                    'option_type': contract.option_type,
                    'last_price': contract.last_price,
                    'bid': contract.bid,
                    'ask': contract.ask,
                    'volume': contract.volume,
                    'open_interest': contract.open_interest,
                    'implied_volatility': contract.implied_volatility,
                    'in_the_money': contract.in_the_money,
                    'last_trade_date': contract.last_trade_date,
                    'download_time': options_chain.download_time
                })
        
        # Add all puts
        for exp_date, contracts in options_chain.puts.items():
            for contract in contracts:
                all_contracts.append({
                    'symbol': contract.symbol,
                    'underlying_price': options_chain.underlying_price,
                    'strike': contract.strike,
                    'expiration': contract.expiration,
                    'option_type': contract.option_type,
                    'last_price': contract.last_price,
                    'bid': contract.bid,
                    'ask': contract.ask,
                    'volume': contract.volume,
                    'open_interest': contract.open_interest,
                    'implied_volatility': contract.implied_volatility,
                    'in_the_money': contract.in_the_money,
                    'last_trade_date': contract.last_trade_date,
                    'download_time': options_chain.download_time
                })
        
        df = pd.DataFrame(all_contracts)
        
        if not df.empty:
            # Add derived columns
            df['moneyness'] = df['strike'] / df['underlying_price']
            df['time_to_expiration'] = (pd.to_datetime(df['expiration']) - datetime.now()).dt.days
            df['mid_price'] = (df['bid'] + df['ask']) / 2
            df['bid_ask_spread'] = df['ask'] - df['bid']
            df['spread_percentage'] = df['bid_ask_spread'] / df['mid_price'].clip(lower=0.01) * 100
            
            # Sort by expiration and strike
            df = df.sort_values(['expiration', 'option_type', 'strike'])
            df = df.reset_index(drop=True)
        
        return df


def download_options_data(symbols: List[str], cache_manager: UnifiedCacheManager = None) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to download options data for multiple symbols.
    
    Args:
        symbols: List of stock symbols to get options for
        cache_manager: Optional cache manager
        
    Returns:
        Dictionary mapping symbols to options DataFrames
    """
    provider = OptionsDataProvider(cache_manager)
    request = DataRequest(symbols=symbols)
    response = provider.download_data(request)
    
    if response.errors:
        logger.warning(f"Options download errors: {response.errors}")
    
    return response.data