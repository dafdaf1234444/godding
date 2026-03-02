"""
Pairs Trading Framework with Statistical Arbitrage.
Implements cointegration tests, VECM models, and pair selection algorithms.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import warnings

# Statistical libraries for cointegration and VECM
try:
    from statsmodels.tsa.vector_ar.vecm import VECM
    from statsmodels.tsa.stattools import coint
    from statsmodels.stats.diagnostic import acorr_ljungbox
    from statsmodels.regression.linear_model import OLS
    import statsmodels.api as sm
except ImportError:
    warnings.warn("statsmodels not available - pairs trading functionality limited")


logger = logging.getLogger(__name__)


class PairSelectionMethod(Enum):
    """Methods for selecting trading pairs."""
    DISTANCE = "distance"
    COINTEGRATION = "cointegration"
    CORRELATION = "correlation"
    SECTOR_NEUTRAL = "sector_neutral"


class TradingSignal(Enum):
    """Trading signals for pairs."""
    LONG_SPREAD = "long_spread"    # Long stock1, short stock2
    SHORT_SPREAD = "short_spread"  # Short stock1, long stock2
    NO_SIGNAL = "no_signal"
    CLOSE_POSITION = "close_position"


@dataclass
class PairTradingSignal:
    """Represents a pairs trading signal."""
    stock1: str
    stock2: str
    signal: TradingSignal
    spread_value: float
    zscore: float
    confidence: float
    timestamp: datetime
    entry_threshold: float
    exit_threshold: float
    stop_loss: float
    expected_return: float
    risk_level: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'stock1': self.stock1,
            'stock2': self.stock2,
            'signal': self.signal.value,
            'spread_value': self.spread_value,
            'zscore': self.zscore,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'entry_threshold': self.entry_threshold,
            'exit_threshold': self.exit_threshold,
            'stop_loss': self.stop_loss,
            'expected_return': self.expected_return,
            'risk_level': self.risk_level
        }


@dataclass
class CointegrationResult:
    """Results from cointegration analysis."""
    stock1: str
    stock2: str
    cointegration_stat: float
    p_value: float
    critical_values: Dict[str, float]
    is_cointegrated: bool
    hedge_ratio: float
    adf_stat: float
    half_life: float
    
    def __post_init__(self):
        """Calculate cointegration strength."""
        if self.p_value <= 0.01:
            self.strength = "very_strong"
        elif self.p_value <= 0.05:
            self.strength = "strong"
        elif self.p_value <= 0.10:
            self.strength = "moderate"
        else:
            self.strength = "weak"


class PairSelector:
    """Algorithms for selecting optimal trading pairs."""
    
    def __init__(self, method: PairSelectionMethod = PairSelectionMethod.COINTEGRATION):
        """Initialize pair selector."""
        self.method = method
        self.min_observations = 252  # Minimum 1 year of data
        
    def select_pairs(self, 
                    data: Dict[str, pd.DataFrame], 
                    max_pairs: int = 10,
                    sector_data: Optional[Dict[str, str]] = None) -> List[Tuple[str, str]]:
        """
        Select optimal trading pairs from available data.
        
        Args:
            data: Dictionary of stock price data
            max_pairs: Maximum number of pairs to select
            sector_data: Optional sector classification for sector-neutral pairs
            
        Returns:
            List of (stock1, stock2) tuples representing selected pairs
        """
        logger.info(f"Selecting pairs using {self.method.value} method")
        
        # Filter data for sufficient observations
        valid_stocks = {}
        for symbol, df in data.items():
            if len(df) >= self.min_observations and 'Close' in df.columns:
                valid_stocks[symbol] = df['Close'].dropna()
        
        if len(valid_stocks) < 2:
            logger.warning("Insufficient data for pair selection")
            return []
        
        symbols = list(valid_stocks.keys())
        logger.info(f"Analyzing {len(symbols)} stocks for pair selection")
        
        if self.method == PairSelectionMethod.COINTEGRATION:
            return self._select_by_cointegration(valid_stocks, max_pairs)
        elif self.method == PairSelectionMethod.DISTANCE:
            return self._select_by_distance(valid_stocks, max_pairs)
        elif self.method == PairSelectionMethod.CORRELATION:
            return self._select_by_correlation(valid_stocks, max_pairs)
        elif self.method == PairSelectionMethod.SECTOR_NEUTRAL:
            return self._select_sector_neutral(valid_stocks, max_pairs, sector_data)
        else:
            raise ValueError(f"Unknown selection method: {self.method}")
    
    def _select_by_cointegration(self, data: Dict[str, pd.Series], max_pairs: int) -> List[Tuple[str, str]]:
        """Select pairs based on cointegration test results."""
        symbols = list(data.keys())
        cointegration_scores = []
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                stock1, stock2 = symbols[i], symbols[j]
                
                try:
                    # Align data
                    common_index = data[stock1].index.intersection(data[stock2].index)
                    if len(common_index) < self.min_observations:
                        continue
                    
                    price1 = data[stock1].loc[common_index]
                    price2 = data[stock2].loc[common_index]
                    
                    # Log prices for cointegration test
                    log_price1 = np.log(price1)
                    log_price2 = np.log(price2)
                    
                    # Perform cointegration test
                    coint_stat, p_value, crit_values = coint(log_price1, log_price2)
                    
                    # Calculate hedge ratio
                    X = sm.add_constant(log_price2)
                    model = OLS(log_price1, X).fit()
                    hedge_ratio = model.params.iloc[1]
                    
                    cointegration_scores.append({
                        'pair': (stock1, stock2),
                        'p_value': p_value,
                        'coint_stat': abs(coint_stat),
                        'hedge_ratio': hedge_ratio,
                        'score': -p_value  # Lower p-value = better pair
                    })
                    
                except Exception as e:
                    logger.debug(f"Error testing cointegration for {stock1}-{stock2}: {e}")
                    continue
        
        # Sort by cointegration strength (lowest p-value first)
        cointegration_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Filter for significant cointegration (p < 0.1)
        significant_pairs = [
            item['pair'] for item in cointegration_scores 
            if item['p_value'] < 0.1
        ]
        
        logger.info(f"Found {len(significant_pairs)} cointegrated pairs")
        return significant_pairs[:max_pairs]
    
    def _select_by_distance(self, data: Dict[str, pd.Series], max_pairs: int) -> List[Tuple[str, str]]:
        """Select pairs using minimum distance approach."""
        symbols = list(data.keys())
        
        # Normalize price series
        normalized_data = {}
        for symbol, prices in data.items():
            normalized_data[symbol] = (prices / prices.iloc[0]).values
        
        # Calculate pairwise distances
        distance_scores = []
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                stock1, stock2 = symbols[i], symbols[j]
                
                try:
                    # Align data
                    common_index = data[stock1].index.intersection(data[stock2].index)
                    if len(common_index) < self.min_observations:
                        continue
                    
                    norm1 = normalized_data[stock1][:len(common_index)]
                    norm2 = normalized_data[stock2][:len(common_index)]
                    
                    # Calculate sum of squared differences
                    distance = np.sum((norm1 - norm2) ** 2)
                    
                    distance_scores.append({
                        'pair': (stock1, stock2),
                        'distance': distance,
                        'score': -distance  # Lower distance = better pair
                    })
                    
                except Exception as e:
                    logger.debug(f"Error calculating distance for {stock1}-{stock2}: {e}")
                    continue
        
        # Sort by distance (smallest first)
        distance_scores.sort(key=lambda x: x['score'], reverse=True)
        
        selected_pairs = [item['pair'] for item in distance_scores[:max_pairs]]
        logger.info(f"Selected {len(selected_pairs)} pairs by distance method")
        return selected_pairs
    
    def _select_by_correlation(self, data: Dict[str, pd.Series], max_pairs: int) -> List[Tuple[str, str]]:
        """Select pairs based on high correlation."""
        symbols = list(data.keys())
        correlation_scores = []
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                stock1, stock2 = symbols[i], symbols[j]
                
                try:
                    # Align data and calculate returns
                    common_index = data[stock1].index.intersection(data[stock2].index)
                    if len(common_index) < self.min_observations:
                        continue
                    
                    returns1 = data[stock1].loc[common_index].pct_change().dropna()
                    returns2 = data[stock2].loc[common_index].pct_change().dropna()
                    
                    # Calculate correlation
                    correlation = returns1.corr(returns2)
                    
                    if not np.isnan(correlation):
                        correlation_scores.append({
                            'pair': (stock1, stock2),
                            'correlation': correlation,
                            'score': correlation
                        })
                        
                except Exception as e:
                    logger.debug(f"Error calculating correlation for {stock1}-{stock2}: {e}")
                    continue
        
        # Sort by correlation (highest first)
        correlation_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Select pairs with correlation > 0.6 (more lenient threshold for testing)
        high_corr_pairs = [
            item['pair'] for item in correlation_scores 
            if item['correlation'] > 0.6
        ]
        
        logger.info(f"Selected {len(high_corr_pairs[:max_pairs])} highly correlated pairs")
        return high_corr_pairs[:max_pairs]
    
    def _select_sector_neutral(self, 
                              data: Dict[str, pd.Series], 
                              max_pairs: int,
                              sector_data: Optional[Dict[str, str]]) -> List[Tuple[str, str]]:
        """Select sector-neutral pairs."""
        if not sector_data:
            logger.warning("No sector data provided, falling back to cointegration method")
            return self._select_by_cointegration(data, max_pairs)
        
        # Group stocks by sector
        sectors = {}
        for symbol in data.keys():
            sector = sector_data.get(symbol, 'unknown')
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(symbol)
        
        # Select pairs within each sector
        sector_pairs = []
        pairs_per_sector = max(1, max_pairs // len(sectors))
        
        for sector, stocks in sectors.items():
            if len(stocks) >= 2:
                sector_data_subset = {symbol: data[symbol] for symbol in stocks}
                sector_specific_pairs = self._select_by_cointegration(
                    sector_data_subset, pairs_per_sector
                )
                sector_pairs.extend(sector_specific_pairs)
        
        logger.info(f"Selected {len(sector_pairs)} sector-neutral pairs")
        return sector_pairs[:max_pairs]


class CointegrationAnalyzer:
    """Advanced cointegration analysis for pairs trading."""
    
    def __init__(self):
        """Initialize cointegration analyzer."""
        self.min_half_life = 1    # Minimum half-life in days
        self.max_half_life = 252  # Maximum half-life in days
        
    def analyze_pair(self, 
                    price1: pd.Series, 
                    price2: pd.Series,
                    stock1: str,
                    stock2: str) -> Optional[CointegrationResult]:
        """
        Perform comprehensive cointegration analysis on a pair.
        
        Args:
            price1: Price series for first stock
            price2: Price series for second stock
            stock1: Symbol for first stock
            stock2: Symbol for second stock
            
        Returns:
            CointegrationResult object or None if analysis fails
        """
        try:
            # Align data
            common_index = price1.index.intersection(price2.index)
            if len(common_index) < 100:
                return None
            
            aligned_price1 = price1.loc[common_index]
            aligned_price2 = price2.loc[common_index]
            
            # Convert to log prices
            log_price1 = np.log(aligned_price1)
            log_price2 = np.log(aligned_price2)
            
            # Perform cointegration test
            coint_stat, p_value, crit_values = coint(log_price1, log_price2)
            crit_dict = {
                '1%': crit_values[0],
                '5%': crit_values[1],
                '10%': crit_values[2]
            }
            
            # Calculate hedge ratio using OLS
            X = sm.add_constant(log_price2)
            model = OLS(log_price1, X).fit()
            hedge_ratio = model.params.iloc[1]
            
            # Calculate spread and test for stationarity
            spread = log_price1 - hedge_ratio * log_price2
            
            # ADF test on spread
            try:
                from statsmodels.tsa.stattools import adfuller
                adf_result = adfuller(spread.dropna())
                adf_stat = adf_result[0]
            except:
                adf_stat = np.nan
            
            # Calculate half-life of mean reversion
            half_life = self._calculate_half_life(spread)
            
            # Determine if cointegrated
            is_cointegrated = (p_value < 0.05 and 
                             self.min_half_life <= half_life <= self.max_half_life)
            
            return CointegrationResult(
                stock1=stock1,
                stock2=stock2,
                cointegration_stat=coint_stat,
                p_value=p_value,
                critical_values=crit_dict,
                is_cointegrated=is_cointegrated,
                hedge_ratio=hedge_ratio,
                adf_stat=adf_stat,
                half_life=half_life
            )
            
        except Exception as e:
            logger.error(f"Error in cointegration analysis for {stock1}-{stock2}: {e}")
            return None
    
    def _calculate_half_life(self, spread: pd.Series) -> float:
        """Calculate the half-life of mean reversion for a spread."""
        try:
            # Clean the spread series
            spread_clean = spread.dropna()
            if len(spread_clean) < 20:
                return np.inf
            
            # Lag the spread
            spread_lag = spread_clean.shift(1).dropna()
            spread_ret = spread_clean.diff().dropna()
            
            # Align series
            min_len = min(len(spread_lag), len(spread_ret))
            spread_lag = spread_lag.iloc[-min_len:]
            spread_ret = spread_ret.iloc[-min_len:]
            
            # Run regression: Δspread = α + β * spread_lag + ε
            X = sm.add_constant(spread_lag)
            model = OLS(spread_ret, X).fit()
            
            # Half-life = -ln(2) / ln(1 + β)
            beta = model.params.iloc[1]
            if beta >= 0:
                return np.inf  # No mean reversion
            
            half_life = -np.log(2) / np.log(1 + beta)
            return max(0, half_life)
            
        except Exception as e:
            logger.debug(f"Error calculating half-life: {e}")
            return np.inf


class VECMPairsTradingModel:
    """Vector Error Correction Model for pairs trading."""
    
    def __init__(self, lookback_period: int = 252):
        """Initialize VECM model."""
        self.lookback_period = lookback_period
        self.model = None
        self.cointegration_result = None
        
    def fit(self, 
           price1: pd.Series, 
           price2: pd.Series) -> bool:
        """
        Fit VECM model to price data.
        
        Args:
            price1: Price series for first stock
            price2: Price series for second stock
            
        Returns:
            True if model fitted successfully, False otherwise
        """
        try:
            # Align data
            common_index = price1.index.intersection(price2.index)
            if len(common_index) < self.lookback_period:
                logger.warning("Insufficient data for VECM fitting")
                return False
            
            # Take most recent data
            recent_data = common_index[-self.lookback_period:]
            log_price1 = np.log(price1.loc[recent_data])
            log_price2 = np.log(price2.loc[recent_data])
            
            # Create matrix for VECM
            data_matrix = pd.DataFrame({
                'stock1': log_price1,
                'stock2': log_price2
            }).dropna()
            
            if len(data_matrix) < 100:
                return False
            
            # Fit VECM with 1 lag (can be optimized)
            self.model = VECM(data_matrix, k_ar_diff=1, coint_rank=1)
            self.vecm_result = self.model.fit()
            
            logger.info("VECM model fitted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error fitting VECM model: {e}")
            return False
    
    def predict_next_period(self) -> Optional[Tuple[float, float]]:
        """
        Predict next period prices using VECM.
        
        Returns:
            Tuple of (stock1_forecast, stock2_forecast) or None if prediction fails
        """
        if self.model is None or self.vecm_result is None:
            return None
        
        try:
            # Get forecast
            forecast = self.vecm_result.forecast(steps=1)
            return float(forecast[0, 0]), float(forecast[0, 1])
            
        except Exception as e:
            logger.error(f"Error predicting with VECM: {e}")
            return None
    
    def get_error_correction_terms(self) -> Optional[pd.Series]:
        """Get error correction terms from the model."""
        if self.vecm_result is None:
            return None
        
        try:
            # Extract error correction terms
            ec_terms = self.vecm_result.resid
            return pd.Series(ec_terms[:, 0])  # First equation's residuals
            
        except Exception as e:
            logger.error(f"Error extracting error correction terms: {e}")
            return None


class PairsTradingStrategy:
    """Complete pairs trading strategy with signal generation."""
    
    def __init__(self, 
                 entry_threshold: float = 2.0,
                 exit_threshold: float = 0.5,
                 stop_loss: float = 3.0,
                 lookback_window: int = 60,
                 min_half_life: int = 1,
                 max_half_life: int = 100):
        """
        Initialize pairs trading strategy.
        
        Args:
            entry_threshold: Z-score threshold for entering trades
            exit_threshold: Z-score threshold for exiting trades
            stop_loss: Z-score threshold for stop-loss
            lookback_window: Window for calculating statistics
            min_half_life: Minimum acceptable half-life for mean reversion
            max_half_life: Maximum acceptable half-life for mean reversion
        """
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.stop_loss = stop_loss
        self.lookback_window = lookback_window
        self.min_half_life = min_half_life
        self.max_half_life = max_half_life
        
        self.pair_selector = PairSelector()
        self.cointegration_analyzer = CointegrationAnalyzer()
        
        # Store active pairs and their models
        self.active_pairs = {}
        self.pair_models = {}
        
    def analyze_universe(self, 
                        data: Dict[str, pd.DataFrame],
                        max_pairs: int = 10) -> List[CointegrationResult]:
        """
        Analyze universe of stocks and identify tradeable pairs.
        
        Args:
            data: Dictionary of stock price data
            max_pairs: Maximum number of pairs to analyze
            
        Returns:
            List of CointegrationResult objects for viable pairs
        """
        logger.info("Analyzing universe for pairs trading opportunities")
        
        # Select pairs using cointegration method
        selected_pairs = self.pair_selector.select_pairs(data, max_pairs * 2)  # Get more candidates
        
        # Perform detailed cointegration analysis
        cointegration_results = []
        
        for stock1, stock2 in selected_pairs:
            if stock1 in data and stock2 in data:
                price1 = data[stock1]['Close'] if 'Close' in data[stock1].columns else data[stock1].iloc[:, 0]
                price2 = data[stock2]['Close'] if 'Close' in data[stock2].columns else data[stock2].iloc[:, 0]
                
                coint_result = self.cointegration_analyzer.analyze_pair(
                    price1, price2, stock1, stock2
                )
                
                if coint_result and coint_result.is_cointegrated:
                    cointegration_results.append(coint_result)
                    logger.info(f"Found cointegrated pair: {stock1}-{stock2} "
                              f"(p-value: {coint_result.p_value:.4f}, "
                              f"half-life: {coint_result.half_life:.1f} days)")
        
        # Sort by cointegration strength (lowest p-value first)
        cointegration_results.sort(key=lambda x: x.p_value)
        
        logger.info(f"Identified {len(cointegration_results)} viable trading pairs")
        return cointegration_results[:max_pairs]
    
    def generate_signals(self, 
                        cointegration_results: List[CointegrationResult],
                        data: Dict[str, pd.DataFrame]) -> List[PairTradingSignal]:
        """
        Generate trading signals for cointegrated pairs.
        
        Args:
            cointegration_results: List of cointegrated pairs
            data: Current price data
            
        Returns:
            List of PairTradingSignal objects
        """
        signals = []
        current_time = datetime.now()
        
        for coint_result in cointegration_results:
            try:
                signal = self._generate_pair_signal(coint_result, data, current_time)
                if signal and signal.signal != TradingSignal.NO_SIGNAL:
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Error generating signal for {coint_result.stock1}-{coint_result.stock2}: {e}")
                continue
        
        logger.info(f"Generated {len(signals)} pairs trading signals")
        return signals
    
    def _generate_pair_signal(self, 
                             coint_result: CointegrationResult,
                             data: Dict[str, pd.DataFrame],
                             timestamp: datetime) -> Optional[PairTradingSignal]:
        """Generate trading signal for a specific pair."""
        stock1, stock2 = coint_result.stock1, coint_result.stock2
        
        if stock1 not in data or stock2 not in data:
            return None
        
        # Get price series
        price1 = data[stock1]['Close'] if 'Close' in data[stock1].columns else data[stock1].iloc[:, 0]
        price2 = data[stock2]['Close'] if 'Close' in data[stock2].columns else data[stock2].iloc[:, 0]
        
        # Align data
        common_index = price1.index.intersection(price2.index)
        if len(common_index) < self.lookback_window:
            return None
        
        # Use recent data for signal generation
        recent_data = common_index[-self.lookback_window:]
        recent_price1 = price1.loc[recent_data]
        recent_price2 = price2.loc[recent_data]
        
        # Calculate log prices and spread
        log_price1 = np.log(recent_price1)
        log_price2 = np.log(recent_price2)
        spread = log_price1 - coint_result.hedge_ratio * log_price2
        
        # Calculate z-score
        spread_mean = spread.mean()
        spread_std = spread.std()
        
        if spread_std == 0:
            return None
        
        current_spread = spread.iloc[-1]
        zscore = (current_spread - spread_mean) / spread_std
        
        # Determine signal
        signal_type = TradingSignal.NO_SIGNAL
        confidence = 0.0
        
        if zscore > self.entry_threshold:
            signal_type = TradingSignal.SHORT_SPREAD  # Spread is too high, expect reversion
            confidence = min(1.0, (abs(zscore) - self.entry_threshold) / self.entry_threshold)
        elif zscore < -self.entry_threshold:
            signal_type = TradingSignal.LONG_SPREAD   # Spread is too low, expect reversion
            confidence = min(1.0, (abs(zscore) - self.entry_threshold) / self.entry_threshold)
        
        # Calculate expected return and risk
        expected_return = self._calculate_expected_return(zscore, coint_result.half_life)
        risk_level = self._assess_risk_level(coint_result, abs(zscore))
        
        return PairTradingSignal(
            stock1=stock1,
            stock2=stock2,
            signal=signal_type,
            spread_value=current_spread,
            zscore=zscore,
            confidence=confidence,
            timestamp=timestamp,
            entry_threshold=self.entry_threshold,
            exit_threshold=self.exit_threshold,
            stop_loss=self.stop_loss,
            expected_return=expected_return,
            risk_level=risk_level
        )
    
    def _calculate_expected_return(self, zscore: float, half_life: float) -> float:
        """Calculate expected return for the trade."""
        # Simple model: return proportional to z-score and inversely to half-life
        if half_life <= 0:
            return 0.0
        
        # Expected mean reversion percentage
        mean_reversion_speed = 1.0 / half_life
        expected_return = abs(zscore) * mean_reversion_speed * 0.01  # Scale to reasonable percentage
        
        return min(expected_return, 0.1)  # Cap at 10%
    
    def _assess_risk_level(self, coint_result: CointegrationResult, abs_zscore: float) -> str:
        """Assess risk level for the trade."""
        # Consider cointegration strength and current deviation
        if coint_result.p_value < 0.01 and abs_zscore < 2.5:
            return "low"
        elif coint_result.p_value < 0.05 and abs_zscore < 3.0:
            return "medium"
        else:
            return "high"
    
    def backtest_strategy(self, 
                         data: Dict[str, pd.DataFrame],
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Backtest the pairs trading strategy.
        
        Args:
            data: Historical price data
            start_date: Start date for backtest
            end_date: End date for backtest
            
        Returns:
            Dictionary with backtest results
        """
        logger.info("Starting pairs trading strategy backtest")
        
        # This would implement a comprehensive backtest
        # For now, return a placeholder structure
        backtest_results = {
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'num_trades': 0,
            'win_rate': 0.0,
            'avg_trade_duration': 0.0,
            'pairs_analyzed': 0,
            'successful_pairs': 0
        }
        
        logger.info("Backtest completed")
        return backtest_results


# Main pairs trading interface
class PairsTradingFramework:
    """Main interface for pairs trading functionality."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize pairs trading framework."""
        self.config = config or {}
        self.strategy = PairsTradingStrategy(
            entry_threshold=self.config.get('entry_threshold', 2.0),
            exit_threshold=self.config.get('exit_threshold', 0.5),
            stop_loss=self.config.get('stop_loss', 3.0),
            lookback_window=self.config.get('lookback_window', 60)
        )
        
        logger.info("Pairs trading framework initialized")
    
    def run_analysis(self, 
                    data: Dict[str, pd.DataFrame],
                    max_pairs: int = 10) -> Dict[str, Any]:
        """
        Run complete pairs trading analysis.
        
        Args:
            data: Stock price data
            max_pairs: Maximum number of pairs to analyze
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("Running pairs trading analysis")
        
        try:
            # Analyze universe and find cointegrated pairs
            cointegration_results = self.strategy.analyze_universe(data, max_pairs)
            
            # Generate trading signals
            trading_signals = self.strategy.generate_signals(cointegration_results, data)
            
            # Compile results
            results = {
                'timestamp': datetime.now().isoformat(),
                'pairs_analyzed': len(cointegration_results),
                'trading_signals': [signal.to_dict() for signal in trading_signals],
                'cointegration_results': [
                    {
                        'stock1': result.stock1,
                        'stock2': result.stock2,
                        'p_value': result.p_value,
                        'hedge_ratio': result.hedge_ratio,
                        'half_life': result.half_life,
                        'strength': result.strength
                    }
                    for result in cointegration_results
                ],
                'summary': {
                    'total_pairs_found': len(cointegration_results),
                    'active_signals': len(trading_signals),
                    'avg_half_life': np.mean([r.half_life for r in cointegration_results]) if cointegration_results else 0,
                    'best_pair': None
                }
            }
            
            # Identify best pair
            if cointegration_results:
                best_pair = min(cointegration_results, key=lambda x: x.p_value)
                results['summary']['best_pair'] = f"{best_pair.stock1}-{best_pair.stock2}"
            
            logger.info(f"Pairs trading analysis completed: {len(cointegration_results)} pairs, {len(trading_signals)} signals")
            return results
            
        except Exception as e:
            logger.error(f"Error in pairs trading analysis: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'pairs_analyzed': 0,
                'trading_signals': [],
                'cointegration_results': []
            }