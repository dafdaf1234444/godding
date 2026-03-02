"""
Advanced anomaly detection for financial time series using modern techniques.
Includes Kalman filters, autoencoders, isolation forests, and time series decomposition.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.covariance import EllipticEnvelope
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class AdvancedAnomalyDetector:
    """
    Advanced anomaly detection using state-of-the-art techniques.
    
    Methods:
    - Kalman Filter for state estimation and anomaly detection
    - Isolation Forest for outlier detection
    - Autoencoder-based anomaly detection (if TensorFlow available)
    - Time series decomposition anomalies
    - Multivariate Gaussian anomaly detection
    - Change point detection
    - Regime switching detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize advanced anomaly detector."""
        self.config = config or self._get_default_config()
        self.scalers = {}
        self.fitted_models = {}
        self.anomaly_scores = {}
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'kalman_filter': {
                'process_variance': 1e-5,
                'measurement_variance': 1e-1,
                'anomaly_threshold': 3.0
            },
            'isolation_forest': {
                'contamination': 0.1,
                'n_estimators': 100,
                'random_state': 42
            },
            'autoencoder': {
                'encoding_dim': 32,
                'epochs': 50,
                'batch_size': 32,
                'anomaly_threshold': 95  # percentile
            },
            'multivariate_gaussian': {
                'contamination': 0.1
            },
            'change_point': {
                'window_size': 30,
                'threshold': 2.0
            }
        }
    
    def detect_kalman_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect anomalies using Kalman Filter for state estimation.
        """
        logger.info("Detecting anomalies using Kalman Filter")
        
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
            
            # Apply Kalman filter to price series
            prices = symbol_data['Close'].values
            kalman_states, innovations, innovation_variances = self._kalman_filter(prices)
            
            # Calculate standardized innovations (anomaly scores)
            standardized_innovations = innovations / np.sqrt(innovation_variances)
            
            # Detect anomalies based on innovation magnitude
            threshold = self.config['kalman_filter']['anomaly_threshold']
            anomaly_mask = np.abs(standardized_innovations) > threshold
            
            symbol_anomalies['kalman_anomalies'] = symbol_data[anomaly_mask].index.tolist()
            symbol_anomalies['innovation_scores'] = standardized_innovations.tolist()
            symbol_anomalies['kalman_states'] = kalman_states.tolist()
            
            # Detect regime changes based on innovation variance
            variance_changes = self._detect_variance_changes(innovation_variances)
            symbol_anomalies['regime_changes'] = symbol_data.iloc[variance_changes].index.tolist()
            
            anomalies[symbol] = symbol_anomalies
        
        return anomalies
    
    def _kalman_filter(self, observations: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Apply Kalman filter to price series.
        
        Returns:
            states: Estimated states (prices)
            innovations: Prediction errors
            innovation_variances: Variance of innovations
        """
        n = len(observations)
        
        # State transition and observation matrices
        F = np.array([[1.0]])  # State transition (random walk)
        H = np.array([[1.0]])  # Observation matrix
        
        # Process and measurement noise covariances
        Q = np.array([[self.config['kalman_filter']['process_variance']]])
        R = np.array([[self.config['kalman_filter']['measurement_variance']]])
        
        # Initialize
        x = np.array([[observations[0]]])  # Initial state
        P = np.array([[1.0]])  # Initial state covariance
        
        states = np.zeros(n)
        innovations = np.zeros(n)
        innovation_variances = np.zeros(n)
        
        for t in range(n):
            # Prediction step
            x_pred = F @ x
            P_pred = F @ P @ F.T + Q
            
            # Update step
            y = observations[t] - H @ x_pred  # Innovation
            S = H @ P_pred @ H.T + R  # Innovation covariance
            K = P_pred @ H.T @ np.linalg.inv(S)  # Kalman gain
            
            x = x_pred + K @ y
            P = (np.eye(1) - K @ H) @ P_pred
            
            # Store results
            states[t] = x[0, 0]
            innovations[t] = y[0, 0]
            innovation_variances[t] = S[0, 0]
        
        return states, innovations, innovation_variances
    
    def _detect_variance_changes(self, variances: np.ndarray, window: int = 20) -> List[int]:
        """Detect significant changes in variance (regime changes)."""
        if len(variances) < 2 * window:
            return []
        
        change_points = []
        
        for i in range(window, len(variances) - window):
            # Compare variance before and after
            var_before = np.mean(variances[i-window:i])
            var_after = np.mean(variances[i:i+window])
            
            # Detect significant change
            if var_after > 2 * var_before or var_before > 2 * var_after:
                change_points.append(i)
        
        return change_points
    
    def detect_isolation_forest_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect anomalies using Isolation Forest on multiple features.
        """
        logger.info("Detecting anomalies using Isolation Forest")
        
        anomalies = {}
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['overall']
        
        for symbol in symbols:
            if symbol != 'overall':
                symbol_data = data[data['symbol'] == symbol].copy()
            else:
                symbol_data = data.copy()
            
            if len(symbol_data) < 50:
                continue
            
            # Prepare features for anomaly detection
            features = self._prepare_multivariate_features(symbol_data)
            
            if features.shape[1] < 2:
                continue
            
            # Apply Isolation Forest
            iso_forest = IsolationForest(**self.config['isolation_forest'])
            anomaly_labels = iso_forest.fit_predict(features)
            anomaly_scores = iso_forest.decision_function(features)
            
            anomaly_mask = anomaly_labels == -1
            
            anomalies[symbol] = {
                'isolation_forest_anomalies': symbol_data[anomaly_mask].index.tolist(),
                'anomaly_scores': anomaly_scores.tolist(),
                'feature_names': features.columns.tolist() if isinstance(features, pd.DataFrame) else None
            }
        
        return anomalies
    
    def detect_autoencoder_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect anomalies using autoencoder reconstruction error.
        Requires TensorFlow/Keras.
        """
        logger.info("Detecting anomalies using Autoencoder")
        
        try:
            import tensorflow as tf
            from tensorflow.keras.models import Model
            from tensorflow.keras.layers import Input, Dense
            from tensorflow.keras.optimizers import Adam
        except ImportError:
            logger.warning("TensorFlow not available, skipping autoencoder anomaly detection")
            return {}
        
        anomalies = {}
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['overall']
        
        for symbol in symbols:
            if symbol != 'overall':
                symbol_data = data[data['symbol'] == symbol].copy()
            else:
                symbol_data = data.copy()
            
            if len(symbol_data) < 100:
                continue
            
            # Prepare features
            features = self._prepare_multivariate_features(symbol_data)
            
            if features.shape[1] < 5:
                continue
            
            # Scale features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Build autoencoder
            input_dim = features_scaled.shape[1]
            encoding_dim = min(self.config['autoencoder']['encoding_dim'], input_dim // 2)
            
            input_layer = Input(shape=(input_dim,))
            encoded = Dense(encoding_dim, activation='relu')(input_layer)
            decoded = Dense(input_dim, activation='linear')(encoded)
            
            autoencoder = Model(input_layer, decoded)
            autoencoder.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
            
            # Train autoencoder
            history = autoencoder.fit(
                features_scaled, features_scaled,
                epochs=self.config['autoencoder']['epochs'],
                batch_size=self.config['autoencoder']['batch_size'],
                verbose=0,
                validation_split=0.1
            )
            
            # Calculate reconstruction errors
            reconstructed = autoencoder.predict(features_scaled, verbose=0)
            reconstruction_errors = np.mean(np.square(features_scaled - reconstructed), axis=1)
            
            # Identify anomalies based on reconstruction error threshold
            threshold = np.percentile(reconstruction_errors, self.config['autoencoder']['anomaly_threshold'])
            anomaly_mask = reconstruction_errors > threshold
            
            anomalies[symbol] = {
                'autoencoder_anomalies': symbol_data[anomaly_mask].index.tolist(),
                'reconstruction_errors': reconstruction_errors.tolist(),
                'threshold': threshold,
                'training_loss': history.history['loss'][-1]
            }
        
        return anomalies
    
    def detect_multivariate_gaussian_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect anomalies using multivariate Gaussian distribution.
        """
        logger.info("Detecting anomalies using Multivariate Gaussian")
        
        anomalies = {}
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['overall']
        
        for symbol in symbols:
            if symbol != 'overall':
                symbol_data = data[data['symbol'] == symbol].copy()
            else:
                symbol_data = data.copy()
            
            if len(symbol_data) < 50:
                continue
            
            # Prepare features
            features = self._prepare_multivariate_features(symbol_data)
            
            if features.shape[1] < 2:
                continue
            
            # Apply Elliptic Envelope (robust covariance estimation)
            contamination = self.config['multivariate_gaussian']['contamination']
            elliptic_env = EllipticEnvelope(contamination=contamination, random_state=42)
            
            anomaly_labels = elliptic_env.fit_predict(features)
            anomaly_mask = anomaly_labels == -1
            
            # Calculate Mahalanobis distances
            mahalanobis_distances = elliptic_env.mahalanobis(features)
            
            anomalies[symbol] = {
                'multivariate_gaussian_anomalies': symbol_data[anomaly_mask].index.tolist(),
                'mahalanobis_distances': mahalanobis_distances.tolist()
            }
        
        return anomalies
    
    def detect_change_points(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect change points in time series using CUSUM-like algorithm.
        """
        logger.info("Detecting change points")
        
        change_points = {}
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['overall']
        
        for symbol in symbols:
            if symbol != 'overall':
                symbol_data = data[data['symbol'] == symbol].copy()
            else:
                symbol_data = data.copy()
            
            if len(symbol_data) < 100:
                continue
            
            symbol_change_points = {}
            
            # Apply change point detection to different series
            for column in ['Close', 'Volume']:
                if column in symbol_data.columns:
                    series = symbol_data[column].values
                    cp_indices = self._detect_change_points_cusum(series)
                    symbol_change_points[f'{column.lower()}_change_points'] = [
                        symbol_data.iloc[idx].name for idx in cp_indices
                    ]
            
            # Volatility change points
            returns = symbol_data['Close'].pct_change().dropna()
            if len(returns) > 50:
                volatility = returns.rolling(window=20).std().dropna()
                vol_cp = self._detect_change_points_cusum(volatility.values)
                symbol_change_points['volatility_change_points'] = [
                    volatility.iloc[idx].name for idx in vol_cp
                ]
            
            change_points[symbol] = symbol_change_points
        
        return change_points
    
    def _detect_change_points_cusum(self, series: np.ndarray) -> List[int]:
        """
        Detect change points using CUSUM algorithm.
        """
        if len(series) < 20:
            return []
        
        # Parameters
        window_size = self.config['change_point']['window_size']
        threshold = self.config['change_point']['threshold']
        
        change_points = []
        n = len(series)
        
        # Calculate CUSUM statistics
        mean_est = np.mean(series[:window_size])
        cumsum_pos = 0
        cumsum_neg = 0
        
        for i in range(window_size, n):
            # Update estimates
            deviation = series[i] - mean_est
            
            # Positive CUSUM
            cumsum_pos = max(0, cumsum_pos + deviation - threshold)
            
            # Negative CUSUM
            cumsum_neg = max(0, cumsum_neg - deviation - threshold)
            
            # Detect change point
            if cumsum_pos > threshold or cumsum_neg > threshold:
                change_points.append(i)
                # Reset
                cumsum_pos = 0
                cumsum_neg = 0
                mean_est = np.mean(series[max(0, i-window_size):i+1])
        
        return change_points
    
    def _prepare_multivariate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for multivariate anomaly detection.
        """
        features = []
        feature_names = []
        
        # Price features
        if 'Close' in data.columns:
            # Returns
            returns = data['Close'].pct_change().fillna(0)
            features.append(returns)
            feature_names.append('returns')
            
            # Rolling volatility
            volatility = returns.rolling(window=20).std().fillna(0)
            features.append(volatility)
            feature_names.append('volatility')
            
            # Price momentum
            momentum = data['Close'] / data['Close'].shift(10) - 1
            features.append(momentum.fillna(0))
            feature_names.append('momentum')
        
        # Volume features
        if 'Volume' in data.columns:
            # Volume changes
            volume_change = data['Volume'].pct_change().fillna(0)
            features.append(volume_change)
            feature_names.append('volume_change')
            
            # Volume ratio to rolling average
            volume_ratio = data['Volume'] / data['Volume'].rolling(window=20).mean()
            features.append(volume_ratio.fillna(1))
            feature_names.append('volume_ratio')
        
        # High-Low range
        if 'High' in data.columns and 'Low' in data.columns and 'Close' in data.columns:
            daily_range = (data['High'] - data['Low']) / data['Close']
            features.append(daily_range.fillna(0))
            feature_names.append('daily_range')
        
        # Combine features
        if features:
            feature_matrix = pd.DataFrame(np.column_stack(features), columns=feature_names)
            # Remove any remaining NaN values
            feature_matrix = feature_matrix.fillna(0)
            return feature_matrix
        
        return pd.DataFrame()
    
    def detect_all_advanced_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run all advanced anomaly detection methods.
        """
        logger.info("Running comprehensive advanced anomaly detection")
        
        results = {}
        
        # Kalman Filter anomalies
        try:
            results['kalman_filter'] = self.detect_kalman_anomalies(data)
        except Exception as e:
            logger.warning(f"Kalman filter anomaly detection failed: {e}")
            results['kalman_filter'] = {}
        
        # Isolation Forest anomalies
        try:
            results['isolation_forest'] = self.detect_isolation_forest_anomalies(data)
        except Exception as e:
            logger.warning(f"Isolation forest anomaly detection failed: {e}")
            results['isolation_forest'] = {}
        
        # Autoencoder anomalies (optional)
        try:
            results['autoencoder'] = self.detect_autoencoder_anomalies(data)
        except Exception as e:
            logger.warning(f"Autoencoder anomaly detection failed: {e}")
            results['autoencoder'] = {}
        
        # Multivariate Gaussian anomalies
        try:
            results['multivariate_gaussian'] = self.detect_multivariate_gaussian_anomalies(data)
        except Exception as e:
            logger.warning(f"Multivariate Gaussian anomaly detection failed: {e}")
            results['multivariate_gaussian'] = {}
        
        # Change point detection
        try:
            results['change_points'] = self.detect_change_points(data)
        except Exception as e:
            logger.warning(f"Change point detection failed: {e}")
            results['change_points'] = {}
        
        logger.info(f"Advanced anomaly detection completed with {len(results)} methods")
        return results
    
    def generate_advanced_report(self, anomalies: Dict[str, Any]) -> str:
        """Generate a comprehensive report of advanced anomaly detection results."""
        report = []
        report.append("ADVANCED ANOMALY DETECTION REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        for method_name, method_results in anomalies.items():
            if not method_results:
                continue
                
            report.append(f"\n{method_name.upper().replace('_', ' ')}")
            report.append("-" * 30)
            
            for symbol, symbol_anomalies in method_results.items():
                if isinstance(symbol_anomalies, dict) and symbol_anomalies:
                    report.append(f"\n  {symbol}:")
                    for anomaly_type, values in symbol_anomalies.items():
                        if isinstance(values, list) and values:
                            report.append(f"    {anomaly_type}: {len(values)} occurrences")
                        elif isinstance(values, (int, float)):
                            report.append(f"    {anomaly_type}: {values:.4f}")
        
        return "\n".join(report)
    
    def detect_anomalies(self, data: Dict[str, pd.DataFrame]) -> List[str]:
        """
        Main method to detect anomalies across all symbols using advanced techniques.
        
        Args:
            data: Dictionary mapping symbols to DataFrames
            
        Returns:
            List of anomaly descriptions
        """
        try:
            all_anomalies = []
            
            for symbol, symbol_data in data.items():
                try:
                    # Run Kalman filter anomaly detection
                    kalman_results = self.detect_kalman_anomalies(symbol_data)
                    if kalman_results.get('anomalies'):
                        for anomaly in kalman_results['anomalies']:
                            all_anomalies.append(f"{symbol}: Kalman filter anomaly at index {anomaly}")
                    
                    # Run Isolation Forest anomaly detection
                    isolation_results = self.detect_isolation_forest_anomalies(symbol_data)
                    if isolation_results.get('anomalies'):
                        anomaly_count = len(isolation_results['anomalies'])
                        all_anomalies.append(f"{symbol}: {anomaly_count} isolation forest anomalies detected")
                    
                    # Run multivariate Gaussian anomaly detection
                    gaussian_results = self.detect_multivariate_gaussian_anomalies(symbol_data)
                    if gaussian_results.get('anomalies'):
                        anomaly_count = len(gaussian_results['anomalies'])
                        all_anomalies.append(f"{symbol}: {anomaly_count} multivariate Gaussian anomalies detected")
                    
                    # Run change point detection
                    changepoint_results = self.detect_change_points(symbol_data)
                    if changepoint_results.get('change_points'):
                        cp_count = len(changepoint_results['change_points'])
                        all_anomalies.append(f"{symbol}: {cp_count} change points detected")
                        
                except Exception as e:
                    logger.warning(f"Error detecting anomalies for {symbol}: {e}")
                    all_anomalies.append(f"{symbol}: Error in advanced anomaly detection - {str(e)}")
            
            logger.info(f"Advanced anomaly detection completed: {len(all_anomalies)} anomalies found")
            return all_anomalies
            
        except Exception as e:
            logger.error(f"Error in advanced anomaly detection: {e}")
            return [f"Advanced anomaly detection failed: {str(e)}"]