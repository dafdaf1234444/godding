"""
Advanced Factor Models for Institutional-Level Risk Attribution and Expected Return Estimation.

Implements Fama-French 5-Factor Model, Carhart 4-Factor, and custom factor construction
for sophisticated portfolio analysis beyond basic technical indicators.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any
import logging
from datetime import datetime
from dataclasses import dataclass
import requests
import zipfile
import io
from pathlib import Path
import warnings

from ..utils.temporal_validation import TemporalValidator

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


@dataclass
class FactorLoadings:
    """Factor loadings and statistics for a security."""
    symbol: str
    date_range: Tuple[str, str]
    loadings: Dict[str, float]  # Factor name -> loading
    alpha: float
    r_squared: float
    t_stats: Dict[str, float]  # Factor name -> t-statistic
    p_values: Dict[str, float]  # Factor name -> p-value
    residual_volatility: float
    observations: int


@dataclass
class FactorPerformance:
    """Factor performance attribution for a portfolio or security."""
    total_return: float
    factor_contributions: Dict[str, float]  # Factor name -> contribution
    alpha_contribution: float
    residual_contribution: float
    factor_loadings: Dict[str, float]


class FamaFrenchDataDownloader:
    """
    Download and process Fama-French research factors from Kenneth French's data library.
    """
    
    def __init__(self, data_dir: str = "data/factors"):
        """Initialize downloader with storage directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # URLs for different factor datasets
        self.factor_urls = {
            'ff5_daily': 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip',
            'ff5_monthly': 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip',
            'momentum_daily': 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip',
            'momentum_monthly': 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip'
        }
        
        self.temporal_validator = TemporalValidator(strict_mode=False)
    
    def download_factor_data(self, factor_set: str = 'ff5_daily', force_download: bool = False) -> pd.DataFrame:
        """
        Download Fama-French factor data.
        
        Args:
            factor_set: Which factor set to download ('ff5_daily', 'ff5_monthly', 'momentum_daily', 'momentum_monthly')
            force_download: Force re-download even if file exists
            
        Returns:
            DataFrame with factor returns
        """
        logger.info(f"Downloading Fama-French factor data: {factor_set}")
        
        cache_file = self.data_dir / f"{factor_set}.parquet"
        
        # Check if we have recent cached data
        if cache_file.exists() and not force_download:
            try:
                cached_data = pd.read_parquet(cache_file)
                # Check if data is recent (within 7 days for daily, 30 days for monthly)
                max_age_days = 7 if 'daily' in factor_set else 30
                if (datetime.now().date() - cached_data.index.max().date()).days <= max_age_days:
                    logger.info(f"Using cached factor data from {cache_file}")
                    return cached_data
            except Exception as e:
                logger.warning(f"Error reading cached data: {e}")
        
        try:
            # Download and extract the ZIP file
            url = self.factor_urls[factor_set]
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract CSV from ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                csv_files = [f for f in zip_file.namelist() if f.endswith('.CSV')]
                if not csv_files:
                    raise ValueError(f"No CSV file found in {factor_set} ZIP")
                
                with zip_file.open(csv_files[0]) as csv_file:
                    # Read the CSV - Fama-French files have specific format
                    factor_data = self._parse_fama_french_csv(csv_file, factor_set)
            
            # Cache the data
            factor_data.to_parquet(cache_file)
            logger.info(f"Downloaded and cached {len(factor_data)} rows of {factor_set} data")
            
            return factor_data
            
        except Exception as e:
            logger.error(f"Error downloading {factor_set} data: {e}")
            # Try to return cached data if available
            if cache_file.exists():
                logger.info("Falling back to cached data")
                return pd.read_parquet(cache_file)
            raise
    
    def _parse_fama_french_csv(self, csv_file, factor_set: str) -> pd.DataFrame:
        """Parse Fama-French CSV file format."""
        # Read the raw CSV content
        content = csv_file.read().decode('utf-8')
        lines = content.strip().split('\n')
        
        # Find the data section (skip copyright notice)
        data_start = 0
        for i, line in enumerate(lines):
            if any(char.isdigit() for char in line) and (',' in line or '\t' in line):
                data_start = i
                break
        
        # Process the data section
        data_lines = []
        for line in lines[data_start:]:
            line = line.strip()
            if not line or line.startswith('Copyright'):
                break
            data_lines.append(line)
        
        # Convert to DataFrame
        data_rows = []
        for line in data_lines:
            # Handle both comma and tab separators
            parts = line.replace('\t', ',').split(',')
            if len(parts) >= 2 and parts[0].strip().isdigit():
                data_rows.append([p.strip() for p in parts])
        
        if not data_rows:
            raise ValueError(f"No valid data rows found in {factor_set}")
        
        # Create DataFrame based on factor set
        if 'ff5' in factor_set:
            columns = ['Date', 'Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'RF']
        elif 'momentum' in factor_set:
            columns = ['Date', 'Mom']
        else:
            # Auto-detect columns
            columns = ['Date'] + [f'Factor_{i}' for i in range(len(data_rows[0]) - 1)]
        
        # Trim to available columns
        max_cols = min(len(columns), max(len(row) for row in data_rows))
        columns = columns[:max_cols]
        
        df = pd.DataFrame(data_rows, columns=columns[:len(data_rows[0])])
        
        # Convert date column
        df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d', errors='coerce')
        df = df.dropna(subset=['Date'])
        df.set_index('Date', inplace=True)
        
        # Convert factor columns to numeric (they're in percentages)
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert percentages to decimal returns
        df = df / 100.0
        
        # Remove any rows with invalid dates or all NaN values
        df = df.dropna(how='all')
        
        # Sort by date
        df = df.sort_index()
        
        return df
    
    def get_complete_factor_data(self, start_date: Optional[str] = None, 
                               end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get complete factor dataset combining FF5 and momentum factors.
        
        Args:
            start_date: Start date for data (YYYY-MM-DD)
            end_date: End date for data (YYYY-MM-DD)
            
        Returns:
            DataFrame with all factors
        """
        try:
            # Download FF5 factors
            ff5_data = self.download_factor_data('ff5_daily')
            
            # Download momentum factor
            momentum_data = self.download_factor_data('momentum_daily')
            
            # Merge the datasets
            factor_data = ff5_data.copy()
            if 'Mom' in momentum_data.columns:
                factor_data = factor_data.join(momentum_data[['Mom']], how='outer')
            
            # Filter by date range if specified
            if start_date:
                factor_data = factor_data[factor_data.index >= start_date]
            if end_date:
                factor_data = factor_data[factor_data.index <= end_date]
            
            # Forward fill missing values (max 5 days)
            factor_data = factor_data.ffill(limit=5)
            
            logger.info(f"Complete factor dataset: {len(factor_data)} observations, {len(factor_data.columns)} factors")
            return factor_data
            
        except Exception as e:
            logger.error(f"Error getting complete factor data: {e}")
            # Return synthetic factor data for testing
            return self._create_synthetic_factor_data()
    
    def _create_synthetic_factor_data(self) -> pd.DataFrame:
        """Create synthetic factor data for testing when download fails."""
        logger.warning("Creating synthetic factor data for testing")
        
        dates = pd.date_range(start='2020-01-01', end=datetime.now().date(), freq='D')
        dates = dates[dates.weekday < 5]  # Business days only
        
        np.random.seed(42)  # For reproducible synthetic data
        n_days = len(dates)
        
        synthetic_data = pd.DataFrame({
            'Mkt-RF': np.random.normal(0.0005, 0.012, n_days),  # Market premium
            'SMB': np.random.normal(0.0001, 0.006, n_days),     # Size factor
            'HML': np.random.normal(0.0001, 0.008, n_days),     # Value factor
            'RMW': np.random.normal(0.0001, 0.005, n_days),     # Profitability factor
            'CMA': np.random.normal(0.0000, 0.004, n_days),     # Investment factor
            'Mom': np.random.normal(0.0002, 0.010, n_days),     # Momentum factor
            'RF': np.random.uniform(0.00005, 0.0002, n_days),   # Risk-free rate
        }, index=dates)
        
        return synthetic_data


class FamaFrenchFactorModel:
    """
    Institutional-level Fama-French 5-Factor Model for risk attribution and expected returns.
    
    Replaces basic technical analysis with sophisticated factor decomposition.
    """
    
    def __init__(self, data_dir: str = "data/factors", lookback_window: int = 252):
        """
        Initialize factor model.
        
        Args:
            data_dir: Directory for factor data storage
            lookback_window: Rolling window for factor loading estimation (days)
        """
        self.data_dir = data_dir
        self.lookback_window = lookback_window
        self.downloader = FamaFrenchDataDownloader(data_dir)
        self.factor_data = None
        self.factor_loadings_cache = {}
        
    def load_factor_data(self, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> pd.DataFrame:
        """Load factor data for analysis."""
        if self.factor_data is None or start_date or end_date:
            self.factor_data = self.downloader.get_complete_factor_data(start_date, end_date)
        return self.factor_data
    
    def estimate_factor_loadings(self, returns: pd.Series, 
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               rolling: bool = False) -> FactorLoadings:
        """
        Estimate factor loadings using regression analysis.
        
        Args:
            returns: Security returns (excess returns preferred)
            start_date: Start date for regression
            end_date: End date for regression
            rolling: Whether to use rolling window estimation
            
        Returns:
            FactorLoadings object with regression results
        """
        # Load factor data
        factor_data = self.load_factor_data(start_date, end_date)
        
        # Align returns with factor data
        aligned_data = pd.concat([returns, factor_data], axis=1, join='inner')
        aligned_data = aligned_data.dropna()
        
        if len(aligned_data) < 60:  # Minimum observations
            logger.warning(f"Insufficient data for factor regression: {len(aligned_data)} observations")
            return self._create_empty_factor_loadings(returns.name or 'Unknown')
        
        y = aligned_data.iloc[:, 0]  # Security returns
        X = aligned_data.iloc[:, 1:]  # Factor returns
        
        # Remove risk-free rate from both sides if present
        if 'RF' in X.columns:
            y = y - X['RF']  # Convert to excess returns
            X = X.drop('RF', axis=1)
        
        try:
            # OLS regression: R_i - R_f = alpha + beta1*(Mkt-RF) + beta2*SMB + ... + epsilon
            from sklearn.linear_model import LinearRegression
            from scipy import stats
            
            reg = LinearRegression(fit_intercept=True)
            reg.fit(X, y)
            
            # Calculate statistics
            y_pred = reg.predict(X)
            residuals = y - y_pred
            mse = np.mean(residuals**2)
            tss = np.sum((y - np.mean(y))**2)
            r_squared = 1 - (np.sum(residuals**2) / tss)
            
            # Calculate t-statistics
            n = len(y)
            k = len(X.columns) + 1  # Including intercept
            residual_std = np.sqrt(mse * n / (n - k))
            
            X_with_intercept = np.column_stack([np.ones(len(X)), X])
            try:
                cov_matrix = residual_std**2 * np.linalg.inv(X_with_intercept.T @ X_with_intercept)
                std_errors = np.sqrt(np.diag(cov_matrix))
                
                # T-statistics
                coefficients = np.concatenate([[reg.intercept_], reg.coef_])
                t_stats = coefficients / std_errors
                p_values = [2 * (1 - stats.t.cdf(abs(t), n - k)) for t in t_stats]
                
                t_stats_dict = {'alpha': t_stats[0]}
                p_values_dict = {'alpha': p_values[0]}
                
                for i, factor in enumerate(X.columns):
                    t_stats_dict[factor] = t_stats[i + 1]
                    p_values_dict[factor] = p_values[i + 1]
                    
            except np.linalg.LinAlgError:
                # Fallback if matrix is singular
                t_stats_dict = {factor: 0.0 for factor in ['alpha'] + list(X.columns)}
                p_values_dict = {factor: 1.0 for factor in ['alpha'] + list(X.columns)}
            
            # Create factor loadings object
            loadings = {factor: beta for factor, beta in zip(X.columns, reg.coef_)}
            
            result = FactorLoadings(
                symbol=returns.name or 'Unknown',
                date_range=(str(aligned_data.index[0].date()), str(aligned_data.index[-1].date())),
                loadings=loadings,
                alpha=reg.intercept_ * 252,  # Annualized alpha
                r_squared=r_squared,
                t_stats=t_stats_dict,
                p_values=p_values_dict,
                residual_volatility=residual_std * np.sqrt(252),  # Annualized
                observations=n
            )
            
            logger.info(f"Factor loadings estimated for {result.symbol}: "
                       f"Alpha={result.alpha:.4f}, R²={result.r_squared:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in factor regression: {e}")
            return self._create_empty_factor_loadings(returns.name or 'Unknown')
    
    def _create_empty_factor_loadings(self, symbol: str) -> FactorLoadings:
        """Create empty factor loadings for error cases."""
        return FactorLoadings(
            symbol=symbol,
            date_range=('N/A', 'N/A'),
            loadings={},
            alpha=0.0,
            r_squared=0.0,
            t_stats={},
            p_values={},
            residual_volatility=0.0,
            observations=0
        )
    
    def calculate_expected_returns(self, factor_loadings: FactorLoadings,
                                 factor_premiums: Dict[str, float]) -> float:
        """
        Calculate expected return using factor model.
        
        Args:
            factor_loadings: Estimated factor loadings
            factor_premiums: Expected factor premiums (annualized)
            
        Returns:
            Expected return (annualized)
        """
        expected_return = factor_loadings.alpha  # Alpha component
        
        for factor, loading in factor_loadings.loadings.items():
            if factor in factor_premiums:
                expected_return += loading * factor_premiums[factor]
        
        return expected_return
    
    def perform_risk_attribution(self, portfolio_weights: Dict[str, float],
                                factor_loadings_dict: Dict[str, FactorLoadings],
                                period_returns: Dict[str, float]) -> FactorPerformance:
        """
        Perform factor-based risk attribution for a portfolio.
        
        Args:
            portfolio_weights: Security weights
            factor_loadings_dict: Factor loadings for each security
            period_returns: Actual returns for the period
            
        Returns:
            FactorPerformance with attribution results
        """
        # Calculate portfolio factor loadings (weighted average)
        portfolio_loadings = {}
        portfolio_alpha = 0.0
        
        for symbol, weight in portfolio_weights.items():
            if symbol in factor_loadings_dict:
                loadings = factor_loadings_dict[symbol]
                portfolio_alpha += weight * loadings.alpha
                
                for factor, loading in loadings.loadings.items():
                    if factor not in portfolio_loadings:
                        portfolio_loadings[factor] = 0.0
                    portfolio_loadings[factor] += weight * loading
        
        # Calculate total portfolio return
        total_return = sum(portfolio_weights[symbol] * period_returns.get(symbol, 0.0) 
                          for symbol in portfolio_weights)
        
        # Get factor returns for the period (would need actual factor returns)
        # This is a simplified version - in practice you'd use actual factor returns
        factor_data = self.load_factor_data()
        if len(factor_data) > 0:
            latest_factor_returns = factor_data.iloc[-1].to_dict()
        else:
            latest_factor_returns = {factor: 0.0 for factor in portfolio_loadings}
        
        # Calculate factor contributions
        factor_contributions = {}
        for factor, loading in portfolio_loadings.items():
            factor_return = latest_factor_returns.get(factor, 0.0)
            factor_contributions[factor] = loading * factor_return
        
        # Calculate residual (unexplained) return
        explained_return = sum(factor_contributions.values()) + portfolio_alpha
        residual_contribution = total_return - explained_return
        
        return FactorPerformance(
            total_return=total_return,
            factor_contributions=factor_contributions,
            alpha_contribution=portfolio_alpha,
            residual_contribution=residual_contribution,
            factor_loadings=portfolio_loadings
        )
    
    def generate_factor_report(self, factor_loadings: FactorLoadings) -> str:
        """Generate a comprehensive factor analysis report."""
        report = []
        report.append("FAMA-FRENCH 5-FACTOR MODEL ANALYSIS")
        report.append("=" * 50)
        report.append(f"Security: {factor_loadings.symbol}")
        report.append(f"Period: {factor_loadings.date_range[0]} to {factor_loadings.date_range[1]}")
        report.append(f"Observations: {factor_loadings.observations}")
        report.append("")
        
        report.append("REGRESSION STATISTICS:")
        report.append(f"  Alpha (annualized): {factor_loadings.alpha:.4f} ({factor_loadings.alpha*100:.2f}%)")
        report.append(f"  R-squared: {factor_loadings.r_squared:.4f}")
        report.append(f"  Residual Volatility: {factor_loadings.residual_volatility:.4f}")
        report.append("")
        
        report.append("FACTOR LOADINGS:")
        for factor, loading in factor_loadings.loadings.items():
            t_stat = factor_loadings.t_stats.get(factor, 0.0)
            p_value = factor_loadings.p_values.get(factor, 1.0)
            significance = "***" if p_value < 0.01 else "**" if p_value < 0.05 else "*" if p_value < 0.10 else ""
            
            report.append(f"  {factor}: {loading:.4f} (t={t_stat:.2f}) {significance}")
        
        report.append("")
        report.append("INTERPRETATION:")
        
        # Market factor interpretation
        mkt_loading = factor_loadings.loadings.get('Mkt-RF', 0.0)
        if mkt_loading > 1.1:
            report.append(f"  High market beta ({mkt_loading:.2f}) - amplifies market movements")
        elif mkt_loading < 0.9:
            report.append(f"  Low market beta ({mkt_loading:.2f}) - defensive characteristics")
        else:
            report.append(f"  Market beta ({mkt_loading:.2f}) - market-like risk")
        
        # Size factor interpretation
        smb_loading = factor_loadings.loadings.get('SMB', 0.0)
        if smb_loading > 0.3:
            report.append("  Small-cap tilt - higher exposure to small company risk premium")
        elif smb_loading < -0.3:
            report.append("  Large-cap tilt - bias toward large company stocks")
        
        # Value factor interpretation
        hml_loading = factor_loadings.loadings.get('HML', 0.0)
        if hml_loading > 0.3:
            report.append("  Value tilt - higher exposure to value vs growth premium")
        elif hml_loading < -0.3:
            report.append("  Growth tilt - bias toward growth stocks")
        
        return "\n".join(report)


class CustomFactorConstructor:
    """
    Construct custom factors beyond Fama-French for enhanced analysis.
    """
    
    def __init__(self):
        """Initialize custom factor constructor."""
        pass
    
    def construct_quality_factor(self, stock_data: Dict[str, pd.DataFrame]) -> pd.Series:
        """
        Construct quality factor based on fundamental metrics.
        
        Args:
            stock_data: Dictionary of stock price data
            
        Returns:
            Quality factor time series
        """
        # This is a simplified implementation
        # In practice, you'd use fundamental data (ROE, debt ratios, earnings quality)
        
        logger.info("Constructing quality factor (simplified)")
        
        # For now, create a synthetic quality factor based on volatility
        # Lower volatility = higher quality
        quality_scores = {}
        
        for symbol, data in stock_data.items():
            if 'Close' in data.columns and len(data) > 60:
                returns = data['Close'].pct_change().dropna()
                # Rolling 60-day volatility (inverse for quality)
                rolling_vol = returns.rolling(60).std()
                quality_scores[symbol] = -rolling_vol  # Negative because lower vol = higher quality
        
        if not quality_scores:
            return pd.Series(dtype=float)
        
        # Combine into factor (equal weighted for simplicity)
        quality_factor = pd.concat(quality_scores.values(), axis=1).mean(axis=1)
        quality_factor.name = 'Quality'
        
        return quality_factor.fillna(0)
    
    def construct_momentum_factor(self, stock_data: Dict[str, pd.DataFrame], 
                                lookback: int = 252) -> pd.Series:
        """
        Construct momentum factor based on price trends.
        
        Args:
            stock_data: Dictionary of stock price data
            lookback: Lookback period for momentum calculation
            
        Returns:
            Momentum factor time series
        """
        logger.info(f"Constructing momentum factor with {lookback}-day lookback")
        
        momentum_scores = {}
        
        for symbol, data in stock_data.items():
            if 'Close' in data.columns and len(data) > lookback:
                prices = data['Close']
                # Calculate rolling momentum (price change over lookback period)
                momentum = (prices / prices.shift(lookback) - 1)
                momentum_scores[symbol] = momentum
        
        if not momentum_scores:
            return pd.Series(dtype=float)
        
        # Combine into factor
        momentum_factor = pd.concat(momentum_scores.values(), axis=1).mean(axis=1)
        momentum_factor.name = 'Momentum'
        
        return momentum_factor.fillna(0)
    
    def construct_low_volatility_factor(self, stock_data: Dict[str, pd.DataFrame]) -> pd.Series:
        """
        Construct low volatility factor.
        
        Args:
            stock_data: Dictionary of stock price data
            
        Returns:
            Low volatility factor time series
        """
        logger.info("Constructing low volatility factor")
        
        vol_scores = {}
        
        for symbol, data in stock_data.items():
            if 'Close' in data.columns and len(data) > 60:
                returns = data['Close'].pct_change().dropna()
                # Rolling 60-day volatility (negative for low-vol factor)
                rolling_vol = returns.rolling(60).std()
                vol_scores[symbol] = -rolling_vol  # Negative because we want LOW volatility
        
        if not vol_scores:
            return pd.Series(dtype=float)
        
        # Combine into factor
        low_vol_factor = pd.concat(vol_scores.values(), axis=1).mean(axis=1)
        low_vol_factor.name = 'LowVol'
        
        return low_vol_factor.fillna(0)


def analyze_factor_model_vs_technical_analysis(returns_data: Dict[str, pd.Series],
                                             stock_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Compare factor model analysis vs basic technical analysis.
    
    Args:
        returns_data: Dictionary of return series by symbol
        stock_data: Dictionary of stock data for technical analysis
        
    Returns:
        Comparison results showing institutional vs basic analysis
    """
    logger.info("Comparing factor model vs technical analysis")
    
    results = {
        'factor_analysis': {},
        'technical_analysis': {},
        'comparison_summary': {}
    }
    
    # Initialize factor model
    factor_model = FamaFrenchFactorModel()
    
    for symbol, returns in returns_data.items():
        if len(returns) < 60:
            continue
            
        try:
            # Factor model analysis (institutional)
            factor_loadings = factor_model.estimate_factor_loadings(returns)
            results['factor_analysis'][symbol] = {
                'alpha': factor_loadings.alpha,
                'market_beta': factor_loadings.loadings.get('Mkt-RF', 0.0),
                'size_loading': factor_loadings.loadings.get('SMB', 0.0),
                'value_loading': factor_loadings.loadings.get('HML', 0.0),
                'r_squared': factor_loadings.r_squared,
                'significance': len([p for p in factor_loadings.p_values.values() if p < 0.05])
            }
            
            # Basic technical analysis (retail-level)
            stock_prices = stock_data.get(symbol, pd.DataFrame())
            if 'Close' in stock_prices.columns:
                prices = stock_prices['Close']
                
                # Simple technical indicators
                sma_20 = prices.rolling(20).mean()
                sma_50 = prices.rolling(50).mean()
                current_price = prices.iloc[-1] if len(prices) > 0 else 0
                
                # Basic momentum
                momentum_1m = (current_price / prices.iloc[-21] - 1) if len(prices) > 21 else 0
                
                # Simple volatility
                volatility = returns.rolling(20).std().iloc[-1] * np.sqrt(252) if len(returns) > 20 else 0
                
                results['technical_analysis'][symbol] = {
                    'price_vs_sma20': (current_price / sma_20.iloc[-1] - 1) if len(sma_20.dropna()) > 0 else 0,
                    'sma20_vs_sma50': (sma_20.iloc[-1] / sma_50.iloc[-1] - 1) if len(sma_50.dropna()) > 0 else 0,
                    'momentum_1m': momentum_1m,
                    'volatility': volatility,
                    'simple_signal': 'BUY' if momentum_1m > 0.05 else 'SELL' if momentum_1m < -0.05 else 'HOLD'
                }
        
        except Exception as e:
            logger.warning(f"Error analyzing {symbol}: {e}")
    
    # Generate comparison summary
    factor_alphas = [fa['alpha'] for fa in results['factor_analysis'].values()]
    tech_momentums = [ta['momentum_1m'] for ta in results['technical_analysis'].values()]
    
    results['comparison_summary'] = {
        'factor_model_advantages': [
            f"Systematic risk decomposition for {len(results['factor_analysis'])} securities",
            f"Average alpha: {np.mean(factor_alphas):.4f}" if factor_alphas else "No alpha data",
            "Statistical significance testing for all factors",
            "Risk attribution to systematic factors vs idiosyncratic risk"
        ],
        'technical_analysis_limitations': [
            "No risk factor decomposition - treats all returns as stock-specific",
            "No statistical significance testing of signals",
            f"Simple momentum signals for {len(results['technical_analysis'])} securities",
            "No systematic risk vs idiosyncratic risk separation"
        ],
        'institutional_upgrade_impact': {
            'risk_understanding': 'Factor model explains systematic risk sources',
            'alpha_identification': 'Separates true alpha from factor exposure',
            'portfolio_construction': 'Enables factor-based portfolio optimization',
            'performance_attribution': 'Identifies sources of returns beyond market timing'
        }
    }
    
    return results