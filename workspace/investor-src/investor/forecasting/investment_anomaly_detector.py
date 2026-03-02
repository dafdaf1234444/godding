"""
Investment-focused anomaly detection with meaningful time frames and actionable insights.
Designed to provide trading signals and investment opportunities.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from dataclasses import dataclass
import warnings

from ..utils.temporal_validation import TemporalValidator

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


@dataclass
class AnomalySignal:
    """Structured anomaly signal for investment decisions."""
    symbol: str
    date: datetime
    anomaly_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    confidence: float  # 0.0 to 1.0
    signal: str  # 'buy', 'sell', 'hold', 'watch'
    description: str
    time_frame: str  # 'immediate', 'short_term', 'medium_term', 'long_term'
    expected_duration: str  # how long the signal is expected to be relevant
    potential_return: Optional[float] = None
    risk_level: Optional[str] = None


class InvestmentAnomalyDetector:
    """
    Investment-focused anomaly detection system.
    
    Provides:
    - Trading signals based on anomalies
    - Time-framed analysis (immediate, short, medium, long term)
    - Risk-adjusted recommendations
    - Portfolio-level insights
    - Market regime detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, events_data: Optional[pd.DataFrame] = None,
                 enable_temporal_validation: bool = True):
        """Initialize investment anomaly detector."""
        self.config = config or self._get_default_config()
        self.signals = []
        self.market_regime = {}
        self.portfolio_alerts = []
        self.events_data = events_data
        self.enable_temporal_validation = enable_temporal_validation
        
        # Initialize temporal validation
        if self.enable_temporal_validation:
            self.temporal_validator = TemporalValidator(strict_mode=False)
        else:
            self.temporal_validator = None
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'time_frames': {
                'immediate': {'hours': 1},  # Next few hours
                'short_term': {'days': 5},  # Next week
                'medium_term': {'days': 21},  # Next month
                'long_term': {'days': 63}  # Next quarter
            },
            'thresholds': {
                'volume_spike': 3.0,  # Standard deviations
                'price_gap': 0.05,  # 5% gap
                'volatility_regime': 2.0,
                'correlation_break': 0.3
            },
            'investment_signals': {
                'confidence_threshold': 0.6,
                'min_expected_return': 0.02,  # 2%
                'max_risk_tolerance': 0.15  # 15%
            }
        }
    
    def detect_investment_anomalies(self, data: pd.DataFrame) -> List[AnomalySignal]:
        """
        Detect anomalies with investment focus.
        
        Returns:
            List of structured anomaly signals
        """
        logger.info("Detecting investment-focused anomalies")
        
        self.signals = []
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['overall']
        
        for symbol in symbols:
            try:
                if symbol != 'overall':
                    symbol_data = data[data['symbol'] == symbol].copy()
                else:
                    symbol_data = data.copy()
                
                if len(symbol_data) < 50:
                    logger.debug(f"Insufficient data for {symbol}: {len(symbol_data)} rows")
                    continue
                
                # Validate temporal integrity if enabled
                if self.enable_temporal_validation and self.temporal_validator:
                    try:
                        validation_result = self.temporal_validator.validate_temporal_integrity(symbol_data)
                        if not validation_result['is_valid']:
                            logger.warning(f"Temporal validation issues for {symbol}: {validation_result['errors']}")
                            # Continue processing but with warnings
                        if validation_result['warnings']:
                            logger.debug(f"Temporal validation warnings for {symbol}: {validation_result['warnings']}")
                    except Exception as e:
                        logger.warning(f"Temporal validation failed for {symbol}: {e}")
                
                logger.debug(f"Processing {symbol} with {len(symbol_data)} rows")
                
                # Different anomaly types with investment implications
                self._detect_breakout_signals(symbol_data, symbol)
                self._detect_reversal_signals(symbol_data, symbol)
                self._detect_volume_anomalies(symbol_data, symbol)
                self._detect_volatility_regime_changes(symbol_data, symbol)
                self._detect_momentum_shifts(symbol_data, symbol)
                self._detect_support_resistance_breaks(symbol_data, symbol)
                
                # Add events-driven anomaly detection
                if self.events_data is not None and not self.events_data.empty:
                    self._detect_event_driven_anomalies(symbol_data, symbol)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        # Add market-wide signals
        if len(symbols) > 1:
            self._detect_market_regime_changes(data)
            self._detect_correlation_anomalies(data)
        
        # Filter and rank signals with events context
        filtered_signals = self._filter_and_rank_signals()
        
        logger.info(f"Generated {len(filtered_signals)} investment signals")
        return filtered_signals
    
    def _detect_breakout_signals(self, data: pd.DataFrame, symbol: str):
        """Detect breakout patterns for trend following."""
        if len(data) < 50:
            return
        
        # Ensure required columns exist
        required_cols = ['High', 'Low', 'Close', 'Volume', 'Date']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            logger.warning(f"Missing columns for breakout detection: {missing_cols}")
            return
        
        # Calculate support and resistance levels
        window = 20
        data = data.copy()
        data['resistance'] = data['High'].rolling(window).max()
        data['support'] = data['Low'].rolling(window).min()
        
        # Detect breakouts
        for i in range(window, len(data)):
            if i >= len(data):
                break
            current = data.iloc[i]
            previous = data.iloc[i-1]
            
            # Resistance breakout (bullish)
            if (current['Close'] > previous['resistance'] and 
                current['Volume'] > data['Volume'].rolling(20).mean().iloc[i] * 1.5):
                
                # Calculate potential target
                range_size = previous['resistance'] - previous['support']
                target_price = current['Close'] + range_size
                potential_return = (target_price - current['Close']) / current['Close']
                
                signal = AnomalySignal(
                    symbol=symbol,
                    date=current['Date'],
                    anomaly_type='resistance_breakout',
                    severity='high' if potential_return > 0.05 else 'medium',
                    confidence=min(0.9, 0.5 + (current['Volume'] / data['Volume'].rolling(20).mean().iloc[i] - 1) * 0.2),
                    signal='buy',
                    description=f"Resistance breakout at ${current['Close']:.2f} with high volume",
                    time_frame='short_term',
                    expected_duration='5-10 trading days',
                    potential_return=potential_return,
                    risk_level='medium'
                )
                self.signals.append(signal)
            
            # Support breakdown (bearish)
            elif (current['Close'] < previous['support'] and 
                  current['Volume'] > data['Volume'].rolling(20).mean().iloc[i] * 1.5):
                
                range_size = previous['resistance'] - previous['support']
                target_price = current['Close'] - range_size
                potential_return = (target_price - current['Close']) / current['Close']
                
                signal = AnomalySignal(
                    symbol=symbol,
                    date=current['Date'],
                    anomaly_type='support_breakdown',
                    severity='high' if abs(potential_return) > 0.05 else 'medium',
                    confidence=min(0.9, 0.5 + (current['Volume'] / data['Volume'].rolling(20).mean().iloc[i] - 1) * 0.2),
                    signal='sell',
                    description=f"Support breakdown at ${current['Close']:.2f} with high volume",
                    time_frame='short_term',
                    expected_duration='5-10 trading days',
                    potential_return=potential_return,
                    risk_level='medium'
                )
                self.signals.append(signal)
    
    def _detect_reversal_signals(self, data: pd.DataFrame, symbol: str):
        """Detect reversal patterns for contrarian strategies."""
        if len(data) < 30:
            return
        
        # Ensure required columns exist
        if 'Close' not in data.columns or 'Date' not in data.columns:
            logger.warning("Missing required columns for reversal detection")
            return
        
        # Calculate RSI
        data = data.copy()
        data['rsi'] = self._calculate_rsi(data['Close'])
        
        # Oversold reversal (bullish)
        oversold_mask = (data['rsi'] < 30) & (data['rsi'].shift(1) >= 30)
        for idx in data[oversold_mask].index:
            if idx in data.index:
                current = data.loc[idx]
                
                signal = AnomalySignal(
                    symbol=symbol,
                    date=current['Date'],
                    anomaly_type='oversold_reversal',
                    severity='medium',
                    confidence=0.7 - (current['rsi'] / 50),  # Lower RSI = higher confidence
                    signal='buy',
                    description=f"Oversold condition (RSI: {current['rsi']:.1f}) potential reversal",
                    time_frame='immediate',
                    expected_duration='1-3 trading days',
                    potential_return=0.03,  # Expected 3% bounce
                    risk_level='medium'
                )
                self.signals.append(signal)
        
        # Overbought reversal (bearish)
        overbought_mask = (data['rsi'] > 70) & (data['rsi'].shift(1) <= 70)
        for idx in data[overbought_mask].index:
            if idx in data.index:
                current = data.loc[idx]
                
                signal = AnomalySignal(
                    symbol=symbol,
                    date=current['Date'],
                    anomaly_type='overbought_reversal',
                    severity='medium',
                    confidence=(current['rsi'] - 50) / 50,  # Higher RSI = higher confidence
                    signal='sell',
                    description=f"Overbought condition (RSI: {current['rsi']:.1f}) potential reversal",
                    time_frame='immediate',
                    expected_duration='1-3 trading days',
                    potential_return=-0.03,  # Expected 3% decline
                    risk_level='medium'
                )
                self.signals.append(signal)
    
    def _detect_volume_anomalies(self, data: pd.DataFrame, symbol: str):
        """Detect volume anomalies with investment implications."""
        if 'Volume' not in data.columns or len(data) < 30:
            return
        
        # Volume surge detection
        data['volume_ma'] = data['Volume'].rolling(20).mean()
        data['volume_zscore'] = (data['Volume'] - data['volume_ma']) / data['Volume'].rolling(20).std()
        
        # High volume with small price change (accumulation/distribution)
        volume_spikes = data['volume_zscore'] > self.config['thresholds']['volume_spike']
        price_change_small = abs(data['Close'].pct_change()) < 0.02
        
        accumulation_mask = volume_spikes & price_change_small
        for idx in data[accumulation_mask].index:
            try:
                if idx in data.index:
                    current = data.loc[idx]
                    
                    # Determine if accumulation or distribution based on price action
                    recent_trend_series = data['Close'].rolling(5).mean().pct_change()
                    if idx in recent_trend_series.index:
                        recent_trend = recent_trend_series.loc[idx]
                    else:
                        recent_trend = 0  # Default to neutral if index not found
                    
                    signal_type = 'buy' if recent_trend >= 0 else 'sell'
                    anomaly_type = 'accumulation' if recent_trend >= 0 else 'distribution'
                    
                    signal = AnomalySignal(
                        symbol=symbol,
                        date=current['Date'],
                        anomaly_type=anomaly_type,
                        severity='high',
                        confidence=min(0.9, current['volume_zscore'] / 5),
                        signal=signal_type,
                        description=f"High volume {anomaly_type} detected (Volume: {current['Volume']:,.0f})",
                        time_frame='medium_term',
                        expected_duration='1-4 weeks',
                        potential_return=0.05 if signal_type == 'buy' else -0.05,
                        risk_level='low'
                    )
                    self.signals.append(signal)
            except Exception as e:
                logger.debug(f"Error processing volume anomaly for {symbol} at index {idx}: {e}")
                continue
    
    def _detect_volatility_regime_changes(self, data: pd.DataFrame, symbol: str):
        """Detect volatility regime changes for risk management."""
        if len(data) < 50:
            return
        
        # Calculate rolling volatility
        data['returns'] = data['Close'].pct_change()
        data['volatility'] = data['returns'].rolling(20).std()
        data['vol_zscore'] = (data['volatility'] - data['volatility'].rolling(60).mean()) / data['volatility'].rolling(60).std()
        
        # High volatility regime
        high_vol_mask = (data['vol_zscore'] > self.config['thresholds']['volatility_regime']) & (data['vol_zscore'].shift(1) <= self.config['thresholds']['volatility_regime'])
        for idx in data[high_vol_mask].index:
            if idx in data.index:
                current = data.loc[idx]
                
                signal = AnomalySignal(
                    symbol=symbol,
                    date=current['Date'],
                    anomaly_type='high_volatility_regime',
                    severity='critical',
                    confidence=0.8,
                    signal='hold',
                    description=f"Entering high volatility regime (Vol: {current['volatility']*100:.1f}%)",
                    time_frame='medium_term',
                    expected_duration='2-8 weeks',
                    potential_return=None,
                    risk_level='high'
                )
                self.signals.append(signal)
        
        # Low volatility regime (compression before expansion)
        low_vol_mask = (data['vol_zscore'] < -1.5) & (data['vol_zscore'].shift(1) >= -1.5)
        for idx in data[low_vol_mask].index:
            if idx in data.index:
                current = data.loc[idx]
                
                signal = AnomalySignal(
                    symbol=symbol,
                    date=current['Date'],
                    anomaly_type='low_volatility_regime',
                    severity='medium',
                    confidence=0.7,
                    signal='watch',
                    description=f"Low volatility compression (Vol: {current['volatility']*100:.1f}%) - expect expansion",
                    time_frame='short_term',
                    expected_duration='1-3 weeks',
                    potential_return=None,
                    risk_level='low'
                )
                self.signals.append(signal)
    
    def _detect_momentum_shifts(self, data: pd.DataFrame, symbol: str):
        """Detect momentum shifts for trend trading."""
        if len(data) < 30:
            return
        
        # Calculate momentum indicators
        data['momentum_5'] = data['Close'] / data['Close'].shift(5) - 1
        data['momentum_21'] = data['Close'] / data['Close'].shift(21) - 1
        
        # Momentum acceleration
        data['momentum_accel'] = data['momentum_5'] - data['momentum_5'].shift(5)
        
        # Strong momentum acceleration
        strong_accel_mask = abs(data['momentum_accel']) > 0.05
        for idx in data[strong_accel_mask].index:
            if idx in data.index:
                current = data.loc[idx]
                
                signal_type = 'buy' if current['momentum_accel'] > 0 else 'sell'
                
                signal = AnomalySignal(
                    symbol=symbol,
                    date=current['Date'],
                    anomaly_type='momentum_acceleration',
                    severity='high',
                    confidence=min(0.9, abs(current['momentum_accel']) * 10),
                    signal=signal_type,
                    description=f"Strong momentum acceleration ({current['momentum_accel']*100:+.1f}%)",
                    time_frame='medium_term',
                    expected_duration='2-6 weeks',
                    potential_return=current['momentum_accel'] * 2,  # Expect continuation
                    risk_level='medium'
                )
                self.signals.append(signal)
    
    def _detect_support_resistance_breaks(self, data: pd.DataFrame, symbol: str):
        """Detect significant support/resistance level breaks."""
        if len(data) < 50:
            return
        
        # Find significant levels (previous highs/lows)
        data['pivot_high'] = data['High'].rolling(10, center=True).max() == data['High']
        data['pivot_low'] = data['Low'].rolling(10, center=True).min() == data['Low']
        
        # Get recent significant levels
        recent_highs = data[data['pivot_high']]['High'].tail(5).values
        recent_lows = data[data['pivot_low']]['Low'].tail(5).values
        
        for i in range(max(0, len(data)-10), len(data)):
            if i < 0 or i >= len(data):
                continue
                
            try:
                current = data.iloc[i]
            except IndexError:
                logger.warning(f"Index {i} out of bounds for data with {len(data)} rows")
                continue
            
            # Check for resistance breaks
            for resistance in recent_highs:
                if (current['Close'] > resistance * 1.01 and  # 1% above resistance
                    data.iloc[i-1]['Close'] <= resistance * 1.01):
                    
                    signal = AnomalySignal(
                        symbol=symbol,
                        date=current['Date'],
                        anomaly_type='resistance_break',
                        severity='high',
                        confidence=0.8,
                        signal='buy',
                        description=f"Breaking resistance at ${resistance:.2f}",
                        time_frame='short_term',
                        expected_duration='1-2 weeks',
                        potential_return=0.05,
                        risk_level='medium'
                    )
                    self.signals.append(signal)
            
            # Check for support breaks
            for support in recent_lows:
                if (current['Close'] < support * 0.99 and  # 1% below support
                    data.iloc[i-1]['Close'] >= support * 0.99):
                    
                    signal = AnomalySignal(
                        symbol=symbol,
                        date=current['Date'],
                        anomaly_type='support_break',
                        severity='high',
                        confidence=0.8,
                        signal='sell',
                        description=f"Breaking support at ${support:.2f}",
                        time_frame='short_term',
                        expected_duration='1-2 weeks',
                        potential_return=-0.05,
                        risk_level='medium'
                    )
                    self.signals.append(signal)
    
    def _detect_event_driven_anomalies(self, data: pd.DataFrame, symbol: str):
        """Detect anomalies driven by major events with enhanced analysis."""
        if self.events_data is None or self.events_data.empty:
            return
        
        # Ensure data has datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            if 'Date' in data.columns:
                data = data.set_index('Date')
            data.index = pd.to_datetime(data.index)
        
        # Filter events relevant to this symbol or market-wide events
        relevant_events = self.events_data[
            (self.events_data['affected_symbols'].apply(
                lambda x: symbol in x if isinstance(x, list) else False
            )) |
            (self.events_data['impact_scope'].isin(['global', 'market'])) |
            (self.events_data['affected_sectors'].apply(
                lambda x: self._is_symbol_in_sector(symbol, x) if isinstance(x, list) else False
            ))
        ].copy()
        
        if relevant_events.empty:
            return
        
        # Analyze each relevant event
        for _, event in relevant_events.iterrows():
            event_date = pd.to_datetime(event['date'])
            
            # Skip events outside our data range
            if event_date < data.index.min() or event_date > data.index.max():
                continue
            
            # Find closest trading day
            closest_idx = data.index.get_indexer([event_date], method='nearest')[0]
            if closest_idx == -1:
                continue
            
            event_trading_date = data.index[closest_idx]
            
            # Enhanced event impact analysis
            impact_analysis = self._analyze_event_impact(data, event, closest_idx)
            
            if impact_analysis is None:
                continue
            
            # Generate sophisticated signals based on event characteristics
            signals = self._generate_event_signals(
                symbol, event, event_trading_date, impact_analysis
            )
            
            self.signals.extend(signals)
    
    def _analyze_event_impact(self, data: pd.DataFrame, event: dict, event_idx: int) -> Optional[dict]:
        """Analyze the comprehensive impact of an event on price and volume."""
        # Define analysis windows
        impact_windows = {
            'immediate': 1,  # 1 day
            'short_term': 3,  # 3 days
            'medium_term': 7,  # 1 week
            'long_term': 21   # 3 weeks
        }
        
        analysis = {}
        
        for window_name, window_days in impact_windows.items():
            # Get pre-event baseline
            pre_start = max(0, event_idx - window_days * 2)
            pre_end = event_idx
            
            # Get post-event period
            post_start = event_idx
            post_end = min(len(data), event_idx + window_days + 1)
            
            if pre_start >= pre_end or post_start >= post_end:
                continue
                
            pre_data = data.iloc[pre_start:pre_end]
            post_data = data.iloc[post_start:post_end]
            
            if len(pre_data) < 2 or len(post_data) < 1:
                continue
            
            # Calculate metrics
            pre_price = pre_data['Close'].iloc[-1]
            post_price = post_data['Close'].iloc[0]
            price_impact = (post_price - pre_price) / pre_price
            
            # Volume analysis
            pre_volume_avg = pre_data['Volume'].mean()
            post_volume_avg = post_data['Volume'].mean()
            volume_spike = (post_volume_avg / pre_volume_avg) if pre_volume_avg > 0 else 1
            
            # Volatility analysis
            pre_volatility = pre_data['Close'].pct_change().std()
            post_volatility = post_data['Close'].pct_change().std()
            volatility_change = (post_volatility - pre_volatility) / pre_volatility if pre_volatility > 0 else 0
            
            # Trend analysis
            pre_trend = (pre_data['Close'].iloc[-1] - pre_data['Close'].iloc[0]) / pre_data['Close'].iloc[0]
            post_trend = (post_data['Close'].iloc[-1] - post_data['Close'].iloc[0]) / post_data['Close'].iloc[0] if len(post_data) > 1 else 0
            
            analysis[window_name] = {
                'price_impact': price_impact,
                'volume_spike': volume_spike,
                'volatility_change': volatility_change,
                'pre_trend': pre_trend,
                'post_trend': post_trend,
                'significance': abs(price_impact) * volume_spike
            }
        
        return analysis if analysis else None
    
    def _generate_event_signals(self, symbol: str, event: dict, event_date: pd.Timestamp, impact_analysis: dict) -> List[AnomalySignal]:
        """Generate sophisticated signals based on event and market reaction."""
        signals = []
        
        event_severity = event.get('severity', 'medium')
        event_category = event.get('category', 'market_events')
        event_title = event.get('title', 'Market Event')
        
        # Analyze immediate impact
        immediate_impact = impact_analysis.get('immediate', {})
        short_term_impact = impact_analysis.get('short_term', {})
        
        if not immediate_impact:
            return signals
        
        price_impact = immediate_impact.get('price_impact', 0)
        volume_spike = immediate_impact.get('volume_spike', 1)
        significance = immediate_impact.get('significance', 0)
        
        # Strong immediate reaction signal
        if abs(price_impact) > 0.03 and volume_spike > 1.5:
            confidence = min(0.95, 0.6 + significance * 0.3)
            
            if price_impact > 0.02:
                signal_type = 'buy'
                anomaly_type = f'event_driven_rally_{event_category}'
                description = f"Strong positive reaction to {event_title[:40]} ({price_impact:.1%} move)"
                expected_return = price_impact * 0.5  # Expect partial continuation
            else:
                signal_type = 'sell'
                anomaly_type = f'event_driven_selloff_{event_category}'
                description = f"Strong negative reaction to {event_title[:40]} ({price_impact:.1%} move)"
                expected_return = price_impact * 0.5
            
            signal = AnomalySignal(
                symbol=symbol,
                date=event_date,
                anomaly_type=anomaly_type,
                severity='high',
                confidence=confidence,
                signal=signal_type,
                description=description,
                time_frame='short_term',
                expected_duration='1-2 weeks',
                potential_return=expected_return,
                risk_level='medium'
            )
            signals.append(signal)
        
        # Event anticipation signal (for future events)
        elif event_severity in ['critical', 'high']:
            confidence = 0.7
            
            if event_category == 'economic' and 'fed' in event_title.lower():
                signal_type = 'watch'
                anomaly_type = 'fed_event_anticipation'
                description = f"Anticipated market reaction to Fed event: {event_title[:30]}"
                time_frame = 'immediate'
            elif event_category == 'earnings':
                signal_type = 'watch'
                anomaly_type = 'earnings_event_anticipation'
                description = f"Earnings event for {symbol}: {event_title[:30]}"
                time_frame = 'immediate'
            else:
                signal_type = 'watch'
                anomaly_type = f'event_anticipation_{event_category}'
                description = f"Potential market impact from {event_severity} event: {event_title[:30]}"
                time_frame = 'immediate'
            
            signal = AnomalySignal(
                symbol=symbol,
                date=event_date,
                anomaly_type=anomaly_type,
                severity='medium',
                confidence=confidence,
                signal=signal_type,
                description=description,
                time_frame=time_frame,
                expected_duration='3-5 days',
                potential_return=None,
                risk_level='low'
            )
            signals.append(signal)
        
        # Delayed reaction signal (if short-term shows different pattern)
        if short_term_impact and 'immediate' in impact_analysis:
            short_price = short_term_impact.get('price_impact', 0)
            immediate_price = immediate_impact.get('price_impact', 0)
            
            # Look for delayed reactions or reversals
            if abs(short_price) > abs(immediate_price) * 1.5:
                signal_type = 'buy' if short_price > 0 else 'sell'
                anomaly_type = f'delayed_event_reaction_{event_category}'
                description = f"Delayed reaction to {event_title[:30]} - {short_price:.1%} move over 3 days"
                
                signal = AnomalySignal(
                    symbol=symbol,
                    date=event_date,
                    anomaly_type=anomaly_type,
                    severity='medium',
                    confidence=0.8,
                    signal=signal_type,
                    description=description,
                    time_frame='medium_term',
                    expected_duration='1-2 weeks',
                    potential_return=short_price * 0.3,
                    risk_level='medium'
                )
                signals.append(signal)
        
        return signals
    
    def _is_symbol_in_sector(self, symbol: str, sectors: List[str]) -> bool:
        """Check if a symbol belongs to any of the specified sectors."""
        # Simple sector mapping - in production, this would be more sophisticated
        sector_mappings = {
            'technology': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'NFLX', 'NVDA', 'TSLA'],
            'finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C'],
            'healthcare': ['JNJ', 'UNH', 'PFE', 'CVX', 'ABBV'],
            'energy': ['XOM', 'CVX', 'COP', 'EOG'],
            'consumer': ['WMT', 'PG', 'KO', 'PEP', 'DIS']
        }
        
        for sector in sectors:
            if sector.lower() in sector_mappings:
                if symbol in sector_mappings[sector.lower()]:
                    return True
        
        return False
    
    def _detect_market_regime_changes(self, data: pd.DataFrame):
        """Detect market-wide regime changes."""
        # Calculate market-wide indicators
        market_data = data.groupby('Date').agg({
            'Close': 'mean',
            'Volume': 'sum',
            'High': 'max',
            'Low': 'min'
        }).reset_index()
        
        market_data['market_return'] = market_data['Close'].pct_change()
        market_data['market_vol'] = market_data['market_return'].rolling(20).std()
        
        # Market stress detection
        stress_threshold = market_data['market_vol'].quantile(0.9)
        current_vol = market_data['market_vol'].iloc[-1]
        
        if current_vol > stress_threshold:
            signal = AnomalySignal(
                symbol='MARKET',
                date=market_data['Date'].iloc[-1],
                anomaly_type='market_stress',
                severity='critical',
                confidence=0.9,
                signal='hold',
                description=f"Market stress detected (Vol: {current_vol*100:.1f}%)",
                time_frame='medium_term',
                expected_duration='2-8 weeks',
                potential_return=None,
                risk_level='high'
            )
            self.signals.append(signal)
    
    def _detect_correlation_anomalies(self, data: pd.DataFrame):
        """Detect unusual correlation patterns."""
        # Calculate rolling correlations between assets
        symbols = data['symbol'].unique()
        
        if len(symbols) < 2:
            return
        
        # Create returns pivot
        returns_data = data.pivot_table(values='Close', index='Date', columns='symbol', fill_value=np.nan)
        returns_data = returns_data.pct_change().dropna()
        
        # Rolling correlation
        window = 20
        for i in range(len(symbols)):
            for j in range(i+1, len(symbols)):
                symbol1, symbol2 = symbols[i], symbols[j]
                
                if symbol1 in returns_data.columns and symbol2 in returns_data.columns:
                    rolling_corr = returns_data[symbol1].rolling(window).corr(returns_data[symbol2])
                    
                    # Detect correlation breaks
                    corr_change = rolling_corr.diff().abs()
                    if len(corr_change) > 0 and corr_change.iloc[-1] > self.config['thresholds']['correlation_break']:
                        
                        signal = AnomalySignal(
                            symbol=f'{symbol1}-{symbol2}',
                            date=returns_data.index[-1],
                            anomaly_type='correlation_break',
                            severity='medium',
                            confidence=0.7,
                            signal='watch',
                            description=f"Correlation break between {symbol1} and {symbol2}",
                            time_frame='medium_term',
                            expected_duration='2-4 weeks',
                            potential_return=None,
                            risk_level='medium'
                        )
                        self.signals.append(signal)
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _filter_and_rank_signals(self) -> List[AnomalySignal]:
        """Filter and rank signals by investment value with events context."""
        # Filter by confidence threshold
        filtered = [s for s in self.signals if s.confidence >= self.config['investment_signals']['confidence_threshold']]
        
        # Sort by severity, confidence, and events context
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        
        def signal_score(signal):
            severity_score = severity_order.get(signal.severity, 0)
            confidence_score = signal.confidence
            
            # Boost score for event-driven signals
            events_boost = 1.0
            if 'event_driven' in signal.anomaly_type or 'event_reaction' in signal.anomaly_type:
                events_boost = 1.2  # 20% boost for event-driven signals
            
            # Consider time frame urgency
            time_frame_multiplier = {
                'immediate': 1.3,
                'short_term': 1.1,
                'medium_term': 1.0,
                'long_term': 0.9
            }.get(signal.time_frame, 1.0)
            
            base_score = severity_score * confidence_score
            return base_score * events_boost * time_frame_multiplier
        
        filtered.sort(key=signal_score, reverse=True)
        
        return filtered
    
    def generate_investment_report(self, signals: List[AnomalySignal]) -> str:
        """Generate investment-focused anomaly report."""
        report = []
        report.append("INVESTMENT ANOMALY DETECTION REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Signals: {len(signals)}")
        report.append("")
        
        # Group by signal type
        buy_signals = [s for s in signals if s.signal == 'buy']
        sell_signals = [s for s in signals if s.signal == 'sell']
        watch_signals = [s for s in signals if s.signal == 'watch']
        
        report.append(f"BUY SIGNALS ({len(buy_signals)})")
        report.append("-" * 20)
        for signal in buy_signals[:5]:  # Top 5
            report.append(f"  {signal.symbol}: {signal.description}")
            report.append(f"    Confidence: {signal.confidence:.1%}, Expected Return: {signal.potential_return:.1%}" if signal.potential_return else f"    Confidence: {signal.confidence:.1%}")
            report.append(f"    Time Frame: {signal.time_frame}, Duration: {signal.expected_duration}")
            report.append("")
        
        report.append(f"SELL SIGNALS ({len(sell_signals)})")
        report.append("-" * 20)
        for signal in sell_signals[:5]:  # Top 5
            report.append(f"  {signal.symbol}: {signal.description}")
            report.append(f"    Confidence: {signal.confidence:.1%}, Expected Return: {signal.potential_return:.1%}" if signal.potential_return else f"    Confidence: {signal.confidence:.1%}")
            report.append(f"    Time Frame: {signal.time_frame}, Duration: {signal.expected_duration}")
            report.append("")
        
        report.append(f"WATCH SIGNALS ({len(watch_signals)})")
        report.append("-" * 20)
        for signal in watch_signals[:3]:  # Top 3
            report.append(f"  {signal.symbol}: {signal.description}")
            report.append(f"    Confidence: {signal.confidence:.1%}")
            report.append(f"    Time Frame: {signal.time_frame}, Duration: {signal.expected_duration}")
            report.append("")
        
        return "\n".join(report)
    
    def get_portfolio_summary(self, signals: List[AnomalySignal]) -> Dict[str, Any]:
        """Get portfolio-level summary of anomalies."""
        summary = {
            'total_signals': len(signals),
            'by_signal': {
                'buy': len([s for s in signals if s.signal == 'buy']),
                'sell': len([s for s in signals if s.signal == 'sell']),
                'hold': len([s for s in signals if s.signal == 'hold']),
                'watch': len([s for s in signals if s.signal == 'watch'])
            },
            'by_severity': {
                'critical': len([s for s in signals if s.severity == 'critical']),
                'high': len([s for s in signals if s.severity == 'high']),
                'medium': len([s for s in signals if s.severity == 'medium']),
                'low': len([s for s in signals if s.severity == 'low'])
            },
            'by_time_frame': {
                'immediate': len([s for s in signals if s.time_frame == 'immediate']),
                'short_term': len([s for s in signals if s.time_frame == 'short_term']),
                'medium_term': len([s for s in signals if s.time_frame == 'medium_term']),
                'long_term': len([s for s in signals if s.time_frame == 'long_term'])
            },
            'avg_confidence': np.mean([s.confidence for s in signals]) if signals else 0,
            'expected_returns': [s.potential_return for s in signals if s.potential_return is not None]
        }
        
        if summary['expected_returns']:
            summary['avg_expected_return'] = np.mean(summary['expected_returns'])
            summary['total_expected_return'] = np.sum(summary['expected_returns'])
        
        return summary