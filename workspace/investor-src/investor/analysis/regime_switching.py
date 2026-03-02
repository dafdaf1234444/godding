"""
Markov Regime Switching Models for Market Analysis

This module implements advanced regime detection using Markov switching models,
replacing basic rule-based regime classification with probabilistic state-space models.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, Union
from scipy.stats import norm
import logging

from investor.core.exceptions import DataValidationError
from investor.core.error_handling import handle_data_errors

logger = logging.getLogger(__name__)


class MarkovRegimeSwitchingModel:
    """
    Implementation of Markov Regime Switching Model using Hamilton Filter.
    
    This model assumes that market returns follow different distributions
    in different regimes (Bull, Bear, Sideways) and estimates:
    - Regime-dependent parameters (mean, volatility)
    - Transition probabilities between regimes
    - Current regime probabilities
    - Expected regime duration
    """
    
    def __init__(self, n_regimes: int = 3, max_iter: int = 1000, tol: float = 1e-6):
        """
        Initialize the Markov Regime Switching Model.
        
        Args:
            n_regimes: Number of regimes (default 3: Bull, Bear, Sideways)
            max_iter: Maximum iterations for EM algorithm
            tol: Convergence tolerance
        """
        self.n_regimes = n_regimes
        self.max_iter = max_iter
        self.tol = tol
        
        # Model parameters (will be estimated)
        self.means_ = None
        self.variances_ = None
        self.transition_matrix_ = None
        self.initial_probs_ = None
        
        # Results
        self.regime_probs_ = None
        self.most_likely_regimes_ = None
        self.log_likelihood_ = None
        self.fitted_ = False
        
        # Regime labels
        if n_regimes == 3:
            self.regime_labels = {0: 'Bear', 1: 'Sideways', 2: 'Bull'}
        elif n_regimes == 2:
            self.regime_labels = {0: 'Low Vol', 1: 'High Vol'}
        else:
            self.regime_labels = {i: f'Regime_{i}' for i in range(n_regimes)}
    
    @handle_data_errors(operation="fit Markov regime switching model")
    def fit(self, returns: Union[pd.Series, np.ndarray]) -> 'MarkovRegimeSwitchingModel':
        """
        Fit the Markov Regime Switching Model using EM algorithm.
        
        Args:
            returns: Time series of returns
            
        Returns:
            Self for method chaining
        """
        if isinstance(returns, pd.Series):
            returns = returns.values
        
        returns = returns[~np.isnan(returns)]
        
        if len(returns) < 50:
            raise DataValidationError(f"Insufficient data for regime switching: {len(returns)} < 50")
        
        self.returns_ = returns
        self.T_ = len(returns)
        
        # Initialize parameters
        self._initialize_parameters()
        
        # EM Algorithm
        prev_log_likelihood = -np.inf
        
        for iteration in range(self.max_iter):
            # E-step: Forward-backward algorithm
            regime_probs, log_likelihood = self._expectation_step()
            
            # M-step: Update parameters
            self._maximization_step(regime_probs)
            
            # Check convergence
            if abs(log_likelihood - prev_log_likelihood) < self.tol:
                logger.info(f"Converged after {iteration + 1} iterations")
                break
                
            prev_log_likelihood = log_likelihood
        else:
            logger.warning(f"Did not converge after {self.max_iter} iterations")
        
        # Store final results
        self.regime_probs_, self.log_likelihood_ = self._expectation_step()
        self.most_likely_regimes_ = np.argmax(self.regime_probs_, axis=1)
        self.fitted_ = True
        
        return self
    
    def _initialize_parameters(self):
        """Initialize model parameters."""
        # Initialize means by sorting returns into quantiles
        sorted_returns = np.sort(self.returns_)
        quantiles = np.linspace(0, 1, self.n_regimes + 1)
        
        self.means_ = np.zeros(self.n_regimes)
        self.variances_ = np.zeros(self.n_regimes)
        
        for i in range(self.n_regimes):
            start_idx = int(quantiles[i] * len(sorted_returns))
            end_idx = int(quantiles[i + 1] * len(sorted_returns))
            if end_idx == start_idx:
                end_idx = start_idx + 1
            
            regime_returns = sorted_returns[start_idx:end_idx]
            self.means_[i] = np.mean(regime_returns)
            self.variances_[i] = np.var(regime_returns)
        
        # Ensure variances are positive
        self.variances_ = np.maximum(self.variances_, 1e-6)
        
        # Initialize transition matrix (slightly favor staying in same regime)
        self.transition_matrix_ = np.full((self.n_regimes, self.n_regimes), 
                                         0.1 / (self.n_regimes - 1))
        np.fill_diagonal(self.transition_matrix_, 0.9)
        
        # Initialize equal regime probabilities
        self.initial_probs_ = np.ones(self.n_regimes) / self.n_regimes
    
    def _expectation_step(self) -> Tuple[np.ndarray, float]:
        """
        E-step of EM algorithm: Forward-backward algorithm.
        
        Returns:
            Tuple of (regime_probabilities, log_likelihood)
        """
        # Forward pass
        forward_probs = np.zeros((self.T_, self.n_regimes))
        forward_probs[0] = self.initial_probs_ * self._emission_probs(0)
        forward_probs[0] /= np.sum(forward_probs[0])
        
        for t in range(1, self.T_):
            for j in range(self.n_regimes):
                forward_probs[t, j] = np.sum(
                    forward_probs[t-1] * self.transition_matrix_[:, j]
                ) * self._emission_probs(t)[j]
            
            # Normalize to prevent underflow
            forward_probs[t] /= np.sum(forward_probs[t])
        
        # Backward pass
        backward_probs = np.zeros((self.T_, self.n_regimes))
        backward_probs[-1] = 1.0
        
        for t in range(self.T_ - 2, -1, -1):
            for i in range(self.n_regimes):
                backward_probs[t, i] = np.sum(
                    self.transition_matrix_[i] * 
                    self._emission_probs(t + 1) * 
                    backward_probs[t + 1]
                )
            
            # Normalize
            if np.sum(backward_probs[t]) > 0:
                backward_probs[t] /= np.sum(backward_probs[t])
        
        # Compute smoothed probabilities
        gamma = forward_probs * backward_probs
        gamma = gamma / np.sum(gamma, axis=1, keepdims=True)
        
        # Compute log likelihood
        log_likelihood = np.sum(np.log(np.sum(forward_probs, axis=1)))
        
        return gamma, log_likelihood
    
    def _emission_probs(self, t: int) -> np.ndarray:
        """Calculate emission probabilities for time t."""
        return_t = self.returns_[t]
        probs = np.zeros(self.n_regimes)
        
        for i in range(self.n_regimes):
            probs[i] = norm.pdf(return_t, self.means_[i], np.sqrt(self.variances_[i]))
        
        # Avoid zeros
        probs = np.maximum(probs, 1e-10)
        return probs
    
    def _maximization_step(self, regime_probs: np.ndarray):
        """M-step of EM algorithm: Update parameters."""
        # Update means and variances
        for i in range(self.n_regimes):
            weights = regime_probs[:, i]
            weight_sum = np.sum(weights)
            
            if weight_sum > 1e-10:
                self.means_[i] = np.sum(weights * self.returns_) / weight_sum
                
                variance = np.sum(weights * (self.returns_ - self.means_[i])**2) / weight_sum
                self.variances_[i] = max(variance, 1e-6)
        
        # Update transition matrix
        xi = self._compute_xi(regime_probs)
        
        for i in range(self.n_regimes):
            for j in range(self.n_regimes):
                numerator = np.sum(xi[:, i, j])
                denominator = np.sum(regime_probs[:-1, i])
                
                if denominator > 1e-10:
                    self.transition_matrix_[i, j] = numerator / denominator
                else:
                    self.transition_matrix_[i, j] = 1.0 / self.n_regimes
        
        # Normalize transition matrix
        self.transition_matrix_ = self.transition_matrix_ / np.sum(
            self.transition_matrix_, axis=1, keepdims=True
        )
        
        # Update initial probabilities
        self.initial_probs_ = regime_probs[0]
    
    def _compute_xi(self, regime_probs: np.ndarray) -> np.ndarray:
        """Compute xi (joint probabilities) for transition matrix update."""
        xi = np.zeros((self.T_ - 1, self.n_regimes, self.n_regimes))
        
        for t in range(self.T_ - 1):
            emission_t1 = self._emission_probs(t + 1)
            
            for i in range(self.n_regimes):
                for j in range(self.n_regimes):
                    xi[t, i, j] = (regime_probs[t, i] * 
                                  self.transition_matrix_[i, j] * 
                                  emission_t1[j])
            
            # Normalize
            xi_sum = np.sum(xi[t])
            if xi_sum > 1e-10:
                xi[t] /= xi_sum
        
        return xi
    
    def predict_regime_probs(self, n_steps: int = 1) -> np.ndarray:
        """
        Predict regime probabilities for future periods.
        
        Args:
            n_steps: Number of steps ahead to predict
            
        Returns:
            Array of shape (n_steps, n_regimes) with predicted probabilities
        """
        if not self.fitted_:
            raise ValueError("Model must be fitted before prediction")
        
        current_probs = self.regime_probs_[-1]
        predictions = np.zeros((n_steps, self.n_regimes))
        
        for step in range(n_steps):
            current_probs = current_probs @ self.transition_matrix_
            predictions[step] = current_probs
        
        return predictions
    
    def get_regime_characteristics(self) -> pd.DataFrame:
        """Get characteristics of each regime."""
        if not self.fitted_:
            raise ValueError("Model must be fitted before getting characteristics")
        
        characteristics = []
        
        for i in range(self.n_regimes):
            # Calculate annualized statistics
            annual_return = self.means_[i] * 252
            annual_volatility = np.sqrt(self.variances_[i] * 252)
            sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
            
            # Expected duration in this regime
            expected_duration = 1 / (1 - self.transition_matrix_[i, i])
            
            characteristics.append({
                'Regime': self.regime_labels[i],
                'Daily_Return': self.means_[i],
                'Daily_Volatility': np.sqrt(self.variances_[i]),
                'Annual_Return': annual_return,
                'Annual_Volatility': annual_volatility,
                'Sharpe_Ratio': sharpe_ratio,
                'Expected_Duration': expected_duration,
                'Prob_Stay': self.transition_matrix_[i, i]
            })
        
        return pd.DataFrame(characteristics)
    
    def get_regime_summary(self, returns_index: Optional[pd.DatetimeIndex] = None) -> pd.DataFrame:
        """Get regime probability time series."""
        if not self.fitted_:
            raise ValueError("Model must be fitted before getting summary")
        
        if returns_index is not None and len(returns_index) == len(self.regime_probs_):
            index = returns_index
        else:
            index = range(len(self.regime_probs_))
        
        regime_df = pd.DataFrame(
            self.regime_probs_,
            index=index,
            columns=[self.regime_labels[i] for i in range(self.n_regimes)]
        )
        
        regime_df['Most_Likely_Regime'] = [
            self.regime_labels[i] for i in self.most_likely_regimes_
        ]
        
        return regime_df
    
    def calculate_regime_filtered_returns(self, returns: pd.Series) -> pd.DataFrame:
        """Calculate returns adjusted for regime uncertainty."""
        if not self.fitted_:
            raise ValueError("Model must be fitted before calculating filtered returns")
        
        if len(returns) != len(self.regime_probs_):
            raise ValueError("Returns length must match fitted data length")
        
        filtered_returns = pd.DataFrame(index=returns.index)
        
        for i in range(self.n_regimes):
            # Weight returns by regime probability
            regime_weighted = returns * self.regime_probs_[:, i]
            filtered_returns[f'{self.regime_labels[i]}_Weighted_Returns'] = regime_weighted
        
        # Expected return given regime probabilities
        expected_return = np.sum(
            self.regime_probs_ * self.means_.reshape(1, -1), axis=1
        )
        filtered_returns['Expected_Return'] = expected_return
        
        return filtered_returns


class VolatilityRegimeSwitching:
    """
    Specialized regime switching model for volatility clustering.
    Implements GARCH-like behavior through regime switching.
    """
    
    def __init__(self, max_iter: int = 500, tol: float = 1e-6):
        """Initialize volatility regime switching model."""
        self.max_iter = max_iter
        self.tol = tol
        self.fitted_ = False
        
    @handle_data_errors(operation="fit volatility regime switching model")
    def fit(self, returns: Union[pd.Series, np.ndarray]) -> 'VolatilityRegimeSwitching':
        """Fit the volatility regime switching model."""
        if isinstance(returns, pd.Series):
            returns = returns.values
        
        returns = returns[~np.isnan(returns)]
        
        # Use 2 regimes for volatility (Low/High)
        self.model = MarkovRegimeSwitchingModel(n_regimes=2, max_iter=self.max_iter, tol=self.tol)
        self.model.fit(returns)
        
        self.fitted_ = True
        return self
    
    def get_volatility_regimes(self) -> pd.DataFrame:
        """Get volatility regime characteristics."""
        if not self.fitted_:
            raise ValueError("Model must be fitted first")
        
        return self.model.get_regime_characteristics()
    
    def predict_volatility_regime(self, n_steps: int = 1) -> np.ndarray:
        """Predict volatility regime probabilities."""
        if not self.fitted_:
            raise ValueError("Model must be fitted first")
        
        return self.model.predict_regime_probs(n_steps)


def detect_market_regimes(returns: pd.Series, 
                         n_regimes: int = 3,
                         include_vol_regimes: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to detect market regimes.
    
    Args:
        returns: Return series
        n_regimes: Number of regimes for main model
        include_vol_regimes: Whether to include volatility regime analysis
        
    Returns:
        Dictionary with regime analysis results
    """
    results = {}
    
    # Main regime switching model
    main_model = MarkovRegimeSwitchingModel(n_regimes=n_regimes)
    main_model.fit(returns)
    
    results['regime_probs'] = main_model.get_regime_summary(returns.index)
    results['regime_characteristics'] = main_model.get_regime_characteristics()
    results['filtered_returns'] = main_model.calculate_regime_filtered_returns(returns)
    
    # Volatility regime analysis
    if include_vol_regimes:
        vol_model = VolatilityRegimeSwitching()
        vol_model.fit(returns)
        
        results['volatility_regimes'] = vol_model.get_volatility_regimes()
        vol_summary = vol_model.model.get_regime_summary(returns.index)
        results['volatility_regime_probs'] = vol_summary
    
    return results