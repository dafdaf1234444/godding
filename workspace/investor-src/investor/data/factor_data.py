"""
Fama-French Factor Data Management

This module handles downloading and processing of Fama-French research factors
from Kenneth French's data library for institutional-level quantitative analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import requests
import zipfile
import io
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from investor.core.exceptions import DataError, DataNotFoundError
from investor.core.error_handling import handle_data_errors

logger = logging.getLogger(__name__)


class FamaFrenchDataManager:
    """
    Manager for downloading and processing Fama-French factor data.
    
    Provides access to:
    - 5-Factor Model: Mkt-RF, SMB, HML, RMW, CMA
    - 3-Factor Model: Mkt-RF, SMB, HML  
    - Momentum Factor: MOM
    - Industry portfolios
    - Size and value portfolios
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the Fama-French data manager."""
        self.data_dir = data_dir or Path("data/factors")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Kenneth French data library URLs
        self.base_url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"
        
        # Factor data files from Kenneth French's website
        self.factor_files = {
            'ff5_factors': 'F-F_Research_Data_5_Factors_2x3_daily_CSV.zip',
            'ff3_factors': 'F-F_Research_Data_Factors_daily_CSV.zip',
            'momentum': 'F-F_Momentum_Factor_daily_CSV.zip',
            'industry_10': 'Siccodes10.zip',
            'industry_30': 'Siccodes30.zip',
            'size_value': 'Portfolios_Formed_on_ME_daily.zip'
        }
        
        # Cache for downloaded data
        self._cache = {}
        
    @handle_data_errors(operation="download Fama-French factors")
    def download_factors(self, factor_set: str = 'ff5_factors', 
                        force_download: bool = False) -> pd.DataFrame:
        """
        Download Fama-French factor data.
        
        Args:
            factor_set: Which factor set to download ('ff5_factors', 'ff3_factors', 'momentum')
            force_download: Force re-download even if cached data exists
            
        Returns:
            DataFrame with factor returns (daily)
        """
        if factor_set not in self.factor_files:
            raise ValueError(f"Unknown factor set: {factor_set}")
            
        cache_key = f"{factor_set}_data"
        cache_file = self.data_dir / f"{factor_set}.parquet"
        
        # Check cache first
        if not force_download and cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age < timedelta(days=1):  # Daily refresh
                logger.info(f"Loading {factor_set} from cache")
                return pd.read_parquet(cache_file)
        
        # Download from Kenneth French website
        logger.info(f"Downloading {factor_set} from Kenneth French data library")
        
        url = f"{self.base_url}/{self.factor_files[factor_set]}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract CSV from ZIP file
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                # Look for CSV files (case insensitive)
                all_files = zip_file.namelist()
                csv_files = [f for f in all_files if f.lower().endswith('.csv')]
                
                if not csv_files:
                    logger.warning(f"Available files in {factor_set} zip: {all_files}")
                    raise DataNotFoundError(f"No CSV file found in {factor_set} zip. Available files: {all_files}")
                
                # Read the first CSV file
                csv_file_name = csv_files[0]
                logger.info(f"Reading CSV file: {csv_file_name}")
                
                with zip_file.open(csv_file_name) as csv_file:
                    # Read all lines to find data start
                    lines = csv_file.read().decode('utf-8').split('\n')
                    
                    # Find where the actual data starts (after headers)
                    data_start_idx = 0
                    for i, line in enumerate(lines):
                        if line.strip() and line.split(',')[0].strip().isdigit():
                            data_start_idx = i
                            break
                    
                    # Create DataFrame from data lines
                    data_lines = lines[data_start_idx:]
                    data_lines = [line for line in data_lines if line.strip()]
                    
                    # Parse the data
                    data = self._parse_factor_data(data_lines, factor_set)
                    
        except requests.RequestException as e:
            raise DataError(f"Failed to download {factor_set}: {str(e)}")
        except Exception as e:
            raise DataError(f"Error processing {factor_set}: {str(e)}")
        
        # Cache the data
        data.to_parquet(cache_file)
        logger.info(f"Downloaded and cached {len(data)} rows of {factor_set} data")
        
        return data
    
    def _parse_factor_data(self, data_lines: List[str], factor_set: str) -> pd.DataFrame:
        """Parse factor data from CSV lines."""
        parsed_data = []
        
        for line in data_lines:
            if not line.strip():
                continue
                
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 2:
                continue
                
            # Parse date (YYYYMMDD format)
            date_str = parts[0]
            if not date_str.isdigit() or len(date_str) != 8:
                continue
                
            try:
                date = pd.to_datetime(date_str, format='%Y%m%d')
            except:
                continue
                
            # Parse factor values
            factor_values = {}
            
            if factor_set == 'ff5_factors':
                # Mkt-RF, SMB, HML, RMW, CMA, RF
                if len(parts) >= 6:
                    factor_values = {
                        'Mkt-RF': float(parts[1]) / 100,  # Convert from percentage
                        'SMB': float(parts[2]) / 100,
                        'HML': float(parts[3]) / 100,
                        'RMW': float(parts[4]) / 100,
                        'CMA': float(parts[5]) / 100,
                        'RF': float(parts[6]) / 100 if len(parts) > 6 else 0.0
                    }
                    
            elif factor_set == 'ff3_factors':
                # Mkt-RF, SMB, HML, RF
                if len(parts) >= 4:
                    factor_values = {
                        'Mkt-RF': float(parts[1]) / 100,
                        'SMB': float(parts[2]) / 100,
                        'HML': float(parts[3]) / 100,
                        'RF': float(parts[4]) / 100 if len(parts) > 4 else 0.0
                    }
                    
            elif factor_set == 'momentum':
                # MOM
                if len(parts) >= 2:
                    factor_values = {
                        'MOM': float(parts[1]) / 100
                    }
            
            if factor_values:
                factor_values['Date'] = date
                parsed_data.append(factor_values)
        
        if not parsed_data:
            raise DataError(f"No valid data found in {factor_set}")
        
        # Create DataFrame
        df = pd.DataFrame(parsed_data)
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        return df
    
    def get_five_factor_model(self, start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get Fama-French 5-Factor model data.
        
        Returns:
            DataFrame with columns: Mkt-RF, SMB, HML, RMW, CMA, RF
        """
        data = self.download_factors('ff5_factors')
        
        if start_date:
            data = data[data.index >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data.index <= pd.to_datetime(end_date)]
            
        return data
    
    def get_three_factor_model(self, start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get Fama-French 3-Factor model data.
        
        Returns:
            DataFrame with columns: Mkt-RF, SMB, HML, RF
        """
        data = self.download_factors('ff3_factors')
        
        if start_date:
            data = data[data.index >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data.index <= pd.to_datetime(end_date)]
            
        return data
    
    def get_momentum_factor(self, start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get momentum factor data.
        
        Returns:
            DataFrame with MOM column
        """
        data = self.download_factors('momentum')
        
        if start_date:
            data = data[data.index >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data.index <= pd.to_datetime(end_date)]
            
        return data
    
    def get_carhart_four_factor(self, start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get Carhart 4-Factor model (FF3 + Momentum).
        
        Returns:
            DataFrame with columns: Mkt-RF, SMB, HML, MOM, RF
        """
        ff3_data = self.get_three_factor_model(start_date, end_date)
        mom_data = self.get_momentum_factor(start_date, end_date)
        
        # Combine the data
        combined = pd.concat([ff3_data, mom_data], axis=1, join='inner')
        
        return combined
    
    def calculate_factor_loadings(self, returns: pd.Series, 
                                 factor_data: pd.DataFrame,
                                 window: int = 252) -> pd.DataFrame:
        """
        Calculate rolling factor loadings (betas) for a return series.
        
        Args:
            returns: Asset return series
            factor_data: Factor return DataFrame
            window: Rolling window size (default 252 trading days = 1 year)
            
        Returns:
            DataFrame with rolling factor loadings
        """
        # Align data
        aligned_data = pd.concat([returns, factor_data], axis=1, join='inner')
        aligned_data.dropna(inplace=True)
        
        if len(aligned_data) < window:
            raise DataError(f"Insufficient data for factor loading calculation: {len(aligned_data)} < {window}")
        
        return_col = aligned_data.columns[0]
        factor_cols = aligned_data.columns[1:]
        
        # Calculate rolling regressions
        loadings = []
        
        for i in range(window, len(aligned_data) + 1):
            window_data = aligned_data.iloc[i-window:i]
            
            y = window_data[return_col]
            X = window_data[factor_cols]
            
            # Add constant for alpha
            X_with_const = pd.concat([pd.Series(1, index=X.index, name='Alpha'), X], axis=1)
            
            # OLS regression
            try:
                beta = np.linalg.lstsq(X_with_const, y, rcond=None)[0]
                
                # Calculate R-squared
                y_pred = X_with_const @ beta
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                r_squared = 1 - (ss_res / ss_tot)
                
                loading_dict = {
                    'Date': aligned_data.index[i-1],
                    'Alpha': beta[0],
                    'R_squared': r_squared
                }
                
                for j, factor in enumerate(factor_cols):
                    loading_dict[f'Beta_{factor}'] = beta[j+1]
                    
                loadings.append(loading_dict)
                
            except Exception as e:
                logger.warning(f"Failed to calculate factor loading for {aligned_data.index[i-1]}: {e}")
                continue
        
        loadings_df = pd.DataFrame(loadings)
        loadings_df.set_index('Date', inplace=True)
        
        return loadings_df
    
    def calculate_factor_attribution(self, returns: pd.Series,
                                   factor_data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate factor attribution for total return.
        
        Args:
            returns: Asset return series
            factor_data: Factor return DataFrame
            
        Returns:
            Dictionary with factor attributions
        """
        # Calculate average factor loadings
        loadings = self.calculate_factor_loadings(returns, factor_data)
        avg_loadings = loadings.mean()
        
        # Calculate factor contributions
        factor_cols = [col for col in factor_data.columns if col != 'RF']
        
        # Align data for calculation
        aligned_data = pd.concat([returns, factor_data], axis=1, join='inner')
        aligned_data.dropna(inplace=True)
        
        total_return = aligned_data.iloc[:, 0].sum()
        
        attribution = {}
        
        for factor in factor_cols:
            beta_col = f'Beta_{factor}'
            if beta_col in avg_loadings:
                factor_return = aligned_data[factor].sum()
                attribution[factor] = avg_loadings[beta_col] * factor_return
        
        # Alpha attribution
        if 'Alpha' in avg_loadings:
            attribution['Alpha'] = avg_loadings['Alpha'] * len(aligned_data)
        
        # Calculate unexplained return
        explained_return = sum(attribution.values())
        attribution['Unexplained'] = total_return - explained_return
        
        return attribution
    
    def get_factor_summary_stats(self, factor_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate summary statistics for factor data.
        
        Returns:
            DataFrame with factor statistics
        """
        stats = {}
        
        for factor in factor_data.columns:
            if factor == 'RF':
                continue
                
            factor_returns = factor_data[factor].dropna()
            
            stats[factor] = {
                'Mean': factor_returns.mean() * 252,  # Annualized
                'Std': factor_returns.std() * np.sqrt(252),  # Annualized
                'Sharpe': (factor_returns.mean() / factor_returns.std()) * np.sqrt(252),
                'Skewness': factor_returns.skew(),
                'Kurtosis': factor_returns.kurtosis(),
                'Min': factor_returns.min(),
                'Max': factor_returns.max(),
                'Count': len(factor_returns)
            }
        
        return pd.DataFrame(stats).T