"""
Sector ETF data management for rotation analysis.
Focus on essential sector ETFs that provide actionable trading signals.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging
from .stock_data import StockDataDownloader

logger = logging.getLogger(__name__)


class SectorDataManager:
    """
    Manage sector ETF data for rotation analysis.
    Focus on liquid, representative sector ETFs only.
    """
    
    def __init__(self):
        """Initialize sector data manager."""
        self.downloader = StockDataDownloader()
        
        # Essential sector ETFs (most liquid and representative)
        self.sector_etfs = {
            # Core Sectors
            'XLK': 'Technology',
            'XLF': 'Financials',
            'XLE': 'Energy', 
            'XLV': 'Healthcare',
            'XLI': 'Industrials',
            'XLP': 'Consumer Staples',
            'XLY': 'Consumer Discretionary',
            'XLU': 'Utilities',
            'XLB': 'Materials',
            'XLRE': 'Real Estate',
            'XLC': 'Communication Services',
            
            # Key Factor ETFs
            'XLG': 'Large Cap Growth',
            'IWM': 'Small Cap',
            'QQQ': 'NASDAQ 100',
            
            # International
            'EFA': 'Developed Markets',
            'EEM': 'Emerging Markets',
            'FXI': 'China',
            
            # Commodities & Alternatives
            'GLD': 'Gold',
            'TLT': '20+ Year Treasury',
            'HYG': 'High Yield Bonds'
        }
    
    def download_sector_data(self, period: str = "2y", interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Download data for all essential sector ETFs.
        
        Args:
            period: Data period (1y, 2y, 5y, etc.)
            interval: Data interval (1d, 1wk, 1mo)
            
        Returns:
            Dictionary mapping sector symbols to DataFrames
        """
        sector_data = {}
        
        symbols = list(self.sector_etfs.keys())
        logger.info(f"Downloading data for {len(symbols)} sector ETFs")
        
        try:
            # Download all sector ETF data
            all_data = self.downloader.download_multiple_stocks(
                symbols=symbols,
                period=period,
                interval=interval
            )
            
            # Process and validate data
            for symbol, data in all_data.items():
                if not data.empty and len(data) > 20:  # Minimum data requirement
                    sector_data[symbol] = data
                    logger.info(f"✅ {symbol} ({self.sector_etfs[symbol]}): {len(data)} rows")
                else:
                    logger.warning(f"⚠️ Insufficient data for {symbol}")
            
            logger.info(f"Successfully downloaded {len(sector_data)} sector ETFs")
            return sector_data
            
        except Exception as e:
            logger.error(f"Error downloading sector data: {e}")
            return {}
    
    def calculate_sector_rotation_signals(self, sector_data: Dict[str, pd.DataFrame], 
                                        lookback_days: int = 20) -> pd.DataFrame:
        """
        Calculate sector rotation signals.
        
        Args:
            sector_data: Dictionary of sector ETF data
            lookback_days: Number of days for momentum calculation
            
        Returns:
            DataFrame with sector rotation analysis
        """
        try:
            rotation_data = []
            
            for symbol, data in sector_data.items():
                if 'Close' in data.columns and len(data) > lookback_days:
                    prices = data['Close']
                    
                    # Calculate various momentum metrics
                    current_price = prices.iloc[-1]
                    
                    # Performance metrics
                    perf_1d = (prices.iloc[-1] - prices.iloc[-2]) / prices.iloc[-2] * 100
                    perf_1w = (prices.iloc[-1] - prices.iloc[-6]) / prices.iloc[-6] * 100 if len(prices) > 5 else 0
                    perf_1m = (prices.iloc[-1] - prices.iloc[-21]) / prices.iloc[-21] * 100 if len(prices) > 20 else 0
                    perf_3m = (prices.iloc[-1] - prices.iloc[-61]) / prices.iloc[-61] * 100 if len(prices) > 60 else 0
                    
                    # Volatility
                    returns = prices.pct_change().dropna()
                    volatility = returns.tail(20).std() * np.sqrt(252) * 100
                    
                    # Relative strength vs SPY (if available)
                    relative_strength = 0
                    if 'SPY' in sector_data:
                        spy_perf_1m = sector_data['SPY']['Close'].pct_change(20).iloc[-1] * 100
                        relative_strength = perf_1m - spy_perf_1m
                    
                    # Volume trend
                    volume_trend = 0
                    if 'Volume' in data.columns:
                        avg_volume_20d = data['Volume'].tail(20).mean()
                        avg_volume_60d = data['Volume'].tail(60).mean()
                        volume_trend = (avg_volume_20d - avg_volume_60d) / avg_volume_60d * 100
                    
                    rotation_data.append({
                        'symbol': symbol,
                        'sector': self.sector_etfs.get(symbol, 'Unknown'),
                        'current_price': current_price,
                        'perf_1d': perf_1d,
                        'perf_1w': perf_1w,
                        'perf_1m': perf_1m,
                        'perf_3m': perf_3m,
                        'volatility': volatility,
                        'relative_strength': relative_strength,
                        'volume_trend': volume_trend,
                        'momentum_score': (perf_1w * 0.3 + perf_1m * 0.5 + relative_strength * 0.2)
                    })
            
            rotation_df = pd.DataFrame(rotation_data)
            
            if not rotation_df.empty:
                # Add rankings
                rotation_df['momentum_rank'] = rotation_df['momentum_score'].rank(ascending=False)
                rotation_df['relative_strength_rank'] = rotation_df['relative_strength'].rank(ascending=False)
                
                # Sort by momentum score
                rotation_df = rotation_df.sort_values('momentum_score', ascending=False)
                
                logger.info(f"Calculated sector rotation signals for {len(rotation_df)} sectors")
            
            return rotation_df
            
        except Exception as e:
            logger.error(f"Error calculating sector rotation signals: {e}")
            return pd.DataFrame()
    
    def get_sector_rotation_summary(self, rotation_df: pd.DataFrame) -> Dict[str, any]:
        """
        Generate sector rotation summary.
        
        Args:
            rotation_df: DataFrame with sector rotation data
            
        Returns:
            Dictionary with rotation summary
        """
        try:
            if rotation_df.empty:
                return {'error': 'No sector data available'}
            
            summary = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'top_performers': {},
                'bottom_performers': {},
                'sector_themes': [],
                'rotation_signals': []
            }
            
            # Top and bottom performers
            top_3 = rotation_df.head(3)
            bottom_3 = rotation_df.tail(3)
            
            for _, row in top_3.iterrows():
                summary['top_performers'][row['symbol']] = {
                    'sector': row['sector'],
                    'perf_1m': row['perf_1m'],
                    'momentum_score': row['momentum_score']
                }
            
            for _, row in bottom_3.iterrows():
                summary['bottom_performers'][row['symbol']] = {
                    'sector': row['sector'],
                    'perf_1m': row['perf_1m'],
                    'momentum_score': row['momentum_score']
                }
            
            # Identify themes
            tech_performance = rotation_df[rotation_df['symbol'] == 'XLK']['perf_1m'].iloc[0] if 'XLK' in rotation_df['symbol'].values else 0
            finance_performance = rotation_df[rotation_df['symbol'] == 'XLF']['perf_1m'].iloc[0] if 'XLF' in rotation_df['symbol'].values else 0
            energy_performance = rotation_df[rotation_df['symbol'] == 'XLE']['perf_1m'].iloc[0] if 'XLE' in rotation_df['symbol'].values else 0
            
            # Generate thematic insights
            if tech_performance > 5:
                summary['sector_themes'].append("Technology leadership continues")
            elif tech_performance < -5:
                summary['sector_themes'].append("Technology sector under pressure")
            
            if finance_performance > energy_performance + 3:
                summary['sector_themes'].append("Financials outperforming energy (steepening curve)")
            elif energy_performance > finance_performance + 3:
                summary['sector_themes'].append("Energy outperforming financials (commodity strength)")
            
            # Rotation signals
            defensive_sectors = ['XLU', 'XLP', 'XLRE']
            defensive_avg = rotation_df[rotation_df['symbol'].isin(defensive_sectors)]['perf_1m'].mean()
            
            cyclical_sectors = ['XLK', 'XLF', 'XLI', 'XLY']
            cyclical_avg = rotation_df[rotation_df['symbol'].isin(cyclical_sectors)]['perf_1m'].mean()
            
            if defensive_avg > cyclical_avg + 2:
                summary['rotation_signals'].append("DEFENSIVE ROTATION - Risk-off environment")
            elif cyclical_avg > defensive_avg + 2:
                summary['rotation_signals'].append("CYCLICAL ROTATION - Risk-on environment")
            else:
                summary['rotation_signals'].append("MIXED ROTATION - No clear trend")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating sector rotation summary: {e}")
            return {'error': str(e)}
    
    def get_essential_symbols(self) -> List[str]:
        """Get list of essential sector ETF symbols."""
        return list(self.sector_etfs.keys())
    
    def get_sector_name(self, symbol: str) -> str:
        """Get sector name for symbol."""
        return self.sector_etfs.get(symbol, 'Unknown')