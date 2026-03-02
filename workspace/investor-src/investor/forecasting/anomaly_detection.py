"""
Anomaly detection for financial time series.
Finds interesting patterns like vol-price dependencies, regime changes, etc.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Any
import logging
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from scipy import stats
from scipy.stats import jarque_bera, normaltest
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class FinancialAnomalyDetector:
    """
    Detect anomalies and interesting patterns in financial time series.
    
    Features:
    - Volume-Price relationship anomalies
    - Volatility regime changes
    - Return distribution anomalies
    - Cross-asset correlation breaks
    - Momentum anomalies
    - Seasonality anomalies
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize anomaly detector."""
        self.config = config or self._get_default_config()
        self.anomalies = {}
        self.patterns = {}
        self.scalers = {}
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'anomaly_detection': {
                'isolation_forest': {
                    'contamination': 0.1,
                    'random_state': 42
                },
                'dbscan': {
                    'eps': 0.5,
                    'min_samples': 5
                },
                'statistical_thresholds': {
                    'z_score_threshold': 3.0,
                    'percentile_threshold': 0.95
                }
            },
            'pattern_detection': {
                'vol_price_window': 20,
                'regime_window': 30,
                'correlation_window': 60,
                'momentum_window': 10
            }
        }
    
    def detect_all_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect all types of anomalies in the dataset.
        
        Args:
            data: DataFrame with OHLCV data and additional features
            
        Returns:
            Dictionary containing all detected anomalies
        """
        logger.info("Starting comprehensive anomaly detection")
        
        results = {}
        
        # Volume-Price Anomalies
        results['volume_price_anomalies'] = self.detect_volume_price_anomalies(data)
        
        # Volatility Regime Changes
        results['volatility_regimes'] = self.detect_volatility_regimes(data)
        
        # Return Distribution Anomalies
        results['return_anomalies'] = self.detect_return_anomalies(data)
        
        # Price Level Anomalies
        results['price_anomalies'] = self.detect_price_anomalies(data)
        
        # Trading Volume Anomalies
        results['volume_anomalies'] = self.detect_volume_anomalies(data)
        
        # Momentum Anomalies
        results['momentum_anomalies'] = self.detect_momentum_anomalies(data)
        
        # Seasonality Anomalies
        results['seasonality_anomalies'] = self.detect_seasonality_anomalies(data)
        
        # Cross-Asset Patterns (if multiple symbols)
        if 'symbol' in data.columns and len(data['symbol'].unique()) > 1:
            results['cross_asset_anomalies'] = self.detect_cross_asset_anomalies(data)
        
        self.anomalies = results
        logger.info(f"Anomaly detection completed. Found {len(results)} anomaly types")
        
        return results
    
    def detect_volume_price_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in volume-price relationships."""
        logger.info("Detecting volume-price anomalies")
        
        anomalies = {}
        
        if 'Volume' not in data.columns:
            return anomalies
        
        # Group by symbol if multivariate
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['overall']
        
        for symbol in symbols:
            if symbol != 'overall':
                symbol_data = data[data['symbol'] == symbol].copy()
            else:
                symbol_data = data.copy()
                
            if len(symbol_data) < 50:
                continue
            
            symbol_anomalies = {}
            
            # Price-Volume Correlation Analysis
            window = self.config['pattern_detection']['vol_price_window']
            
            # Rolling correlation between price changes and volume
            symbol_data['price_change'] = symbol_data['Close'].pct_change()
            symbol_data['log_volume'] = np.log(symbol_data['Volume'] + 1)
            
            rolling_corr = symbol_data['price_change'].rolling(window).corr(symbol_data['log_volume'])
            
            # Detect correlation regime changes
            corr_changes = rolling_corr.diff().abs()
            high_corr_changes = corr_changes > corr_changes.quantile(0.95)
            
            symbol_anomalies['correlation_breaks'] = symbol_data[high_corr_changes].index.tolist()
            
            # Volume-Price Divergence
            # High volume with small price change (accumulation/distribution)
            log_volume_values = symbol_data['log_volume'].fillna(0)
            symbol_data['volume_zscore'] = pd.Series(stats.zscore(log_volume_values), index=log_volume_values.index)
            symbol_data['price_change_abs'] = symbol_data['price_change'].abs()
            
            # High volume + low price change
            high_vol_low_change = (
                (symbol_data['volume_zscore'] > 2) & 
                (symbol_data['price_change_abs'] < symbol_data['price_change_abs'].quantile(0.3))
            )
            
            symbol_anomalies['high_volume_low_change'] = symbol_data[high_vol_low_change].index.tolist()
            
            # Low volume + high price change (potential manipulation or news)
            low_vol_high_change = (
                (symbol_data['volume_zscore'] < -1) & 
                (symbol_data['price_change_abs'] > symbol_data['price_change_abs'].quantile(0.9))
            )
            
            symbol_anomalies['low_volume_high_change'] = symbol_data[low_vol_high_change].index.tolist()
            
            # Volume spikes
            volume_spikes = symbol_data['volume_zscore'] > 3
            symbol_anomalies['volume_spikes'] = symbol_data[volume_spikes].index.tolist()
            
            anomalies[symbol] = symbol_anomalies
        
        return anomalies
    
    def detect_volatility_regimes(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect volatility regime changes."""
        logger.info("Detecting volatility regimes")
        
        regimes = {}
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['overall']
        
        for symbol in symbols:
            if symbol != 'overall':
                symbol_data = data[data['symbol'] == symbol].copy()
            else:
                symbol_data = data.copy()
                
            if len(symbol_data) < 100:
                continue
            
            # Calculate returns and volatility
            symbol_data['returns'] = symbol_data['Close'].pct_change()
            
            # Rolling volatility
            window = self.config['pattern_detection']['regime_window']
            symbol_data['volatility'] = symbol_data['returns'].rolling(window).std()
            
            # Detect regime changes using volatility clustering
            volatility_values = symbol_data['volatility'].fillna(0)
            vol_zscore = pd.Series(stats.zscore(volatility_values), index=volatility_values.index)
            
            # High volatility regime
            high_vol_regime = vol_zscore > 1.5
            
            # Low volatility regime  
            low_vol_regime = vol_zscore < -1.0
            
            # Regime transitions
            regime_changes = (
                (high_vol_regime.shift(1) != high_vol_regime) |
                (low_vol_regime.shift(1) != low_vol_regime)
            )
            
            regimes[symbol] = {
                'high_volatility_periods': symbol_data[high_vol_regime].index.tolist(),
                'low_volatility_periods': symbol_data[low_vol_regime].index.tolist(),
                'regime_changes': symbol_data[regime_changes].index.tolist(),
                'volatility_percentiles': {
                    'p95': symbol_data['volatility'].quantile(0.95),
                    'p50': symbol_data['volatility'].quantile(0.50),
                    'p05': symbol_data['volatility'].quantile(0.05)
                }
            }
        
        return regimes
    
    def detect_return_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in return distributions."""
        logger.info("Detecting return distribution anomalies")
        
        anomalies = {}
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['overall']
        
        for symbol in symbols:
            if symbol != 'overall':
                symbol_data = data[data['symbol'] == symbol].copy()
            else:
                symbol_data = data.copy()
                
            if len(symbol_data) < 100:
                continue
            
            symbol_data['returns'] = symbol_data['Close'].pct_change().dropna()
            returns = symbol_data['returns'].dropna()
            
            if len(returns) < 50:
                continue
            
            symbol_anomalies = {}
            
            # Statistical tests for normality
            try:
                jb_stat, jb_pvalue = jarque_bera(returns)
                nt_stat, nt_pvalue = normaltest(returns)
                
                symbol_anomalies['normality_tests'] = {
                    'jarque_bera': {'statistic': jb_stat, 'pvalue': jb_pvalue},
                    'normaltest': {'statistic': nt_stat, 'pvalue': nt_pvalue}
                }
            except:
                pass
            
            # Tail risk analysis
            symbol_anomalies['tail_analysis'] = {
                'skewness': returns.skew(),
                'kurtosis': returns.kurtosis(),
                'var_95': returns.quantile(0.05),
                'var_99': returns.quantile(0.01),
                'expected_shortfall_95': returns[returns <= returns.quantile(0.05)].mean(),
                'expected_shortfall_99': returns[returns <= returns.quantile(0.01)].mean()
            }
            
            # Extreme returns
            z_scores = pd.Series(stats.zscore(returns), index=returns.index)
            extreme_returns = np.abs(z_scores) > self.config['anomaly_detection']['statistical_thresholds']['z_score_threshold']
            
            symbol_anomalies['extreme_returns'] = {
                'dates': symbol_data[symbol_data['returns'].index.isin(returns[extreme_returns].index)].index.tolist(),
                'values': returns[extreme_returns].tolist()
            }
            
            # Return clustering (using DBSCAN)
            try:
                returns_reshaped = returns.values.reshape(-1, 1)
                scaler = StandardScaler()
                returns_scaled = scaler.fit_transform(returns_reshaped)
                
                dbscan = DBSCAN(**self.config['anomaly_detection']['dbscan'])
                clusters = dbscan.fit_predict(returns_scaled)
                
                # Outliers are labeled as -1
                outliers = clusters == -1
                symbol_anomalies['return_outliers'] = returns[outliers].index.tolist()
                
            except:
                pass
            
            anomalies[symbol] = symbol_anomalies
        
        return anomalies
    
    def detect_price_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect price level anomalies."""
        logger.info("Detecting price anomalies")
        
        anomalies = {}
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['overall']
        
        for symbol in symbols:
            if symbol != 'overall':
                symbol_data = data[data['symbol'] == symbol].copy()
            else:
                symbol_data = data.copy()
                
            if len(symbol_data) < 50:
                continue
            
            symbol_anomalies = {}
            
            # Gap analysis
            symbol_data['gap'] = (symbol_data['Open'] - symbol_data['Close'].shift(1)) / symbol_data['Close'].shift(1)
            gap_threshold = symbol_data['gap'].std() * 2
            large_gaps = symbol_data['gap'].abs() > gap_threshold
            symbol_anomalies['large_gaps'] = symbol_data[large_gaps].index.tolist()
            
            # Price level breaks (support/resistance)
            # Rolling max/min levels
            window = 20
            symbol_data['resistance'] = symbol_data['High'].rolling(window).max()
            symbol_data['support'] = symbol_data['Low'].rolling(window).min()
            
            # Breakouts
            resistance_breaks = symbol_data['Close'] > symbol_data['resistance'].shift(1)
            support_breaks = symbol_data['Close'] < symbol_data['support'].shift(1)
            
            symbol_anomalies['resistance_breaks'] = symbol_data[resistance_breaks].index.tolist()
            symbol_anomalies['support_breaks'] = symbol_data[support_breaks].index.tolist()
            
            # Price isolation forest
            try:
                price_features = symbol_data[['Open', 'High', 'Low', 'Close']].fillna(method='ffill')
                if len(price_features) > 20:
                    isolation_forest = IsolationForest(**self.config['anomaly_detection']['isolation_forest'])
                    outliers = isolation_forest.fit_predict(price_features)
                    price_outliers = outliers == -1
                    symbol_anomalies['price_outliers'] = symbol_data[price_outliers].index.tolist()
            except:
                pass
            
            anomalies[symbol] = symbol_anomalies
        
        return anomalies
    
    def detect_volume_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect volume anomalies."""
        logger.info("Detecting volume anomalies")
        
        anomalies = {}
        
        if 'Volume' not in data.columns:
            return anomalies
        
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['overall']
        
        for symbol in symbols:
            if symbol != 'overall':
                symbol_data = data[data['symbol'] == symbol].copy()
            else:
                symbol_data = data.copy()
                
            if len(symbol_data) < 50:
                continue
            
            symbol_anomalies = {}
            
            # Volume isolation forest
            try:
                volume_features = symbol_data[['Volume']].fillna(0)
                volume_features['log_volume'] = np.log(volume_features['Volume'] + 1)
                
                isolation_forest = IsolationForest(**self.config['anomaly_detection']['isolation_forest'])
                outliers = isolation_forest.fit_predict(volume_features[['log_volume']])
                volume_outliers = outliers == -1
                
                symbol_anomalies['volume_outliers'] = symbol_data[volume_outliers].index.tolist()
            except:
                pass
            
            # Volume dry-ups (extremely low volume)
            log_volume = np.log(symbol_data['Volume'] + 1)
            volume_threshold = log_volume.quantile(0.05)
            volume_dryups = log_volume < volume_threshold
            symbol_anomalies['volume_dryups'] = symbol_data[volume_dryups].index.tolist()
            
            anomalies[symbol] = symbol_anomalies
        
        return anomalies
    
    def detect_momentum_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect momentum anomalies."""
        logger.info("Detecting momentum anomalies")
        
        anomalies = {}
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['overall']
        
        for symbol in symbols:
            if symbol != 'overall':
                symbol_data = data[data['symbol'] == symbol].copy()
            else:
                symbol_data = data.copy()
                
            if len(symbol_data) < 50:
                continue
            
            symbol_anomalies = {}
            
            # Calculate momentum indicators
            window = self.config['pattern_detection']['momentum_window']
            symbol_data['momentum'] = symbol_data['Close'] / symbol_data['Close'].shift(window) - 1
            symbol_data['roc'] = symbol_data['Close'].pct_change(window)
            
            # Momentum reversals
            momentum_values = symbol_data['momentum'].fillna(0)
            momentum_zscore = pd.Series(stats.zscore(momentum_values), index=momentum_values.index)
            extreme_momentum = np.abs(momentum_zscore) > 2
            
            # Look for reversals after extreme momentum
            momentum_reversals = (
                (extreme_momentum.shift(1) == True) & 
                (np.sign(symbol_data['momentum']) != np.sign(symbol_data['momentum'].shift(1)))
            )
            
            symbol_anomalies['momentum_reversals'] = symbol_data[momentum_reversals].index.tolist()
            symbol_anomalies['extreme_momentum'] = symbol_data[extreme_momentum].index.tolist()
            
            anomalies[symbol] = symbol_anomalies
        
        return anomalies
    
    def detect_seasonality_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect seasonality anomalies."""
        logger.info("Detecting seasonality anomalies")
        
        anomalies = {}
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['overall']
        
        for symbol in symbols:
            if symbol != 'overall':
                symbol_data = data[data['symbol'] == symbol].copy()
            else:
                symbol_data = data.copy()
                
            if len(symbol_data) < 252:  # Need at least a year of data
                continue
            
            symbol_anomalies = {}
            
            # Add time features
            symbol_data['day_of_week'] = symbol_data['Date'].dt.dayofweek
            symbol_data['month'] = symbol_data['Date'].dt.month
            symbol_data['returns'] = symbol_data['Close'].pct_change()
            
            # Day of week effects
            dow_returns = symbol_data.groupby('day_of_week')['returns'].agg(['mean', 'std', 'count'])
            dow_anomalies = dow_returns[dow_returns['count'] > 20]  # Sufficient data
            dow_anomalies = dow_returns[np.abs(stats.zscore(dow_returns['mean'])) > 1.5]
            
            symbol_anomalies['day_of_week_effects'] = dow_anomalies.to_dict()
            
            # Monthly effects
            monthly_returns = symbol_data.groupby('month')['returns'].agg(['mean', 'std', 'count'])
            monthly_anomalies = monthly_returns[monthly_returns['count'] > 10]
            monthly_anomalies = monthly_returns[np.abs(stats.zscore(monthly_returns['mean'])) > 1.5]
            
            symbol_anomalies['monthly_effects'] = monthly_anomalies.to_dict()
            
            anomalies[symbol] = symbol_anomalies
        
        return anomalies
    
    def detect_cross_asset_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect cross-asset anomalies."""
        logger.info("Detecting cross-asset anomalies")
        
        anomalies = {}
        
        if 'symbol' not in data.columns:
            return anomalies
        
        symbols = data['symbol'].unique()
        
        if len(symbols) < 2:
            return anomalies
        
        # Create pivot table of returns
        data['returns'] = data.groupby('symbol')['Close'].pct_change()
        returns_pivot = data.pivot_table(values='returns', index='Date', columns='symbol', fill_value=0)
        
        if returns_pivot.shape[1] < 2:
            return anomalies
        
        # Rolling correlation analysis
        window = self.config['pattern_detection']['correlation_window']
        
        correlations = {}
        correlation_breaks = {}
        
        for i, symbol1 in enumerate(symbols):
            for symbol2 in symbols[i+1:]:
                if symbol1 in returns_pivot.columns and symbol2 in returns_pivot.columns:
                    # Rolling correlation
                    rolling_corr = returns_pivot[symbol1].rolling(window).corr(returns_pivot[symbol2])
                    
                    # Detect correlation breaks
                    corr_changes = rolling_corr.diff().abs()
                    breaks = corr_changes > corr_changes.quantile(0.95)
                    
                    correlation_breaks[f"{symbol1}_{symbol2}"] = returns_pivot[breaks].index.tolist()
                    correlations[f"{symbol1}_{symbol2}"] = rolling_corr.dropna().tolist()
        
        anomalies['correlation_breaks'] = correlation_breaks
        anomalies['correlations'] = correlations
        
        # Cross-asset momentum divergence
        momentum_divergences = {}
        
        for symbol in symbols:
            if symbol in returns_pivot.columns:
                symbol_momentum = returns_pivot[symbol].rolling(10).mean()
                market_momentum = returns_pivot.mean(axis=1).rolling(10).mean()
                
                divergence = symbol_momentum - market_momentum
                divergence_values = divergence.fillna(0)
                extreme_divergence = np.abs(pd.Series(stats.zscore(divergence_values), index=divergence_values.index)) > 2
                
                momentum_divergences[symbol] = returns_pivot[extreme_divergence].index.tolist()
        
        anomalies['momentum_divergences'] = momentum_divergences
        
        return anomalies
    
    def generate_anomaly_report(self) -> str:
        """Generate a text report of all detected anomalies."""
        if not self.anomalies:
            return "No anomalies detected. Run detect_all_anomalies() first."
        
        report = []
        report.append("FINANCIAL ANOMALY DETECTION REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        for anomaly_type, anomaly_data in self.anomalies.items():
            report.append(f"\n{anomaly_type.upper().replace('_', ' ')}")
            report.append("-" * 30)
            
            if isinstance(anomaly_data, dict):
                for symbol, symbol_anomalies in anomaly_data.items():
                    if isinstance(symbol_anomalies, dict) and symbol_anomalies:
                        report.append(f"\n  {symbol}:")
                        for pattern, values in symbol_anomalies.items():
                            if isinstance(values, list) and values:
                                report.append(f"    {pattern}: {len(values)} occurrences")
                            elif isinstance(values, dict):
                                report.append(f"    {pattern}: {values}")
        
        return "\n".join(report)
    
    def get_top_anomalies(self, limit: int = 10) -> Dict[str, Any]:
        """Get the most significant anomalies across all types."""
        if not self.anomalies:
            return {}
        
        top_anomalies = {}
        
        for anomaly_type, anomaly_data in self.anomalies.items():
            type_counts = {}
            
            if isinstance(anomaly_data, dict):
                for symbol, symbol_anomalies in anomaly_data.items():
                    if isinstance(symbol_anomalies, dict):
                        for pattern, values in symbol_anomalies.items():
                            if isinstance(values, list):
                                count = len(values)
                                if count > 0:
                                    type_counts[f"{symbol}_{pattern}"] = count
            
            # Get top patterns for this anomaly type
            if type_counts:
                sorted_patterns = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
                top_anomalies[anomaly_type] = sorted_patterns[:limit]
        
        return top_anomalies