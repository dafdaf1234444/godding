"""
Options pricing models including Black-Scholes and Greeks calculation.
"""
import numpy as np
import pandas as pd
from scipy.stats import norm
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BlackScholesInputs:
    """Inputs for Black-Scholes option pricing model."""
    S: float  # Current stock price
    K: float  # Strike price
    T: float  # Time to expiration (in years)
    r: float  # Risk-free rate
    sigma: float  # Volatility
    q: float = 0.0  # Dividend yield


@dataclass
class OptionGreeks:
    """Option Greeks values."""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


@dataclass
class OptionPricing:
    """Complete option pricing result."""
    call_price: float
    put_price: float
    greeks: OptionGreeks
    inputs: BlackScholesInputs
    intrinsic_value_call: float
    intrinsic_value_put: float
    time_value_call: float
    time_value_put: float


class BlackScholesModel:
    """Black-Scholes option pricing model with Greeks calculation."""
    
    @staticmethod
    def calculate_d1_d2(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> Tuple[float, float]:
        """
        Calculate d1 and d2 parameters for Black-Scholes formula.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Volatility
            q: Dividend yield
            
        Returns:
            Tuple of (d1, d2)
        """
        if T <= 0 or sigma <= 0:
            raise ValueError("Time to expiration and volatility must be positive")
            
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        return d1, d2
    
    @staticmethod
    def call_price(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """
        Calculate Black-Scholes call option price.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Volatility
            q: Dividend yield
            
        Returns:
            Call option price
        """
        if T <= 0:
            return max(S - K, 0)
            
        d1, d2 = BlackScholesModel.calculate_d1_d2(S, K, T, r, sigma, q)
        
        call_price = (S * np.exp(-q * T) * norm.cdf(d1) - 
                     K * np.exp(-r * T) * norm.cdf(d2))
        
        return max(call_price, 0)
    
    @staticmethod
    def put_price(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """
        Calculate Black-Scholes put option price.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Volatility
            q: Dividend yield
            
        Returns:
            Put option price
        """
        if T <= 0:
            return max(K - S, 0)
            
        d1, d2 = BlackScholesModel.calculate_d1_d2(S, K, T, r, sigma, q)
        
        put_price = (K * np.exp(-r * T) * norm.cdf(-d2) - 
                    S * np.exp(-q * T) * norm.cdf(-d1))
        
        return max(put_price, 0)
    
    @staticmethod
    def calculate_greeks(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> OptionGreeks:
        """
        Calculate option Greeks.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Volatility
            q: Dividend yield
            
        Returns:
            OptionGreeks object with all Greeks
        """
        if T <= 0:
            # Handle expiration case
            return OptionGreeks(
                delta=1.0 if S > K else 0.0,
                gamma=0.0,
                theta=0.0,
                vega=0.0,
                rho=0.0
            )
        
        d1, d2 = BlackScholesModel.calculate_d1_d2(S, K, T, r, sigma, q)
        sqrt_T = np.sqrt(T)
        
        # Delta (price sensitivity to underlying)
        delta_call = np.exp(-q * T) * norm.cdf(d1)
        # delta_put = np.exp(-q * T) * (norm.cdf(d1) - 1)  # For reference
        
        # Gamma (delta sensitivity to underlying)
        gamma = (np.exp(-q * T) * norm.pdf(d1)) / (S * sigma * sqrt_T)
        
        # Theta (price sensitivity to time decay) - per day
        theta_call = (-(S * norm.pdf(d1) * sigma * np.exp(-q * T)) / (2 * sqrt_T) -
                     r * K * np.exp(-r * T) * norm.cdf(d2) +
                     q * S * np.exp(-q * T) * norm.cdf(d1)) / 365
        
        # theta_put = (-(S * norm.pdf(d1) * sigma * np.exp(-q * T)) / (2 * sqrt_T) +
        #             r * K * np.exp(-r * T) * norm.cdf(-d2) -
        #             q * S * np.exp(-q * T) * norm.cdf(-d1)) / 365  # For reference
        
        # Vega (price sensitivity to volatility)
        vega = S * np.exp(-q * T) * norm.pdf(d1) * sqrt_T / 100  # Per 1% change in volatility
        
        # Rho (price sensitivity to interest rate)
        rho_call = K * T * np.exp(-r * T) * norm.cdf(d2) / 100  # Per 1% change in rate
        # rho_put = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100  # For reference
        
        # Return call Greeks (can be used for both call and put with appropriate signs)
        return OptionGreeks(
            delta=delta_call,
            gamma=gamma,
            theta=theta_call,
            vega=vega,
            rho=rho_call
        )
    
    @staticmethod
    def price_option(inputs: BlackScholesInputs) -> OptionPricing:
        """
        Calculate complete option pricing with Greeks.
        
        Args:
            inputs: BlackScholesInputs object
            
        Returns:
            OptionPricing object with prices and Greeks
        """
        call_price = BlackScholesModel.call_price(
            inputs.S, inputs.K, inputs.T, inputs.r, inputs.sigma, inputs.q
        )
        
        put_price = BlackScholesModel.put_price(
            inputs.S, inputs.K, inputs.T, inputs.r, inputs.sigma, inputs.q
        )
        
        greeks = BlackScholesModel.calculate_greeks(
            inputs.S, inputs.K, inputs.T, inputs.r, inputs.sigma, inputs.q
        )
        
        # Calculate intrinsic and time values
        intrinsic_call = max(inputs.S - inputs.K, 0)
        intrinsic_put = max(inputs.K - inputs.S, 0)
        time_value_call = call_price - intrinsic_call
        time_value_put = put_price - intrinsic_put
        
        return OptionPricing(
            call_price=call_price,
            put_price=put_price,
            greeks=greeks,
            inputs=inputs,
            intrinsic_value_call=intrinsic_call,
            intrinsic_value_put=intrinsic_put,
            time_value_call=time_value_call,
            time_value_put=time_value_put
        )


class ImpliedVolatilityCalculator:
    """Calculator for implied volatility using Black-Scholes model."""
    
    @staticmethod
    def calculate_implied_volatility(market_price: float, S: float, K: float, T: float, 
                                   r: float, option_type: str = 'call', q: float = 0.0,
                                   max_iterations: int = 100, tolerance: float = 1e-6) -> Optional[float]:
        """
        Calculate implied volatility using Newton-Raphson method.
        
        Args:
            market_price: Observed market price of option
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            option_type: 'call' or 'put'
            q: Dividend yield
            max_iterations: Maximum iterations for convergence
            tolerance: Convergence tolerance
            
        Returns:
            Implied volatility or None if convergence fails
        """
        if T <= 0 or market_price <= 0:
            return None
        
        # Initial guess
        sigma = 0.2
        
        for i in range(max_iterations):
            try:
                if option_type.lower() == 'call':
                    price = BlackScholesModel.call_price(S, K, T, r, sigma, q)
                else:
                    price = BlackScholesModel.put_price(S, K, T, r, sigma, q)
                
                # Calculate vega for Newton-Raphson
                if T > 0 and sigma > 0:
                    d1, _ = BlackScholesModel.calculate_d1_d2(S, K, T, r, sigma, q)
                    vega = S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T)
                else:
                    return None
                
                # Newton-Raphson iteration
                price_diff = price - market_price
                
                if abs(price_diff) < tolerance:
                    return sigma
                
                if vega == 0:
                    return None
                
                sigma = sigma - price_diff / vega
                
                # Keep sigma in reasonable bounds
                sigma = max(0.001, min(sigma, 5.0))
                
            except Exception as e:
                logger.warning(f"Error in implied volatility calculation: {str(e)}")
                return None
        
        logger.warning(f"Implied volatility did not converge after {max_iterations} iterations")
        return None


class VolatilitySurface:
    """Volatility surface construction and analysis."""
    
    def __init__(self, options_data: pd.DataFrame):
        """
        Initialize volatility surface with options data.
        
        Args:
            options_data: DataFrame with options data including strikes, expirations, and IVs
        """
        self.options_data = options_data.copy()
        self.surface_data = None
        self._prepare_surface_data()
    
    def _prepare_surface_data(self):
        """Prepare data for volatility surface construction."""
        if self.options_data.empty:
            return
        
        # Calculate time to expiration
        if 'expiration' in self.options_data.columns:
            self.options_data['time_to_expiration'] = (
                pd.to_datetime(self.options_data['expiration']) - datetime.now()
            ).dt.days / 365.25
        
        # Calculate moneyness if not already present
        if 'moneyness' not in self.options_data.columns and 'underlying_price' in self.options_data.columns:
            self.options_data['moneyness'] = self.options_data['strike'] / self.options_data['underlying_price']
        
        # Filter valid data
        valid_data = self.options_data[
            (self.options_data['implied_volatility'] > 0) &
            (self.options_data['time_to_expiration'] > 0) &
            (self.options_data['volume'] > 0)  # Only consider traded options
        ].copy()
        
        self.surface_data = valid_data
    
    def get_surface_grid(self, moneyness_range: Tuple[float, float] = (0.8, 1.2),
                        time_range: Tuple[float, float] = (0.02, 1.0),
                        grid_size: Tuple[int, int] = (20, 20)) -> Dict:
        """
        Get volatility surface data on a regular grid.
        
        Args:
            moneyness_range: (min_moneyness, max_moneyness)
            time_range: (min_time, max_time) in years
            grid_size: (moneyness_points, time_points)
            
        Returns:
            Dictionary with grid data
        """
        if self.surface_data is None or self.surface_data.empty:
            return {}
        
        # Create grid
        moneyness_grid = np.linspace(moneyness_range[0], moneyness_range[1], grid_size[0])
        time_grid = np.linspace(time_range[0], time_range[1], grid_size[1])
        
        # Group by expiration and moneyness buckets
        surface_points = []
        
        for _, option in self.surface_data.iterrows():
            surface_points.append({
                'moneyness': option['moneyness'],
                'time_to_expiration': option['time_to_expiration'],
                'implied_volatility': option['implied_volatility'],
                'volume': option['volume'],
                'option_type': option['option_type']
            })
        
        return {
            'moneyness_grid': moneyness_grid,
            'time_grid': time_grid,
            'surface_points': surface_points,
            'interpolated_surface': self._interpolate_surface(moneyness_grid, time_grid)
        }
    
    def _interpolate_surface(self, moneyness_grid: np.ndarray, time_grid: np.ndarray) -> Optional[np.ndarray]:
        """Interpolate volatility surface on grid."""
        if self.surface_data is None or len(self.surface_data) < 4:
            return None
        
        try:
            from scipy.interpolate import griddata
            
            points = self.surface_data[['moneyness', 'time_to_expiration']].values
            values = self.surface_data['implied_volatility'].values
            
            # Create meshgrid
            M, T = np.meshgrid(moneyness_grid, time_grid)
            grid_points = np.column_stack([M.ravel(), T.ravel()])
            
            # Interpolate
            interpolated = griddata(points, values, grid_points, method='linear')
            return interpolated.reshape(M.shape)
            
        except ImportError:
            logger.warning("scipy not available for surface interpolation")
            return None
        except Exception as e:
            logger.warning(f"Error interpolating volatility surface: {str(e)}")
            return None
    
    def get_term_structure(self, moneyness: float = 1.0, tolerance: float = 0.05) -> pd.DataFrame:
        """
        Get volatility term structure for a specific moneyness level.
        
        Args:
            moneyness: Target moneyness level
            tolerance: Tolerance for moneyness matching
            
        Returns:
            DataFrame with time to expiration and implied volatility
        """
        if self.surface_data is None or self.surface_data.empty:
            return pd.DataFrame()
        
        # Filter options near target moneyness
        filtered_data = self.surface_data[
            abs(self.surface_data['moneyness'] - moneyness) <= tolerance
        ].copy()
        
        if filtered_data.empty:
            return pd.DataFrame()
        
        # Group by expiration and take volume-weighted average
        term_structure = []
        
        for exp_date, group in filtered_data.groupby('expiration'):
            if len(group) > 0:
                # Volume-weighted average IV
                total_volume = group['volume'].sum()
                if total_volume > 0:
                    weighted_iv = (group['implied_volatility'] * group['volume']).sum() / total_volume
                else:
                    weighted_iv = group['implied_volatility'].mean()
                
                term_structure.append({
                    'expiration': exp_date,
                    'time_to_expiration': group['time_to_expiration'].iloc[0],
                    'implied_volatility': weighted_iv,
                    'total_volume': total_volume,
                    'contracts_count': len(group)
                })
        
        return pd.DataFrame(term_structure).sort_values('time_to_expiration')
    
    def calculate_volatility_skew(self, expiration: str) -> pd.DataFrame:
        """
        Calculate volatility skew for a specific expiration.
        
        Args:
            expiration: Target expiration date
            
        Returns:
            DataFrame with strike/moneyness and implied volatility
        """
        if self.surface_data is None or self.surface_data.empty:
            return pd.DataFrame()
        
        # Filter by expiration
        exp_data = self.surface_data[
            self.surface_data['expiration'] == expiration
        ].copy()
        
        if exp_data.empty:
            return pd.DataFrame()
        
        # Sort by strike and calculate skew metrics
        exp_data = exp_data.sort_values('strike')
        
        if len(exp_data) > 1:
            # Calculate skew slope (change in IV per unit change in moneyness)
            exp_data['iv_slope'] = exp_data['implied_volatility'].diff() / exp_data['moneyness'].diff()
            
            # Mark ATM point (closest to moneyness = 1.0)
            exp_data['distance_from_atm'] = abs(exp_data['moneyness'] - 1.0)
            atm_idx = exp_data['distance_from_atm'].idxmin()
            exp_data['is_atm'] = False
            exp_data.loc[atm_idx, 'is_atm'] = True
        
        return exp_data[['strike', 'moneyness', 'implied_volatility', 'volume', 'option_type']].copy()


def calculate_portfolio_greeks(positions: List[Dict], current_prices: Dict[str, float],
                             risk_free_rate: float = 0.02) -> Dict[str, float]:
    """
    Calculate portfolio-level Greeks for multiple option positions.
    
    Args:
        positions: List of position dictionaries with symbol, strike, expiration, quantity, option_type
        current_prices: Dictionary mapping symbols to current prices
        risk_free_rate: Risk-free rate for calculations
        
    Returns:
        Dictionary with total portfolio Greeks
    """
    total_greeks = {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
    
    for position in positions:
        symbol = position['symbol']
        if symbol not in current_prices:
            continue
        
        try:
            # Calculate time to expiration
            exp_date = pd.to_datetime(position['expiration'])
            time_to_exp = (exp_date - datetime.now()).total_seconds() / (365.25 * 24 * 3600)
            
            if time_to_exp <= 0:
                continue
            
            # Estimate volatility (this would normally come from market data)
            estimated_vol = position.get('volatility', 0.25)
            
            inputs = BlackScholesInputs(
                S=current_prices[symbol],
                K=position['strike'],
                T=time_to_exp,
                r=risk_free_rate,
                sigma=estimated_vol
            )
            
            greeks = BlackScholesModel.calculate_greeks(
                inputs.S, inputs.K, inputs.T, inputs.r, inputs.sigma
            )
            
            # Apply position quantity and option type
            quantity = position['quantity']
            if position['option_type'].lower() == 'put':
                # Adjust for put Greeks
                delta_multiplier = -1
            else:
                delta_multiplier = 1
            
            total_greeks['delta'] += greeks.delta * quantity * delta_multiplier
            total_greeks['gamma'] += greeks.gamma * quantity
            total_greeks['theta'] += greeks.theta * quantity
            total_greeks['vega'] += greeks.vega * quantity
            total_greeks['rho'] += greeks.rho * quantity
            
        except Exception as e:
            logger.warning(f"Error calculating Greeks for position {position}: {str(e)}")
            continue
    
    return total_greeks