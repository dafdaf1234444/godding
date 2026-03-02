"""
Market Regime Analysis - Essential signals for quantitative trading decisions.
Focus on high-signal, low-noise indicators that actually matter.
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarketRegimeAnalyzer:
    """
    Analyze market regimes using essential indicators that actually drive decisions.
    Focus on yield curve, volatility, momentum, and cross-asset behavior.
    """
    
    def __init__(self):
        """Initialize market regime analyzer."""
        self.regime_thresholds = {
            'yield_curve_inversion': 0.0,  # 10Y-2Y spread
            'vix_low': 20.0,
            'vix_high': 30.0,
            'momentum_threshold': 0.05,  # 5% monthly return threshold
            'volatility_threshold': 0.02  # 2% daily volatility threshold
        }
    
    def analyze_yield_curve_regime(self, treasury_data: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze yield curve regime - the most important macro signal.
        
        Args:
            treasury_data: DataFrame with 10Y and 2Y treasury yields
            
        Returns:
            DataFrame with yield curve analysis
        """
        regime_data = treasury_data.copy()
        
        if '10Y' in treasury_data.columns and '2Y' in treasury_data.columns:
            # Calculate yield curve slope (10Y - 2Y)
            regime_data['yield_curve_slope'] = treasury_data['10Y'] - treasury_data['2Y']
            
            # Regime classification
            regime_data['curve_regime'] = np.where(
                regime_data['yield_curve_slope'] < 0, 'INVERTED',
                np.where(regime_data['yield_curve_slope'] < 0.5, 'FLAT', 'NORMAL')
            )
            
            # Rate of change in slope (early warning)
            regime_data['slope_change_1m'] = regime_data['yield_curve_slope'].diff(20)  # 20-day change
            regime_data['slope_momentum'] = np.where(
                regime_data['slope_change_1m'] < -0.2, 'STEEPENING',
                np.where(regime_data['slope_change_1m'] > 0.2, 'FLATTENING', 'STABLE')
            )
            
            logger.info("Yield curve regime analysis completed")
        
        return regime_data
    
    def analyze_volatility_regime(self, vix_data: pd.DataFrame, 
                                stock_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Analyze volatility regime using VIX and realized volatility.
        
        Args:
            vix_data: DataFrame with VIX values
            stock_data: Dictionary of stock DataFrames for realized vol calculation
            
        Returns:
            DataFrame with volatility regime analysis
        """
        regime_data = vix_data.copy()
        
        # Handle VIX data in different formats
        vix_series = None
        if 'VIX' in vix_data.columns:
            vix_series = vix_data['VIX']
        elif 'Close' in vix_data.columns:
            vix_series = vix_data['Close']
        elif not vix_data.empty and len(vix_data.columns) > 0:
            vix_series = vix_data.iloc[:, 0]  # Use first column
        
        if vix_series is not None:
            # VIX regime classification
            regime_data['vix_regime'] = pd.cut(
                vix_series,
                bins=[0, self.regime_thresholds['vix_low'], 
                     self.regime_thresholds['vix_high'], 100],
                labels=['LOW_VOL', 'MEDIUM_VOL', 'HIGH_VOL']
            )
            
            # VIX momentum (fear/greed acceleration)
            regime_data['vix_change_5d'] = vix_series.pct_change(5)
            regime_data['vix_momentum'] = np.where(
                regime_data['vix_change_5d'] > 0.2, 'FEAR_RISING',
                np.where(regime_data['vix_change_5d'] < -0.2, 'FEAR_FALLING', 'STABLE')
            )
        
        # Calculate realized volatility from stock data
        if stock_data:
            realized_vols = []
            for symbol, data in stock_data.items():
                if 'Close' in data.columns:
                    returns = data['Close'].pct_change().dropna()
                    realized_vol = returns.rolling(window=20).std() * np.sqrt(252) * 100
                    realized_vols.append(realized_vol)
            
            if realized_vols:
                avg_realized_vol = pd.concat(realized_vols, axis=1).mean(axis=1)
                
                # Align with VIX data
                common_dates = regime_data.index.intersection(avg_realized_vol.index)
                if len(common_dates) > 0:
                    regime_data.loc[common_dates, 'realized_vol'] = avg_realized_vol.loc[common_dates]
                    
                    # VIX vs realized vol spread (fear premium)
                    regime_data['vol_premium'] = regime_data['VIX'] - regime_data['realized_vol']
                    regime_data['vol_premium_regime'] = np.where(
                        regime_data['vol_premium'] > 5, 'HIGH_FEAR_PREMIUM',
                        np.where(regime_data['vol_premium'] < -2, 'COMPLACENCY', 'NORMAL')
                    )
        
        logger.info("Volatility regime analysis completed")
        return regime_data
    
    def analyze_cross_asset_regime(self, asset_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Analyze cross-asset behavior for risk-on/risk-off regime detection.
        
        Args:
            asset_data: Dictionary with SPY, TLT, GLD, etc.
            
        Returns:
            DataFrame with cross-asset regime analysis
        """
        # Calculate returns for all assets
        returns_data = {}
        for asset, data in asset_data.items():
            if 'Close' in data.columns:
                returns = data['Close'].pct_change().dropna()
                returns_data[f'{asset}_return'] = returns
        
        if not returns_data:
            return pd.DataFrame()
        
        # Combine all returns
        returns_df = pd.DataFrame(returns_data)
        
        # Risk-on/Risk-off scoring
        regime_data = pd.DataFrame(index=returns_df.index)
        
        # Stock-bond correlation (risk-on when negative)
        if 'SPY_return' in returns_df.columns and 'TLT_return' in returns_df.columns:
            rolling_corr = returns_df['SPY_return'].rolling(60).corr(returns_df['TLT_return'])
            regime_data['stock_bond_corr'] = rolling_corr
            
            regime_data['risk_regime_bonds'] = np.where(
                rolling_corr < -0.3, 'RISK_ON',
                np.where(rolling_corr > 0.3, 'RISK_OFF', 'NEUTRAL')
            )
        
        # Gold behavior (safe haven flows)
        if 'GLD_return' in returns_df.columns and 'SPY_return' in returns_df.columns:
            gold_stock_corr = returns_df['GLD_return'].rolling(60).corr(returns_df['SPY_return'])
            regime_data['gold_stock_corr'] = gold_stock_corr
            
            regime_data['safe_haven_regime'] = np.where(
                gold_stock_corr < -0.2, 'SAFE_HAVEN_DEMAND',
                np.where(gold_stock_corr > 0.2, 'RISK_APPETITE', 'NEUTRAL')
            )
        
        # Momentum scoring across assets
        momentum_scores = []
        for asset in ['SPY', 'TLT', 'GLD']:
            return_col = f'{asset}_return'
            if return_col in returns_df.columns:
                momentum_1m = returns_df[return_col].rolling(20).sum()  # 20-day return
                momentum_scores.append(momentum_1m)
        
        if momentum_scores:
            avg_momentum = pd.concat(momentum_scores, axis=1).mean(axis=1)
            regime_data['market_momentum'] = avg_momentum
            
            regime_data['momentum_regime'] = np.where(
                avg_momentum > self.regime_thresholds['momentum_threshold'], 'STRONG_MOMENTUM',
                np.where(avg_momentum < -self.regime_thresholds['momentum_threshold'], 'WEAK_MOMENTUM', 'NEUTRAL')
            )
        
        logger.info("Cross-asset regime analysis completed")
        return regime_data
    
    def generate_regime_summary(self, yield_curve_data: pd.DataFrame,
                               volatility_data: pd.DataFrame,
                               cross_asset_data: pd.DataFrame) -> Dict[str, str]:
        """
        Generate current market regime summary.
        
        Returns:
            Dictionary with current regime assessment
        """
        summary = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_regime': 'UNKNOWN',
            'yield_curve': 'UNKNOWN',
            'volatility': 'UNKNOWN',
            'risk_sentiment': 'UNKNOWN',
            'key_signals': [],
            'risk_level': 'UNKNOWN'
        }
        
        try:
            # Get latest values
            latest_date = None
            
            # Yield curve regime
            if not yield_curve_data.empty and 'curve_regime' in yield_curve_data.columns:
                latest_date = yield_curve_data.index[-1]
                summary['yield_curve'] = yield_curve_data['curve_regime'].iloc[-1]
                
                if summary['yield_curve'] == 'INVERTED':
                    summary['key_signals'].append('YIELD_CURVE_INVERTED')
            
            # Volatility regime
            if not volatility_data.empty and 'vix_regime' in volatility_data.columns:
                summary['volatility'] = volatility_data['vix_regime'].iloc[-1]
                
                if 'vix_momentum' in volatility_data.columns:
                    vix_momentum = volatility_data['vix_momentum'].iloc[-1]
                    if vix_momentum == 'FEAR_RISING':
                        summary['key_signals'].append('FEAR_SPIKING')
            
            # Risk sentiment
            if not cross_asset_data.empty and 'risk_regime_bonds' in cross_asset_data.columns:
                summary['risk_sentiment'] = cross_asset_data['risk_regime_bonds'].iloc[-1]
            
            # Overall regime assessment
            risk_score = 0
            if 'YIELD_CURVE_INVERTED' in summary['key_signals']:
                risk_score += 2
            if summary['volatility'] == 'HIGH_VOL':
                risk_score += 2
            if 'FEAR_SPIKING' in summary['key_signals']:
                risk_score += 1
            if summary['risk_sentiment'] == 'RISK_OFF':
                risk_score += 1
            
            if risk_score >= 4:
                summary['overall_regime'] = 'HIGH_RISK'
                summary['risk_level'] = 'HIGH'
            elif risk_score >= 2:
                summary['overall_regime'] = 'ELEVATED_RISK'
                summary['risk_level'] = 'MEDIUM'
            else:
                summary['overall_regime'] = 'NORMAL_RISK'
                summary['risk_level'] = 'LOW'
            
            summary['latest_data_date'] = latest_date.strftime('%Y-%m-%d') if latest_date else 'UNKNOWN'
            
        except Exception as e:
            logger.error(f"Error generating regime summary: {e}")
            summary['error'] = str(e)
        
        return summary
    
    def get_actionable_insights(self, regime_summary: Dict[str, str]) -> List[str]:
        """
        Generate actionable trading insights based on regime analysis.
        
        Args:
            regime_summary: Current regime summary
            
        Returns:
            List of actionable insights
        """
        insights = []
        
        try:
            # Yield curve insights
            if regime_summary.get('yield_curve') == 'INVERTED':
                insights.append("WARNING: YIELD CURVE INVERTED - Consider defensive positioning")
                insights.append("ANALYSIS: Monitor financials (XLF) for weakness")
            elif regime_summary.get('yield_curve') == 'FLAT':
                insights.append("SIGNAL: YIELD CURVE FLATTENING - Watch for inversion signal")
            
            # Volatility insights
            vol_regime = regime_summary.get('volatility')
            if vol_regime == 'HIGH_VOL':
                insights.append("ALERT: HIGH VOLATILITY - Reduce position sizing")
                insights.append("STRATEGY: Consider volatility selling strategies")
            elif vol_regime == 'LOW_VOL':
                insights.append("SIGNAL: LOW VOLATILITY - Opportunity for momentum strategies")
            
            # Risk sentiment insights
            risk_sentiment = regime_summary.get('risk_sentiment')
            if risk_sentiment == 'RISK_OFF':
                insights.append("REGIME: RISK-OFF MODE - Favor quality, defensives")
                insights.append("ASSETS: TLT/Gold may outperform")
            elif risk_sentiment == 'RISK_ON':
                insights.append("REGIME: RISK-ON MODE - Growth/tech may outperform")
                insights.append("ANALYSIS: Monitor for overextension")
            
            # Overall risk insights
            risk_level = regime_summary.get('risk_level')
            if risk_level == 'HIGH':
                insights.append("ALERT: HIGH RISK ENVIRONMENT - Consider hedging")
                insights.append("ALLOCATION: Increase cash allocation")
            elif risk_level == 'LOW':
                insights.append("SIGNAL: FAVORABLE RISK ENVIRONMENT - Consider increasing exposure")
            
            # Add key signals context
            key_signals = regime_summary.get('key_signals', [])
            if 'FEAR_SPIKING' in key_signals:
                insights.append("SIGNAL: FEAR SPIKING - Potential contrarian opportunity")
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            insights.append(f"ERROR: Error generating insights: {e}")
        
        return insights